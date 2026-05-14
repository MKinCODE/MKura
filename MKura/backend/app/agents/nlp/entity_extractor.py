import re
from typing import Optional, Tuple


def extract_email(text: str) -> Optional[str]:
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    match = re.search(phone_pattern, text)
    if match:
        phone = re.sub(r'[^\d+]', '', match.group(0))
        if len(phone) >= 10:
            return phone
    return None


def extract_name(text: str) -> Optional[str]:
    text = text.strip()
    if len(text) < 2 or len(text) > 50:
        return None
    if '@' in text or any(char.isdigit() for char in text):
        return None
    words = text.split()
    if len(words) >= 1 and len(words) <= 4:
        return text.title()
    return None


def validate_email(email: str) -> bool:
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    digits = re.sub(r'\D', '', phone)
    return 10 <= len(digits) <= 15