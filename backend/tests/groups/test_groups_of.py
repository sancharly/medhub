"""TC-005.x / TC-018.7 (real DB): ``GroupService.groups_of`` result and query count.

SR-014 AC 4 / RISK-004: the set of groups returned for an account must not change when the
lookup is rewritten (characterisation, written before the rewrite and green on the old code).
SR-026 AC 6 (TASK-220, PRB-024): the number of queries is constant, independent of the number of
memberships.

Order rule: ``groups_of`` has no ORDER BY, before and after the rewrite, so the order of the
returned groups is unspecified and the tests compare sorted ids.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register every model with Base.metadata
from app.authz.module_guard import ModuleAccessGuard
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.base import Base
from app.db.models.group import Group, GroupMembership, MembershipSource
from app.db.models.module import GroupModuleEnablement, ModuleRegistry
from app.db.repositories.group_repo import GroupRepository
from app.db.repositories.module_repo import ModuleRepository
from app.groups.service import GroupService
from postgres_image import POSTGRES_IMAGE

_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    with PostgresContainer(POSTGRES_IMAGE) as container:
        eng = create_engine(container.get_connection_url())
        Base.metadata.create_all(eng)
        yield eng
        eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    s = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


def _svc(session: Session) -> GroupService:
    return GroupService(
        GroupRepository(session),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        AuthorizationService(MagicMock(), MagicMock()),
    )


def _account(session: Session) -> Account:
    acct = Account(
        email=f"{uuid.uuid4()}@example.com",
        user_type=UserType.PATIENT,
        status=AccountStatus.ACTIVE,
    )
    session.add(acct)
    session.flush()
    return acct


def _groups(session: Session, n: int) -> list[Group]:
    groups = [Group(name=f"g-{uuid.uuid4()}") for _ in range(n)]
    session.add_all(groups)
    session.flush()
    return groups


def _join(session: Session, acct: Account, group: Group, source: MembershipSource) -> None:
    session.add(GroupMembership(group_id=group.id, account_id=acct.id, source=source))
    session.flush()


def _ids(groups: list[Group]) -> list[uuid.UUID]:
    return sorted(g.id for g in groups)


def test_groups_of_characterisation(session: Session) -> None:
    """The exact set of groups for 0, 1 and several AUTO and MANUAL memberships."""
    svc = _svc(session)
    g = _groups(session, 5)

    none = _account(session)
    assert svc.groups_of(none.id) == []

    one = _account(session)
    _join(session, one, g[0], MembershipSource.AUTO)
    assert _ids(svc.groups_of(one.id)) == _ids([g[0]])

    several = _account(session)
    _join(session, several, g[0], MembershipSource.AUTO)
    _join(session, several, g[1], MembershipSource.MANUAL)
    _join(session, several, g[2], MembershipSource.MANUAL)
    _join(session, several, g[3], MembershipSource.AUTO)
    # another account's memberships never leak in
    _join(session, one, g[4], MembershipSource.MANUAL)
    assert _ids(svc.groups_of(several.id)) == _ids(g[:4])
    assert _ids(svc.groups_of(one.id)) == _ids([g[0], g[4]])


def test_groups_of_lists_a_group_once_per_account(session: Session) -> None:
    """A group reached through AUTO and MANUAL appears once: the primary key allows one row."""
    svc = _svc(session)
    group = _groups(session, 1)[0]
    acct = _account(session)
    _join(session, acct, group, MembershipSource.AUTO)
    with pytest.raises(Exception, match="group_membership_pkey|duplicate key"):
        _join(session, acct, group, MembershipSource.MANUAL)
    session.rollback()
    group = _groups(session, 1)[0]
    acct = _account(session)
    _join(session, acct, group, MembershipSource.MANUAL)
    assert _ids(svc.groups_of(acct.id)) == _ids([group])


def test_groups_of_skips_a_membership_whose_group_is_missing(session: Session) -> None:
    """A membership row without a group row is skipped (today's behaviour)."""
    svc = _svc(session)
    group = _groups(session, 1)[0]
    acct = _account(session)
    _join(session, acct, group, MembershipSource.AUTO)
    session.execute(text("SET LOCAL session_replication_role = replica"))
    session.add(
        GroupMembership(group_id=uuid.uuid4(), account_id=acct.id, source=MembershipSource.MANUAL)
    )
    session.flush()
    assert _ids(svc.groups_of(acct.id)) == _ids([group])


def _count_queries(engine: Engine, fn) -> int:  # type: ignore[no-untyped-def]
    n = 0

    def _inc(*_args: object) -> None:
        nonlocal n
        n += 1

    event.listen(engine, "before_cursor_execute", _inc)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", _inc)
    return n


def test_groups_of_query_count_constant(engine: Engine, session: Session) -> None:
    """SR-026 AC 6: 1, 10 and 100 memberships cost the same number of queries."""
    svc = _svc(session)
    counts: dict[int, int] = {}
    for size in (1, 10, 100):
        acct = _account(session)
        for group in _groups(session, size):
            _join(session, acct, group, MembershipSource.MANUAL)
        session.flush()
        session.expire_all()  # the identity map must not hide the per-membership lookups
        counts[size] = _count_queries(engine, lambda: svc.groups_of(acct.id))
        assert len(svc.groups_of(acct.id)) == size
    assert counts[1] == counts[10] == counts[100], counts


def test_module_gate_query_count_constant(engine: Engine, session: Session) -> None:
    """SR-026 AC 6: the module-gating paths cost the same queries at 1, 10 and 100 memberships.

    Covers ``ModuleAccessGuard.is_module_enabled`` (every module route, ``api/deps.py``) and the
    two repository calls of ``GET /me/modules`` (``api/routers/me.py``).
    """
    key = f"mod-{uuid.uuid4()}"
    module = ModuleRegistry(module_key=key, name="m", version="1")
    session.add(module)
    session.flush()
    guard = ModuleAccessGuard(GroupRepository(session), ModuleRepository(session))
    group_repo, module_repo = GroupRepository(session), ModuleRepository(session)

    def _me_modules(account_id: uuid.UUID) -> list[str]:
        memberships = group_repo.memberships_for_account(account_id)
        return module_repo.enabled_module_keys_for_groups([m.group_id for m in memberships])

    gate: dict[int, int] = {}
    me: dict[int, int] = {}
    for size in (1, 10, 100):
        acct = _account(session)
        for group in _groups(session, size):
            _join(session, acct, group, MembershipSource.MANUAL)
            session.add(GroupModuleEnablement(group_id=group.id, module_id=module.id, enabled=True))
        session.flush()
        session.expire_all()
        gate[size] = _count_queries(engine, lambda: guard.is_module_enabled(acct.id, key))
        session.expire_all()
        me[size] = _count_queries(engine, lambda: _me_modules(acct.id))
        assert guard.is_module_enabled(acct.id, key)
        assert _me_modules(acct.id).count(key) == size
    assert gate[1] == gate[10] == gate[100], gate
    assert me[1] == me[10] == me[100], me
