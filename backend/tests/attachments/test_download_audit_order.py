"""SR-023 AC 10, SR-013 AC 5 (TC-007.15, TC-009.13; ADR-0023): download audit rows precede the body.

Real PostgreSQL, the real ``get_db`` on the runtime role and the real services. The storage stub
runs a probe when it produces the first chunk of pass 2, i.e. while the response is being sent:
the probe reads the audit rows on a separate connection and the pool's checked-out count.
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
from app.api.deps import get_current_user
from app.audit.actions import AuditAction
from app.auth.password import PasswordService
from app.db import roles
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.db.models.audit import AuditLog, AuditOutcome
from app.db.models.base import Base
from app.db.models.clinical import ClinicalEntry
from app.db.models.consent import ConsentGrant, ConsentSourceType
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.session import DbSession
from app.main import create_app
from postgres_image import POSTGRES_IMAGE
from tests.attachments.fake_object_store import FakeObjectStore

DATA = b"0123456789abcdef"  # four 4-byte chunks (CHUNK patched below)


@pytest.fixture(scope="module")
def pg_engine():
    with PostgresContainer(POSTGRES_IMAGE) as container:
        engine = create_engine(container.get_connection_url())
        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture(scope="module")
def runtime_engine(pg_engine):
    roles.apply(pg_engine, "medhub_app", "runtime-pw-4k9x2m7q")
    engine = create_engine(
        pg_engine.url.set(username="medhub_app", password="runtime-pw-4k9x2m7q"),
        pool_size=2,
        max_overflow=0,
    )
    yield engine
    engine.dispose()


class _ProbingStore(FakeObjectStore):
    """Runs ``probe`` when the first chunk of pass 2 is produced (the response is being sent)."""

    def __init__(self, *args: Any, probe=None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._probe = probe
        self.pass2_chunks = 0

    def get_object_stream(self, key, if_match=None):
        chunks, etag = super().get_object_stream(key, if_match)
        if self.stream_reads != 2:
            return chunks, etag

        def _counted() -> Iterator[bytes]:
            for chunk in chunks:
                if self.pass2_chunks == 0 and self._probe is not None:
                    self._probe()
                self.pass2_chunks += 1
                yield chunk

        return _counted(), etag


@pytest.fixture
def world(pg_engine, runtime_engine, monkeypatch):
    monkeypatch.setattr("app.db.repositories.session.get_engine", lambda: runtime_engine)
    monkeypatch.setattr("tests.attachments.fake_object_store.CHUNK", 4)
    owner = sessionmaker(bind=pg_engine)

    def _account(user_type: UserType) -> Account:
        acct = Account(
            email=f"{uuid.uuid4().hex}@example.com",
            password_hash=PasswordService().hash("Correct-Horse-Battery-9!"),
            user_type=user_type,
            status=AccountStatus.ACTIVE,
        )
        with owner() as s:
            s.add(acct)
            s.commit()
            s.refresh(acct)
            s.expunge(acct)
        return acct

    doctor, patient = _account(UserType.DOCTOR), _account(UserType.PATIENT)
    with owner() as s:
        s.add(
            ConsentGrant(
                patient_id=patient.id,
                doctor_id=doctor.id,
                source_type=ConsentSourceType.MANUAL,
                active=True,
            )
        )
        s.flush()
        from datetime import UTC, datetime  # noqa: PLC0415

        entry = ClinicalEntry(
            patient_id=patient.id,
            author_doctor_id=doctor.id,
            occurred_at=datetime.now(UTC),
            description="x",
        )
        s.add(entry)
        s.flush()
        attachment = Attachment(
            clinical_entry_id=entry.id,
            patient_id=patient.id,
            filename="a.bin",
            content_type="application/octet-stream",
            size=len(DATA),
            storage_key="attachments/a.bin",
            checksum=hashlib.sha256(DATA).hexdigest(),
        )
        s.add(attachment)
        s.commit()
        attachment_id = attachment.id
    yield doctor, attachment_id, owner
    with owner() as s:
        for model in (AuditLog, Attachment, ClinicalEntry, ConsentGrant, Account):
            s.execute(delete(model))
        s.commit()


def _rows(owner, attachment_id) -> list[tuple[str, AuditOutcome]]:
    """Audit rows of the download, oldest first (read on a connection of their own)."""
    with owner() as s:
        rows = s.execute(select(AuditLog).order_by(AuditLog.timestamp, AuditLog.id)).scalars().all()
        return [(r.action, r.outcome) for r in rows]


def _download(world, monkeypatch, store: FakeObjectStore, **client_kwargs: Any):
    doctor, attachment_id, _ = world
    monkeypatch.setattr("app.core.object_storage.ObjectStorageClient", lambda: store)

    def _actor(db: DbSession) -> Account:
        # Loaded on the request session, as get_current_user does: expired by the commit and
        # detached by the close before the response generator runs.
        return AccountRepository(db).get_by_id(doctor.id)  # type: ignore[return-value]

    application = create_app()
    application.dependency_overrides[get_current_user] = _actor
    client = TestClient(application, raise_server_exceptions=False, **client_kwargs)
    return client.get(f"/api/v1/attachments/{attachment_id}")


def test_success_rows_are_committed_before_the_first_body_chunk(
    world, pg_engine, runtime_engine, monkeypatch
) -> None:
    """(a) and (d): both rows are visible on another connection when the first chunk of pass 2 is
    produced, and the download holds no pooled connection during the transfer."""
    _, attachment_id, owner = world
    seen: dict[str, Any] = {}

    def _probe() -> None:
        seen["rows"] = _rows(owner, attachment_id)
        seen["checked_out"] = runtime_engine.pool.checkedout()

    store = _ProbingStore(DATA, probe=_probe)
    resp = _download(world, monkeypatch, store)

    assert resp.status_code == 200 and resp.content == DATA
    assert (AuditAction.AUTHZ_ALLOWED, AuditOutcome.SUCCESS) in seen["rows"]
    assert (AuditAction.ATTACHMENT_ACCESS, AuditOutcome.SUCCESS) in seen["rows"]
    assert seen["checked_out"] == 0  # (d)


def test_failed_commit_of_the_success_row_serves_no_byte(world, monkeypatch) -> None:
    """(b): the commit of the SUCCESS rows fails -> 5xx, no body byte, no SUCCESS row stored."""
    _, attachment_id, owner = world
    store = _ProbingStore(DATA)

    def _boom(self: Session) -> None:
        raise OperationalError("COMMIT", {}, Exception("connection lost"))

    monkeypatch.setattr(Session, "commit", _boom)
    resp = _download(world, monkeypatch, store)
    monkeypatch.undo()

    assert 500 <= resp.status_code < 600
    assert DATA not in resp.content and store.pass2_chunks == 0
    assert (AuditAction.ATTACHMENT_ACCESS, AuditOutcome.SUCCESS) not in _rows(owner, attachment_id)


def test_pass_two_mismatch_after_the_response_started_adds_a_failure_row(
    world, monkeypatch
) -> None:
    """(c): the transfer is aborted, the SUCCESS rows stay and one FAILURE row follows, written
    from the generator after the request session is closed (no DetachedInstanceError)."""
    _, attachment_id, owner = world
    store = _ProbingStore(DATA, second_read_bytes=b"0123456789abcdeX")
    resp = _download(world, monkeypatch, store, client=("203.0.113.9", 5000))

    assert resp.content != DATA and b"X" not in resp.content
    rows = _rows(owner, attachment_id)
    assert rows == [
        (AuditAction.AUTHZ_ALLOWED, AuditOutcome.SUCCESS),
        (AuditAction.ATTACHMENT_ACCESS, AuditOutcome.SUCCESS),
        (AuditAction.ATTACHMENT_ACCESS, AuditOutcome.FAILURE),
    ]
