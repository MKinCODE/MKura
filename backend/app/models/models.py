from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Time, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from ..database import Base


class SlotStatus(str, enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"


class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"


class UpgradationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    specialization = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    degrees = Column(String(500), nullable=True)
    awards = Column(Text, nullable=True)
    experience = Column(String(100), nullable=True)
    photo_url = Column(String(500), nullable=True)
    clinic_address = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    schedules = relationship("WeeklySchedule", back_populates="doctor", lazy="selectin")
    slots = relationship("Slot", back_populates="doctor", lazy="selectin")


class WeeklySchedule(Base):
    __tablename__ = "weekly_schedules"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)

    doctor = relationship("Doctor", back_populates="schedules")


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(SQLEnum(SlotStatus), default=SlotStatus.AVAILABLE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    doctor = relationship("Doctor", back_populates="slots", lazy="selectin")
    booking = relationship("Booking", back_populates="slot", uselist=False, lazy="selectin")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), unique=True, nullable=False)
    patient_name = Column(String(255), nullable=False)
    patient_email = Column(String(255), nullable=False)
    patient_phone = Column(String(20), nullable=False)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.CONFIRMED, nullable=False)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_intent_id = Column(String(255), nullable=True)
    wants_waitlist = Column(Boolean, default=False)
    cancellation_token = Column(String(64), unique=True, nullable=False)
    cancellation_token_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    slot = relationship("Slot", back_populates="booking", lazy="selectin")
    upgradations = relationship("Upgradation", back_populates="booking", lazy="selectin")


class Upgradation(Base):
    __tablename__ = "upgradations"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    status = Column(SQLEnum(UpgradationStatus), default=UpgradationStatus.PENDING, nullable=False)
    offered_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    response_at = Column(DateTime(timezone=True), nullable=True)

    booking = relationship("Booking", back_populates="upgradations")
    slot = relationship("Slot", lazy="selectin")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String(255), primary_key=True, index=True)
    stage = Column(String(50), default="name", nullable=False)
    patient_name = Column(String(255), nullable=True)
    patient_email = Column(String(255), nullable=True)
    patient_phone = Column(String(20), nullable=True)
    confirmed_slot_id = Column(Integer, nullable=True)
    wants_waitlist = Column(Boolean, nullable=True)
    messages = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())