"""Email Celery tasks (TASK-031).

- send_activation_email(account_id, activation_token)
- send_appointment_notification(appointment_id)

SMTP config comes from Settings. Best-effort: bounded retries with
exponential backoff. Never blocks the request path.

Audit:
  ACTIVATION_LINK_SENT — audit row by account id; no email address, NOT the token.
Logs carry identifiers only (SR-043): never an address, name or token.
"""

from __future__ import annotations

import logging
import smtplib
import uuid
from datetime import UTC, datetime
from email.message import EmailMessage
from typing import Any

from celery import shared_task

from app.core.config import get_settings
from app.workers.email_renderer import render_activation_email, render_appointment_notification
from app.workers.notifications import Notification, NotificationChannel

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF = 60  # seconds base; Celery doubles per retry with exponential=True
# Erasure code e-mail (TASK-228): re-checks that the erasure committed, 2 s doubling to 60 s,
# about 10 minutes in all. Kept apart from the SMTP retries (_MAX_RETRIES).
_COMMIT_CHECKS = 14
_COMMIT_CHECK_MAX_COUNTDOWN = 60


def _send_smtp(notification: Notification) -> None:
    """Send an email via SMTP. Raises on failure so Celery can retry."""
    settings = get_settings()
    msg = EmailMessage()
    msg["Subject"] = notification.subject
    msg["From"] = settings.mail_from or settings.smtp_user
    msg["To"] = notification.recipient
    msg.set_content(notification.body)

    smtp_host = settings.smtp_host
    smtp_port = settings.smtp_port
    smtp_user = settings.smtp_user.strip() if settings.smtp_user else ""
    smtp_password = (
        settings.smtp_password.get_secret_value() if smtp_user and settings.smtp_password else ""
    )

    if settings.smtp_use_ssl:
        # Implicit TLS (port 465)
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
            if smtp_user:
                smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
    elif settings.smtp_use_tls:
        # STARTTLS (port 587)
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.starttls()
            if smtp_user:
                smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
    else:
        # Plaintext (local relay only, e.g. MailHog on port 1025)
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            if smtp_user:
                smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)


