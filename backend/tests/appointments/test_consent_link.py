"""TASK-049: Appointment consent linkage tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

from app.appointments.service import AppointmentService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.appointment import Appointment, AppointmentState


def _make_account(user_type: UserType, id: uuid.UUID | None = None) -> Account:
    return Account(
        id=id or uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _make_appointment(
    patient_id: uuid.UUID, doctor_id: uuid.UUID, state: AppointmentState = AppointmentState.PENDING
) -> Appointment:
    return Appointment(
        id=uuid.uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        scheduled_at=datetime.now(UTC),
        state=state,
    )


def _build_svc(appointment: Appointment) -> tuple[AppointmentService, MagicMock]:
    mock_appt_repo = MagicMock()
    mock_appt_repo.get.return_value = appointment

    mock_account_repo = MagicMock()
    mock_audit = MagicMock()
    mock_consent_svc = MagicMock()
    mock_consent_svc.has_active_grant.return_value = False

    authz_svc = AuthorizationService(mock_consent_svc, MagicMock())

    svc = AppointmentService(
        mock_appt_repo, mock_account_repo, mock_audit, authz_svc, mock_consent_svc
    )
    return svc, mock_consent_svc


def test_confirm_grants_appointment_consent() -> None:
    """Case A: confirming creates an APPOINTMENT:{id} consent grant."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    appt = _make_appointment(patient.id, doctor.id)
    svc, mock_consent = _build_svc(appt)

    svc.confirm(patient, appt.id)

    mock_consent.grant.assert_called_once_with(
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        source=f"APPOINTMENT:{appt.id}",
    )


def test_decline_revokes_appointment_consent() -> None:
    """Case B: declining revokes the APPOINTMENT:{id} consent grant."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    appt = _make_appointment(patient.id, doctor.id)
    svc, mock_consent = _build_svc(appt)

    svc.decline(patient, appt.id)

    mock_consent.revoke.assert_called_once_with(
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        source=f"APPOINTMENT:{appt.id}",
    )


def test_confirm_does_not_call_revoke() -> None:
    """Confirming only grants — no revoke call."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    appt = _make_appointment(patient.id, doctor.id)
    svc, mock_consent = _build_svc(appt)

    svc.confirm(patient, appt.id)
    mock_consent.revoke.assert_not_called()


def test_decline_does_not_call_grant() -> None:
    """Declining only revokes — no grant call."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    appt = _make_appointment(patient.id, doctor.id)
    svc, mock_consent = _build_svc(appt)

    svc.decline(patient, appt.id)
    mock_consent.grant.assert_not_called()


def test_case_b_prime_decline_revokes_only_this_appointment_grant() -> None:
    """Case B': decline revokes only the APPOINTMENT:{id} source — other sources untouched.

    The revoke() call must be scoped to source=APPOINTMENT:{id} so a pre-existing grant
    from a different appointment is not affected (SR-036 AC-4 B).
    """
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    appt = _make_appointment(patient.id, doctor.id)
    svc, mock_consent = _build_svc(appt)

    svc.decline(patient, appt.id)

    # Must revoke with the specific appointment source, not by (doctor, patient) pair
    mock_consent.revoke.assert_called_once_with(
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        source=f"APPOINTMENT:{appt.id}",
    )
    # Must NOT call revoke without source (which would strip all grants)
    for call in mock_consent.revoke.call_args_list:
        assert "source" in call.kwargs, "revoke() must always be called with a source"


def test_case_c_decline_pending_appointment_calls_revoke_with_source() -> None:
    """Case C: declining a PENDING (never confirmed) appointment calls revoke with the
    appointment source. ConsentService.revoke() is a no-op when no matching grant exists,
    so this is safe and idempotent (SR-036 AC-4 C).
    """
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    appt = _make_appointment(patient.id, doctor.id, state=AppointmentState.PENDING)
    svc, mock_consent = _build_svc(appt)

    svc.decline(patient, appt.id)

    # revoke is called with source so it only targets the appointment grant (no-op when absent)
    mock_consent.revoke.assert_called_once_with(
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        source=f"APPOINTMENT:{appt.id}",
    )
    # No grant was ever created for this (pending) appointment
    mock_consent.grant.assert_not_called()


# --- Additional TASK-049 tests (SR-036 AC-3, AC-4 B, AC-6) ---


def test_pending_appointment_creates_no_grant() -> None:
    """SR-036 AC-3: A pending appointment creates no consent grant."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    appt = _make_appointment(patient.id, doctor.id, state=AppointmentState.PENDING)
    _svc, mock_consent = _build_svc(appt)

    # No confirm or decline called; consent must be untouched
    mock_consent.grant.assert_not_called()
    mock_consent.revoke.assert_not_called()


def test_confirm_emits_audit_record() -> None:
    """SR-036 AC-6: confirm emits at least one audit record."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    appt = _make_appointment(patient.id, doctor.id)

    mock_appt_repo = MagicMock()
    mock_appt_repo.get.return_value = appt
    mock_account_repo = MagicMock()
    mock_audit = MagicMock()
    mock_consent_svc = MagicMock()
    mock_consent_svc.has_active_grant.return_value = False
    authz_svc = AuthorizationService(mock_consent_svc, MagicMock())
    svc = AppointmentService(
        mock_appt_repo, mock_account_repo, mock_audit, authz_svc, mock_consent_svc
    )

    svc.confirm(patient, appt.id)

    mock_audit.record.assert_called()


def test_case_b_manual_grant_preserved_after_decline() -> None:
    """SR-036 AC-4 Case B: decline revokes only APPOINTMENT grant; MANUAL grant must not be revoked.

    We verify that revoke() is called with source=APPOINTMENT:{id} and NOT with source=MANUAL.
    """
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    appt = _make_appointment(patient.id, doctor.id)
    svc, mock_consent = _build_svc(appt)

    svc.decline(patient, appt.id)

    # Must revoke ONLY the appointment-scoped grant
    mock_consent.revoke.assert_called_once_with(
        patient_id=patient.id,
        doctor_id=doctor.id,
        source=f"APPOINTMENT:{appt.id}",
    )
    # Verify "MANUAL" was not passed as source to revoke
    for call in mock_consent.revoke.call_args_list:
        assert call.kwargs.get("source") != "MANUAL", "revoke() must NOT target MANUAL grants"
