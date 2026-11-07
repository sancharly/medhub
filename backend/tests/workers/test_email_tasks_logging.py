"""TASK-138: worker and notification logs carry no personal data (SR-043 AC 1, AC 2, AC 3).

Output is captured from the root handler that Celery's ``setup_logging`` signal installs, the
handler a started worker uses, so Celery's own retry and failure records are included.
"""

from __future__ import annotations

import io
import logging
import smtplib
import sys
import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

ADDRESS = "a.person@example.org"
CODE = "RETRIEVAL-CODE-7F3K"
TOKEN = "ACTIVATION-TOKEN-9Q2"


def _enable_loggers() -> list[logging.Logger]:
    """Other tests (an Alembic ``fileConfig``) can leave existing loggers disabled."""
    disabled = [
        lg
        for lg in logging.Logger.manager.loggerDict.values()
        if isinstance(lg, logging.Logger) and lg.disabled
    ]
    for lg in disabled:
        lg.disabled = False
    return disabled


@pytest.fixture
def worker_log(monkeypatch: pytest.MonkeyPatch) -> Iterator[io.StringIO]:
    """Fire Celery's setup_logging signal, as a worker or beat does at start-up."""
    from celery.signals import setup_logging  # noqa: PLC0415

    import app.workers.celery_app  # noqa: F401, PLC0415  (connects the receiver)

    root = logging.getLogger()
    saved = (root.handlers[:], root.level)
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)
    monkeypatch.setattr(logging.root.manager, "disable", logging.NOTSET)
    reenabled = _enable_loggers()
    setup_logging.send(sender=None)
    yield buffer
    root.handlers, root.level = saved
    for lg in reenabled:
        lg.disabled = True


def _refused(*_a: object, **_k: object) -> None:
    raise smtplib.SMTPRecipientsRefused({ADDRESS: (550, b"no")})


def test_setup_logging_signal_installs_the_filtered_handler(worker_log) -> None:
    """SR-043 AC 2: the worker's root handler has the redaction filter."""
    from app.core.logging import RedactionFilter  # noqa: PLC0415

    # pytest adds its own capture handlers; the one writing to stdout is the worker's.
    handlers = [h for h in logging.getLogger().handlers if getattr(h, "stream", None) is worker_log]
    assert len(handlers) == 1
    assert any(isinstance(f, RedactionFilter) for f in handlers[0].filters)


def test_erasure_code_email_success_logs_no_address(worker_log) -> None:
    """SR-043 AC 1, AC 3: success path of send_erasure_code_email."""
    import app.workers.email_tasks as et  # noqa: PLC0415

    with patch.object(et, "_send_smtp"):
        et.send_erasure_code_email.run(ADDRESS, CODE)  # type: ignore[attr-defined]
    out = worker_log.getvalue()
    assert "Erasure retrieval code email sent" in out
    assert ADDRESS not in out and CODE not in out


def test_activation_email_success_logs_no_address(worker_log) -> None:
    """SR-043 AC 1, AC 3: success path of send_activation_email."""
    import app.audit.service as audit_mod  # noqa: PLC0415
    import app.db.repositories.account_repo as ar  # noqa: PLC0415
    import app.db.repositories.audit_repo as audr  # noqa: PLC0415
    import app.db.repositories.session as sess_mod  # noqa: PLC0415
    import app.workers.email_tasks as et  # noqa: PLC0415

    account = MagicMock(first_name="Ada", surname="Lovelace", email=ADDRESS)
    account_id = str(uuid.uuid4())
    with (
        patch.object(sess_mod, "get_db", return_value=iter([MagicMock()])),
        patch.object(ar.AccountRepository, "__init__", return_value=None),
        patch.object(ar.AccountRepository, "get_by_id", return_value=account),
        patch.object(audr.AuditRepository, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "record"),
        patch.object(et, "_send_smtp"),
    ):
        et.send_activation_email.run(account_id, TOKEN)  # type: ignore[attr-defined]
    out = worker_log.getvalue()
    assert "Activation email sent" in out and account_id in out
    for secret in (ADDRESS, "Ada", "Lovelace", TOKEN):
        assert secret not in out


def test_erasure_code_email_failure_logs_no_address(worker_log) -> None:
    """SR-043 AC 3: failure path. _send_smtp raises SMTPRecipientsRefused naming the recipient;
    Celery's retry and failure records (message, exception text, traceback) are logged."""
    import app.workers.email_tasks as et  # noqa: PLC0415

    with patch.object(et, "_send_smtp", _refused):
        result = et.send_erasure_code_email.apply(args=(ADDRESS, CODE))
    assert result.failed()
    out = worker_log.getvalue()
    assert "SMTPRecipientsRefused" in out  # the failure was logged: real output is inspected
    assert ADDRESS not in out and CODE not in out


def test_appointment_notification_failure_logs_no_address(worker_log) -> None:
    """SR-043 AC 1, AC 3: the in-app-fallback warning on an SMTP refusal logs ids only."""
    import app.db.repositories.account_repo as ar  # noqa: PLC0415
    import app.db.repositories.appointment_repo as apr  # noqa: PLC0415
    import app.db.repositories.session as sess_mod  # noqa: PLC0415
    import app.workers.email_tasks as et  # noqa: PLC0415

    appt = MagicMock()
    appt.scheduled_at.strftime.return_value = "Monday"
    patient = MagicMock(first_name="Ada", email=ADDRESS)
    appointment_id = str(uuid.uuid4())
    with (
        patch.object(sess_mod, "get_db", return_value=iter([MagicMock()])),
        patch.object(apr.AppointmentRepository, "__init__", return_value=None),
        patch.object(apr.AppointmentRepository, "get", return_value=appt),
        patch.object(ar.AccountRepository, "__init__", return_value=None),
        patch.object(ar.AccountRepository, "get_by_id", return_value=patient),
        patch.object(et, "_send_smtp", _refused),
    ):
        et.send_appointment_notification.run(appointment_id)  # type: ignore[attr-defined]
    out = worker_log.getvalue()
    assert "in-app notification recorded as FAILED" in out and appointment_id in out
    assert ADDRESS not in out and "Ada" not in out


def test_success_records_hold_no_address_at_the_source() -> None:
    """SR-043 AC 1: the records the tasks create (before any filter) carry identifiers only."""
    import app.workers.email_tasks as et  # noqa: PLC0415

    seen: list[logging.LogRecord] = []

    class _Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            seen.append(record)

    reenabled = _enable_loggers()
    handler, task_logger = _Collect(), logging.getLogger(et.__name__)
    saved_level = task_logger.level
    task_logger.addHandler(handler)
    task_logger.setLevel(logging.INFO)
    try:
        with patch.object(et, "_send_smtp"):
            et.send_erasure_code_email.run(ADDRESS, CODE)  # type: ignore[attr-defined]
    finally:
        task_logger.removeHandler(handler)
        task_logger.setLevel(saved_level)
        for lg in reenabled:
            lg.disabled = True
    assert seen
    assert all(ADDRESS not in str(r.__dict__) for r in seen)
