"""Clinical entries API router (TASK-044)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas.clinical import ClinicalEntryCreate, ClinicalEntryResponse
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.clinical.service import ClinicalDataService
from app.db.models.account import Account
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.clinical_repo import ClinicalRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.session import get_db

router = APIRouter(prefix="/patients", tags=["clinical"])


def _get_clinical_service(db: Session = Depends(get_db)) -> ClinicalDataService:
    from app.authz.consent import ConsentService  # noqa: PLC0415

    audit_svc = AuditService(AuditRepository(db))
    consent_svc = ConsentService(ConsentRepository(db), audit_svc)
    authz_svc = AuthorizationService(consent_svc, audit_svc)
    return ClinicalDataService(
        ClinicalRepository(db),
        AccountRepository(db),
        audit_svc,
        authz_svc,
    )


@router.post(
    "/{patient_id}/clinical-entries",
    status_code=status.HTTP_201_CREATED,
    response_model=ClinicalEntryResponse,
)
def create_clinical_entry(
    patient_id: uuid.UUID,
    body: ClinicalEntryCreate,
    actor: Account = Depends(get_current_user),
    svc: ClinicalDataService = Depends(_get_clinical_service),
) -> ClinicalEntryResponse:
    entry = svc.create_entry(actor, patient_id, body.occurred_at, body.description)
    return ClinicalEntryResponse(
        id=entry.id,
        patient_id=entry.patient_id,
        author_id=entry.author_doctor_id,
        occurred_at=entry.occurred_at,
        description=entry.description,
        created_at=entry.created_at,
    )


@router.get("/{patient_id}/clinical-entries", response_model=list[ClinicalEntryResponse])
def list_clinical_entries(
    patient_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: ClinicalDataService = Depends(_get_clinical_service),
) -> list[ClinicalEntryResponse]:
    entries = svc.list_entries(actor, patient_id)
    return [
        ClinicalEntryResponse(
            id=e.id,
            patient_id=e.patient_id,
            author_id=e.author_doctor_id,
            occurred_at=e.occurred_at,
            description=e.description,
            created_at=e.created_at,
        )
        for e in entries
    ]
