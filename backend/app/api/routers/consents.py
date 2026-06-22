"""Consent API router (TASK-064)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.errors import AuthorizationError, NotFoundError
from app.api.schemas.consent import ConsentGrantRequest, ConsentGrantResponse
from app.audit.service import AuditService
from app.auth.csrf import require_csrf
from app.authz.consent import ConsentService
from app.db.models.account import Account, UserType
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.session import get_db

router = APIRouter(tags=["consents"])


def _get_consent_service(db: Session = Depends(get_db)) -> ConsentService:
    audit_svc = AuditService(AuditRepository(db))
    return ConsentService(ConsentRepository(db), audit_svc)


def _get_consent_repo(db: Session = Depends(get_db)) -> ConsentRepository:
    return ConsentRepository(db)


@router.post(
    "/consents",
    status_code=status.HTTP_201_CREATED,
    response_model=ConsentGrantResponse,
)
def grant_consent(
    body: ConsentGrantRequest,
    actor: Account = Depends(get_current_user),
    svc: ConsentService = Depends(_get_consent_service),
    _csrf: None = Depends(require_csrf),
) -> ConsentGrantResponse:
    """Patient grants a named doctor access to their clinical data (SR-008)."""
    if actor.user_type != UserType.PATIENT:
        raise AuthorizationError("Only patients may grant consent.")
    result = svc.grant(actor.id, body.doctor_id, body.source)
    return ConsentGrantResponse(
        id=result.id,
        patient_id=result.patient_id,
        doctor_id=result.doctor_id,
        source_type=result.source_type,
        appointment_id=result.appointment_id,
        active=result.active,
    )


@router.delete("/consents/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_consent(
    grant_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: ConsentService = Depends(_get_consent_service),
    repo: ConsentRepository = Depends(_get_consent_repo),
    _csrf: None = Depends(require_csrf),
) -> None:
    """Patient revokes a consent grant they own (SR-008.3/4)."""
    if actor.user_type != UserType.PATIENT:
        raise AuthorizationError("Only patients may revoke consent.")
    # Verify ownership — return 404 rather than 403 to avoid enumeration
    grant = repo.get(grant_id)
    if grant is None or grant.patient_id != actor.id:
        raise NotFoundError("Consent grant not found.")
    svc.revoke(grant_id)


@router.get("/me/consents", response_model=list[ConsentGrantResponse])
def list_my_consents(
    actor: Account = Depends(get_current_user),
    svc: ConsentService = Depends(_get_consent_service),
) -> list[ConsentGrantResponse]:
    """Return unified list of all consent grants for the calling patient (SR-036.7)."""
    if actor.user_type != UserType.PATIENT:
        raise AuthorizationError("Only patients may list their consent grants.")
    grants = svc.list_grants(actor.id)
    return [
        ConsentGrantResponse(
            id=g.id,
            patient_id=g.patient_id,
            doctor_id=g.doctor_id,
            source_type=g.source_type,
            appointment_id=g.appointment_id,
            active=g.active,
        )
        for g in grants
    ]
