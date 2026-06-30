"""Email Celery tasks (TASK-031).

- send_activation_email(account_id, activation_token)
- send_appointment_notification(appointment_id)

SMTP config comes from Settings. Best-effort: bounded retries with
exponential backoff. Never blocks the request path.

Audit:
  ACTIVATION_LINK_SENT — logs email + timestamp, NOT the token.
"""

from __future__ import annotations

import logging
import smtplib
import uuid
from datetime import UTC, datetime
from email.message import EmailMessage

from celery import shared_task

from app.core.config import get_settings
from app.workers.email_renderer import render_activation_email, render_appointment_notification
from app.workers.notifications import Notification, NotificationChannel

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF = 60  # seconds base; Celery doubles per retry with exponential=True


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
    smtp_password = settings.smtp_password.get_secret_value() if smtp_user else ""

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

        link = f"{settings.public_base_url}/activate?token={activation_token}"
        subject, body = render_activation_email(account.first_name, link)
        notification = Notification(
            channel=NotificationChannel.EMAIL,
            recipient=account.email,
            subject=subject,
            body=body,
        )

        _send_smtp(notification)
        notification.mark_sent()

        # Audit: log email + timestamp, NEVER the token
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
                "email": account.email,
                "ts": datetime.now(UTC).isoformat(),
            },
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@shared_task(  # type: ignore[untyped-decorator]
    bind=True,
    max_retries=_MAX_RETRIES,
    default_retry_delay=_RETRY_BACKOFF,
    autoretry_for=(Exception,),
    retry_backoff=True,
    name="workers.send_erasure_code_email",
)
def send_erasure_code_email(self: object, recipient_email: str, retrieval_code: str) -> None:
    """Email the anonymized-data retrieval code to the erased account's pre-erasure email.

    The code is passed in-memory only; it is NEVER logged or stored.
    """
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
    _send_smtp(notification)
    notification.mark_sent()
    logger.info(
        "Erasure retrieval code email sent",
        extra={"recipient": recipient_email, "ts": datetime.now(UTC).isoformat()},
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
