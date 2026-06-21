"""ConsentService — manages patient→doctor consent grants (TASK-028)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.db.models.audit import AuditOutcome
from app.db.models.consent import ConsentGrant, ConsentSourceType
from app.db.repositories.consent_repo import ConsentRepository


@dataclass
class ConsentGrantResult:
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    source_type: ConsentSourceType
    appointment_id: uuid.UUID | None
    active: bool


class ConsentService:
    def __init__(
        self,
        consent_repo: ConsentRepository,
        audit_svc: AuditService,
    ) -> None:
        self._repo = consent_repo
        self._audit_svc = audit_svc

    def grant(
        self,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        source: str,
        *,
        appointment_id: uuid.UUID | None = None,
    ) -> ConsentGrantResult:
        """Create an active consent grant.

        source: "MANUAL" or "APPOINTMENT:{appointment_id}"
        """
        source_type, appt_id = _parse_source(source, appointment_id)

        grant = ConsentGrant(
            patient_id=patient_id,
            doctor_id=doctor_id,
            source_type=source_type,
            appointment_id=appt_id,
            active=True,
        )
        self._repo.add(grant)

        self._audit_svc.record(
            actor=patient_id,
            action=AuditAction.CONSENT_GRANTED,
            target_type="consent_grant",
            target_id=str(grant.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

        return _to_result(grant)

    def revoke(
        self,
        grant_id: uuid.UUID | None = None,
        *,
        patient_id: uuid.UUID | None = None,
        doctor_id: uuid.UUID | None = None,
        source: str | None = None,
    ) -> None:
        """Deactivate a specific consent grant.

        Only the matching source row is deactivated; siblings are unchanged (SR-036).
        """
        if grant_id is not None:
            grant = self._repo.get(grant_id)
            if grant is None or not grant.active:
                return
            grant.active = False
            grant.revoked_at = datetime.now(UTC)
            self._audit_svc.record(
                actor=grant.patient_id,
                action=AuditAction.CONSENT_REVOKED,
                target_type="consent_grant",
                target_id=str(grant.id),
                outcome=AuditOutcome.SUCCESS,
                ip=None,
            )
            return

        # Revoke by source
        if patient_id is not None and doctor_id is not None and source is not None:
            source_type, appt_id = _parse_source(source, None)
            grants = self._repo.list_active_for_patient_doctor(patient_id, doctor_id)
            for g in grants:
                if g.source_type == source_type and g.appointment_id == appt_id:
                    g.active = False
                    g.revoked_at = datetime.now(UTC)
                    self._audit_svc.record(
                        actor=patient_id,
                        action=AuditAction.CONSENT_REVOKED,
                        target_type="consent_grant",
                        target_id=str(g.id),
                        outcome=AuditOutcome.SUCCESS,
                        ip=None,
                    )
                    break  # Revoke only the first matching row

    def list_grants(self, patient_id: uuid.UUID) -> list[ConsentGrantResult]:
        grants = self._repo.list_for_patient(patient_id)
        return [_to_result(g) for g in grants]

    def has_active_grant(self, doctor_id: uuid.UUID, patient_id: uuid.UUID) -> bool:
        """EXISTS query: True if any active grant exists for this doctor/patient pair."""
        grants = self._repo.list_active_for_patient_doctor(patient_id, doctor_id)
        return len(grants) > 0


def _parse_source(
    source: str, appointment_id: uuid.UUID | None
) -> tuple[ConsentSourceType, uuid.UUID | None]:
    if source == "MANUAL":
        return ConsentSourceType.MANUAL, None
    if source.startswith("APPOINTMENT:"):
        appt_id_str = source.split(":", 1)[1]
        return ConsentSourceType.APPOINTMENT, uuid.UUID(appt_id_str)
    raise ValueError(f"Unknown consent source: {source!r}")


def _to_result(grant: ConsentGrant) -> ConsentGrantResult:
    return ConsentGrantResult(
        id=grant.id,
        patient_id=grant.patient_id,
        doctor_id=grant.doctor_id,
        source_type=grant.source_type,
        appointment_id=grant.appointment_id,
        active=grant.active,
    )
