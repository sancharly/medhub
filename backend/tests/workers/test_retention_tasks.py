"""TASK-141 (CR-006): retention sweep isolation, session release and retries.

SR-024 AC 5 (a failure is isolated to its dataset, every session opened is closed, a transient
failure is retried at most 3 times, the failed count is logged without personal data; SR-043)
and SR-024 AC 4 / RISK-008 cause 7 (nothing is deleted before its deadline, across retries).

The database is a small in-memory fake that counts the sessions opened and closed, and applies a
delete only when its session commits, so a rollback leaves the dataset in place. The task runs
through ``Task.apply()``: Celery's own eager retry loop, ``max_retries`` included.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import app.workers.retention_tasks as rt

_PAST = timedelta(days=1)


def _dataset(expired: bool = True) -> SimpleNamespace:
    delta = -_PAST if expired else _PAST
    return SimpleNamespace(id=uuid.uuid4(), retention_deadline=datetime.now(UTC) + delta)


class _World:
    """The datasets table, the sessions handed out, and which deletes are made to fail."""

    def __init__(self, datasets: list[SimpleNamespace]) -> None:
        self.rows = {d.id: d for d in datasets}
        self.opened = 0
        self.closed = 0
        self.sweeps = 0
        self.fail: dict[uuid.UUID, int] = {}  # dataset id -> remaining failures (-1 = always)
        self.audited: list[str] = []

    def get_db(self) -> Any:
        self.opened += 1
        return iter([_FakeDb(self)])


class _FakeDb:
    def __init__(self, world: _World) -> None:
        self._w = world
        self._pending: list[uuid.UUID] = []

    def execute(self, _stmt: Any) -> Any:
        # The sweep's listing session: a new sweep starts here. Expired ids only.
        self._w.sweeps += 1
        now = datetime.now(UTC)
        ids = [i for i, d in self._w.rows.items() if d.retention_deadline <= now]
        result = MagicMock()
        result.scalars.return_value.all.return_value = ids
        return result

    def get(self, _model: Any, dataset_id: uuid.UUID) -> SimpleNamespace | None:
        return self._w.rows.get(dataset_id)

    def delete(self, dataset: SimpleNamespace) -> None:
        left = self._w.fail.get(dataset.id, 0)
        if left:
            if left > 0:
                self._w.fail[dataset.id] = left - 1
            raise ConnectionError("server closed the connection unexpectedly")
        self._pending.append(dataset.id)

    def flush(self) -> None:
        return None

    def commit(self) -> None:
        for i in self._pending:
            self._w.rows.pop(i, None)
        self._pending.clear()

    def rollback(self) -> None:
        self._pending.clear()

    def close(self) -> None:
        self._w.closed += 1


@pytest.fixture
def run_sweep():
    """Return ``run(world)``: the task through ``Task.apply()`` with the fake database."""
    audit_calls: list[dict[str, Any]] = []

    def _record(self: Any, **kwargs: Any) -> None:
        audit_calls.append(kwargs)

    def run(world: _World) -> Any:
        with (
            patch("app.db.repositories.session.get_db", side_effect=world.get_db),
            patch("app.audit.service.AuditService.record", _record),
            patch("app.audit.service.AuditService.__init__", return_value=None),
            patch("app.db.repositories.audit_repo.AuditRepository.__init__", return_value=None),
        ):
            return rt.erase_expired_anonymized_datasets.apply()

    run.audit_calls = audit_calls  # type: ignore[attr-defined]
    return run


def test_sweep_failing_dataset_closes_every_session(run_sweep) -> None:
    """SR-024 AC 5: a dataset whose delete raises is isolated; every session opened is closed
    and the datasets after it are still erased."""
    first, bad, last = _dataset(), _dataset(), _dataset()
    world = _World([first, bad, last])
    world.fail[bad.id] = -1

    run_sweep(world)

    assert world.opened == world.closed and world.opened >= 4  # listing + one per dataset
    assert first.id not in world.rows and last.id not in world.rows
    assert bad.id in world.rows


def test_sweep_retries_at_most_three_times_then_logs_count(run_sweep, caplog, monkeypatch) -> None:
    """SR-024 AC 5, SR-043: a transient error on every run gives 1 run + 3 retries; the final
    ERROR holds the failed count and no dataset field."""
    # An Alembic ``fileConfig`` in another test can leave existing loggers disabled.
    monkeypatch.setattr(logging.getLogger(rt.__name__), "disabled", False)
    bad_one, bad_two, fine = _dataset(), _dataset(), _dataset()
    world = _World([bad_one, bad_two, fine])
    world.fail[bad_one.id] = -1
    world.fail[bad_two.id] = -1

    with caplog.at_level(logging.INFO):
        run_sweep(world)

    assert world.sweeps == 4  # the first run and exactly three retries
    assert world.opened == world.closed
    final = [
        r for r in caplog.records if r.levelno == logging.ERROR and "gave up" in r.getMessage()
    ]
    assert len(final) == 1
    message = final[0].getMessage()
    assert "2" in message
    assert not hasattr(final[0], "dataset_id")
    for ds in (bad_one, bad_two, fine):
        assert str(ds.id) not in message


def test_sweep_dataset_failing_once_then_succeeding_is_erased(run_sweep) -> None:
    """SR-024 AC 5: a transient failure is retried and the dataset is erased by the retry."""
    flaky = _dataset()
    world = _World([flaky])
    world.fail[flaky.id] = 1

    run_sweep(world)

    assert world.sweeps == 2
    assert flaky.id not in world.rows
    assert [c["target_id"] for c in run_sweep.audit_calls] == [str(flaky.id)]
    assert world.opened == world.closed


def test_sweep_never_deletes_before_deadline_across_retries(run_sweep) -> None:
    """SR-024 AC 4, AC 5; RISK-008 cause 7: a dataset whose deadline is in the future is never
    deleted, in any run or retry, even if it is returned by the listing (its deadline moved
    between the listing and its own session)."""
    bad, future = _dataset(), _dataset(expired=False)
    world = _World([bad, future])
    world.fail[bad.id] = -1

    original = _FakeDb.execute

    def _listing_returns_everything(self: _FakeDb, stmt: Any) -> Any:
        result = original(self, stmt)
        result.scalars.return_value.all.return_value = list(self._w.rows)
        return result

    with patch.object(_FakeDb, "execute", _listing_returns_everything):
        run_sweep(world)

    assert world.sweeps == 4
    assert future.id in world.rows
    assert all(c["target_id"] != str(future.id) for c in run_sweep.audit_calls)