@shared_task(  # type: ignore[untyped-decorator]
    bind=True,
    max_retries=_MAX_RETRIES,
    default_retry_delay=_RETRY_BACKOFF,
    autoretry_for=(Exception,),
    retry_backoff=True,
    name="workers.send_activation_email",
)
def send_activation_email(self: object, account_id: str, activation_token: str) -> None:
    """Load account, render activation email, send via SMTP, audit (no token in audit)."""
    from app.audit.actions import AuditAction  # noqa: PLC0415
    from app.audit.service import AuditService  # noqa: PLC0415
    from app.db.models.audit import AuditOutcome  # noqa: PLC0415
    from app.db.repositories.account_repo import AccountRepository  # noqa: PLC0415
    from app.db.repositories.audit_repo import AuditRepository  # noqa: PLC0415
    from app.db.repositories.session import get_db  # noqa: PLC0415

    settings = get_settings()
    db = next(get_db())
    try:
        repo = AccountRepository(db)
        account = repo.get_by_id(uuid.UUID(account_id))
        if account is None:
            logger.warning("send_activation_email: account %s not found", account_id)
            return

        link = f"{settings.public_base_url}/activation/{activation_token}"
        subject, body = render_activation_email(account.first_name, link)
        notification = Notification(
            channel=NotificationChannel.EMAIL,
            recipient=account.email,
            subject=subject,
            body=body,
        )

        _send_smtp(notification)
        notification.mark_sent()

        # Audit by account id, NEVER the token or the address
        audit_svc = AuditService(AuditRepository(db))
        audit_svc.record(
            actor=None,
            action=AuditAction.ACTIVATION_LINK_SENT,
            target_type="account",
            target_id=account_id,
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        db.commit()
        logger.info(
            "Activation email sent",
            extra={
                "account_id": account_id,
                "ts": datetime.now(UTC).isoformat(),
            },
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _erasure_committed(dataset_id: str) -> bool:
    """True when the ``anonymized_dataset`` row of the erasure is visible to this session.

    The dataset insert, the PII severance and the audit rows are one transaction, so the row
    being visible (READ COMMITTED) means the whole erasure committed. Read-only; the session
    is closed on every path.
    """
    from sqlalchemy import select  # noqa: PLC0415

    from app.db.models.anonymized_dataset import AnonymizedDataset  # noqa: PLC0415
    from app.db.repositories.session import get_db  # noqa: PLC0415

    db = next(get_db())
    try:
        stmt = select(AnonymizedDataset.id).where(AnonymizedDataset.id == uuid.UUID(dataset_id))
        return db.execute(stmt).first() is not None
    finally:
        db.close()


@shared_task(  # type: ignore[untyped-decorator]
    bind=True,
    max_retries=_COMMIT_CHECKS + _MAX_RETRIES,
    default_retry_delay=_RETRY_BACKOFF,
    name="workers.send_erasure_code_email",
)
def send_erasure_code_email(
    self: Any,
    recipient_email: str,
    retrieval_code: str,
    dataset_id: str,
    commit_checks: int = 0,
) -> None:
    """Email the anonymized-data retrieval code to the erased account's pre-erasure email.

    The code is passed in-memory only; it is NEVER logged or stored. It is sent only once the
    erasure's dataset row is visible, i.e. the erasure committed (SR-024 AC 6, PRB-083): while
    it is absent the task re-checks (``commit_checks``), and at the last check it drops the
    code. If the check itself cannot be made the e-mail is sent anyway, so a committed erasure
    never loses its code. SMTP failures keep their own budget of ``_MAX_RETRIES`` retries.
    """
    try:
        committed: bool | None = _erasure_committed(dataset_id)
    except Exception:
        committed = None  # unknown; no exception text is logged
    if committed is not True:
        if commit_checks < _COMMIT_CHECKS:
            countdown = min(2 ** (commit_checks + 1), _COMMIT_CHECK_MAX_COUNTDOWN)
            raise self.retry(
                countdown=countdown,
                kwargs={**(self.request.kwargs or {}), "commit_checks": commit_checks + 1},
            )
        if committed is False:
            logger.warning(
                "Erasure code e-mail not sent: dataset %s was never committed", dataset_id
            )
            return
        logger.warning(
            "Erasure code e-mail sent without confirming that dataset %s was committed",
            dataset_id,
        )

    settings = get_settings()
    subject = "Your MedHub data retrieval code"
    retrieve_url = settings.public_base_url + "/erasure/retrieve"
    body = "\n".join(
        [
            "Your MedHub account has been erased per your request.",
            "",
            "Use the retrieval code below to access your anonymized dataset:",
            "",
            "  " + retrieval_code,
            "",
            "Go to " + retrieve_url + " to use this code.",
            "This code is valid for 5 years.",
        ]
    )
    notification = Notification(
        channel=NotificationChannel.EMAIL,
        recipient=recipient_email,
        subject=subject,
        body=body,
    )
    try:
        _send_smtp(notification)
    except Exception as exc:
        smtp_retries = self.request.retries - commit_checks
        if smtp_retries >= _MAX_RETRIES:
            raise
        raise self.retry(exc=exc, countdown=_RETRY_BACKOFF * 2**smtp_retries) from exc
    notification.mark_sent()
    logger.info(
        "Erasure retrieval code email sent",
        extra={"ts": datetime.now(UTC).isoformat()},
    )


@shared_task(  # type: ignore[untyped-decorator]
    bind=True,
    max_retries=_MAX_RETRIES,
    default_retry_delay=_RETRY_BACKOFF,
    autoretry_for=(Exception,),
    retry_backoff=True,
    name="workers.send_appointment_notification",
)
def send_appointment_notification(self: object, appointment_id: str) -> None:
    """Load appointment, render email with doctor name/datetime/link, send."""
    from app.db.repositories.account_repo import AccountRepository  # noqa: PLC0415
    from app.db.repositories.appointment_repo import AppointmentRepository  # noqa: PLC0415
    from app.db.repositories.session import get_db  # noqa: PLC0415

    settings = get_settings()
    db = next(get_db())
    try:
        appt_repo = AppointmentRepository(db)
        appt = appt_repo.get(uuid.UUID(appointment_id))
        if appt is None:
            logger.warning(
                "send_appointment_notification: appointment %s not found", appointment_id
            )
            return

        acct_repo = AccountRepository(db)
        patient = acct_repo.get_by_id(appt.patient_id)
        doctor = acct_repo.get_by_id(appt.doctor_id)
        if patient is None:
            logger.warning(
                "send_appointment_notification: patient not found for appointment %s",
                appointment_id,
            )
            return

        patient_name = patient.first_name
        doctor_name = f"Dr. {doctor.surname}" if doctor and doctor.surname else "your doctor"
        scheduled_str = appt.scheduled_at.strftime("%A %d %B %Y at %H:%M UTC")
        link = f"{settings.public_base_url}/appointments/{appointment_id}"

        subject, body = render_appointment_notification(
            patient_name, doctor_name, scheduled_str, link
        )
        notification = Notification(
            channel=NotificationChannel.EMAIL,
            recipient=patient.email,
            subject=subject,
            body=body,
        )
        # Write in-app notification row FIRST (TASK-050a: resilience)
        from app.db.models.notification import InAppNotification  # noqa: PLC0415

        in_app = InAppNotification(
            recipient_account_id=appt.patient_id,
            appointment_id=appt.id,
            message=body,
            status="QUEUED",
        )
        db.add(in_app)
        db.flush()  # assign id but don't commit yet

        # Attempt SMTP send (best-effort)
        try:
            _send_smtp(notification)
            notification.mark_sent()
            in_app.status = "SENT"
        except Exception:
            notification.mark_failed()
            in_app.status = "FAILED"
            logger.warning(
                "Appointment notification email failed; in-app notification recorded as FAILED",
                extra={"appointment_id": appointment_id},
            )

        db.commit()
        logger.info("Appointment notification sent", extra={"appointment_id": appointment_id})
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
