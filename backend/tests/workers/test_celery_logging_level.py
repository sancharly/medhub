"""TASK-206 slice C (TASK-138 QA follow-up): the worker and beat honour ``--loglevel``."""

from __future__ import annotations

import json
import logging

import pytest

from app.core.logging import configure_logging


def _receiver():
    # Imported inside the tests, as in test_celery_start_up.py: see the note there.
    from app.workers import celery_app  # noqa: PLC0415

    return celery_app._configure_worker_logging


@pytest.fixture(autouse=True)
def _restore_root():
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    root.handlers, root.level = handlers, level


def test_receiver_with_loglevel_debug_sets_the_root_level() -> None:
    _receiver()(loglevel=logging.DEBUG)
    assert logging.getLogger().level == logging.DEBUG


def test_receiver_accepts_a_level_name() -> None:
    _receiver()(loglevel="WARNING")
    assert logging.getLogger().level == logging.WARNING


def test_receiver_without_loglevel_defaults_to_info() -> None:
    _receiver()()
    assert logging.getLogger().level == logging.INFO
    _receiver()(loglevel=None)
    assert logging.getLogger().level == logging.INFO


def test_configure_logging_defaults_to_info() -> None:
    configure_logging()
    assert logging.getLogger().level == logging.INFO


def test_debug_record_is_emitted_redacted(capsys) -> None:
    _receiver()(loglevel=logging.DEBUG)
    logging.getLogger("app.workers.test").debug(
        "sending", extra={"detail": "ada@example.org", "recipient": "ada@example.org"}
    )
    out = capsys.readouterr().out
    assert out, "the DEBUG record was not emitted"
    assert "ada@example.org" not in out
    record = json.loads(out.strip().splitlines()[-1])
    assert record["level"] == "DEBUG"


def test_debug_task_message_does_not_carry_the_task_arguments(capsys) -> None:
    """SR-043 AC 4: at --loglevel=debug Celery logs the task headers, with ``argsrepr`` (the
    activation token and the account id) and ``kwargsrepr``. Both values are replaced."""
    _receiver()(loglevel=logging.DEBUG)
    headers = {
        "task": "workers.send_activation_email",
        "argsrepr": "('63425424-731e-410c-91a9-32f1ecd2ca07', 'TOKEN-abc_123')",
        "kwargsrepr": "{'activation_token': 'TOKEN-abc_123'}",
        "origin": "gen7@host",
    }
    logging.getLogger("celery.pool").debug(
        "TaskPool: Apply %s (args:%s kwargs:%s)", "<function fast_trace_task>", (headers,), {}
    )
    out = capsys.readouterr().out
    assert "TOKEN-abc_123" not in out
    assert "63425424-731e-410c-91a9-32f1ecd2ca07" not in out
    assert "workers.send_activation_email" in out  # the record stays useful
    assert json.loads(out.strip().splitlines()[-1])["logger"] == "celery.pool"
