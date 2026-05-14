from datetime import time
from sqlalchemy.orm import Session
from .models import Doctor, WeeklySchedule, Slot, SlotStatus
from .core.security import get_password_hash
from .database import sync_engine
from .database import Base
from .core.config import settings
from datetime import date, timedelta
from dateutil.rrule import rrule, DAILY


def seed_doctor(session: Session):
    doctor = session.query(Doctor).filter(Doctor.email == "dr.mehta@mkhealth.com").first()

    if not doctor:
        doctor = Doctor(
            email="dr.mehta@mkhealth.com",
            password_hash=get_password_hash("doctor123"),
            name="Dr. Vikram Mehta",
            specialization="General Physician & Internal Medicine",
            bio="Committed to providing personalized healthcare with a patient-first approach. Specialized in diabetes, hypertension, and preventive health checkups.",
            degrees="MBBS (AIIMS Delhi), MD (Medicine), FIACM",
            awards="Best Physician Award 2022 (IJCP), Health Excellence Award 2023",
            experience="15+ years",
            photo_url="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400",
            clinic_address="Sector 21, Gandhinagar, Jaipur, Rajasthan 302015",
            phone="+91 98765 43210",
            is_active=True,
        )
        session.add(doctor)
        session.commit()
        session.refresh(doctor)

    return doctor


def seed_weekly_schedule(session: Session, doctor: Doctor):
    existing = session.query(WeeklySchedule).filter(WeeklySchedule.doctor_id == doctor.id).first()

    if not existing:
        schedules = []
        for day in range(7):  # All 7 days: Mon(0) to Sun(6)
            schedule = WeeklySchedule(
                doctor_id=doctor.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(18, 0),
                is_active=True,
            )
            schedules.append(schedule)

        session.add_all(schedules)
        session.commit()


def generate_slots_for_doctor(session: Session, doctor: Doctor, days: int = 30):
    today = date.today()
    end_date = today + timedelta(days=days)

    existing_count = session.query(Slot).filter(
        Slot.doctor_id == doctor.id,
        Slot.date >= today,
        Slot.date <= end_date,
    ).count()

    if existing_count > 100:
        return

    for dt in rrule(DAILY, dtstart=today, until=end_date):
        day_of_week = dt.weekday()

        schedule = session.query(WeeklySchedule).filter(
            WeeklySchedule.doctor_id == doctor.id,
            WeeklySchedule.day_of_week == day_of_week,
            WeeklySchedule.is_active == True,
        ).first()

        if not schedule:
            continue

        current_time = dt.replace(
            hour=schedule.start_time.hour,
            minute=schedule.start_time.minute,
            second=0,
            microsecond=0,
        )
        end_datetime = dt.replace(
            hour=schedule.end_time.hour,
            minute=schedule.end_time.minute,
            second=0,
            microsecond=0,
        )

        slot_duration_minutes = 20

        while current_time + timedelta(minutes=slot_duration_minutes) <= end_datetime:
            slot_time = current_time.time()
            slot_end_time = (current_time + timedelta(minutes=slot_duration_minutes)).time()

            existing_slot = session.query(Slot).filter(
                Slot.doctor_id == doctor.id,
                Slot.date == dt.date(),
                Slot.start_time == slot_time,
            ).first()

            if not existing_slot:
                slot = Slot(
                    doctor_id=doctor.id,
                    date=dt.date(),
                    start_time=slot_time,
                    end_time=slot_end_time,
                    status=SlotStatus.AVAILABLE,
                )
                session.add(slot)

            current_time += timedelta(minutes=slot_duration_minutes)

    session.commit()


def seed_all():
    Base.metadata.create_all(bind=sync_engine)

    with Session(sync_engine) as session:
        doctor = seed_doctor(session)
        seed_weekly_schedule(session, doctor)
        generate_slots_for_doctor(session, doctor)
        print(f"Seeded doctor: {doctor.name}")
        print("Weekly schedule created (Mon-Sun, 9AM-6PM)")
        print("Slots generated for next 30 days")


if __name__ == "__main__":
    seed_all()