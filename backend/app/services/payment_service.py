from typing import Optional
import uuid

def create_payment_intent(amount: int = None, currency: str = "inr") -> tuple[str, str]:
    # Mocking payment intent for demo
    client_secret = f"pi_mock_secret_{uuid.uuid4()}"
    payment_intent_id = f"pi_mock_{uuid.uuid4()}"
    return client_secret, payment_intent_id


def verify_webhook_signature(payload: bytes, sig_header: str) -> dict:
    # Mock webhook verify
    return {}


def refund_payment(payment_intent_id: str) -> None:
    # Mock refund
    pass