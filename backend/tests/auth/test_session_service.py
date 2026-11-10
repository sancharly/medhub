"""TASK-021: SessionService tests using fakeredis."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import fakeredis
import pytest

from app.auth.session import (
    _MAX_CAP_ATTEMPTS,
    SessionCapContentionError,
    SessionService,
    _account_sessions_key,
    _session_key,
)
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


def test_cap_holds_over_many_sequential_logins() -> None:
    """SR-030 AC 7 (sequential): never more than 3 sessions; each login past the cap evicts one."""
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    results = [svc.create_session(acct) for _ in range(8)]
    ids = [x.session.session_id for x in results]
    assert svc.list_account_session_ids(acct.id) == ids[-3:]
    assert [x.evicted_session_id for x in results] == [None, None, None, *ids[:5]]
    assert len(r.keys("session:*")) == 3


# --- expired members and score (TASK-205, PRB-065; TASK-199 QA finding 1) ---


def _expire(r: fakeredis.FakeRedis, session_id: str) -> None:  # type: ignore[type-arg]
    """Simulate inactivity expiry: the session key is gone, its id stays in the account set."""
    r.delete(_session_key(session_id))


def _members(r: fakeredis.FakeRedis, acct: Account) -> list[str]:  # type: ignore[type-arg]
    raw = r.zrange(_account_sessions_key(str(acct.id)), 0, -1)
    return [m.decode() if isinstance(m, bytes) else m for m in raw]


def test_cap_ignores_expired_members() -> None:
    """SR-030 AC 7: an expired session does not count toward the cap and is pruned."""
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    a, b, c = (svc.create_session(acct).session.session_id for _ in range(3))
    _expire(r, b)
    result = svc.create_session(acct)
    assert result.evicted_session_id is None
    assert r.exists(_session_key(a)) and r.exists(_session_key(c))
    assert _members(r, acct) == [a, c, result.session.session_id]


def test_cap_evicts_oldest_live_not_dead() -> None:
    """SR-030 AC 7: A (oldest, live), B (dead), C, D live at the cap: the next login evicts A."""
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    a, b, c = (svc.create_session(acct).session.session_id for _ in range(3))
    _expire(r, b)
    d = svc.create_session(acct).session.session_id  # prunes b; a, c, d live: at the cap
    # Re-introduce the dead id, as an expiry between two logins would leave it.
    r.zadd(_account_sessions_key(str(acct.id)), {b: 0.5})
    result = svc.create_session(acct)
    assert result.evicted_session_id == a
    assert not r.exists(_session_key(a))
    assert r.exists(_session_key(c)) and r.exists(_session_key(d))
    assert r.exists(_session_key(result.session.session_id))
    assert _members(r, acct) == [c, d, result.session.session_id]


def test_new_member_score_above_a_future_scored_member() -> None:
    """Score = commit order: never below the newest existing score; the seeded member goes first."""
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    key = _account_sessions_key(str(acct.id))
    future = datetime.now(UTC).timestamp() + 10
    r.set(_session_key("future"), "{}")
    r.zadd(key, {"future": future})
    first = svc.create_session(acct).session.session_id
    assert r.zscore(key, first) > future
    second = svc.create_session(acct)
    assert second.evicted_session_id is None  # future, first, second = 3 = cap
    third = svc.create_session(acct)
    assert third.evicted_session_id == "future"


def _interfere_on_zrange(
    monkeypatch: pytest.MonkeyPatch, r: fakeredis.FakeRedis, account_key: str, times: int  # type: ignore[type-arg]
) -> list[int]:
    """Write to the account's set between WATCH and EXEC the first `times` times."""
    pipe_cls = type(r.pipeline())
    real = pipe_cls.zrange
    calls = [0]

    def zrange(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        out = real(self, *args, **kwargs)
        calls[0] += 1
        if calls[0] <= times:
            r.set(_session_key(f"rival-{calls[0]}"), "{}")  # a live session ...
            r.zadd(account_key, {f"rival-{calls[0]}": 1.0})  # ... of a concurrent login
        return out

    monkeypatch.setattr(pipe_cls, "zrange", zrange)
    return calls


def test_cap_transaction_retries_after_concurrent_write(monkeypatch: pytest.MonkeyPatch) -> None:
    """SR-030 AC 7: a write between WATCH and EXEC aborts the attempt; the retry re-reads."""
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    key = _account_sessions_key(str(acct.id))
    for _ in range(2):
        svc.create_session(acct)
    calls = _interfere_on_zrange(monkeypatch, r, key, times=1)
    result = svc.create_session(acct)
    assert calls[0] == 2  # one aborted attempt, one that committed
    # The retry saw the rival: 2 + rival at the cap, so the oldest (the rival, score 1.0) went.
    assert result.evicted_session_id == "rival-1"
    assert r.zcard(key) == 3
    assert r.exists(_session_key(result.session.session_id))


def test_cap_transaction_gives_up_after_bounded_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    """SR-030 AC 7: contention that never clears raises instead of looping or skipping the cap."""
    r = _redis()
    svc = _svc(r)
    acct = _make_account()
    key = _account_sessions_key(str(acct.id))
    calls = _interfere_on_zrange(monkeypatch, r, key, times=10_000)
    with pytest.raises(SessionCapContentionError):
        svc.create_session(acct)
    assert calls[0] == _MAX_CAP_ATTEMPTS
    # nothing stored without the cap applied (only the interference's rival keys exist)
    assert all(k.startswith(b"session:rival-") for k in r.keys("session:*"))


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


class _DeleteAfterGet:
    """Redis client proxy: deletes a key right after a GET of it returns (a racing logout)."""

    def __init__(self, inner: fakeredis.FakeRedis, key: str) -> None:  # type: ignore[type-arg]
        self._inner = inner
        self._key = key

    def get(self, name: str) -> bytes | None:
        value: bytes | None = self._inner.get(name)
        if name == self._key:
            self._inner.delete(name)
        return value

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)


def test_resolve_does_not_recreate_a_deleted_session() -> None:
    """SR-030 AC 5 (PRB-064): a key deleted after resolve()'s GET is not written back."""
    r = _redis()
    acct = _make_account()
    s = _svc(r).create_session(acct).session
    racing = SessionService(_DeleteAfterGet(r, _session_key(s.session_id)))  # type: ignore[arg-type]
    assert racing.resolve(s.session_id) is None
    assert not r.exists(_session_key(s.session_id))
    assert _svc(r).resolve(s.session_id) is None


def test_resolve_refreshes_ttl_of_a_live_session() -> None:
    """Sliding TTL unchanged by the conditional write; the key is rewritten with fresh last_seen."""
    r = _redis()
    svc = _svc(r)
    s = svc.create_session(_make_account(UserType.PATIENT)).session
    r.expire(_session_key(s.session_id), 100)
    resolved = svc.resolve(s.session_id)
    assert resolved is not None
    assert 890 <= r.ttl(_session_key(s.session_id)) <= 910


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
