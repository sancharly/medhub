"""LockoutService — rate-limiting failed login attempts via Redis (TASK-024).

Redis key: lockout:{sha256(normalised_email)}
TTL: LOCK_DURATION (1800s = 30 min)
Lock threshold: MAX_FAILURES (5)
"""

from __future__ import annotations

import hashlib
import uuid

import redis

from app.api.errors import AuthorizationError
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.db.models.audit import AuditOutcome

MAX_FAILURES = 5
LOCK_DURATION = 1800  # seconds


def _lockout_key(normalised_email: str) -> str:
    digest = hashlib.sha256(normalised_email.encode()).hexdigest()
    return "lockout:" + digest


def _lockout_id_key(account_id: uuid.UUID) -> str:
    return "lockout:id:" + str(account_id)


class LockoutService:
    def __init__(
        self,
        redis_client: redis.Redis,
        audit_svc: AuditService | None = None,
    ) -> None:
        self._redis = redis_client
        self._audit_svc = audit_svc

    def is_locked(self, account_id: uuid.UUID | None) -> bool:
        """Return True if the failure counter >= MAX_FAILURES."""
        # We key on account_id when available to avoid email enumeration
        if account_id is None:
            return False
        key = _lockout_id_key(account_id)
        raw = self._redis.get(key)
        if raw is None:
            return False
        return int(raw) >= MAX_FAILURES

    def is_email_locked(self, email: str) -> bool:
        """Check if the normalised email address is locked out (unknown account path)."""
        key = _lockout_key(email.strip().lower())
        count_raw = self._redis.get(key)
        if count_raw is None:
            return False
        return int(count_raw) >= MAX_FAILURES

    def record_failure(
        self, account_id: uuid.UUID | None, email: str, ip: str | None
    ) -> None:
        """Increment failure counter; lock and audit if threshold is reached."""
        normalised = email.strip().lower()
        email_key = _lockout_key(normalised)

        # Increment email-keyed counter (for unknown accounts)
        pipe = self._redis.pipeline()
        pipe.incr(email_key)
        pipe.expire(email_key, LOCK_DURATION)
        pipe.execute()

        # Also maintain account-keyed counter when account_id is known
        if account_id is not None:
            id_key = _lockout_id_key(account_id)
            pipe2 = self._redis.pipeline()
            pipe2.incr(id_key)
            pipe2.expire(id_key, LOCK_DURATION)
            id_results = pipe2.execute()
            id_count = id_results[0]

            if id_count >= MAX_FAILURES and self._audit_svc is not None:
                self._audit_svc.record(
                    actor=None,
                    action=AuditAction.ACCOUNT_LOCKOUT,
                    target_type="account",
                    target_id=str(account_id),
                    outcome=AuditOutcome.SUCCESS,
                    ip=ip,
                )

    def reset(self, account_id: uuid.UUID) -> None:
        """Clear lockout on successful login."""
        self._redis.delete(_lockout_id_key(account_id))

    def admin_unlock(
        self,
        account_id: uuid.UUID,
        actor_role: str,
        email: str = "",
        ip: str | None = None,
    ) -> None:
        """SYSADMIN-only: clear lockout (both id and email keys) and audit the action."""
        if actor_role != "SYSADMIN":
            raise AuthorizationError("Only SYSADMIN can unlock accounts.")

        self._redis.delete(_lockout_id_key(account_id))
        if email:
            self._redis.delete(_lockout_key(email.strip().lower()))

        if self._audit_svc is not None:
            self._audit_svc.record(
                actor=None,
                action=AuditAction.ACCOUNT_UNLOCK,
                target_type="account",
                target_id=str(account_id),
                outcome=AuditOutcome.SUCCESS,
                ip=ip,
            )
