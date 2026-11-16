"""TC-018.6 (real DB): activation reads at most one account row (SR-026 AC 6, PRB-022 regression).

PRB-022 was rejected as already fixed (CR-006 D-1); this is the guard that keeps it fixed. The
statements that reach the ``account`` table and the rows they return are counted with 1 and with
1 000 accounts.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 - register every model
from app.auth.password import PasswordService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.base import Base
from app.db.repositories.account_repo import AccountRepository
from app.identity.activation import ActivationService, issue_activation_token
from postgres_image import POSTGRES_IMAGE

_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"

VALID_PW = "Str0ng!Pass#99"


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    with PostgresContainer(POSTGRES_IMAGE) as container:
        eng = create_engine(container.get_connection_url())
        Base.metadata.create_all(eng)
        yield eng
        eng.dispose()


def _activate_with(engine: Engine, others: int) -> tuple[list[str], int]:
    """Seed ``others`` + 1 accounts, activate one; return account statements and rows fetched."""
    with Session(engine) as session:
        session.execute(Account.__table__.delete())
        session.add_all(
            Account(
                id=uuid.uuid4(),
                email=f"other{n}@example.com",
                user_type=UserType.PATIENT,
                status=AccountStatus.INACTIVE,
            )
            for n in range(others)
        )
        target = Account(
            id=uuid.uuid4(),
            email="target@example.com",
            user_type=UserType.PATIENT,
            status=AccountStatus.INACTIVE,
        )
        raw = issue_activation_token(target)
        session.add(target)
        session.commit()
        target_id = target.id
        session.expire_all()  # the activation must read from the database, not the identity map

        statements: list[str] = []
        fetched = 0

        @event.listens_for(engine, "before_cursor_execute")
        def _count_statement(conn, cursor, statement, parameters, context, executemany):
            if "account" in statement:
                statements.append(statement)

        @event.listens_for(engine, "after_cursor_execute")
        def _count_rows(conn, cursor, statement, parameters, context, executemany):
            nonlocal fetched
            if "account" in statement and statement.lstrip().upper().startswith("SELECT"):
                fetched += cursor.rowcount

        try:
            svc = ActivationService(
                AccountRepository(session),
                PasswordService(),
                MagicMock(),
                AuthorizationService(MagicMock(), MagicMock()),
            )
            account = svc.activate(target_id, raw, VALID_PW)
            assert account.status == AccountStatus.ACTIVE
        finally:
            event.remove(engine, "before_cursor_execute", _count_statement)
            event.remove(engine, "after_cursor_execute", _count_rows)
        return statements, fetched


def test_activation_reads_one_account_row(engine):
    one_stmts, one_rows = _activate_with(engine, others=0)
    many_stmts, many_rows = _activate_with(engine, others=1_000)

    assert one_rows == 1
    assert many_rows == 1  # not the 1 001 rows a table scan would return
    assert len(many_stmts) == len(one_stmts)
