"""AuditService — server-assigned timestamps, credential scrubbing (SR-023)."""

import datetime
import re
import uuid

from app.audit.actions import AuditAction
from app.core.client_address import current_client_address
from app.core.module_key import MODULE_KEY
from app.db.models.audit import AuditLog, AuditOutcome
from app.db.repositories.audit_repo import AuditRepository

# Pattern matches key=value pairs that look credential-like
_CREDENTIAL_PATTERN = re.compile(
    r"\b(password|passwd|secret|token|key|credential)s?\s*=\s*\S+",
    re.IGNORECASE,
)

# Events committed on their own transaction although their outcome is SUCCESS: the lockout
# is recorded inside a failing login that ends in a 401 (ADR-0016).
_INDEPENDENT_ACTIONS = frozenset({AuditAction.ACCOUNT_LOCKOUT})


# Closed set of audit fields (SR-023 AC 5, AC 9, ADD-013): a value outside these shapes is
# refused, whatever field it arrives under, so a secret cannot be stored by mistake.
_USER_TYPE_ID = re.compile(r"user_type:(DOCTOR|PATIENT|ADMIN|SYSADMIN)")
_UUID = "uuid"
_UUID_PAIR = "uuid:uuid"
_UUID_MODULE = "uuid:module"
_MODULE = "module"
_NONE = "none"
# target_type -> the one shape its target_id may take (None is always allowed).
_TARGETS: dict[str, str] = {
    "account": _UUID,
    "appointment": _UUID,
    "attachment": _UUID,
    "clinical_entry": _UUID,
    "consent": _UUID,
    "consent_grant": _UUID,
    "group": _UUID,
    "patient_roster": _UUID,
    "anonymized_dataset": _UUID,
    "group_membership": _UUID_PAIR,
    "group_module": _UUID_MODULE,
    "module": _MODULE,
    "module_registry": _NONE,
}
_ACTIONS = frozenset(v for k, v in vars(AuditAction).items() if k.isupper() and isinstance(v, str))


class AuditFieldError(ValueError):
    """An audit field is outside its closed shape. The message names the field, never the value."""


def _is_uuid(value: str) -> bool:
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False


def _target_id_ok(target_type: str, target_id: str) -> bool:
    shape = _TARGETS[target_type]
    if shape == _UUID:
        return _is_uuid(target_id) or (
            target_type == "account" and _USER_TYPE_ID.fullmatch(target_id) is not None
        )
    if shape == _MODULE:
        return MODULE_KEY.fullmatch(target_id) is not None
    head, _, tail = target_id.partition(":")
    if not _is_uuid(head):
        return False
    if shape == _UUID_PAIR:
        return _is_uuid(tail)
    return shape == _UUID_MODULE and MODULE_KEY.fullmatch(tail) is not None


def _validate(action: str, target_type: str | None, target_id: str | None) -> None:
    if action not in _ACTIONS:
        raise AuditFieldError("audit field 'action' is not a known AuditAction")
    if target_type is not None and target_type not in _TARGETS:
        raise AuditFieldError("audit field 'target_type' is not a known target type")
    if target_id:  # an empty id (a decision with no resource id) carries nothing
        if target_type is None or not _target_id_ok(target_type, target_id):
            raise AuditFieldError("audit field 'target_id' is not a permitted identifier shape")


def _scrub(value: str) -> str:
    """Remove credential-like key=value pairs from a string.

    Defence in depth only: ``action`` and ``target_type`` are closed sets and ``target_id`` a
    closed shape (``_validate``), so a value that reaches here is already one of those.
    """
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
        When ``ip`` is None the originating client address of the current request is used
        (SR-023 AC 6, SR-042); outside a request there is none and the row records no address.
        An event is independent when its outcome is FAILURE or its action is in
        ``_INDEPENDENT_ACTIONS``: it is committed at once on its own session, so it survives
        the request ending in an error (get_db rolls the request session back on any
        exception). An independent row is not atomic with the request (ADR-0016). Every
        other event joins the request transaction.
        Raises ``AuditFieldError`` before anything is written when ``action``, ``target_type``
        or ``target_id`` is outside its closed shape (SR-023 AC 9).
        Raises on persistence failure — never swallows exceptions.
        """
        _validate(action, target_type, target_id)
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
            ip=ip if ip is not None else current_client_address(),
            # timestamp has a server_default in the DB; we also set it here
            # so in-memory objects have a value before flush.
            timestamp=datetime.datetime.now(datetime.UTC),
        )
        if outcome is AuditOutcome.FAILURE or action in _INDEPENDENT_ACTIONS:
            self._repo.add_independent(log)
        else:
            self._repo.add(log)
