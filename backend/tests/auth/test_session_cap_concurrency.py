"""TC-001.6, TC-001.8, TC-001.9 (real Redis): the session cap and refresh hold under races.

SR-030 AC 7: at most ``SESSION_MAX_CONCURRENT`` (3) sessions per account, the oldest evicted,
also when logins race (PRB-023, RISK-005, TASK-199).
A refresh never re-creates an ended session (PRB-064) and expired members do not count toward
the cap (PRB-065), TASK-205. Runs against a real Redis server in a
container, started from the image pinned in ``infra/docker-compose.yml``; needs a Docker daemon.
"""

from __future__ import annotations

import re
import threading
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
import redis
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from app.auth.session import (
    CreateSessionResult,
    SessionService,
    _account_sessions_key,
    _session_key,
)
from app.db.models.account import Account, AccountStatus, UserType

CAP = 3
LOGINS = 10
REPETITIONS = 20

_COMPOSE = Path(__file__).resolve().parents[3] / "infra" / "docker-compose.yml"


def _pinned_redis_image() -> str:
    match = re.search(r"^\s+image:\s+(redis:\S+)\s*$", _COMPOSE.read_text(), re.MULTILINE)
    assert match, "no redis image in infra/docker-compose.yml"
    return match.group(1)


@pytest.fixture(scope="module")
def real_redis() -> Iterator[redis.Redis]:  # type: ignore[type-arg]
    container = (
        DockerContainer(_pinned_redis_image())
        .with_exposed_ports(6379)
        .waiting_for(LogMessageWaitStrategy("Ready to accept connections"))
    )
    with container:
        client: redis.Redis = redis.Redis(  # type: ignore[type-arg]
            host=container.get_container_host_ip(),
            port=int(container.get_exposed_port(6379)),
        )
        yield client
        client.close()


def _account() -> Account:
    return Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=UserType.PATIENT,
        status=AccountStatus.ACTIVE,
    )


@pytest.mark.parametrize("repetition", range(REPETITIONS))
def test_concurrent_logins_keep_exactly_the_cap(
    real_redis: redis.Redis,  # type: ignore[type-arg]
    repetition: int,
) -> None:
    """SR-030 AC 7: 10 simultaneous logins at the cap leave exactly 3 sessions, newest kept."""
    real_redis.flushdb()  # `session:*` keys below then belong to this repetition's account only
    account = _account()
    svc = SessionService(real_redis)
    account_key = _account_sessions_key(str(account.id))
    original = [svc.create_session(account).session.session_id for _ in range(CAP)]

    results: list[CreateSessionResult] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(LOGINS)

    def login() -> None:
        try:
            barrier.wait()
            results.append(svc.create_session(account))
        except BaseException as exc:  # noqa: BLE001 - surfaced by the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=login) for _ in range(LOGINS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors
    assert len(results) == LOGINS

    in_set = {m.decode() for m in real_redis.zrange(account_key, 0, -1)}  # type: ignore[union-attr]
    keys = {k.decode() for k in real_redis.scan_iter("session:*")}
    assert len(in_set) == CAP, f"{len(in_set)} sessions in the account set, cap is {CAP}"
    # Every remaining session has its key; every evicted session has none.
    assert {f"session:{sid}" for sid in in_set} == keys

    # The oldest are evicted: all three originals are gone and only new sessions remain ...
    assert in_set.isdisjoint(original)
    # ... and every login at the cap evicted exactly one session, each a different one, so the
    # evicted ids are exactly the sessions that no longer exist (no double eviction, no leak).
    new_ids = {r.session.session_id for r in results}
    evicted_ids = [r.evicted_session_id for r in results]
    assert None not in evicted_ids
    assert len(set(evicted_ids)) == LOGINS
    assert set(evicted_ids) == (set(original) | new_ids) - in_set


class _DeleteAfterGet:
    """Redis client proxy: after a GET of `key` returns, deletes it through a second connection."""

    def __init__(self, inner: redis.Redis, key: str) -> None:  # type: ignore[type-arg]
        self._inner = inner
        kwargs = inner.connection_pool.connection_kwargs
        self._other: redis.Redis = redis.Redis(  # type: ignore[type-arg]
            host=kwargs["host"], port=kwargs["port"]
        )
        self._key = key

    def get(self, name: str) -> bytes | None:
        value: bytes | None = self._inner.get(name)
        if name == self._key:
            self._other.delete(name)
        return value

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)


