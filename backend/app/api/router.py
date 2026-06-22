"""API v1 router — all feature routers are registered here."""

from fastapi import APIRouter

from app.api.routers.accounts import router as accounts_router
from app.api.routers.activation import router as activation_router
from app.api.routers.anonymized_data import router as anonymized_data_router
from app.api.routers.appointments import router as appointments_router
from app.api.routers.attachments import router as attachments_router
from app.api.routers.auth import router as auth_router
from app.api.routers.clinical import router as clinical_router
from app.api.routers.consents import router as consents_router
from app.api.routers.groups import router as groups_router
from app.api.routers.lifecycle import router as lifecycle_router
from app.api.routers.me import router as me_router
from app.api.routers.modules import router as modules_router

api_router = APIRouter(prefix="/api/v1")

# Auth
api_router.include_router(auth_router)

# Identity
api_router.include_router(accounts_router)
api_router.include_router(activation_router)
api_router.include_router(lifecycle_router)
api_router.include_router(anonymized_data_router)

# Groups
api_router.include_router(groups_router)

# Clinical & attachments
api_router.include_router(clinical_router)
api_router.include_router(attachments_router)

# Appointments
api_router.include_router(appointments_router)

# Consent
api_router.include_router(consents_router)

# Me
api_router.include_router(me_router)

# Modules (sysadmin)
api_router.include_router(modules_router)
