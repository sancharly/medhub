"""API v1 router — other tasks include_router into this."""

from fastapi import APIRouter

from app.api.routers.appointments import router as appointments_router
from app.api.routers.attachments import router as attachments_router
from app.api.routers.clinical import router as clinical_router
from app.api.routers.groups import router as groups_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(groups_router)
api_router.include_router(clinical_router)
api_router.include_router(attachments_router)
api_router.include_router(appointments_router)
