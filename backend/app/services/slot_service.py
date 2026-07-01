from datetime import datetime, date, time, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import select, and_, or_, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models import Slot, Booking, WeeklySchedule, Doctor, SlotStatus, BookingStatus, Upgradation
from ..core.config import settings


def get_clinic_now() -> datetime:
    from datetime import timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).replace(tzinfo=None)


async def cleanup_past_empty_slots(db: AsyncSession):
    from ..models import Slot, Booking, Upgradation, SlotStatus
    from sqlalchemy import exists
    now = get_clinic_now()
    today = now.date()
    current_time = now.time()

    booking_exists = exists().where(Booking.slot_id == Slot.id)
    upgradation_exists = exists().where(Upgradation.slot_id == Slot.id)

    query_past_days = delete(Slot).where(
        and_(
            Slot.date < today,
            Slot.status == SlotStatus.AVAILABLE,
            ~booking_exists,
            ~upgradation_exists
        )
    )
    query_today_passed = delete(Slot).where(
        and_(
            Slot.date == today,
            Slot.start_time <= current_time,
            Slot.status == SlotStatus.AVAILABLE,
            ~booking_exists,
            ~upgradation_exists
        )
    )

    await db.execute(query_past_days)
    await db.execute(query_today_passed)


async def generate_slots_for_date(
    db: AsyncSession,
    doctor_id: int,
    target_date: date,
    existing_slots: Optional[List[Slot]] = None,
) -> List[Slot]:
    day_of_week = target_date.weekday()
    schedule_query = select(WeeklySchedule).where(
        and_(
            WeeklySchedule.doctor_id == doctor_id,
            WeeklySchedule.day_of_week == day_of_week,
            WeeklySchedule.is_active == True,
        )
    )
    result = await db.execute(schedule_query)
    schedule = result.scalar_one_or_none()

    if not schedule:
        return []

    slots_to_create = []
    current_time = datetime.combine(target_date, schedule.start_time)
    end_datetime = datetime.combine(target_date, schedule.end_time)
    slot_duration = timedelta(minutes=settings.SLOT_DURATION_MINUTES)

    if existing_slots is None:
        existing_query = select(Slot).where(
            and_(Slot.doctor_id == doctor_id, Slot.date == target_date)
        )
        existing_result = await db.execute(existing_query)
        existing_slots = existing_result.scalars().all()
    existing_times = {(s.date, s.start_time) for s in existing_slots}

    while current_time + slot_duration <= end_datetime:
        slot_time = current_time.time()
        if (target_date, slot_time) not in existing_times:
            slot = Slot(
                doctor_id=doctor_id,
                date=target_date,
                start_time=slot_time,
                end_time=(current_time + slot_duration).time(),
                status=SlotStatus.AVAILABLE,
            )
            slots_to_create.append(slot)
        current_time += slot_duration

    if slots_to_create:
        db.add_all(slots_to_create)
        await db.flush()

    return slots_to_create


async def get_or_generate_slots(
    db: AsyncSession,
    doctor_id: int,
    target_date: date,
    run_cleanup: bool = False,
) -> List[Slot]:
    if run_cleanup:
        pass

    query = select(Slot).where(
        and_(Slot.doctor_id == doctor_id, Slot.date == target_date)
    ).order_by(Slot.start_time)

    result = await db.execute(query)
    slots = result.scalars().all()

    if not slots:
        slots = await generate_slots_for_date(db, doctor_id, target_date, existing_slots=slots)

    now = get_clinic_now()
    today = now.date()

    if target_date < today:
        return []

    if target_date == today:
        current_time = now.time()
        slots = [s for s in slots if s.start_time > current_time]

    return slots


async def find_earliest_available_slot(
    db: AsyncSession,
    doctor_id: Optional[int] = None,
    min_lead_time_minutes: int = 60,
) -> Optional[Slot]:
    now = get_clinic_now()
    min_booking_time = now + timedelta(minutes=min_lead_time_minutes)

    cutoff_time = datetime.combine(min_booking_time.date(), datetime.min.time()).replace(
        hour=settings.SAME_DAY_CUTOFF_HOUR
    )
    if min_booking_time.date() == now.date() and min_booking_time < cutoff_time:
        search_start = min_booking_time
    else:
        search_start = datetime.combine(
            min_booking_time.date(),
            datetime.min.time().replace(hour=settings.CLINIC_OPEN_HOUR),
        ) + timedelta(days=1 if min_booking_time.hour >= settings.CLINIC_CLOSE_HOUR else 0)

    current_date = search_start.date()
    max_date = current_date + timedelta(days=settings.MAX_ADVANCE_BOOKING_DAYS)

    doctor_query = select(Doctor).where(Doctor.is_active == True)
    if doctor_id:
        doctor_query = doctor_query.where(Doctor.id == doctor_id)
    doctor_result = await db.execute(doctor_query)
    doctors = doctor_result.scalars().all()

    while current_date <= max_date:
        for doc in doctors:
            slots = await get_or_generate_slots(db, doc.id, current_date)
            for slot in slots:
                if slot.status != SlotStatus.AVAILABLE:
                    continue
                slot_datetime = datetime.combine(slot.date, slot.start_time)
                if slot_datetime <= min_booking_time:
                    continue
                if slot_datetime.hour < settings.CLINIC_OPEN_HOUR or slot_datetime.hour >= settings.CLINIC_CLOSE_HOUR:
                    continue
                return slot

        current_date += timedelta(days=1)

    # Edge case: No slots available in MAX_ADVANCE_BOOKING_DAYS. Generate a slot 1 hour in the future.
    if doctors:
        doc = doctors[0]
        slot_dt = now + timedelta(hours=1)
        minutes_to_add = (10 - slot_dt.minute % 10) % 10
        slot_dt += timedelta(minutes=minutes_to_add)
        slot_dt = slot_dt.replace(second=0, microsecond=0)

        if slot_dt.hour < settings.CLINIC_OPEN_HOUR:
            slot_dt = slot_dt.replace(hour=settings.CLINIC_OPEN_HOUR, minute=0)
        elif slot_dt.hour >= settings.CLINIC_CLOSE_HOUR:
            slot_dt = slot_dt + timedelta(days=1)
            slot_dt = slot_dt.replace(hour=settings.CLINIC_OPEN_HOUR, minute=0)

        existing_query = select(Slot).where(
            and_(
                Slot.doctor_id == doc.id,
                Slot.date == slot_dt.date(),
                Slot.start_time == slot_dt.time()
            )
        )
        existing_result = await db.execute(existing_query)
        existing_slot = existing_result.scalars().first()

        if existing_slot:
            if existing_slot.status == SlotStatus.AVAILABLE:
                return existing_slot
            slot_dt += timedelta(minutes=settings.SLOT_DURATION_MINUTES)

        new_slot = Slot(
            doctor_id=doc.id,
            date=slot_dt.date(),
            start_time=slot_dt.time(),
            end_time=(slot_dt + timedelta(minutes=settings.SLOT_DURATION_MINUTES)).time(),
            status=SlotStatus.AVAILABLE,
        )
        db.add(new_slot)
        await db.flush()
        await db.refresh(new_slot, ["doctor"])
        return new_slot

    return None


