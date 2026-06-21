"""TASK-028: ConsentService tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from app.authz.consent import ConsentService
from app.db.models.consent import ConsentGrant, ConsentSourceType


def _make_grant(
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    source_type: ConsentSourceType = ConsentSourceType.MANUAL,
    active: bool = True,
    appointment_id: uuid.UUID | None = None,
) -> ConsentGrant:
    g = ConsentGrant(
        id=uuid.uuid4(),
        patient_id=patient_id,
        doctor_id=doctor_id,
        source_type=source_type,
        appointment_id=appointment_id,
        active=active,
    )
    return g


def _svc() -> tuple[ConsentService, MagicMock, MagicMock]:
    mock_repo = MagicMock()
    mock_audit = MagicMock()
    svc = ConsentService(mock_repo, mock_audit)
    return svc, mock_repo, mock_audit


# --- grant ---

def test_grant_creates_active_grant() -> None:
    svc, mock_repo, _ = _svc()
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    grant = _make_grant(patient_id, doctor_id)
    mock_repo.add.return_value = grant

    result = svc.grant(patient_id, doctor_id, "MANUAL")
    assert result.active is True
    assert result.source_type == ConsentSourceType.MANUAL
    mock_repo.add.assert_called_once()


def test_grant_appointment_source_parses_id() -> None:
    svc, mock_repo, _ = _svc()
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    appt_id = uuid.uuid4()
    grant = _make_grant(
        patient_id, doctor_id, ConsentSourceType.APPOINTMENT, appointment_id=appt_id
    )
    mock_repo.add.return_value = grant

    result = svc.grant(patient_id, doctor_id, f"APPOINTMENT:{appt_id}")
    assert result.source_type == ConsentSourceType.APPOINTMENT


def test_grant_audits_event() -> None:
    svc, mock_repo, mock_audit = _svc()
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    grant = _make_grant(patient_id, doctor_id)
    mock_repo.add.return_value = grant

    svc.grant(patient_id, doctor_id, "MANUAL")
    mock_audit.record.assert_called_once()
    assert "CONSENT_GRANTED" in str(mock_audit.record.call_args)


# --- has_active_grant ---

def test_has_active_grant_true_when_active_grant_exists() -> None:
    svc, mock_repo, _ = _svc()
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    mock_repo.list_active_for_patient_doctor.return_value = [
        _make_grant(patient_id, doctor_id)
    ]
    assert svc.has_active_grant(doctor_id, patient_id) is True


def test_has_active_grant_false_when_no_grants() -> None:
    svc, mock_repo, _ = _svc()
    mock_repo.list_active_for_patient_doctor.return_value = []
    assert svc.has_active_grant(uuid.uuid4(), uuid.uuid4()) is False


# --- revoke ---

def test_revoke_by_id_deactivates_grant() -> None:
    svc, mock_repo, mock_audit = _svc()
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    grant = _make_grant(patient_id, doctor_id)
    mock_repo.get.return_value = grant

    svc.revoke(grant_id=grant.id)

    assert grant.active is False
    mock_audit.record.assert_called_once()
    assert "CONSENT_REVOKED" in str(mock_audit.record.call_args)


def test_revoke_by_source_only_revokes_matching_row() -> None:
    """SR-036: revoking one source must not affect siblings."""
    svc, mock_repo, mock_audit = _svc()
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    appt_id = uuid.uuid4()

    # Two active grants: MANUAL and APPOINTMENT
    manual_grant = _make_grant(patient_id, doctor_id, ConsentSourceType.MANUAL)
    appt_grant = _make_grant(
        patient_id, doctor_id, ConsentSourceType.APPOINTMENT, appointment_id=appt_id
    )
    mock_repo.list_active_for_patient_doctor.return_value = [manual_grant, appt_grant]

    # Revoke only the MANUAL one
    svc.revoke(patient_id=patient_id, doctor_id=doctor_id, source="MANUAL")

    assert manual_grant.active is False
    assert appt_grant.active is True  # sibling unchanged


# --- list_grants ---

def test_list_grants_returns_all() -> None:
    svc, mock_repo, _ = _svc()
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    grants = [_make_grant(patient_id, doctor_id), _make_grant(patient_id, uuid.uuid4())]
    mock_repo.list_for_patient.return_value = grants

    results = svc.list_grants(patient_id)
    assert len(results) == 2
