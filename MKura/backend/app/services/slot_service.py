from datetime import datetime, date, time, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models import Slot, Booking, WeeklySchedule, Doctor, SlotStatus, BookingStatus
from ..core.config import settings


async def generate_slots_for_date(db: AsyncSession, doctor_id: int, target_date: date) -> List[Slot]:
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
        await db.commit()

    return slots_to_create


async def get_or_generate_slots(db: AsyncSession, doctor_id: int, target_date: date) -> List[Slot]:
    query = select(Slot).where(
        and_(Slot.doctor_id == doctor_id, Slot.date == target_date)
    ).order_by(Slot.start_time)

    result = await db.execute(query)
    slots = result.scalars().all()

    if not slots:
        slots = await generate_slots_for_date(db, doctor_id, target_date)

    # Filter out expired slots: past dates entirely, and past times on today
    now = datetime.now()
    today = now.date()

    if target_date < today:
        return []  # Never return past-date slots

    if target_date == today:
        current_time = now.time()
        slots = [s for s in slots if s.start_time > current_time]

    return slots


async def find_earliest_available_slot(
    db: AsyncSession,
    doctor_id: Optional[int] = None,
    min_lead_time_minutes: int = 60,
) -> Optional[Slot]:
    now = datetime.now()
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

    return None


async def block_slot_with_reassignment(
    db: AsyncSession,
    slot_id: int,
) -> Tuple[bool, Optional[Booking], Optional[Slot]]:
    slot_query = select(Slot).where(Slot.id == slot_id).options(selectinload(Slot.booking))
    result = await db.execute(slot_query)
    slot = result.scalar_one_or_none()

    if not slot:
        return False, None, None

    if slot.booking and slot.booking.status == BookingStatus.CONFIRMED:
        patient_booking = slot.booking
        new_slot = await find_next_available_slot(
            db, slot.doctor_id, slot.date, slot.start_time
        )

        if new_slot:
            patient_booking.slot_id = new_slot.id
            new_slot.status = SlotStatus.BOOKED
            slot.status = SlotStatus.BLOCKED
            await db.commit()
            return True, patient_booking, new_slot
        else:
            slot.status = SlotStatus.BLOCKED
            patient_booking.status = BookingStatus.CANCELLED
            await db.commit()
            return True, patient_booking, None
    else:
        slot.status = SlotStatus.BLOCKED
        await db.commit()
        return True, None, None


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