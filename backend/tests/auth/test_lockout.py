"""TASK-024: LockoutService tests using fakeredis."""

from __future__ import annotations

import uuid

import fakeredis
import pytest

from app.api.errors import AuthorizationError
from app.auth.lockout import MAX_FAILURES, LockoutService


def _svc(audit_svc=None) -> LockoutService:
    r = fakeredis.FakeRedis()
    return LockoutService(r, audit_svc)


def test_is_locked_false_initially() -> None:
    svc = _svc()
    acct_id = uuid.uuid4()
    assert svc.is_locked(acct_id) is False


def test_is_locked_false_for_none_account_id() -> None:
    svc = _svc()
    assert svc.is_locked(None) is False


def test_record_failure_locks_at_threshold() -> None:
    svc = _svc()
    acct_id = uuid.uuid4()
    email = "user@example.com"
    for _ in range(MAX_FAILURES):
        svc.record_failure(acct_id, email, "1.2.3.4")
    assert svc.is_locked(acct_id) is True


def test_record_failure_below_threshold_not_locked() -> None:
    svc = _svc()
    acct_id = uuid.uuid4()
    for _ in range(MAX_FAILURES - 1):
        svc.record_failure(acct_id, "user@example.com", None)
    assert svc.is_locked(acct_id) is False


def test_reset_clears_lockout() -> None:
    svc = _svc()
    acct_id = uuid.uuid4()
    for _ in range(MAX_FAILURES):
        svc.record_failure(acct_id, "user@example.com", None)
    assert svc.is_locked(acct_id) is True
    svc.reset(acct_id)
    assert svc.is_locked(acct_id) is False


def test_admin_unlock_requires_sysadmin() -> None:
    svc = _svc()
    acct_id = uuid.uuid4()
    with pytest.raises(AuthorizationError):
        svc.admin_unlock(acct_id, actor_role="ADMIN")


def test_admin_unlock_sysadmin_clears_lock() -> None:
    from unittest.mock import MagicMock
    mock_audit = MagicMock()
    svc = _svc(mock_audit)
    acct_id = uuid.uuid4()
    for _ in range(MAX_FAILURES):
        svc.record_failure(acct_id, "user@example.com", None)
    assert svc.is_locked(acct_id) is True
    svc.admin_unlock(acct_id, actor_role="SYSADMIN", ip="1.2.3.4")
    assert svc.is_locked(acct_id) is False


def test_admin_unlock_audits_event() -> None:
    from unittest.mock import MagicMock
    mock_audit = MagicMock()
    svc = _svc(mock_audit)
    acct_id = uuid.uuid4()
    svc.admin_unlock(acct_id, actor_role="SYSADMIN")
    mock_audit.record.assert_called_once()
    call_str = str(mock_audit.record.call_args)
    assert "ACCOUNT_UNLOCK" in call_str


def test_record_failure_without_account_id_uses_email_key() -> None:
    """Unknown accounts still track failures by email key."""
    r = fakeredis.FakeRedis()
    svc = LockoutService(r)
    for _ in range(3):
        svc.record_failure(None, "unknown@example.com", "5.6.7.8")
    # No account_id: is_locked(None) always False, but email key exists
    import hashlib
    key = f"lockout:{hashlib.sha256(b'unknown@example.com').hexdigest()}"
    assert int(r.get(key)) == 3


def test_is_email_locked_true_after_threshold_failures_unknown_account() -> None:
    """Email-keyed lock must be enforced even when account_id is None."""
    svc = _svc()
    email = "nonexistent@example.com"
    for _ in range(MAX_FAILURES):
        svc.record_failure(None, email, "9.8.7.6")
    assert svc.is_email_locked(email) is True


def test_is_email_locked_false_below_threshold() -> None:
    svc = _svc()
    email = "sparse@example.com"
    for _ in range(MAX_FAILURES - 1):
        svc.record_failure(None, email, None)
    assert svc.is_email_locked(email) is False


def test_admin_unlock_clears_email_key() -> None:
    """admin_unlock with email must also delete the email-keyed counter."""
    from unittest.mock import MagicMock
    mock_audit = MagicMock()
    r = fakeredis.FakeRedis()
    svc = LockoutService(r, mock_audit)
    acct_id = uuid.uuid4()
    email = "locked@example.com"
    for _ in range(MAX_FAILURES):
        svc.record_failure(acct_id, email, None)
    assert svc.is_email_locked(email) is True
    svc.admin_unlock(acct_id, actor_role="SYSADMIN", email=email)
    assert svc.is_email_locked(email) is False


def test_record_failure_locks_and_audits() -> None:
    from unittest.mock import MagicMock
    mock_audit = MagicMock()
    svc = _svc(mock_audit)
    acct_id = uuid.uuid4()
    for i in range(MAX_FAILURES):
        svc.record_failure(acct_id, "user@example.com", "1.2.3.4")
    # Audit should have been called with ACCOUNT_LOCKOUT
    calls_str = str(mock_audit.record.call_args_list)
    assert "ACCOUNT_LOCKOUT" in calls_str
