from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid

from .nlp import extract_email, extract_phone, extract_name, classify_intent, ConfirmationIntent


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
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]

        agent = BookingAgent()
        self.sessions[agent.session_id] = agent
        return agent

    def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        slot_info: Optional[Dict[str, Any]] = None,
        payment_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        agent = self.get_or_create_session(session_id)
        message = message.strip()
        agent.add_message("user", message)

        if agent.stage == BookingStage.SLOT_SELECTION:
            return self._handle_slot_selection(agent, message)

        if agent.stage == BookingStage.WAITLIST_PROMPT:
            return self._handle_waitlist_prompt(agent, message)

        if agent.stage == BookingStage.PAYMENT:
            if payment_status == "success" or message.lower() == "payment_success":
                return self._handle_payment_success(agent)
            return {"response": "Please complete the payment to confirm your booking.", "session_id": agent.session_id, "stage": agent.stage.value}

        if agent.stage == BookingStage.COMPLETE:
            return {
                "response": "Your booking is already complete. If you need to cancel, please use the cancellation link in your confirmation email.",
                "session_id": agent.session_id,
                "stage": agent.stage.value,
            }

        return self._collect_information(agent, message)

    def _collect_information(self, agent: BookingAgent, message: str) -> Dict[str, Any]:
        if agent.stage == BookingStage.NAME:
            name = extract_name(message)
            if name:
                agent.data.name = name
                agent.stage = BookingStage.EMAIL
                response = f"Nice to meet you, {name}! What's your email address?"
            else:
                response = "I didn't catch your name. Could you please tell me your full name?"
            agent.add_message("assistant", response)
            return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}

        if agent.stage == BookingStage.EMAIL:
            email = extract_email(message)
            if email:
                agent.data.email = email
                agent.stage = BookingStage.PHONE
                response = f"Got it! What's your phone number? (We'll only use it for appointment-related communications)"
            else:
                response = "I couldn't find a valid email. Please enter your email address (e.g., name@example.com)"
            agent.add_message("assistant", response)
            return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}

        if agent.stage == BookingStage.PHONE:
            phone = extract_phone(message)
            if phone:
                agent.data.phone = phone
                agent.stage = BookingStage.SLOT_SELECTION
                response = "PERFECT! I'll now find the earliest available slot for you."
                agent.context["search_slots"] = True
            else:
                response = "I couldn't find a valid phone number. Please enter your 10-digit phone number."
            agent.add_message("assistant", response)
            return {"response": response, "session_id": agent.session_id, "stage": agent.stage.value}

        return {"response": "Something went wrong. Please start again.", "session_id": agent.session_id, "stage": agent.stage.value}

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
            "Thank you! Your booking is confirmed.\n\n"
            "You'll receive a confirmation email shortly with all the details and a cancellation link.\n\n"
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


booking_agent_service = BookingAgentService()