def test_refresh_racing_invalidate_never_recreates(
    real_redis: redis.Redis,  # type: ignore[type-arg]
) -> None:
    """TC-001.8, SR-030 AC 5 (PRB-064): a key deleted after the GET stays deleted."""
    real_redis.flushdb()
    account = _account()
    session_id = SessionService(real_redis).create_session(account).session.session_id
    key = _session_key(session_id)
    racing = SessionService(_DeleteAfterGet(real_redis, key))  # type: ignore[arg-type]
    assert racing.resolve(session_id) is None
    assert not real_redis.exists(key)
    assert SessionService(real_redis).resolve(session_id) is None


@pytest.mark.parametrize("repetition", range(REPETITIONS * 5 // 2))
def test_refresh_loop_racing_invalidate_leaves_the_session_ended(
    real_redis: redis.Redis,  # type: ignore[type-arg]
    repetition: int,
) -> None:
    """TC-001.8: a thread refreshing in a loop cannot bring back a session invalidated once."""
    real_redis.flushdb()
    account = _account()
    svc = SessionService(real_redis)
    session_id = svc.create_session(account).session.session_id
    stop = threading.Event()
    errors: list[BaseException] = []

    def refresh() -> None:
        try:
            while not stop.is_set():
                svc.resolve(session_id)
        except BaseException as exc:  # noqa: BLE001 - surfaced by the assertion below
            errors.append(exc)

    refresher = threading.Thread(target=refresh)
    refresher.start()
    time.sleep(0.005)
    svc.invalidate(session_id)
    time.sleep(0.01)
    stop.set()
    refresher.join()

    assert not errors, errors
    assert not real_redis.exists(_session_key(session_id))
    assert svc.resolve(session_id) is None


def _expire_newest(
    real_redis: redis.Redis,  # type: ignore[type-arg]
    svc: SessionService,
    account: Account,
) -> tuple[list[str], str]:
    """Three sessions at the cap, the NEWEST one expired (its id stays in the account set).

    Expiring the newest, not the oldest, is what separates counting live members from ranking
    all members: rank-based eviction removes a dead *oldest* id anyway (PRB-065).
    """
    original = [svc.create_session(account).session.session_id for _ in range(CAP)]
    dead = original[-1]
    real_redis.pexpire(_session_key(dead), 50)
    time.sleep(0.2)
    assert not real_redis.exists(_session_key(dead))
    return original, dead


@pytest.mark.parametrize("repetition", range(REPETITIONS))
def test_one_login_with_the_newest_member_expired_evicts_nothing(
    real_redis: redis.Redis,  # type: ignore[type-arg]
    repetition: int,
) -> None:
    """TC-001.9: two live plus one expired session are below the cap; nothing is evicted."""
    real_redis.flushdb()
    account = _account()
    svc = SessionService(real_redis)
    original, dead = _expire_newest(real_redis, svc, account)

    result = svc.create_session(account)

    assert result.evicted_session_id is None
    members = [m.decode() for m in real_redis.zrange(_account_sessions_key(str(account.id)), 0, -1)]  # type: ignore[union-attr]
    assert members == [original[0], original[1], result.session.session_id]
    assert real_redis.exists(_session_key(original[0]))


@pytest.mark.parametrize("repetition", range(REPETITIONS))
def test_concurrent_logins_with_expired_members_keep_cap_of_live(
    real_redis: redis.Redis,  # type: ignore[type-arg]
    repetition: int,
) -> None:
    """TC-001.9, SR-030 AC 7 (PRB-065): expired members are pruned; the set holds the live cap."""
    real_redis.flushdb()
    account = _account()
    svc = SessionService(real_redis)
    account_key = _account_sessions_key(str(account.id))
    original, dead = _expire_newest(real_redis, svc, account)

    results: list[CreateSessionResult] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(LOGINS)

    def login() -> None:
        try:
            barrier.wait()
            results.append(svc.create_session(account))
        except BaseException as exc:  # noqa: BLE001 - surfaced by the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=login) for _ in range(LOGINS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors
    in_set = {m.decode() for m in real_redis.zrange(account_key, 0, -1)}  # type: ignore[union-attr]
    assert len(in_set) == CAP, f"{len(in_set)} sessions in the account set, cap is {CAP}"
    assert dead not in in_set, "an expired id was left in the account set"
    assert all(real_redis.exists(_session_key(sid)) for sid in in_set)
    keys = {k.decode() for k in real_redis.scan_iter("session:*")}
    assert {f"session:{sid}" for sid in in_set} == keys
    # Only live sessions are evicted: the expired id is never reported, and exactly the
    # live ones beyond the cap are (2 original live + LOGINS new, minus the CAP that remain).
    evicted = [r.evicted_session_id for r in results if r.evicted_session_id is not None]
    assert dead not in evicted
    assert len(evicted) == 2 + LOGINS - CAP
