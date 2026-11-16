"""TASK-228 (CR-006 D-30, PRB-084): overlapping retention sweeps erase a dataset once.

SR-024 AC 3, AC 5 (TS-004 TC-004.7). Real PostgreSQL (testcontainers). Session A plays the first
sweep: it deletes an expired dataset and writes the audit row without committing. The sweep under
test then reaches the same dataset, must wait on the row lock (seen in ``pg_stat_activity``, not
guessed with a sleep), and after A ends either finds the row gone (no second audit row) or, when A
rolled back, erases it itself.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import create_engine, delete, func, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
import app.workers.retention_tasks as rt
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.db.models.anonymized_dataset import AnonymizedDataset
from app.db.models.audit import AuditLog, AuditOutcome
from app.db.models.base import Base
from app.db.repositories.audit_repo import AuditRepository
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
        for model in (AuditLog, AnonymizedDataset):
            s.execute(delete(model))
        s.commit()


def _expired_dataset(factory: sessionmaker[Session]) -> uuid.UUID:
    with factory() as s:
        dataset = AnonymizedDataset(
            code_hash="h",
            payload={},
            retention_deadline=datetime.now(UTC) - timedelta(days=1),
        )
        s.add(dataset)
        s.commit()
        return dataset.id


def _first_sweep_holds_the_row(a: Session, dataset_id: uuid.UUID) -> None:
    dataset = a.get(AnonymizedDataset, dataset_id)
    a.delete(dataset)
    a.flush()
    AuditService(AuditRepository(a)).record(
        actor=None,
        action=AuditAction.ANONYMIZED_DATASET_ERASED,
        target_type="anonymized_dataset",
        target_id=str(dataset_id),
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )


def _wait_until_blocked(pg_engine: Any, thread: threading.Thread) -> None:
    deadline = time.monotonic() + 20
    query = text(
        "select count(*) from pg_stat_activity "
        "where wait_event_type = 'Lock' and query ilike '%anonymized_dataset%'"
    )
    while time.monotonic() < deadline:
        with pg_engine.connect() as conn:
            if conn.execute(query).scalar_one():
                return
        assert thread.is_alive(), "the sweep ended without waiting for the lock"
        time.sleep(0.05)
    raise AssertionError("the sweep never blocked on the row lock")


def _sweep_in_a_thread() -> tuple[threading.Thread, dict[str, Any]]:
    outcome: dict[str, Any] = {}

    def _run() -> None:
        outcome["result"] = rt.erase_expired_anonymized_datasets.apply().result

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread, outcome


def _audit_rows(factory: sessionmaker[Session], dataset_id: uuid.UUID) -> int:
    with factory() as s:
        return s.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.action == "ANONYMIZED_DATASET_ERASED",
                AuditLog.target_id == str(dataset_id),
            )
        ).scalar_one()


def test_second_sweep_waits_and_writes_no_audit_row(factory, pg_engine) -> None:
    """SR-024 AC 5: the first sweep's delete is uncommitted -> the second waits on the lock;
    when the first commits the second finds nothing: erased 0, failed 0, one audit row."""
    dataset_id = _expired_dataset(factory)
    with factory() as a:
        _first_sweep_holds_the_row(a, dataset_id)
        thread, outcome = _sweep_in_a_thread()
        _wait_until_blocked(pg_engine, thread)
        a.commit()
    thread.join(timeout=30)

    assert not thread.is_alive()
    assert outcome["result"] == {"erased": 0, "failed": 0}
    assert _audit_rows(factory, dataset_id) == 1
    with factory() as s:
        assert s.get(AnonymizedDataset, dataset_id) is None


def test_second_sweep_erases_after_the_first_rolls_back(factory, pg_engine) -> None:
    """SR-024 AC 3, AC 5: the first sweep rolls back -> the dataset is not skipped: the second
    erases it and writes exactly one audit row."""
    dataset_id = _expired_dataset(factory)
    with factory() as a:
        _first_sweep_holds_the_row(a, dataset_id)
        thread, outcome = _sweep_in_a_thread()
        _wait_until_blocked(pg_engine, thread)
        a.rollback()
    thread.join(timeout=30)

    assert not thread.is_alive()
    assert outcome["result"] == {"erased": 1, "failed": 0}
    assert _audit_rows(factory, dataset_id) == 1
    with factory() as s:
        assert s.get(AnonymizedDataset, dataset_id) is None


def test_locked_select_rechecks_the_deadline(factory) -> None:
    """SR-024 AC 3: the dataset statement is ``FOR UPDATE`` (no ``SKIP LOCKED``) and carries the
    deadline, so a dataset that is not due is not returned under the lock."""
    now = datetime.now(UTC)
    stmt = rt._locked_due_dataset(uuid.uuid4(), now)  # noqa: SLF001
    sql = str(stmt.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in sql and "SKIP LOCKED" not in sql
    assert "retention_deadline" in sql

    with factory() as s:
        future = AnonymizedDataset(
            code_hash="h", payload={}, retention_deadline=now + timedelta(days=1)
        )
        due = AnonymizedDataset(
            code_hash="h", payload={}, retention_deadline=now - timedelta(days=1)
        )
        s.add_all([future, due])
        s.flush()
        assert (
            s.execute(rt._locked_due_dataset(future.id, now)).scalar_one_or_none() is None
        )  # noqa: SLF001
        assert (
            s.execute(rt._locked_due_dataset(due.id, now)).scalar_one_or_none() is due
        )  # noqa: SLF001
