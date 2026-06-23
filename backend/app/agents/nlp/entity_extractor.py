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
        
    blacklist = {
        "hi", "hello", "hey", "bro", "yes", "no", "cancel", "ok", "okay", "sure", "yeah", "ya",
        "doctor", "appointment", "schedule", "book", "consult", "consultation", "avail", "available",
        "today", "tomorrow", "time", "date", "timings", "help", "please", "clinic", "assistant",
        "general", "specialist", "check-up", "checkup", "cardiology", "pediatric", "orthopedics", 
        "cardiologist", "physician", "physio", "therapy", "teeth", "dental", "dentist", "eye", 
        "skin", "dermatology", "flu", "fever", "cough", "sick", "ill", "pain", "injury", "broken", 
        "sprain", "vaccine", "vaccination", "check", "test", "report", "cleaning", "surgery", 
        "operation", "filling", "root canal", "medical", "health", "booking", "first", "second", 
        "third", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
        "me", "my", "your", "his", "her", "their", "our", "us", "them", "i", "you", "he", "she", 
        "they", "we", "who", "what", "where", "when", "why", "how", "want", "like", "need", "love", 
        "prefer", "choose", "select", "have", "has", "had", "do", "does", "did", "go", "went", 
        "gone", "come", "came", "run", "walk", "talk", "speak", "tell", "say", "said", "ask", 
        "give", "take", "bring", "send", "receive", "get", "make", "made", "find", "found", "lose", 
        "lost", "keep", "kept", "hold", "held", "show", "shown", "see", "saw", "seen", "look", 
        "hear", "heard", "listen", "feel", "felt", "think", "thought", "know", "knew", "known", 
        "understand", "understood", "remember", "forget", "forgot", "forgotten", "learn", "teach", 
        "taught", "read", "write", "wrote", "written", "open", "close", "start", "stop", "begin", 
        "end", "finish", "complete", "arrive", "leave", "left", "stay", "remain", "wait", "hope", 
        "wish", "expect", "believe", "doubt", "fear", "worry", "care", "mind", "matter", "happen", 
        "occur", "seem", "appear", "become", "became", "grow", "grew", "grown", "fall", "fell", 
        "fallen", "rise", "rose", "risen", "raise", "raised", "set", "put", "lay", "laid", 
        "lie", "sit", "sat", "stand", "stood", "good", "morning", "afternoon", "evening", "night", 
        "day", "hola", "greetings", "dear", "friend", "buddy", "mate", "dude", "pal", "folks", 
        "guys", "yep", "nah", "nope", "maybe", "perhaps", "definitely", "absolutely", "indeed", 
        "correct", "right", "wrong", "false", "true", "halt", "abort", "reset", "restart", "clear", 
        "delete", "remove", "change", "update", "modify", "edit", "fix", "repair", "support", 
        "info", "information", "details", "contact", "about", "services", "pricing", "fees", 
        "cost", "price", "insurance", "payment", "pay", "card", "cash", "upi", "netbanking", 
        "wallet", "discount", "offer", "promo", "code", "coupon"
    }
    
    words = text.split()
    if any(w.lower() in blacklist for w in words):
        return None
        
    if len(words) >= 1 and len(words) <= 4:
        return text.title()
    return None


def validate_email(email: str) -> bool:
    from email_validator import validate_email as check_email, EmailNotValidError
    try:
        check_email(email, check_deliverability=True)
        return True
    except EmailNotValidError:
        return False
    except Exception:
        # Fallback to standard regex if DNS resolution or network fails
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


def redact_sensitive_info(text: str) -> str:
    if not text:
        return text
    # Redact email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    redacted = re.sub(email_pattern, "[EMAIL]", text)
    
    # Phone patterns to match various international/local structures
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\d{5}[-.\s]?\d{5}\b',
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\b\d{5}[-.\s]?\d{5}\b',
        r'\b\d{10,15}\b'
    ]
    for pattern in phone_patterns:
        redacted = re.sub(pattern, "[PHONE]", redacted)
        
    return redacted


def extract_entities_with_llm(text: str) -> dict:
    if not groq_client:
        return {}
    
    # Redact sensitive data from the message before passing to Groq
    text = redact_sensitive_info(text)
    
    try:
        system_prompt = (
            "You are a strict entity extraction assistant. Extract the user's personal details (name, email, phone) ONLY if they are explicitly and unambiguously provided in their message. "
            "If the user is greeting you, asking a question (e.g. availability, timings), or not providing their own info, return null for those fields. "
            "Do NOT extract words like 'doctor', 'bro', 'clinic', 'appointment', 'general', 'specialist', 'consultation', 'check-up', 'checkup' or generic appointment types as names. "
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