"""Session kill propagation Celery task (TASK-034)."""

from __future__ import annotations

import logging
import uuid

from celery import shared_task

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF = 30


@shared_task(  # type: ignore[untyped-decorator]
    bind=True,
    max_retries=_MAX_RETRIES,
    default_retry_delay=_RETRY_BACKOFF,
    autoretry_for=(Exception,),
    retry_backoff=True,
    name="workers.propagate_session_kill",
)
def propagate_session_kill(self: object, account_id: str) -> None:
    """Idempotently invalidate all sessions for an account.

    Audits SESSION_KILL_PROPAGATED with account_id and timestamp — never token values.
    """
    from datetime import UTC, datetime  # noqa: PLC0415

    import redis  # noqa: PLC0415

    from app.audit.actions import AuditAction  # noqa: PLC0415
    from app.audit.service import AuditService  # noqa: PLC0415
    from app.auth.session import SessionService  # noqa: PLC0415
    from app.core.config import get_settings  # noqa: PLC0415
    from app.db.models.audit import AuditOutcome  # noqa: PLC0415
    from app.db.repositories.audit_repo import AuditRepository  # noqa: PLC0415
    from app.db.repositories.session import get_db  # noqa: PLC0415

    settings = get_settings()
    r = redis.Redis.from_url(settings.redis_url)
    session_svc = SessionService(r)
    session_svc.invalidate_all(uuid.UUID(account_id))

    db = next(get_db())
    try:
        audit_svc = AuditService(AuditRepository(db))
        audit_svc.record(
            actor=None,
            action=AuditAction.SESSION_KILL_PROPAGATED,
            target_type="account",
            target_id=account_id,
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    logger.info(
        "Session kill propagated",
        extra={"account_id": account_id, "ts": datetime.now(UTC).isoformat()},
    )
