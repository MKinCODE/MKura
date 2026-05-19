import re
import json
import logging
from typing import Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

groq_client = None
if settings.GROQ_API_KEY:
    try:
        from groq import Groq
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to initialize Groq client in entity_extractor: {e}")


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


def extract_name_smart(text: str) -> Optional[str]:
    # Clean email
    email = extract_email(text)
    if email:
        text = text.replace(email, "")
    # Clean phone
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    text = re.sub(phone_pattern, "", text)
    
    # Strip common introductions
    intro_patterns = [
        r'(?i)\bmy\s+name\s+is\s+',
        r'(?i)\bi\s+am\s+',
        r'(?i)\bcall\s+me\s+',
        r'(?i)\bthis\s+is\s+'
    ]
    for pat in intro_patterns:
        text = re.sub(pat, "", text)
        
    # Clean punctuation and extra spaces
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return extract_name(text)


def extract_entities_with_llm(text: str) -> dict:
    if not groq_client:
        return {}
    try:
        system_prompt = (
            "You are an entity extraction assistant. Extract the person's name, email, and phone number from the user's message. "
            "Respond ONLY with a JSON object containing keys: 'name', 'email', 'phone'. Use null if not found. "
            "Do not include any markdown, code blocks, or extra text. Example response:\n"
            '{"name": "John Doe", "email": "john@example.com", "phone": "9876543210"}'
        )
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            max_tokens=60,
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            if content.startswith("json"):
                content = content[4:].strip()
        data = json.loads(content)
        return {
            "name": data.get("name") if data.get("name") else None,
            "email": data.get("email") if data.get("email") else None,
            "phone": data.get("phone") if data.get("phone") else None
        }
    except Exception as e:
        logger.error(f"Failed to extract entities with LLM: {e}")
        return {}