import stripe
from typing import Optional
from ..core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(amount: int = None, currency: str = "inr") -> tuple[str, str]:
    if amount is None:
        amount = settings.PAYMENT_AMOUNT_INR * 100  # ₹1 = 100 paise

    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        automatic_payment_methods={"enabled": True},
        metadata={
            "demo": "true",
            "environment": "test",
            "note": "Demo/test payment - no real charges",
        },
    )
    return intent.client_secret, intent.id


def verify_webhook_signature(payload: bytes, sig_header: str) -> stripe.Event:
    return stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )


def refund_payment(payment_intent_id: str) -> stripe.Refund:
    refund = stripe.Refund.create(payment_intent=payment_intent_id)
    return refund