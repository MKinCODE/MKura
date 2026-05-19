from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Booking, Slot, Upgradation, UpgradationStatus, SlotStatus, BookingStatus
from ..services.email_service import get_upgradation_offer_html, send_email
from ..core.config import settings
from ..database import async_session_maker


async def find_waitlist_patients(
    db: AsyncSession,
    doctor_id: int,
    date_after: datetime,
) -> List[Booking]:
    query = select(Booking).join(Slot).where(
        and_(
            Slot.doctor_id == doctor_id,
            Booking.wants_waitlist == True,
            Booking.status == BookingStatus.CONFIRMED,
            Slot.date >= date_after.date(),
        )
    ).order_by(Booking.created_at)

    result = await db.execute(query)
    return list(result.scalars().all())


async def offer_slot_to_waitlist(
    db: AsyncSession,
    slot_id: int,
    booking_id: Optional[int] = None,
) -> Optional[Upgradation]:
    slot_query = select(Slot).where(Slot.id == slot_id)
    slot_result = await db.execute(slot_query)
    slot = slot_result.scalar_one_or_none()

    if not slot or slot.status != SlotStatus.AVAILABLE:
        return None

    from app.services.slot_service import get_clinic_now
    waitlist_patients = await find_waitlist_patients(db, slot.doctor_id, get_clinic_now())

    if not waitlist_patients:
        return None

    patient = waitlist_patients[0]

    upgradation = Upgradation(
        booking_id=patient.id,
        slot_id=slot_id,
        status=UpgradationStatus.PENDING,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.UPGRADATION_TIMEOUT_MINUTES),
    )
    db.add(upgradation)
    await db.commit()
    await db.refresh(upgradation)

    base_url = settings.CLIENT_URL or "http://localhost:3000"
    accept_link = f"{base_url}/upgrade/{upgradation.id}/accept"
    decline_link = f"{base_url}/upgrade/{upgradation.id}/decline"

    slot_date = slot.date.strftime("%A, %d %B %Y")
    slot_time = slot.start_time.strftime("%I:%M %p")

    html = get_upgradation_offer_html(
        patient_name=patient.patient_name,
        doctor_name="Dr. Vikram Mehta",
        date=slot_date,
        time=slot_time,
        accept_link=accept_link,
        decline_link=decline_link,
        expires_in_minutes=settings.UPGRADATION_TIMEOUT_MINUTES,
    )

    await send_email(
        to_email=patient.patient_email,
        subject="Earlier Slot Available - MK Health Clinic",
        html_content=html,
    )

    return upgradation


async def process_upgradation_response(
    db: AsyncSession,
    upgradation_id: int,
    accept: bool,
) -> tuple[bool, str]:
    query = select(Upgradation).where(Upgradation.id == upgradation_id).options(
        selectinload(Upgradation.booking).selectinload(Booking.slot),
        selectinload(Upgradation.slot),
    )
    result = await db.execute(query)
    upgradation = result.scalar_one_or_none()

    if not upgradation:
        return False, "Upgradation offer not found"

    if upgradation.status != UpgradationStatus.PENDING:
        return False, f"Upgradation already {upgradation.status.value}"

    if datetime.utcnow() > upgradation.expires_at:
        upgradation.status = UpgradationStatus.EXPIRED
        upgradation.response_at = datetime.utcnow()
        await db.commit()
        return False, "Offer has expired"

    if accept:
        old_slot = upgradation.booking.slot
        old_slot.status = SlotStatus.AVAILABLE
        old_slot.booking_id = None

        new_slot = upgradation.slot
        new_slot.status = SlotStatus.BOOKED

        upgradation.booking.slot_id = new_slot.id
        upgradation.status = UpgradationStatus.ACCEPTED
        upgradation.response_at = datetime.utcnow()

        await db.commit()
        return True, "Slot upgraded successfully"
    else:
        upgradation.status = UpgradationStatus.DECLINED
        upgradation.response_at = datetime.utcnow()
        await db.commit()

        remaining = await find_next_waitlist_patient(db, upgradation.slot.doctor_id, upgradation.booking.id)
        if remaining:
            await offer_slot_to_waitlist(db, upgradation.slot.id, upgradation.booking.id)

        return True, "Declined successfully"


async def find_next_waitlist_patient(
    db: AsyncSession,
    doctor_id: int,
    exclude_booking_id: int,
) -> Optional[Booking]:
    query = select(Booking).join(Slot).where(
        and_(
            Slot.doctor_id == doctor_id,
            Booking.wants_waitlist == True,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.id != exclude_booking_id,
        )
    ).order_by(Booking.created_at).limit(1)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def cleanup_expired_upgradations(db: AsyncSession):
    query = select(Upgradation).where(
        and_(
            Upgradation.status == UpgradationStatus.PENDING,
            Upgradation.expires_at < datetime.utcnow(),
        )
    )
    result = await db.execute(query)
    expired = result.scalars().all()

    for upg in expired:
        upg.status = UpgradationStatus.EXPIRED
        await offer_slot_to_waitlist(db, upg.slot_id, upg.booking_id)

    if expired:
        await db.commit()

    return len(expired)