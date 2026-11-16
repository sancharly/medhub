"""TASK-141 (CR-006 D-5, D-11, D-21): an erasure whose e-mail cannot be enqueued is rolled back.

SR-024 AC 6 (TS-004 TC-004.4). Requests go through ``create_app()`` with the real ``get_db``
(``DbSession``, ``scope="function"``, ADR-0023) against a PostgreSQL container, so the rollback
is the request transaction's own, not a mock's. An ASGI wrapper notes ``http.response.start`` and
``Session.rollback`` / ``Session.commit`` are wrapped, so the order is observed: the transaction
ends before the 503 goes out. The broker failure is ``send_erasure_code_email.delay`` raising.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from unittest.mock import patch

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
from app.api.deps import get_current_user, get_session_service
from app.auth.password import PasswordService
from app.auth.session import SessionService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.anonymized_dataset import AnonymizedDataset
from app.db.models.audit import AuditLog
from app.db.models.base import Base
from app.main import create_app
from postgres_image import POSTGRES_IMAGE


@pytest.fixture(scope="module")
def pg_engine():
    with PostgresContainer(POSTGRES_IMAGE) as container:
        engine = create_engine(container.get_connection_url())
        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def factory(pg_engine, monkeypatch) -> Iterator[sessionmaker[Session]]:
    monkeypatch.setattr("app.db.repositories.session.get_engine", lambda: pg_engine)
    maker = sessionmaker(bind=pg_engine)
    yield maker
    with maker() as s:
        for model in (AuditLog, AnonymizedDataset, Account):
            s.execute(delete(model))
        s.commit()


def _account(factory, user_type: UserType, **extra: object) -> Account:
    acct = Account(
        email=f"{uuid.uuid4().hex}@example.com",
        password_hash=PasswordService().hash("Correct-Horse-Battery-9!"),
        user_type=user_type,
        status=AccountStatus.ACTIVE,
        **extra,
    )
    with factory() as s:
        s.add(acct)
        s.commit()
        s.refresh(acct)
        s.expunge(acct)
    return acct


class _Probe:
    def __init__(self, app, events: list[str]) -> None:
        self._app = app
        self._events = events

    async def __call__(self, scope, receive, send) -> None:
        async def _send(message) -> None:
            if message["type"] == "http.response.start":
                self._events.append("response_start")
            await send(message)

        await self._app(scope, receive, _send)


@pytest.fixture
def events(monkeypatch) -> list[str]:
    log: list[str] = []
    commit, rollback = Session.commit, Session.rollback

    def _commit(self: Session) -> None:
        log.append("commit")
        commit(self)

    def _rollback(self: Session) -> None:
        log.append("rollback")
        rollback(self)

    monkeypatch.setattr(Session, "commit", _commit)
    monkeypatch.setattr(Session, "rollback", _rollback)
    return log


@pytest.fixture
def world(factory, events):
    admin = _account(factory, UserType.SYSADMIN)
    target = _account(factory, UserType.PATIENT, first_name="Alice", surname="Smith")
    redis_client = fakeredis.FakeRedis()
    sessions = SessionService(redis_client)
    live = sessions.create_session(target).session

    application = create_app()
    application.dependency_overrides[get_current_user] = lambda: admin
    application.dependency_overrides[get_session_service] = lambda: sessions
    client = TestClient(_Probe(application, events), raise_server_exceptions=False)
    client.cookies.set("medhub_csrf", "tok")
    client.headers["X-CSRF-Token"] = "tok"
    events.clear()  # the set-up commits are not the request's
    return client, target, live, redis_client


def _erase(client: TestClient, target: Account):
    return client.request(
        "DELETE",
        f"/api/v1/accounts/{target.id}",
        json={"confirmEmail": target.email, "confirmAccountType": "PATIENT"},
    )


def test_erasure_enqueue_failure_rolls_back_and_returns_503(factory, world, events) -> None:
    """SR-024 AC 6: the broker is down. 503 problem with Retry-After; the account, its PII, its
    sessions are unchanged; no anonymized dataset and no erasure audit row; the rollback happens
    before the response is sent."""
    client, target, live, redis_client = world

    with patch(
        "app.workers.email_tasks.send_erasure_code_email.delay",
        side_effect=ConnectionError("redis://:secret@broker:6379 down"),
    ):
        response = _erase(client, target)

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["retry-after"]
    body = response.json()
    assert body["type"].endswith("/erasure-notification-unavailable")
    assert target.email not in response.text and "secret" not in response.text

    start = events.index("response_start")
    assert "rollback" in events[:start] and "commit" not in events[:start], events

    with factory() as check:
        account = check.get(Account, target.id)
        assert account.status == AccountStatus.ACTIVE
        assert account.email == target.email
        assert (account.first_name, account.surname) == ("Alice", "Smith")
        assert account.password_hash is not None
        assert check.execute(select(AnonymizedDataset)).scalars().all() == []
        actions = set(check.execute(select(AuditLog.action)).scalars())
        assert not actions & {"ACCOUNT_DELETED", "DATA_ANONYMIZED"}
    assert redis_client.exists(f"session:{live.session_id}")


def test_erasure_with_a_working_broker_commits_before_the_response(factory, world, events) -> None:
    """Control: with the broker up the same request erases, the commit precedes the response and
    the sessions are gone (so the failure test above is not passing for an unrelated reason)."""
    client, target, live, redis_client = world

    with patch("app.workers.email_tasks.send_erasure_code_email.delay") as delay:
        response = _erase(client, target)

    assert response.status_code == 200
    delay.assert_called_once()
    start = events.index("response_start")
    assert "commit" in events[:start]
    with factory() as check:
        assert check.get(Account, target.id).status == AccountStatus.DELETED
        assert len(check.execute(select(AnonymizedDataset)).scalars().all()) == 1
        actions = set(check.execute(select(AuditLog.action)).scalars())
        assert {"ACCOUNT_DELETED", "DATA_ANONYMIZED"} <= actions
    assert not redis_client.exists(f"session:{live.session_id}")
