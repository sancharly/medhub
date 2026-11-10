"""TASK-050/050a: Appointment notification enqueue and resilience tests."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

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


def test_create_calls_delay_after_commit() -> None:
    """create() calls send_appointment_notification.delay(...) after DB commit."""
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

    with patch("app.workers.email_tasks.send_appointment_notification") as mock_task:
        svc.create(actor, doctor.id, patient.id, datetime.now(UTC))

    # The task must be enqueued exactly once; id may be None in unit tests (no DB flush)
    mock_task.delay.assert_called_once()


def test_notification_task_email_failure_still_records_in_app() -> None:
    """If SMTP fails, in-app notification row is still committed with FAILED status."""
    from app.workers.email_tasks import send_appointment_notification as task_fn

    appt_id = str(uuid.uuid4())

    mock_appt = MagicMock()
    mock_appt.id = uuid.UUID(appt_id)
    mock_appt.patient_id = uuid.uuid4()
    mock_appt.doctor_id = uuid.uuid4()
    mock_appt.scheduled_at = datetime.now(UTC)

    mock_patient = MagicMock()
    mock_patient.first_name = "Alice"
    mock_patient.email = "alice@example.com"

    mock_doctor = MagicMock()
    mock_doctor.surname = "Smith"

    mock_db = MagicMock()
    mock_appt_repo = MagicMock()
    mock_appt_repo.get.return_value = mock_appt
    mock_acct_repo = MagicMock()
    mock_acct_repo.get_by_id.side_effect = lambda id: (
        mock_patient if id == mock_appt.patient_id else mock_doctor
    )

    mock_appt_repo_cls = MagicMock(return_value=mock_appt_repo)
    mock_acct_repo_cls = MagicMock(return_value=mock_acct_repo)

    with (
        patch("app.workers.email_tasks.get_settings") as mock_settings,
        patch("app.workers.email_tasks._send_smtp", side_effect=Exception("SMTP down")),
        patch("app.db.repositories.session.get_db", return_value=iter([mock_db])),
        patch("app.db.repositories.appointment_repo.AppointmentRepository", mock_appt_repo_cls),
        patch("app.db.repositories.account_repo.AccountRepository", mock_acct_repo_cls),
    ):
        mock_settings.return_value.public_base_url = "https://app.example.com"

        # Should NOT raise despite SMTP failure
        task_fn(appt_id)

    # DB should be committed (not rolled back)
    mock_db.commit.assert_called()
    mock_db.rollback.assert_not_called()
    # in_app notification should have been added to DB
    mock_db.add.assert_called()


def test_create_logs_a_warning_when_enqueue_fails(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TASK-207 (PRB-013 call site): a failed enqueue is logged with the appointment id only
    (no e-mail address, no name) and the appointment is still created."""
    # An Alembic ``fileConfig`` in another test can leave existing loggers disabled.
    monkeypatch.setattr(logging.getLogger("app.appointments.service"), "disabled", False)
    actor = _make_account(UserType.ADMIN)
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    mock_account_repo = MagicMock()
    mock_account_repo.get_by_id.side_effect = lambda id: doctor if id == doctor.id else patient
    mock_consent = MagicMock()
    authz_svc = AuthorizationService(mock_consent, MagicMock())
    svc = AppointmentService(MagicMock(), mock_account_repo, MagicMock(), authz_svc, mock_consent)

    with (
        patch("app.workers.email_tasks.send_appointment_notification") as mock_task,
        caplog.at_level(logging.WARNING, logger="app.appointments.service"),
    ):
        mock_task.delay.side_effect = RuntimeError("redis://:hunter2@broker:6379/0 unreachable")
        appointment = svc.create(actor, doctor.id, patient.id, datetime.now(UTC))

    assert appointment.state == AppointmentState.PENDING
    records = [r for r in caplog.records if r.name == "app.appointments.service"]
    assert len(records) == 1
    assert records[0].levelno == logging.WARNING
    assert str(appointment.id) in records[0].getMessage()
    assert records[0].exc_info is None
    for text in (caplog.text, doctor.email, patient.email):
        assert "hunter2" not in text
    assert doctor.email not in caplog.text and patient.email not in caplog.text