async def block_slot_with_reassignment(
    db: AsyncSession,
    slot_id: int,
) -> Tuple[bool, List[Tuple[Booking, Slot, Optional[Slot]]]]:
    slot_query = select(Slot).where(Slot.id == slot_id).options(selectinload(Slot.booking))
    result = await db.execute(slot_query)
    slot = result.scalar_one_or_none()

    if not slot:
        return False, []

    if slot.status == SlotStatus.BLOCKED:
        return True, []

    if not (slot.booking and slot.booking.status == BookingStatus.CONFIRMED):
        slot.status = SlotStatus.BLOCKED
        await db.commit()
        return True, []

    # Get all subsequent slots for this doctor chronologically.
    all_slots_query = select(Slot).where(
        and_(
            Slot.doctor_id == slot.doctor_id,
            or_(
                Slot.date > slot.date,
                and_(Slot.date == slot.date, Slot.start_time >= slot.start_time)
            )
        )
    ).order_by(Slot.date, Slot.start_time).options(selectinload(Slot.booking))
    
    result = await db.execute(all_slots_query)
    loaded_slots = list(result.scalars().all())

    start_idx = -1
    for idx, s in enumerate(loaded_slots):
        if s.id == slot_id:
            start_idx = idx
            break
            
    if start_idx == -1:
        return False, []

    loaded_slots = loaded_slots[start_idx:]

    shift_slots = [loaded_slots[0]]
    found_available = False

    for s in loaded_slots[1:]:
        if s.status == SlotStatus.BLOCKED:
            continue
        if s.status == SlotStatus.AVAILABLE:
            shift_slots.append(s)
            found_available = True
            break
        elif s.status == SlotStatus.BOOKED:
            shift_slots.append(s)

    if not found_available:
        last_date = loaded_slots[-1].date if loaded_slots else slot.date
        current_date = last_date + timedelta(days=1)
        max_search_date = slot.date + timedelta(days=settings.MAX_ADVANCE_BOOKING_DAYS)
        
        while current_date <= max_search_date and not found_available:
            new_day_slots = await get_or_generate_slots(db, slot.doctor_id, current_date)
            new_day_slots = sorted(new_day_slots, key=lambda x: x.start_time)
            
            for s in new_day_slots:
                if s.status == SlotStatus.BLOCKED:
                    continue
                if s.status == SlotStatus.AVAILABLE:
                    shift_slots.append(s)
                    found_available = True
                    break
                elif s.status == SlotStatus.BOOKED:
                    shift_slots.append(s)
            current_date += timedelta(days=1)

    bookings_to_shift = [s.booking for s in shift_slots]
    bookings_to_shift = [b for b in bookings_to_shift if b is not None]

    reassignments = []
    slot.status = SlotStatus.BLOCKED

    if found_available:
        for i in range(len(bookings_to_shift)):
            booking = bookings_to_shift[i]
            old_slot = shift_slots[i]
            new_slot = shift_slots[i + 1]
            
            booking.slot_id = new_slot.id
            new_slot.status = SlotStatus.BOOKED
            
            reassignments.append((booking, old_slot, new_slot))
    else:
        for i in range(len(bookings_to_shift) - 1):
            booking = bookings_to_shift[i]
            old_slot = shift_slots[i]
            new_slot = shift_slots[i + 1]
            
            booking.slot_id = new_slot.id
            new_slot.status = SlotStatus.BOOKED
            
            reassignments.append((booking, old_slot, new_slot))
            
        last_booking = bookings_to_shift[-1]
        old_slot = shift_slots[-1]
        
        last_booking.status = BookingStatus.CANCELLED
        last_booking.slot_id = slot.id
        
        reassignments.append((last_booking, old_slot, None))

    await db.commit()
    return True, reassignments


async def find_next_available_slot(
    db: AsyncSession,
    doctor_id: int,
    after_date: date,
    after_time: time,
) -> Optional[Slot]:
    query = select(Slot).where(
        and_(
            Slot.doctor_id == doctor_id,
            Slot.date >= after_date,
            Slot.status == SlotStatus.AVAILABLE,
            or_(Slot.date > after_date, Slot.start_time > after_time),
        )
    ).order_by(Slot.date, Slot.start_time).limit(1)

    result = await db.execute(query)
    return result.scalar_one_or_none()