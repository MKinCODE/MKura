from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app.models import Slot, Booking, SlotStatus, BookingStatus, PaymentStatus, Doctor
from app.schemas import SlotResponse, BookingCreate, BookingResponse, BlockSlotRequest
from app.services.slot_service import get_or_generate_slots, find_earliest_available_slot, block_slot_with_reassignment
from app.services.email_service import send_email, get_booking_confirmation_html, get_reschedule_notification_html
from app.core.config import settings
from app.api.deps import get_current_doctor

router = APIRouter()


@router.get("/available", response_model=List[SlotResponse])
async def get_available_slots(
    doctor_id: Optional[int] = None,
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    from app.services.slot_service import get_clinic_now
    now = get_clinic_now()
    today = now.date()

    if target_date:
        # Never return slots for past dates
        if target_date < today:
            return []
        slots = await get_or_generate_slots(db, doctor_id or 1, target_date)
        return [s for s in slots if s.status == SlotStatus.AVAILABLE]

    min_time = now + timedelta(minutes=settings.MIN_LEAD_TIME_MINUTES)
    slots = []
    current_date = max(min_time.date(), today)  # Never go before today

    for _ in range(settings.MAX_ADVANCE_BOOKING_DAYS):
        doctor_query = select(Doctor).where(Doctor.is_active == True)
        if doctor_id:
            doctor_query = doctor_query.where(Doctor.id == doctor_id)
        doctor_result = await db.execute(doctor_query)
        doctors = doctor_result.scalars().all()

        for doc in doctors:
            day_slots = await get_or_generate_slots(db, doc.id, current_date)
            slots.extend([s for s in day_slots if s.status == SlotStatus.AVAILABLE])

        if slots:
            break
        current_date += timedelta(days=1)

    return slots


@router.get("/earliest")
async def get_earliest_slot(
    doctor_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    slot = await find_earliest_available_slot(db, doctor_id)

    if not slot:
        raise HTTPException(status_code=404, detail="No available slots found")

    await db.refresh(slot, ["doctor"])
    return {
        "id": slot.id,
        "doctor_id": slot.doctor_id,
        "date": slot.date.isoformat(),
        "start_time": slot.start_time.strftime("%H:%M"),
        "end_time": slot.end_time.strftime("%H:%M"),
        "doctor_name": slot.doctor.name,
        "specialization": slot.doctor.specialization,
    }


@router.post("/block")
async def block_slot(
    request: BlockSlotRequest,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    slot_query = select(Slot).where(
        and_(Slot.id == request.slot_id, Slot.doctor_id == doctor.id)
    ).options()
    result = await db.execute(slot_query)
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    success, booking, new_slot = await block_slot_with_reassignment(db, request.slot_id)

    if booking and new_slot:
        old_date = slot.date.strftime("%A, %d %B %Y")
        old_time = slot.start_time.strftime("%I:%M %p")
        new_date = new_slot.date.strftime("%A, %d %B %Y")
        new_time = new_slot.start_time.strftime("%I:%M %p")

        base_url = settings.CLIENT_URL or "http://localhost:3000"
        cancel_link = f"{base_url}/cancel/{booking.id}/{booking.cancellation_token}"

        html = get_reschedule_notification_html(
            patient_name=booking.patient_name,
            old_date=old_date,
            old_time=old_time,
            new_date=new_date,
            new_time=new_time,
            doctor_name=doctor.name,
            cancellation_link=cancel_link,
        )
        await send_email(
            to_email=booking.patient_email,
            subject="[MK Health Clinic] Appointment Rescheduled",
            html_content=html,
        )
        return {"message": "Slot blocked. Patient has been rescheduled.", "rescheduled": True}

    elif booking and not new_slot:
        base_url = settings.CLIENT_URL or "http://localhost:3000"
        cancel_link = f"{base_url}/cancel/{booking.id}/{booking.cancellation_token}"
        html = get_reschedule_notification_html(
            patient_name=booking.patient_name,
            old_date=slot.date.strftime("%A, %d %B %Y"),
            old_time=slot.start_time.strftime("%I:%M %p"),
            new_date="To be announced",
            new_time="We will contact you",
            doctor_name=doctor.name,
            cancellation_link=cancel_link,
        )
        await send_email(
            to_email=booking.patient_email,
            subject="[MK Health Clinic] Appointment Cancelled",
            html_content=html,
        )
        return {"message": "Slot blocked. Patient has been notified.", "rescheduled": False, "cancelled": True}

    return {"message": "Slot blocked successfully."}


from datetime import timedelta