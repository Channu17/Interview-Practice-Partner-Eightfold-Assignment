from fastapi import APIRouter

from .users import router as users_router
from .interview import router as interview_router
from .voice import router as voice_router

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(interview_router)
api_router.include_router(voice_router)

__all__ = ["api_router"]
