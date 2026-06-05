from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from .nlp import (
    extract_email,
    extract_phone,
    extract_name,
    classify_intent,
    ConfirmationIntent,
    extract_name_smart,
    extract_entities_with_llm,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

groq_client = None
if settings.GROQ_API_KEY:
    try:
        from groq import Groq
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("Groq client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Groq client: {e}")


class BookingStage(str, Enum):
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    SLOT_SELECTION = "slot_selection"
    WAITLIST_PROMPT = "waitlist_prompt"
    PAYMENT = "payment"
    COMPLETE = "complete"


@dataclass
class BookingData:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    wants_waitlist: Optional[bool] = None
    confirmed_slot_id: Optional[int] = None
    selected_slot_info: Optional[Dict[str, Any]] = None


@dataclass
class BookingAgent:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stage: BookingStage = BookingStage.NAME
    data: BookingData = field(default_factory=BookingData)
    messages: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def reset(self):
        self.stage = BookingStage.NAME
        self.data = BookingData()
        self.messages = []
        self.context = {}

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def get_last_user_message(self) -> Optional[str]:
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg["content"]
        return None


class BookingAgentService:
    def __init__(self):
        self.sessions: Dict[str, BookingAgent] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> BookingAgent:
        # Fallback sync version for backward compatibility if any
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        agent = BookingAgent()
        if session_id:
            agent.session_id = session_id
        self.sessions[agent.session_id] = agent
        return agent

    async def load_session_from_db(self, db: AsyncSession, session_id: str) -> Optional[BookingAgent]:
        from app.models.models import ChatSession
        from sqlalchemy import select
        import json
        
        try:
            result = await db.execute(select(ChatSession).filter_by(session_id=session_id))
            db_session = result.scalars().first()
            if not db_session:
                return None
                
            agent = BookingAgent(
                session_id=db_session.session_id,
                stage=BookingStage(db_session.stage),
                data=BookingData(
                    name=db_session.patient_name,
                    email=db_session.patient_email,
                    phone=db_session.patient_phone,
                    confirmed_slot_id=db_session.confirmed_slot_id,
                    wants_waitlist=db_session.wants_waitlist,
                ),
                messages=json.loads(db_session.messages) if db_session.messages else [],
                context={}
            )
            return agent
        except Exception as e:
            logger.error(f"Error loading session {session_id} from DB: {e}")
            return None

    async def save_session_to_db(self, db: AsyncSession, agent: BookingAgent):
        from app.models.models import ChatSession
        from sqlalchemy import select
        import json
        
        try:
            result = await db.execute(select(ChatSession).filter_by(session_id=agent.session_id))
            db_session = result.scalars().first()
            
            messages_json = json.dumps(agent.messages)
            
            if db_session:
                db_session.stage = agent.stage.value
                db_session.patient_name = agent.data.name
                db_session.patient_email = agent.data.email
                db_session.patient_phone = agent.data.phone
                db_session.confirmed_slot_id = agent.data.confirmed_slot_id
                db_session.wants_waitlist = agent.data.wants_waitlist
                db_session.messages = messages_json
            else:
                db_session = ChatSession(
                    session_id=agent.session_id,
                    stage=agent.stage.value,
                    patient_name=agent.data.name,
                    patient_email=agent.data.email,
                    patient_phone=agent.data.phone,
                    confirmed_slot_id=agent.data.confirmed_slot_id,
                    wants_waitlist=agent.data.wants_waitlist,
                    messages=messages_json
                )
                db.add(db_session)
                
            await db.commit()
        except Exception as e:
            logger.error(f"Error saving session {agent.session_id} to DB: {e}")

    async def get_or_create_session_async(self, db: AsyncSession, session_id: Optional[str] = None) -> BookingAgent:
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
            
        if session_id:
            agent = await self.load_session_from_db(db, session_id)
            if agent:
                self.sessions[session_id] = agent
                return agent
                
        agent = BookingAgent()
        if session_id:
            agent.session_id = session_id
            
        await self.save_session_to_db(db, agent)
        self.sessions[agent.session_id] = agent
        return agent

    async def process_message(
        self,
        db: AsyncSession,
        message: str,
        session_id: Optional[str] = None,
        slot_info: Optional[Dict[str, Any]] = None,
        payment_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        agent = await self.get_or_create_session_async(db, session_id)
        message = message.strip()
        agent.add_message("user", message)

        if agent.stage == BookingStage.SLOT_SELECTION:
            res = self._handle_slot_selection(agent, message)
        elif agent.stage == BookingStage.WAITLIST_PROMPT:
            res = self._handle_waitlist_prompt(agent, message)
        elif agent.stage == BookingStage.PAYMENT:
            if payment_status == "success" or message.lower() == "payment_success":
                res = self._handle_payment_success(agent)
            else:
                res = {"response": "Please complete the payment to confirm your booking.", "session_id": agent.session_id, "stage": agent.stage.value}
        elif agent.stage == BookingStage.COMPLETE:
            res = {
                "response": "Your booking is already complete. If you need to cancel, please use the cancellation link in your confirmation email.",
                "session_id": agent.session_id,
                "stage": agent.stage.value,
            }
        else:
            res = self._collect_information(agent, message)

        await self.save_session_to_db(db, agent)
        return res

    def _collect_information(self, agent: BookingAgent, message: str) -> Dict[str, Any]:
        # Track what we had before extracting
        had_name = bool(agent.data.name)
        had_email = bool(agent.data.email)
        had_phone = bool(agent.data.phone)

        # 1. Run LLM-based entity extraction as a primary pass
        extracted = {}
        if groq_client:
            extracted = extract_entities_with_llm(message)
            
        # 2. Update agent data from LLM extraction
        if extracted.get("name") and not agent.data.name:
            agent.data.name = extracted["name"].title()
        if extracted.get("phone") and not agent.data.phone:
            from .nlp import validate_phone
            if validate_phone(extracted["phone"]):
                agent.data.phone = extracted["phone"]

        # 3. Fallback/Regex extraction for anything still missing
        raw_email = extracted.get("email") or extract_email(message)
        if raw_email and not agent.data.email:
            from .nlp import validate_email
            if validate_email(raw_email):
                agent.data.email = raw_email.lower()
                agent.context.pop("email_error", None)
            else:
                agent.context["email_error"] = True

        if not agent.data.phone:
            phone = extract_phone(message)
            if phone:
                agent.data.phone = phone

        if not agent.data.name:
            name = extract_name_smart(message)
            if name:
                agent.data.name = name.title()

        # Track what we have now
        has_name = bool(agent.data.name)
        has_email = bool(agent.data.email)
        has_phone = bool(agent.data.phone)

        # 4. Determine current stage and response based on what is missing
        if not has_name:
            agent.stage = BookingStage.NAME
            instruction = (
                "The user is booking an appointment but hasn't provided a valid full name. "
                "Politely request their full name (e.g. John Doe). Do not ask for email or phone yet. "
                "Keep the response brief."
            )
            response = self._get_groq_fallback(message, instruction)
            
        elif not has_email:
            agent.stage = BookingStage.EMAIL
            if agent.context.get("email_error"):
                response = "I'm sorry, but that email address could not be verified (invalid format or unreachable domain). Please enter a valid, active email address."
                agent.context.pop("email_error", None)
            elif not had_name:
                response = f"Thank you, {agent.data.name}! Could you please provide your email address so we can send you appointment confirmations?"
            else:
                instruction = (
                    f"The user's name is {agent.data.name}. Politely ask them to provide their email address "
                    f"so we can send appointment confirmations. Do not ask for name or phone. Keep the response brief."
                )
                response = self._get_groq_fallback(message, instruction)
            
        elif not has_phone:
            agent.stage = BookingStage.PHONE
            if not had_email or not had_name:
                response = f"Got it, thanks! To keep you updated on your appointments and for any urgent notifications, could you please share your phone number?"
            else:
                instruction = (
                    f"The user has provided their name ({agent.data.name}) and email ({agent.data.email}). "
                    f"Politely ask them for their phone number for urgent notifications. Do not ask for name or email. Keep it brief."
                )
                response = self._get_groq_fallback(message, instruction)
            
        else:
            # Everything is gathered! Move to slot selection.
            agent.stage = BookingStage.SLOT_SELECTION
            response = (
                f"PERFECT! I've recorded your details:\n👤 Name: {agent.data.name}\n✉️ Email: {agent.data.email}\n📞 Phone: {agent.data.phone}\n\n"
                f"I'll now find the earliest available slot for you."
            )
            agent.context["search_slots"] = True

        agent.add_message("assistant", response)
        return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}

    def _get_groq_fallback(self, user_message: str, instruction: str) -> str:
        is_name_stage = "request their full name" in instruction or "ask them for their name" in instruction
        is_email_stage = "provide their email" in instruction or "ask them for their email" in instruction
        is_phone_stage = "phone number" in instruction
        
        if not groq_client:
            if is_name_stage:
                return "I didn't catch your name. Could you please tell me your full name?"
            elif is_email_stage:
                return "I couldn't find a valid email. Please enter your email address (e.g., name@example.com)"
            elif is_phone_stage:
                return "I couldn't find a valid phone number. Please enter your 10-digit phone number."
            return "Please provide the requested information."

        try:
            system_prompt = (
                "You are MKura, a friendly healthcare scheduling assistant at MK Health Clinic. "
                f"{instruction} "
                "Be concise, polite, and guide the user to provide the required information."
            )
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            if is_name_stage:
                return "I didn't catch your name. Could you please tell me your full name?"
            elif is_email_stage:
                return "I couldn't find a valid email. Please enter your email address (e.g., name@example.com)"
            elif is_phone_stage:
                return "I couldn't find a valid phone number. Please enter your 10-digit phone number."
            return "Please provide the requested information."

    def _handle_slot_selection(self, agent: BookingAgent, message: str) -> Dict[str, Any]:
        intent = classify_intent(message)

        if intent == "confirm":
            agent.stage = BookingStage.PAYMENT
            agent.context["confirmed_slot"] = True
            response = (
                "To confirm your booking, a refundable deposit of ₹100 is required.\n\n"
                "🧪 *Demo/Test Payment – No real charges are made.*\n\n"
                "You'll be redirected to complete payment."
            )
            agent.add_message("assistant", response)
            return {
                "response": response,
                "session_id": agent.session_id,
                "stage": agent.stage.value,
                "action": "redirect_payment",
                "data": {
                    "patient_name": agent.data.name,
                    "patient_email": agent.data.email,
                    "patient_phone": agent.data.phone,
                    "slot_id": agent.data.confirmed_slot_id,
                },
            }

        if intent == "cancel":
            agent.stage = BookingStage.COMPLETE
            response = "No problem! Your booking has been cancelled. If you change your mind, feel free to book again."
            agent.add_message("assistant", response)
            return {"response": response, "session_id": agent.session_id, "stage": "cancelled"}

        agent.add_message("assistant", "Please type YES to confirm or CANCEL to cancel the slot.")
        return {"response": "I didn't understand that. Type YES to confirm or CANCEL to cancel.", "session_id": agent.session_id, "stage": agent.stage.value}

    def _handle_waitlist_prompt(self, agent: BookingAgent, message: str) -> Dict[str, Any]:
        intent = classify_intent(message)

        if intent in ["waitlist_yes", "confirm"]:
            agent.data.wants_waitlist = True
        elif intent in ["waitlist_no", "cancel"]:
            agent.data.wants_waitlist = False
        else:
            response = "Please answer YES to join the waitlist or NO to skip."
            agent.add_message("assistant", response)
            return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}

        agent.stage = BookingStage.COMPLETE
        response = (
            "Thank you! Your booking is confirmed and a confirmation email has been sent to your specified email address.\n\n"
            "We look forward to seeing you! Take care! 👋"
        )
        agent.add_message("assistant", response)
        return {
            "response": response,
            "session_id": agent.session_id,
            "stage": "complete",
            "action": "complete",
            "data": {
                "patient_name": agent.data.name,
                "patient_email": agent.data.email,
                "patient_phone": agent.data.phone,
                "wants_waitlist": agent.data.wants_waitlist,
                "slot_id": agent.data.confirmed_slot_id,
            },
        }

    def _handle_payment_success(self, agent: BookingAgent) -> Dict[str, Any]:
        agent.stage = BookingStage.WAITLIST_PROMPT
        response = (
            "🎉 Payment successful! Your appointment is confirmed!\n\n"
            "Would you like to join our waitlist for earlier slots? "
            "If someone cancels, we'll offer you the earlier slot first.\n\n"
            "Type YES to join or NO to skip."
        )
        agent.add_message("assistant", response)
        return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}

    def set_slot_info(self, agent: BookingAgent, slot_info: Dict[str, Any]):
        agent.data.selected_slot_info = slot_info
        agent.data.confirmed_slot_id = slot_info.get("id")

    def get_session_data(self, session_id: str) -> Optional[BookingData]:
        if session_id in self.sessions:
            return self.sessions[session_id].data
        return None

    def check_slot_valid(self, slot_id: int, slot_datetime: Optional[datetime] = None) -> bool:
        if slot_datetime is None:
            return True
        from app.services.slot_service import get_clinic_now
        return slot_datetime > get_clinic_now()

    def prepare_slot_expired_response(self, agent: BookingAgent) -> Dict[str, Any]:
        agent.stage = BookingStage.SLOT_SELECTION
        agent.context["search_slots"] = True
        agent.data.confirmed_slot_id = None
        agent.data.selected_slot_info = None
        response = (
            "The previous slot is no longer available. I'll find the new earliest available slot for you. "
            "Please wait..."
        )
        agent.add_message("assistant", response)
        return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value, "action": "search_new_slot"}


booking_agent_service = BookingAgentService()