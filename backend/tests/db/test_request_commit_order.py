"""PRB-080 / ADR-0023: the request transaction ends before the response is sent.

SR-012 AC 5 (a 201 is sent only after the commit; a failed commit is a 5xx) and SR-008 AC 4 (a
revoke that was answered is in effect; one whose commit fails is not reported as done). Requests
go through ``create_app()`` with the real ``get_db`` against a PostgreSQL container. An ASGI
wrapper on the outside of the application notes the moment ``http.response.start`` goes out, and
``Session.commit`` is wrapped to note each commit, so the order is observed, not assumed.
"""

from __future__ import annotations

import contextlib
import io
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
from app.api.deps import get_current_user
from app.auth.password import PasswordService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.db.models.audit import AuditLog
from app.db.models.base import Base
from app.db.models.clinical import ClinicalEntry
from app.db.models.consent import ConsentGrant, ConsentSourceType
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
        for model in (AuditLog, Attachment, ClinicalEntry, ConsentGrant, Account):
            s.execute(delete(model))
        s.commit()


class _FakeStore:
    """Object-store stand-in for the upload: the bytes are not under test here."""

    def put_object(self, key: str, body: Any, size: int, content_type: str) -> None:
        body.read()

    def delete_object(self, key: str) -> None:
        return None


@pytest.fixture(autouse=True)
def _fake_store(monkeypatch) -> None:
    monkeypatch.setattr("app.core.object_storage.ObjectStorageClient", _FakeStore)


def _account(factory, user_type: UserType) -> Account:
    acct = Account(
        email=f"{uuid.uuid4().hex}@example.com",
        password_hash=PasswordService().hash("Correct-Horse-Battery-9!"),
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )
    with factory() as s:
        s.add(acct)
        s.commit()
        s.refresh(acct)
        s.expunge(acct)
    return acct


def _grant(factory, patient: Account, doctor: Account) -> uuid.UUID:
    grant = ConsentGrant(
        patient_id=patient.id,
        doctor_id=doctor.id,
        source_type=ConsentSourceType.MANUAL,
        active=True,
    )
    with factory() as s:
        s.add(grant)
        s.commit()
        return grant.id


class _Probe:
    """ASGI wrapper that records ``http.response.start`` in the shared event list."""

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
    original = Session.commit

    def _recording_commit(self: Session) -> None:
        log.append("commit")
        original(self)

    monkeypatch.setattr(Session, "commit", _recording_commit)
    return log


@pytest.fixture
def world(factory):
    doctor = _account(factory, UserType.DOCTOR)
    patient = _account(factory, UserType.PATIENT)
    grant_id = _grant(factory, patient, doctor)
    return doctor, patient, grant_id


def _client(events: list[str], actor: Account) -> TestClient:
    application = create_app()
    application.dependency_overrides[get_current_user] = lambda: actor
    client = TestClient(_Probe(application, events), raise_server_exceptions=False)
    client.cookies.set("medhub_csrf", "tok")
    client.headers["X-CSRF-Token"] = "tok"
    return client


def _entry_body() -> dict[str, str]:
    return {"occurredAt": datetime.now(UTC).isoformat(), "description": "Observed, stable."}


def test_success_response_is_sent_after_commit(factory, world, events) -> None:
    """SR-012 AC 5 (TC-007.14): the commit is recorded before the response starts, for a clinical
    entry and for an attachment; an immediate read by a second client returns the new entry."""
    doctor, patient, _ = world
    client = _client(events, doctor)

    created = client.post(f"/api/v1/patients/{patient.id}/clinical-entries", json=_entry_body())
    assert created.status_code == 201
    start = events.index("response_start")
    assert "commit" in events[:start]
    assert "commit" not in events[start:], events

    entry_id = created.json()["id"]
    reread = _client(events, doctor).get(f"/api/v1/patients/{patient.id}/clinical-entries")
    assert [e["id"] for e in reread.json()] == [entry_id]

    events.clear()
    upload = client.post(
        f"/api/v1/clinical-entries/{entry_id}/attachments",
        files={"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert upload.status_code == 201
    start = events.index("response_start")
    assert "commit" in events[:start]
    assert "commit" not in events[start:], events


@contextlib.contextmanager
def failing_commit() -> Iterator[None]:
    """``Session.commit`` raises inside the block; set-up and clean-up stay outside."""

    def _boom(self: Session) -> None:
        raise OperationalError("COMMIT", {}, Exception("connection lost"))

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Session, "commit", _boom)
        yield


def test_commit_failure_is_a_5xx_not_a_success(factory, world, events) -> None:
    """SR-012 AC 5 / SR-008 AC 4 (TC-007.14, TC-002.10): a commit that fails is reported as a
    5xx problem, never as the prepared 201 or 204, and the change is not stored."""
    doctor, patient, grant_id = world
    doctor_client = _client(events, doctor)
    patient_client = _client(events, patient)
    with failing_commit():
        created = doctor_client.post(
            f"/api/v1/patients/{patient.id}/clinical-entries", json=_entry_body()
        )
    assert 500 <= created.status_code < 600
    assert created.headers["content-type"].startswith("application/problem+json")
    with factory() as check:
        assert check.execute(select(ClinicalEntry)).scalars().all() == []

    with failing_commit():
        revoked = patient_client.delete(f"/api/v1/consents/{grant_id}")
    assert 500 <= revoked.status_code < 600
    with factory() as check:
        assert check.get(ConsentGrant, grant_id).active is True
