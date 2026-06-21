"""TASK-031: Email tasks and notification abstraction tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from app.workers.email_renderer import render_activation_email, render_appointment_notification
from app.workers.notifications import Notification, NotificationChannel, NotificationStatus

# --- email_renderer ---


def test_render_activation_email_contains_link() -> None:
    subject, body = render_activation_email("Alice", "https://example.com/activate?token=abc")
    assert "https://example.com/activate?token=abc" in body
    assert "72" in body
    assert "Alice" in body
    assert "activate" in subject.lower()


def test_render_activation_email_handles_no_name() -> None:
    subject, body = render_activation_email(None, "https://example.com/activate")
    assert "there" in body  # fallback greeting


def test_render_appointment_notification_contains_details() -> None:
    subject, body = render_appointment_notification(
        "Bob", "Dr. Smith", "Monday 01 January 2026 at 10:00 UTC", "https://example.com/appt/123"
    )
    assert "Bob" in body
    assert "Dr. Smith" in body
    assert "Monday 01 January 2026 at 10:00 UTC" in body
    assert "https://example.com/appt/123" in body


def test_render_appointment_notification_handles_missing_names() -> None:
    subject, body = render_appointment_notification(None, None, "2026-01-01", "https://example.com")
    assert "Patient" in body or "there" in body or "Hi" in body


# --- Notification abstraction ---


def test_notification_initial_status_queued() -> None:
    n = Notification(
        channel=NotificationChannel.EMAIL,
        recipient="a@b.com",
        subject="Hello",
        body="World",
    )
    assert n.status == NotificationStatus.QUEUED


def test_notification_mark_sent_calls_hook() -> None:
    hook = MagicMock()
    n = Notification(
        channel=NotificationChannel.EMAIL,
        recipient="a@b.com",
        subject="Hello",
        body="World",
        post_send_hook=hook,
    )
    n.mark_sent()
    assert n.status == NotificationStatus.SENT
    hook.assert_called_once()


def test_notification_mark_failed() -> None:
    n = Notification(
        channel=NotificationChannel.EMAIL,
        recipient="a@b.com",
        subject="Hello",
        body="World",
    )
    n.mark_failed()
    assert n.status == NotificationStatus.FAILED


# --- send_activation_email task (unit, no real SMTP) ---


def test_send_activation_email_task_calls_smtp() -> None:
    """send_activation_email loads account, renders email, calls SMTP.

    Because imports are local inside the task, we patch at the source modules.
    """
    acct_id = str(uuid.uuid4())

    mock_account = MagicMock()
    mock_account.first_name = "Test"
    mock_account.email = "test@example.com"
    mock_db = MagicMock()
    mock_smtp = MagicMock()

    import app.audit.service as audit_mod  # noqa: PLC0415
    import app.db.repositories.account_repo as ar  # noqa: PLC0415
    import app.db.repositories.audit_repo as audr  # noqa: PLC0415
    import app.db.repositories.session as sess_mod  # noqa: PLC0415
    import app.workers.email_tasks as et  # noqa: PLC0415

    with (
        patch.object(sess_mod, "get_db", return_value=iter([mock_db])),
        patch.object(ar.AccountRepository, "__init__", return_value=None),
        patch.object(ar.AccountRepository, "get_by_id", return_value=mock_account),
        patch.object(audr.AuditRepository, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "record"),
        patch.object(et, "_send_smtp", mock_smtp),
    ):
        # With bind=True, call .run() which doesn't pass the task instance
        et.send_activation_email.run(acct_id, "fake-token-123")  # type: ignore[attr-defined]

    mock_smtp.assert_called_once()
    notification_arg = mock_smtp.call_args[0][0]
    assert notification_arg.recipient == "test@example.com"


# --- _send_smtp TLS branching ---


def _make_notification() -> Notification:
    return Notification(
        channel=NotificationChannel.EMAIL,
        recipient="test@example.com",
        subject="Test",
        body="Body",
    )


def test_send_smtp_uses_smtp_ssl_when_smtp_use_ssl_true() -> None:
    """smtp_use_ssl=True → SMTP_SSL is used; starttls() is NOT called."""
    import smtplib
    from unittest.mock import MagicMock, patch

    import app.workers.email_tasks as et

    mock_settings = MagicMock()
    mock_settings.smtp_host = "smtp.example.com"
    mock_settings.smtp_port = 465
    mock_settings.smtp_user = "user"
    mock_settings.smtp_password.get_secret_value.return_value = "pass"
    mock_settings.mail_from = ""
    mock_settings.smtp_use_ssl = True
    mock_settings.smtp_use_tls = False

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(et, "get_settings", return_value=mock_settings),
        patch.object(smtplib, "SMTP_SSL", return_value=mock_smtp_instance) as mock_ssl_cls,
        patch.object(smtplib, "SMTP") as mock_smtp_cls,
    ):
        et._send_smtp(_make_notification())

    mock_ssl_cls.assert_called_once_with("smtp.example.com", 465)
    mock_smtp_cls.assert_not_called()
    mock_smtp_instance.starttls.assert_not_called()


def test_send_smtp_uses_starttls_when_smtp_use_tls_true() -> None:
    """smtp_use_tls=True, smtp_use_ssl=False → SMTP is used and starttls() is called."""
    import smtplib
    from unittest.mock import MagicMock, patch

    import app.workers.email_tasks as et

    mock_settings = MagicMock()
    mock_settings.smtp_host = "smtp.example.com"
    mock_settings.smtp_port = 587
    mock_settings.smtp_user = "user"
    mock_settings.smtp_password.get_secret_value.return_value = "pass"
    mock_settings.mail_from = ""
    mock_settings.smtp_use_ssl = False
    mock_settings.smtp_use_tls = True

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(et, "get_settings", return_value=mock_settings),
        patch.object(smtplib, "SMTP", return_value=mock_smtp_instance) as mock_smtp_cls,
        patch.object(smtplib, "SMTP_SSL") as mock_ssl_cls,
    ):
        et._send_smtp(_make_notification())

    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)
    mock_ssl_cls.assert_not_called()
    mock_smtp_instance.starttls.assert_called_once()


def test_send_smtp_plaintext_no_starttls_when_both_false() -> None:
    """smtp_use_tls=False, smtp_use_ssl=False → SMTP is used; starttls() is NOT called."""
    import smtplib
    from unittest.mock import MagicMock, patch

    import app.workers.email_tasks as et

    mock_settings = MagicMock()
    mock_settings.smtp_host = "localhost"
    mock_settings.smtp_port = 1025
    mock_settings.smtp_user = ""
    mock_settings.smtp_password.get_secret_value.return_value = ""
    mock_settings.mail_from = "noreply@example.com"
    mock_settings.smtp_use_ssl = False
    mock_settings.smtp_use_tls = False

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(et, "get_settings", return_value=mock_settings),
        patch.object(smtplib, "SMTP", return_value=mock_smtp_instance) as mock_smtp_cls,
        patch.object(smtplib, "SMTP_SSL") as mock_ssl_cls,
    ):
        et._send_smtp(_make_notification())

    mock_smtp_cls.assert_called_once_with("localhost", 1025)
    mock_ssl_cls.assert_not_called()
    mock_smtp_instance.starttls.assert_not_called()
    mock_smtp_instance.login.assert_not_called()


def test_send_activation_email_token_not_in_audit() -> None:
    """Audit record must not contain the token value (SR-023)."""
    acct_id = str(uuid.uuid4())

    mock_account = MagicMock()
    mock_account.first_name = "Test"
    mock_account.email = "test@example.com"
    mock_db = MagicMock()
    captured: list = []

    import app.audit.service as audit_mod  # noqa: PLC0415
    import app.db.repositories.account_repo as ar  # noqa: PLC0415
    import app.db.repositories.audit_repo as audr  # noqa: PLC0415
    import app.db.repositories.session as sess_mod  # noqa: PLC0415
    import app.workers.email_tasks as et  # noqa: PLC0415

    with (
        patch.object(sess_mod, "get_db", return_value=iter([mock_db])),
        patch.object(ar.AccountRepository, "__init__", return_value=None),
        patch.object(ar.AccountRepository, "get_by_id", return_value=mock_account),
        patch.object(audr.AuditRepository, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "__init__", return_value=None),
        patch.object(
            audit_mod.AuditService,
            "record",
            side_effect=lambda *a, **kw: captured.append((a, kw)),
        ),
        patch.object(et, "_send_smtp"),
    ):
        et.send_activation_email.run(acct_id, "secret-token-xyz")  # type: ignore[attr-defined]

    assert len(captured) == 1
    all_audit_str = str(captured)
    assert "secret-token-xyz" not in all_audit_str
