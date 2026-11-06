"""TC-001.6 (real Redis): the concurrent-session cap holds under simultaneous logins.

SR-030 AC 7: at most ``SESSION_MAX_CONCURRENT`` (3) sessions per account, the oldest evicted,
also when logins race (PRB-023, RISK-005, TASK-199). Runs against a real Redis server in a
container, started from the image pinned in ``infra/docker-compose.yml``; needs a Docker daemon.
"""

from __future__ import annotations

import re
import threading
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
import redis
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from app.auth.session import CreateSessionResult, SessionService, _account_sessions_key
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
