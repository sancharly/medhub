"""TASK-228 (CR-006 D-30, PRB-083): the erasure code e-mail is sent only for a committed erasure.

SR-024 AC 6 (TS-004 TC-004.6), SR-043 (TS-017 TC-017.9). The task re-checks that the
``anonymized_dataset`` row with the erasure's id is visible to its own session before it sends:
absent -> ``self.retry`` (up to 14 times, 2 s doubling to 60 s), absent at the last check -> the
code is dropped; the check cannot be made at the last check -> the e-mail is sent anyway.
SMTP retries keep their own budget of 3.

The task runs through ``Task.apply()`` (Celery's eager retry loop); ``Task.retry`` is spied on
to read the countdowns and keyword arguments. The database is a fake that answers the check and
counts sessions; one test uses PostgreSQL (testcontainers).
"""

from __future__ import annotations

import logging
import smtplib
import uuid
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
import app.workers.email_tasks as et
from app.db.models.anonymized_dataset import AnonymizedDataset
from app.db.models.base import Base
from postgres_image import POSTGRES_IMAGE

ADDRESS = "a.person@example.org"
CODE = "RETRIEVAL-CODE-7F3K"
DATASET_ID = str(uuid.uuid4())
EXC_TEXT = "connection to server at db.internal refused for a.person@example.org"

_SCHEDULE = [2, 4, 8, 16, 32] + [60] * 9


class _Db:
    """Answers the commit check from the script and counts opens and closes."""

    def __init__(self, script: list[str]) -> None:
        self.script = script
        self.checks = 0
        self.opened = 0
        self.closed = 0

    def get_db(self) -> Any:
        self.opened += 1
        return iter([self._session()])

    def _session(self) -> Any:
        world = self

        class _Session:
            def execute(self, _stmt: Any) -> Any:
                outcome = world.script[min(world.checks, len(world.script) - 1)]
                world.checks += 1
                if outcome == "raise":
                    raise ConnectionError(EXC_TEXT)
                result = MagicMock()
                result.first.return_value = (
                    (uuid.UUID(DATASET_ID),) if outcome == "present" else None
                )
                return result

            def close(self) -> None:
                world.closed += 1

        return _Session()


@pytest.fixture
def run(monkeypatch: pytest.MonkeyPatch):
    """``run(script, smtp=None)``: the task through ``apply()``; returns (result, spy, send)."""
    monkeypatch.setattr(logging.getLogger(et.__name__), "disabled", False)

    def _run(script: list[str], smtp: Any = None):
        db = _Db(script)
        retries: list[dict[str, Any]] = []
        original = Task.retry

        def _spy(self: Task, *args: Any, **kwargs: Any) -> Any:
            retries.append(kwargs)
            return original(self, *args, **kwargs)

        send = MagicMock(side_effect=smtp)
        with (
            patch("app.db.repositories.session.get_db", side_effect=db.get_db),
            patch.object(et, "_send_smtp", send),
            patch.object(Task, "retry", _spy),
        ):
            result = et.send_erasure_code_email.apply(args=(ADDRESS, CODE, DATASET_ID))
        return result, retries, send, db

    return _run


def _commit_retries(retries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in retries if "exc" not in r]


def test_sends_when_the_dataset_is_committed(run) -> None:
    """SR-024 AC 6: the row is there on the first check -> one send, no retry."""
    result, retries, send, _ = run(["present"])

    assert result.successful()
    send.assert_called_once()
    assert retries == []


def test_rechecks_until_the_dataset_is_committed(run) -> None:
    """SR-024 AC 6: absent twice, then present -> two retries (2 s, 4 s; commit_checks 1, 2)
    and then one send."""
    result, retries, send, _ = run(["absent", "absent", "present"])

    assert [r["countdown"] for r in retries] == [2, 4]
    assert [r["kwargs"]["commit_checks"] for r in retries] == [1, 2]
    assert all("exc" not in r for r in retries)
    send.assert_called_once()
    assert result.state in {"RETRY", "SUCCESS"}


