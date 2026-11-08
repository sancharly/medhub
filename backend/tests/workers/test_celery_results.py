"""TASK-207: dispatching a task never waits on a result store (finding 1 of the TASK-206 review)."""

from __future__ import annotations

import re
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
SOURCE_DIRS = (BACKEND / "app", BACKEND / "modules")


def test_task_ignore_result_is_set() -> None:
    # Imported inside the test: see test_celery_start_up.py.
    from app.workers.celery_app import celery_app  # noqa: PLC0415

    assert celery_app.conf.task_ignore_result is True


def test_no_code_reads_a_task_result() -> None:
    """With ``task_ignore_result`` no result exists to read: keep it that way."""
    offenders: list[str] = []
    for directory in SOURCE_DIRS:
        for path in directory.rglob("*.py"):
            for number, line in enumerate(path.read_text().splitlines(), start=1):
                code = line.split("#", 1)[0]
                uses_value = re.search(r"(=|return|\()\s*[\w.]+\.delay\(", code) or re.search(
                    r"\.delay\([^)]*\)\s*\.", code
                )
                if "AsyncResult" in code or uses_value:
                    offenders.append(f"{path.relative_to(BACKEND)}:{number}")
    assert offenders == []


def test_enqueue_with_unreachable_redis_fails_fast() -> None:
    from celery import Celery  # noqa: PLC0415

    from app.workers.celery_app import celery_app  # noqa: PLC0415

    # Closed port: nothing listens on 1 (privileged, unused).
    url = "redis://127.0.0.1:1/0"
    app = Celery("scratch", broker=url, backend=url)
    # The setting under test is the real application's, so removing it there fails this test.
    app.conf.update(task_ignore_result=celery_app.conf.task_ignore_result)

    @app.task
    def noop() -> None:  # pragma: no cover - never runs
        return None

    started = time.monotonic()
    try:
        noop.delay()
    except Exception:  # noqa: BLE001 - raising is as fast a failure as returning
        pass
    assert time.monotonic() - started < 5
