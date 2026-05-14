from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Doctor
from app.schemas import DoctorLogin, Token, DoctorResponse, DoctorCreate
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.api.deps import get_current_doctor

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(credentials: DoctorLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).where(Doctor.email == credentials.email))
    doctor = result.scalar_one_or_none()

    if not doctor or not verify_password(credentials.password, doctor.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token({"sub": doctor.id})
    refresh_token = create_refresh_token({"sub": doctor.id})

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    payload = verify_token(refresh_token, "refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    doctor_id = payload.get("sub")
    new_access_token = create_access_token({"sub": doctor_id})
    new_refresh_token = create_refresh_token({"sub": doctor_id})

    return Token(access_token=new_access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=DoctorResponse)
async def get_me(doctor: Doctor = Depends(get_current_doctor)):
    return doctor