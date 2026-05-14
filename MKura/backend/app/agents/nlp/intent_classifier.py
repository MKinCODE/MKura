from typing import Literal

ConfirmationIntent = Literal["confirm", "cancel", "waitlist_yes", "waitlist_no", "greeting", "unknown"]


def classify_intent(text: str) -> ConfirmationIntent:
    text_lower = text.strip().lower()

    if text_lower in ["yes", "y", "confirm", "ok", "okay", "sure", "yeah", "ya", "book", "confirm booking", "proceed"]:
        return "confirm"

    if text_lower in ["cancel", "no", "n", "exit", "quit", "stop", "not interested", "discard"]:
        return "cancel"

    if text_lower in ["yes to waitlist", "add to waitlist", "join waitlist", "yes waitlist", "waitlist yes", "i want waitlist"]:
        return "waitlist_yes"

    if text_lower in ["no waitlist", "not waitlist", "skip waitlist", "don't add waitlist", "without waitlist"]:
        return "waitlist_no"

    greeting_patterns = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "how are you", "start", "book appointment", "appointment", "i want to book", "need appointment", "doctor", "consultation"]
    if any(text_lower.startswith(g) or g in text_lower for g in greeting_patterns):
        if any(word in text_lower for word in ["book", "appointment", "schedule", "consult", "doctor"]):
            return "greeting"
        if any(word in text_lower for word in ["hi", "hello", "hey", "start"]):
            return "greeting"

    return "unknown"