"""TASK-021: SessionService tests using fakeredis."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import fakeredis

from app.auth.session import SessionService, _account_sessions_key, _session_key
from app.db.models.account import Account, AccountStatus, UserType


def _redis() -> fakeredis.FakeRedis:  # type: ignore[type-arg]
    return fakeredis.FakeRedis()


def _make_account(user_type: UserType = UserType.PATIENT) -> Account:
    return Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _svc(r: fakeredis.FakeRedis) -> SessionService:  # type: ignore[type-arg]
    return SessionService(r)


# --- create_session ---


def test_create_session_returns_session_with_token() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    result = svc.create_session(acct, ip="1.2.3.4")
    s = result.session
    assert len(s.session_id) > 20
    assert s.account_id == acct.id
    assert s.role == UserType.PATIENT
    assert s.ip == "1.2.3.4"
    assert result.evicted_session_id is None


def test_create_session_stored_in_redis() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    result = svc.create_session(acct)
    assert r.exists(_session_key(result.session.session_id))


def test_create_session_adds_to_account_set() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    result = svc.create_session(acct)
    members = r.zrange(_account_sessions_key(str(acct.id)), 0, -1)
    ids = [m.decode() if isinstance(m, bytes) else m for m in members]
    assert result.session.session_id in ids


def test_create_session_clinical_ttl() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account(UserType.PATIENT)
    result = svc.create_session(acct)
    ttl = r.ttl(_session_key(result.session.session_id))
    assert 890 <= ttl <= 910  # 900s ± margin


def test_create_session_admin_ttl() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account(UserType.ADMIN)
    result = svc.create_session(acct)
    ttl = r.ttl(_session_key(result.session.session_id))
    assert 1790 <= ttl <= 1810


# --- concurrency cap ---


def test_concurrency_cap_evicts_oldest() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    # Create 3 sessions (at cap)
    s1 = svc.create_session(acct).session
    s2 = svc.create_session(acct).session
    s3 = svc.create_session(acct).session
    assert r.exists(_session_key(s1.session_id))
    assert r.exists(_session_key(s2.session_id))
    assert r.exists(_session_key(s3.session_id))
    # 4th should evict s1 (oldest)
    result4 = svc.create_session(acct)
    assert result4.evicted_session_id == s1.session_id
    assert not r.exists(_session_key(s1.session_id))
    assert r.exists(_session_key(s2.session_id))
    assert r.exists(_session_key(result4.session.session_id))


# --- resolve ---


def test_resolve_returns_session() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    s = svc.create_session(acct).session
    resolved = svc.resolve(s.session_id)
    assert resolved is not None
    assert resolved.account_id == acct.id


def test_resolve_returns_none_for_missing() -> None:
    r = _redis()
    svc = _svc(r)
    assert svc.resolve("nonexistent-id") is None


def test_resolve_returns_none_after_invalidate() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    s = svc.create_session(acct).session
    svc.invalidate(s.session_id)
    assert svc.resolve(s.session_id) is None


def test_resolve_refreshes_ttl() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account(UserType.PATIENT)  # 900s inactivity
    s = svc.create_session(acct).session
    # Manually reduce TTL
    r.expire(_session_key(s.session_id), 100)
    assert r.ttl(_session_key(s.session_id)) <= 100
    svc.resolve(s.session_id)
    # TTL should be refreshed back toward 900
    ttl_after = r.ttl(_session_key(s.session_id))
    assert ttl_after > 100


def test_resolve_returns_none_after_absolute_expiry() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    s = svc.create_session(acct).session

    # Fake "now" past absolute_expires_at
    future = s.absolute_expires_at + timedelta(seconds=1)
    with patch("app.auth.session.datetime") as mock_dt:
        mock_dt.now.return_value = future
        mock_dt.fromtimestamp.side_effect = datetime.fromtimestamp
        mock_dt.fromisoformat.side_effect = datetime.fromisoformat
        result = svc.resolve(s.session_id)
    assert result is None


# --- invalidate_all ---


def test_invalidate_all_removes_all_sessions() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    s1 = svc.create_session(acct).session
    s2 = svc.create_session(acct).session
    svc.invalidate_all(acct.id)
    assert not r.exists(_session_key(s1.session_id))
    assert not r.exists(_session_key(s2.session_id))
    assert not r.exists(_account_sessions_key(str(acct.id)))


def test_invalidate_all_is_idempotent() -> None:
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    svc.create_session(acct)
    svc.invalidate_all(acct.id)
    svc.invalidate_all(acct.id)  # second call must not raise
