"""Appointments API router (TASK-047/048/051)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas.appointments import AppointmentCreate, AppointmentResponse
from app.appointments.service import AppointmentService
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.db.models.account import Account
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.appointment_repo import AppointmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.session import get_db

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _get_appointment_service(db: Session = Depends(get_db)) -> AppointmentService:
    from app.authz.consent import ConsentService  # noqa: PLC0415

    audit_svc = AuditService(AuditRepository(db))
    consent_svc = ConsentService(ConsentRepository(db), audit_svc)
    authz_svc = AuthorizationService(consent_svc, audit_svc)
    return AppointmentService(
        AppointmentRepository(db),
        AccountRepository(db),
        audit_svc,
        authz_svc,
        consent_svc,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AppointmentResponse)
def create_appointment(
    body: AppointmentCreate,
    actor: Account = Depends(get_current_user),
    svc: AppointmentService = Depends(_get_appointment_service),
) -> AppointmentResponse:
    appointment = svc.create(actor, body.doctor_id, body.patient_id, body.scheduled_at)
    return AppointmentResponse.model_validate(appointment)


@router.get("", response_model=list[AppointmentResponse])
def list_appointments(
    actor: Account = Depends(get_current_user),
    svc: AppointmentService = Depends(_get_appointment_service),
) -> list[AppointmentResponse]:
    appointments = svc.list_for(actor)
    return [AppointmentResponse.model_validate(a) for a in appointments]


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: AppointmentService = Depends(_get_appointment_service),
) -> AppointmentResponse:
    appointment = svc.get(actor, appointment_id)
    return AppointmentResponse.model_validate(appointment)


@router.post("/{appointment_id}/confirm", response_model=AppointmentResponse)
def confirm_appointment(
    appointment_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: AppointmentService = Depends(_get_appointment_service),
) -> AppointmentResponse:
    appointment = svc.confirm(actor, appointment_id)
    return AppointmentResponse.model_validate(appointment)


@router.post("/{appointment_id}/decline", response_model=AppointmentResponse)
def decline_appointment(
    appointment_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: AppointmentService = Depends(_get_appointment_service),
) -> AppointmentResponse:
    appointment = svc.decline(actor, appointment_id)
    return AppointmentResponse.model_validate(appointment)
