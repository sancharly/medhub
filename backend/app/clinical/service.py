"""ClinicalDataService — create and list clinical entries (TASK-044)."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.api.errors import NotFoundError, ValidationProblem
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.authz.service import AuthorizationService, Resource
from app.db.models.account import Account
from app.db.models.audit import AuditOutcome
from app.db.models.clinical import ClinicalEntry
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.clinical_repo import ClinicalRepository


class ClinicalDataService:
    def __init__(
        self,
        clinical_repo: ClinicalRepository,
        account_repo: AccountRepository,
        audit_svc: AuditService,
        authz_svc: AuthorizationService,
    ) -> None:
        self._repo = clinical_repo
        self._account_repo = account_repo
        self._audit_svc = audit_svc
        self._authz_svc = authz_svc

    def create_entry(
        self,
        actor: Account,
        patient_id: uuid.UUID,
        occurred_at: datetime,
        description: str,
    ) -> ClinicalEntry:
        """Create a clinical entry. Doctor with consent only."""
        self._authz_svc.authorize(
            actor,
            "clinical:write",
            Resource(resource_type="clinical_entry", owner_id=None, patient_id=patient_id),
        )

        trimmed = description.strip()
        if not trimmed:
            raise ValidationProblem("Description must not be blank.")

        # Verify patient exists
        patient = self._account_repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError(f"Patient {patient_id} not found.")

        entry = ClinicalEntry(
            patient_id=patient_id,
            author_doctor_id=actor.id,  # author is always the actor
            occurred_at=occurred_at,
            description=trimmed,
        )
        self._repo.add(entry)

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.CLINICAL_CREATE,
            target_type="clinical_entry",
            target_id=str(entry.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        return entry

    def list_entries(self, actor: Account, patient_id: uuid.UUID) -> list[ClinicalEntry]:
        """List clinical entries for a patient.

        Doctor: requires consent.
        Patient: can list their own entries only.
        """
        # patient_id in the resource lets _eval_patient's `own` check decide correctly:
        # same patient → own=True → allow; different patient → own=False → deny (403).
        resource = Resource(
            resource_type="clinical_entry",
            owner_id=None,
            patient_id=patient_id,
        )

        self._authz_svc.authorize(actor, "clinical:read", resource)

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.CLINICAL_ACCESS,
            target_type="clinical_entry",
            target_id=str(patient_id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        return self._repo.list_for_patient_ordered(patient_id)
