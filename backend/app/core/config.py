from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "MK Health Clinic API"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/clinic_db"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/clinic_db"

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GROQ_API_KEY: str = ""

    PAYMENT_AMOUNT_INR: int = 100
    DEMO_MODE: bool = True

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"
    SMTP_FROM_EMAIL: str = "MK Health Clinic <noreply@mkhealthclinic.com>"

    CLINIC_NAME: str = "MK Health Clinic"
    CLINIC_ADDRESS: str = "Sector 21, Gandhinagar, Jaipur, Rajasthan 302015"
    CLINIC_PHONE: str = "+91 98765 43210"

    SLOT_DURATION_MINUTES: int = 20
    MIN_LEAD_TIME_MINUTES: int = 60
    CLINIC_OPEN_HOUR: int = 9
    CLINIC_CLOSE_HOUR: int = 18
    SAME_DAY_CUTOFF_HOUR: int = 17
    MAX_ADVANCE_BOOKING_DAYS: int = 30
    UPGRADATION_TIMEOUT_MINUTES: int = 15

    RATE_LIMIT_BOOKING: int = 5
    RATE_LIMIT_CHAT: int = 20
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()