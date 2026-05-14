from .auth import router as auth_router
from .bookings import router as bookings_router
from .slots import router as slots_router
from .chat import router as chat_router

__all__ = ["auth_router", "bookings_router", "slots_router", "chat_router"]