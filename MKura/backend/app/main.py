from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from .database import init_db
from .core.config import settings
from .api.routes import auth_router, bookings_router, slots_router, chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="MKura - MK Health Clinic API",
    description="Backend API for MKura, the AI-powered clinic scheduler",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(bookings_router, prefix="/api/bookings", tags=["bookings"])
app.include_router(slots_router, prefix="/api/slots", tags=["slots"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])


@app.get("/")
async def root():
    return {"message": "MKura API - MK Health Clinic", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}