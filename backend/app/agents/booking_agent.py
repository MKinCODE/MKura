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
    redact_sensitive_info,
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


def redact_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    redacted = []
    for msg in messages:
        redacted.append({
            "role": msg["role"],
            "content": redact_sensitive_info(msg["content"])
        })
    return redacted


class BookingStage(str, Enum):
    NAME = "name"
    CONFIRM_NAME = "confirm_name"
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
        elif agent.stage == BookingStage.CONFIRM_NAME:
            res = self._handle_confirm_name(agent, message)
        elif agent.stage == BookingStage.WAITLIST_PROMPT:
            res = self._handle_waitlist_prompt(agent, message)
        elif agent.stage == BookingStage.PAYMENT:
            if any(word in message.lower() for word in ["new", "reset", "restart", "another", "book again", "clear", "cancel"]):
                agent.reset()
                res = self._collect_information(agent, message)
            elif payment_status == "success" or message.lower() == "payment_success":
                res = self._handle_payment_success(agent)
            else:
                response = (
                    "Please complete the payment to confirm your booking.\n\n"
                    "⚠️ *Note: If you accidentally closed the payment window, please type 'restart' or 'new' to start a new booking session, as closed payment sessions cannot be resumed.*"
                )
                res = {
                    "response": response,
                    "session_id": agent.session_id,
                    "stage": agent.stage.value
                }
        elif agent.stage == BookingStage.COMPLETE:
            intent = classify_intent(message)
            if intent == "greeting" or any(word in message.lower() for word in ["new", "reset", "restart", "another", "book again", "clear"]):
                agent.reset()
                res = self._collect_information(agent, message)
            else:
                instruction = (
                    "The user's booking is already complete. If they want to schedule another appointment, "
                    "tell them to type 'new booking' or 'restart' to clear the session and start over. "
                    "Otherwise, answer their message politely. Keep it brief."
                )
                response = self._get_groq_fallback(message, instruction, agent)
                agent.add_message("assistant", response)
                res = {
                    "response": response,
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
            
        # 2. Extract email and phone locally
        local_email = extract_email(message)
        local_phone = extract_phone(message)

        # 3. Handle email extraction and validation
        raw_email = local_email
        if raw_email and not agent.data.email:
            from .nlp import validate_email
            if validate_email(raw_email):
                agent.data.email = raw_email.lower()
                agent.context.pop("email_error", None)
            else:
                agent.context["email_error"] = True
        elif not agent.data.email and "@" in message:
            # User typed something with @ but it's not a valid email format
            agent.context["email_error"] = True

        # 4. Handle phone extraction and validation
        raw_phone = local_phone
        if raw_phone and not agent.data.phone:
            from .nlp import validate_phone
            if validate_phone(raw_phone):
                agent.data.phone = raw_phone
                agent.context.pop("phone_error", None)
            else:
                agent.context["phone_error"] = True
        elif not agent.data.phone:
            import re
            digits_only = re.sub(r'\D', '', message)
            if len(digits_only) >= 5:
                agent.context["phone_error"] = True

        # 5. Extract name (only fall back to extract_name_smart if LLM is NOT active)
        extracted_name = extracted.get("name")
        if not extracted_name and not groq_client:
            extracted_name = extract_name_smart(message)

        if extracted_name and not agent.data.name:
            agent.context["temp_name"] = extracted_name.title()
            agent.stage = BookingStage.CONFIRM_NAME
            response = f"Is '{agent.context['temp_name']}' your correct full name? Please reply YES or NO."
            agent.add_message("assistant", response)
            return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}

        # Track what we have now
        has_name = bool(agent.data.name)
        has_email = bool(agent.data.email)
        has_phone = bool(agent.data.phone)

        # 4. Determine current stage and response based on what is missing
        if not has_name:
            agent.stage = BookingStage.NAME
            intent = classify_intent(message)
            if intent == "greeting" or not any(word in message.lower() for word in ["book", "appointment", "schedule", "reserve"]):
                instruction = (
                    "The user is greeting you or asking a general question about the clinic. "
                    "Answer their question politely or greet them warmly. Let them know you can help them book an appointment with Dr. Mousam. "
                    "Ask for their full name to get started with the booking. "
                    "Do NOT ask what type of appointment they want, as we only schedule general consultations. "
                    "Do not demand their name, email, or phone number yet. Keep the response brief. "
                    f"Clinic Info: Name={settings.CLINIC_NAME}, Hours={settings.CLINIC_OPEN_HOUR}am-{settings.CLINIC_CLOSE_HOUR}pm, Location={settings.CLINIC_ADDRESS}, Phone={settings.CLINIC_PHONE}."
                )
                response = self._get_groq_fallback(message, instruction, agent)
            else:
                instruction = (
                    "The user is booking an appointment but hasn't provided a valid full name. "
                    "Politely request their full name (e.g. John Doe). Do not ask for email or phone yet. "
                    "Keep the response brief."
                )
                response = self._get_groq_fallback(message, instruction, agent)
            
        elif not has_email:
            agent.stage = BookingStage.EMAIL
            if agent.context.get("email_error"):
                response = "I'm sorry, but that email address could not be verified (invalid format or unreachable domain). Please enter a valid, active email address."
                agent.context.pop("email_error", None)
                agent.add_message("assistant", response)
                return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}
            
            if not had_name:
                response = f"Thank you, {agent.data.name}! Could you please provide your email address so we can send you appointment confirmations?"
            else:
                instruction = (
                    f"The user's name is {agent.data.name}. Politely ask them to provide their email address "
                    f"so we can send appointment confirmations. Do not ask for name or phone. Keep the response brief."
                )
                response = self._get_groq_fallback(message, instruction, agent)
            
        elif not has_phone:
            agent.stage = BookingStage.PHONE
            if agent.context.get("phone_error"):
                response = "I'm sorry, but that phone number appears to be invalid. Please enter a valid 10 to 15 digit phone number (e.g., 9876543210)."
                agent.context.pop("phone_error", None)
                agent.add_message("assistant", response)
                return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}

            if not had_email or not had_name:
                response = f"Got it, thanks! To keep you updated on your appointments and for any urgent notifications, could you please share your phone number?"
            else:
                instruction = (
                    f"The user has provided their name ({agent.data.name}) and email ({agent.data.email}). "
                    f"Politely ask them for their phone number for urgent notifications. Do not ask for name or email. Keep it brief."
                )
                response = self._get_groq_fallback(message, instruction, agent)
            
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

    def _handle_confirm_name(self, agent: BookingAgent, message: str) -> Dict[str, Any]:
        intent = classify_intent(message)
        temp_name = agent.context.get("temp_name")

        if not temp_name:
            agent.stage = BookingStage.NAME
            response = "Could you please tell me your full name?"
            agent.add_message("assistant", response)
            return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}

        if intent == "confirm":
            agent.data.name = temp_name
            agent.context.pop("temp_name", None)
            
            has_email = bool(agent.data.email)
            has_phone = bool(agent.data.phone)
            
            if not has_email:
                agent.stage = BookingStage.EMAIL
                response = f"Great! Could you please provide your email address so we can send you appointment confirmations?"
            elif not has_phone:
                agent.stage = BookingStage.PHONE
                response = f"Got it, thanks! To keep you updated on your appointments and for any urgent notifications, could you please share your phone number?"
            else:
                agent.stage = BookingStage.SLOT_SELECTION
                response = (
                    f"PERFECT! I've recorded your details:\n👤 Name: {agent.data.name}\n✉️ Email: {agent.data.email}\n📞 Phone: {agent.data.phone}\n\n"
                    f"I'll now find the earliest available slot for you."
                )
                agent.context["search_slots"] = True
                
        elif intent == "cancel":
            agent.context.pop("temp_name", None)
            agent.stage = BookingStage.NAME
            response = "No problem! Could you please tell me your correct full name?"
        else:
            response = f"Please reply YES to confirm that your name is '{temp_name}', or NO if it is incorrect."

        agent.add_message("assistant", response)
        return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}

    def _get_groq_fallback(self, user_message: str, instruction: str, agent: Optional[BookingAgent] = None) -> str:
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
            
            # Construct messages with history
            messages = [{"role": "system", "content": system_prompt}]
            if agent and agent.messages:
                # Get redacted history excluding the current user message which we will append next
                redacted_history = redact_messages(agent.messages[:-1])
                messages.extend(redacted_history)
                
            # Append the current user message, redacted for privacy
            messages.append({"role": "user", "content": redact_sensitive_info(user_message)})
            
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=150,
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