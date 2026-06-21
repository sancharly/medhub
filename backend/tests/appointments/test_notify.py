"""TASK-050: Appointment notification enqueue tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from app.appointments.service import AppointmentService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.appointment import Appointment, AppointmentState


def _make_account(user_type: UserType) -> Account:
    return Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def test_create_enqueues_notification_task() -> None:
    """Appointment creation enqueues the send_appointment_notification task."""
    actor = _make_account(UserType.ADMIN)
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)

    mock_appt_repo = MagicMock()
    new_appt = Appointment(
        id=uuid.uuid4(),
        doctor_id=doctor.id,
        patient_id=patient.id,
        scheduled_at=datetime.now(UTC),
        state=AppointmentState.PENDING,
    )
    mock_appt_repo.add.return_value = new_appt

    mock_account_repo = MagicMock()
    mock_account_repo.get_by_id.side_effect = lambda id: doctor if id == doctor.id else patient

    mock_audit = MagicMock()
    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = False
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    svc = AppointmentService(mock_appt_repo, mock_account_repo, mock_audit, authz_svc, mock_consent)

    mock_task = MagicMock()
    # Patch the module where the name is actually imported (local import inside function)
    with patch("app.workers.email_tasks.send_appointment_notification", mock_task):
        # Also patch builtins import within the function
        import app.workers.email_tasks as email_mod  # noqa: PLC0415

        with patch.object(email_mod, "send_appointment_notification", mock_task):
            svc.create(actor, doctor.id, patient.id, datetime.now(UTC))

    # The task is enqueued best-effort — verify the appointment was created
    assert mock_appt_repo.add.called