def test_drops_the_e_mail_when_the_erasure_never_commits(run, caplog) -> None:
    """SR-024 AC 6: never committed -> exactly 14 retries on the Design 1 schedule, no send,
    one WARNING, the task ends without raising."""
    with caplog.at_level(logging.INFO, logger=et.__name__):
        _, retries, send, _ = run(["absent"])

    assert [r["countdown"] for r in retries] == _SCHEDULE
    assert [r["kwargs"]["commit_checks"] for r in retries] == list(range(1, 15))
    send.assert_not_called()
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1 and DATASET_ID in warnings[0].getMessage()


def test_sends_when_the_commit_cannot_be_confirmed(run, caplog) -> None:
    """SR-024 AC 6: the check raises every time -> after the last re-check the e-mail is sent
    and a WARNING says the commit was not confirmed."""
    with caplog.at_level(logging.INFO, logger=et.__name__):
        _, retries, send, _ = run(["raise"])

    assert [r["countdown"] for r in retries] == _SCHEDULE
    send.assert_called_once()
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1 and DATASET_ID in warnings[0].getMessage()


def _refused(*_a: object, **_k: object) -> None:
    raise smtplib.SMTPRecipientsRefused({ADDRESS: (550, b"no")})


def test_smtp_retry_budget_unchanged_after_commit_checks(run) -> None:
    """TC-017.3 budget: one commit re-check, then SMTP failing every time -> exactly 3 SMTP
    retries (60, 120, 240 s) and the task raises; the commit re-check does not use them up."""
    result, retries, send, _ = run(["absent", "present"], smtp=_refused)

    assert result.failed()
    assert [r["countdown"] for r in retries] == [2, 60, 120, 240]
    assert len(_commit_retries(retries)) == 1
    assert send.call_count == 4  # first attempt + 3 SMTP retries


@pytest.mark.parametrize(
    "script", [["present"], ["absent"], ["raise"], ["absent", "present"]], ids=str
)
def test_commit_check_session_closed_on_every_path(run, script) -> None:
    """Sessions opened = sessions closed for present, absent, raising and mixed checks."""
    _, _, _, db = run(script)

    assert db.opened == db.checks > 0
    assert db.opened == db.closed


def test_erasure_e_mail_drop_and_unconfirmed_logs_hold_no_personal_data(run, caplog) -> None:
    """SR-043: the drop and the unconfirmed records name the dataset id and hold neither the
    address, the code nor the exception text; the re-check retries carry no ``exc``."""
    with caplog.at_level(logging.DEBUG, logger=et.__name__):
        _, drop_retries, _, _ = run(["absent"])
        _, unconfirmed_retries, _, _ = run(["raise"])

    records = [r for r in caplog.records if r.name == et.__name__ and r.levelno >= logging.WARNING]
    assert len(records) == 2
    for record in records:
        text = record.getMessage() + str(record.__dict__)
        assert DATASET_ID in text
        assert ADDRESS not in text and CODE not in text and "refused" not in text
        assert record.exc_info is None
    assert all("exc" not in r for r in drop_retries + unconfirmed_retries)


# --- real PostgreSQL ---------------------------------------------------------------------


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
    yield sessionmaker(bind=pg_engine)


def test_gate_does_not_see_an_uncommitted_erasure(factory) -> None:
    """SR-024 AC 6: an erasure transaction left open with its dataset flushed -> the check
    reports absent (READ COMMITTED); after the commit -> present."""
    from datetime import UTC, datetime, timedelta  # noqa: PLC0415

    dataset = AnonymizedDataset(
        code_hash="h",
        payload={},
        retention_deadline=datetime.now(UTC) + timedelta(days=365),
    )
    with factory() as erasure:
        erasure.add(dataset)
        erasure.flush()
        dataset_id = str(dataset.id)

        assert et._erasure_committed(dataset_id) is False  # noqa: SLF001

        erasure.commit()

    assert et._erasure_committed(dataset_id) is True  # noqa: SLF001
    assert et._erasure_committed(str(uuid.uuid4())) is False  # noqa: SLF001
