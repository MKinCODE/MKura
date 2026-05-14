from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List

from app.database import get_db
from app.models import Slot, Doctor
from app.schemas import ChatMessage, ChatResponse
from app.services.slot_service import find_earliest_available_slot
from app.agents.booking_agent import booking_agent_service
from app.core.rate_limit import check_rate_limit
from app.core.config import settings
from app.api.deps import get_current_doctor

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    message: ChatMessage,
    db: AsyncSession = Depends(get_db),
):
    passed, remaining = await check_rate_limit(
        f"chat:{message.session_id or 'anonymous'}",
        settings.RATE_LIMIT_CHAT,
        settings.RATE_LIMIT_WINDOW_SECONDS,
    )

    if not passed:
        raise HTTPException(status_code=429, detail="Too many messages. Please wait a moment.")

    session_id = message.session_id

    response_data = booking_agent_service.process_message(
        message=message.message,
        session_id=session_id,
    )

    response_text = response_data.get("response", "")

    if response_data.get("stage") == "slot_selection" and response_data.get("session_id"):
        agent = booking_agent_service.get_or_create_session(response_data["session_id"])
        agent.stage = "slot_selection"

        slot = await find_earliest_available_slot(db)

        if slot:
            await db.refresh(slot, ["doctor"])
            slot_date = slot.date.strftime("%A, %d %B %Y")
            slot_time = slot.start_time.strftime("%I:%M %p")

            slot_info = {
                "id": slot.id,
                "doctor_name": slot.doctor.name,
                "specialization": slot.doctor.specialization,
                "date": slot_date,
                "time": slot_time,
            }

            response_text = (
                f"I found the earliest available slot:\n\n"
                f"📅 {slot_date}\n"
                f"⏰ {slot_time}\n"
                f"👨‍⚕️ {slot.doctor.name} ({slot.doctor.specialization})\n\n"
                f"Type YES to confirm or CANCEL to cancel."
            )

            booking_agent_service.set_slot_info(agent, slot_info)

            return ChatResponse(
                response=response_text,
                session_id=agent.session_id,
                action="show_slot",
                data=slot_info,
            )

    return ChatResponse(
        response=response_text,
        session_id=response_data.get("session_id", session_id or "new"),
        action=response_data.get("action"),
        data=response_data.get("data"),
    )


@router.get("/slots/earliest")
async def get_earliest_slot_info(
    db: AsyncSession = Depends(get_db),
):
    slot = await find_earliest_available_slot(db)

    if not slot:
        raise HTTPException(status_code=404, detail="No slots available")

    await db.refresh(slot, ["doctor"])

    return {
        "id": slot.id,
        "doctor_name": slot.doctor.name,
        "specialization": slot.doctor.specialization,
        "date": slot.date.strftime("%A, %d %B %Y"),
        "time": slot.start_time.strftime("%I:%M %p"),
    }


@router.get("/doctors")
async def get_doctors(db: AsyncSession = Depends(get_db)):
    query = select(Doctor).where(Doctor.is_active == True)
    result = await db.execute(query)
    doctors = result.scalars().all()

    return [
        {
            "id": doc.id,
            "name": doc.name,
            "specialization": doc.specialization,
            "degrees": doc.degrees,
            "experience": doc.experience,
            "bio": doc.bio,
        }
        for doc in doctors
    ]