from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date, time
from ..models import SlotStatus, BookingStatus, PaymentStatus, UpgradationStatus


class DoctorBase(BaseModel):
    email: EmailStr
    name: str
    specialization: str
    bio: Optional[str] = None
    degrees: Optional[str] = None
    awards: Optional[str] = None
    experience: Optional[str] = None
    photo_url: Optional[str] = None
    clinic_address: Optional[str] = None
    phone: Optional[str] = None


class DoctorCreate(DoctorBase):
    password: str = Field(..., min_length=6)


class DoctorResponse(DoctorBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DoctorLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int
    exp: datetime
    type: str


class WeeklyScheduleBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time


class WeeklyScheduleCreate(WeeklyScheduleBase):
    pass


class WeeklyScheduleResponse(WeeklyScheduleBase):
    id: int
    doctor_id: int
    is_active: bool

    class Config:
        from_attributes = True


class SlotBase(BaseModel):
    date: date
    start_time: time
    end_time: time


class SlotResponse(SlotBase):
    id: int
    doctor_id: int
    status: SlotStatus

    class Config:
        from_attributes = True


class SlotWithDoctor(SlotResponse):
    doctor: DoctorResponse


class BookingBase(BaseModel):
    patient_name: str
    patient_email: EmailStr
    patient_phone: str = Field(..., pattern=r"^\+?[\d\s-]{10,}$")
    wants_waitlist: bool = False


class BookingCreate(BookingBase):
    slot_id: int


class BookingResponse(BookingBase):
    id: int
    slot_id: int
    status: BookingStatus
    payment_status: PaymentStatus
    payment_intent_id: Optional[str]
    cancellation_token: str
    created_at: datetime
    slot: Optional[SlotWithDoctor] = None

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    action: Optional[str] = None
    data: Optional[dict] = None


class PaymentIntentResponse(BaseModel):
    client_secret: str
    amount: int
    currency: str = "inr"


class CancellationConfirm(BaseModel):
    confirmed: bool


class UpgradationResponse(BaseModel):
    id: int
    booking_id: int
    slot_id: int
    status: UpgradationStatus
    offered_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class AvailableSlotSearch(BaseModel):
    doctor_id: Optional[int] = None


class BlockSlotRequest(BaseModel):
    slot_id: int
    reason: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)