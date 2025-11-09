from fastapi import APIRouter

from app.api.routes import test, analyze
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(test.router)
api_router.include_router(analyze.router)