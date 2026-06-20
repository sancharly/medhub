"""AuditService — server-assigned timestamps, credential scrubbing (SR-023)."""

import datetime
import re
import uuid

from app.db.models.audit import AuditLog, AuditOutcome
from app.db.repositories.audit_repo import AuditRepository

# Pattern matches key=value pairs that look credential-like
_CREDENTIAL_PATTERN = re.compile(
    r"\b(password|passwd|secret|token|key|credential)s?\s*=\s*\S+",
    re.IGNORECASE,
)


def _scrub(value: str) -> str:
    """Remove credential-like key=value pairs from a string."""
    return _CREDENTIAL_PATTERN.sub(r"\1=[REDACTED]", value)


class AuditService:
    def __init__(self, audit_repo: AuditRepository) -> None:
        self._repo = audit_repo

    def record(
        self,
        actor: uuid.UUID | None,
        action: str,
        target_type: str | None,
        target_id: str | None,
        outcome: AuditOutcome,
        ip: str | None,
    ) -> None:
        """Persist an immutable audit record.

        The timestamp is server-assigned here; callers cannot supply it.
        Credential-like patterns in the action string are scrubbed before storage.
        Raises on persistence failure — never swallows exceptions.
        """
        safe_action = _scrub(action)
        # Scrub all free-text fields; target_type/target_id should be opaque
        # identifiers, but apply the same scrub defensively (SR-023.5).
        safe_target_type = _scrub(target_type) if target_type else target_type
        safe_target_id = _scrub(target_id) if target_id else target_id
        log = AuditLog(
            actor_id=actor,
            action=safe_action,
            target_type=safe_target_type,
            target_id=safe_target_id,
            outcome=outcome,
            ip=ip,
            # timestamp has a server_default in the DB; we also set it here
            # so in-memory objects have a value before flush.
            timestamp=datetime.datetime.now(datetime.UTC),
        )
        self._repo.add(log)
