from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, timedelta
import secrets

from app.database import get_db
from app.models import Slot, Booking, Doctor, SlotStatus, BookingStatus, PaymentStatus
from app.schemas import BookingResponse, CancellationConfirm
from app.services.email_service import send_email, get_booking_confirmation_html, get_cancellation_confirmed_html
from app.services.payment_service import create_payment_intent, refund_payment
from app.services.slot_service import find_earliest_available_slot
from app.agents.upgradation_agent import offer_slot_to_waitlist
from app.core.config import settings
from app.api.deps import get_current_doctor

router = APIRouter()


@router.post("/create", response_model=dict)
async def create_booking(
    slot_id: int,
    patient_name: str,
    patient_email: str,
    patient_phone: str,
    wants_waitlist: bool = False,
    db: AsyncSession = Depends(get_db),
):
    slot_query = select(Slot).where(Slot.id == slot_id).options()
    result = await db.execute(slot_query)
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot.status != SlotStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="Slot is not available")

    booking = Booking(
        slot_id=slot_id,
        patient_name=patient_name,
        patient_email=patient_email,
        patient_phone=patient_phone,
        status=BookingStatus.CONFIRMED,
        payment_status=PaymentStatus.PENDING,
        wants_waitlist=wants_waitlist,
        cancellation_token=secrets.token_urlsafe(32),
        cancellation_token_expires=datetime.utcnow() + timedelta(days=30),
    )
    db.add(booking)

    slot.status = SlotStatus.BOOKED
    await db.commit()
    await db.refresh(booking, ["slot"])
    await db.refresh(booking.slot, ["doctor"])

    client_secret, payment_intent_id = create_payment_intent()

    booking.payment_intent_id = payment_intent_id
    await db.commit()

    return {
        "booking_id": booking.id,
        "client_secret": client_secret,
        "slot_id": slot_id,
    }


@router.post("/{booking_id}/confirm-payment")
async def confirm_payment(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
):
    booking_query = select(Booking).where(Booking.id == booking_id).options()
    result = await db.execute(booking_query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.payment_status = PaymentStatus.PAID
    await db.commit()
    await db.refresh(booking, ["slot"])

    slot = booking.slot
    slot_date = slot.date.strftime("%A, %d %B %Y")
    slot_time = slot.start_time.strftime("%I:%M %p")

    await db.refresh(slot, ["doctor"])
    doctor = slot.doctor

    base_url = settings.CLIENT_URL or "http://localhost:3000"
    cancel_link = f"{base_url}/cancel/{booking.id}/{booking.cancellation_token}"

    html = get_booking_confirmation_html(
        patient_name=booking.patient_name,
        doctor_name=doctor.name,
        specialization=doctor.specialization,
        date=slot_date,
        time=slot_time,
        clinic_address=doctor.clinic_address or settings.CLINIC_ADDRESS,
        cancellation_link=cancel_link,
        clinic_phone=settings.CLINIC_PHONE,
    )

    await send_email(
        to_email=booking.patient_email,
        subject="Appointment Confirmed - MK Health Clinic",
        html_content=html,
    )

    return {"message": "Payment confirmed and booking completed"}


@router.get("/{booking_id}/cancel/{token}")
async def validate_cancellation_token(
    booking_id: int,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    booking_query = select(Booking).where(
        and_(Booking.id == booking_id, Booking.cancellation_token == token)
    ).options()
    result = await db.execute(booking_query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Invalid cancellation link")

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Booking already cancelled")

    await db.refresh(booking, ["slot"])
    await db.refresh(booking.slot, ["doctor"])

    return {
        "booking_id": booking.id,
        "patient_name": booking.patient_name,
        "date": booking.slot.date.strftime("%A, %d %B %Y"),
        "time": booking.slot.start_time.strftime("%I:%M %p"),
        "doctor_name": booking.slot.doctor.name,
        "valid": True,
    }


@router.post("/{booking_id}/cancel/{token}")
async def cancel_booking(
    booking_id: int,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    booking_query = select(Booking).where(
        and_(Booking.id == booking_id, Booking.cancellation_token == token)
    ).options()
    result = await db.execute(booking_query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Invalid cancellation link")

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Booking already cancelled")

    booking.status = BookingStatus.CANCELLED

    await db.refresh(booking, ["slot"])
    slot = booking.slot
    slot.status = SlotStatus.AVAILABLE

    if booking.payment_status == PaymentStatus.PAID and booking.payment_intent_id:
        try:
            refund_payment(booking.payment_intent_id)
            booking.payment_status = PaymentStatus.REFUNDED
        except Exception:
            pass

    await db.commit()

    html = get_cancellation_confirmed_html(booking.patient_name)
    await send_email(
        to_email=booking.patient_email,
        subject="Appointment Cancelled - MK Health Clinic",
        html_content=html,
    )

    if booking.wants_waitlist:
        await offer_slot_to_waitlist(db, slot.id)

    return {"message": "Booking cancelled successfully"}


@router.get("/doctor/all", response_model=List[BookingResponse])
async def get_doctor_bookings(
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    bookings_query = select(Booking).join(Slot).where(
        and_(
            Slot.doctor_id == doctor.id,
            Booking.status == BookingStatus.CONFIRMED,
        )
    ).order_by(Slot.date, Slot.start_time)

    result = await db.execute(bookings_query)
    bookings = result.scalars().all()
    return bookings


@router.get("/doctor/slots")
async def get_doctor_slots_with_bookings(
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    from app.services.slot_service import get_clinic_now
    now = get_clinic_now()
    start_date = now.date()
    end_date = start_date + timedelta(days=7)

    slots_query = select(Slot).where(
        and_(
            Slot.doctor_id == doctor.id,
            Slot.date >= start_date,
            Slot.date <= end_date,
        )
    ).order_by(Slot.date, Slot.start_time)

    result = await db.execute(slots_query)
    slots = result.scalars().all()

    # Filter out expired same-day slots
    filtered = []
    for slot in slots:
        if slot.date == start_date and slot.start_time <= now.time():
            continue  # Skip past slots for today
        filtered.append(slot)

    return [
        {
            "id": slot.id,
            "date": slot.date.isoformat(),
            "start_time": slot.start_time.strftime("%H:%M"),
            "end_time": slot.end_time.strftime("%H:%M"),
            "status": slot.status.value,
            "patient_name": slot.booking.patient_name if slot.booking else None,
            "patient_email": slot.booking.patient_email if slot.booking else None,
        }
        for slot in filtered
    ]