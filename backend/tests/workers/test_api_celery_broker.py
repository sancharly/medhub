"""PRB-071 / TASK-206: the API process dispatches Celery tasks through the configured broker.

The tasks are ``@shared_task``s, which bind to the *current* Celery app. Unless the API process
sets ``app.workers.celery_app`` as the default app, tasks use Celery's built-in one, whose broker is
``amqp://guest@localhost//``: every ``.delay()`` from the API then fails with "Connection refused"
(no activation e-mail, no session-kill propagation). The check runs in a worker thread, like a sync
FastAPI route: Celery's *current* app is thread-local, only the *default* app is global.

Each case runs in a fresh interpreter that starts the API's lifespan (module discovery patched
out), so another test's import of ``celery_app`` cannot hide it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[2]
_BROKER = "redis://broker-under-test:6379/5"

# (module, task) for every call site that dispatches from the API process.
_CALL_SITES = [
    ("app.workers.email_tasks", "send_activation_email"),  # account_service, activation (resend)
    ("app.workers.session_tasks", "propagate_session_kill"),  # lifecycle (deactivation)
    ("app.workers.email_tasks", "send_erasure_code_email"),  # erasure
    ("app.workers.email_tasks", "send_appointment_notification"),  # appointments
]


def _broker_seen_by_the_api(module: str, task: str) -> str:
    code = (
        "import asyncio\n"
        "from unittest.mock import patch\n"
        f"from {module} import {task} as t\n"  # before start-up
        "import app.main as m\n"
        "async def run():\n"
        "    with patch('app.modules.discovery.discover_modules', return_value=[]):\n"
        "        async with m._lifespan(m.create_app()):\n"
        "            uri = await asyncio.to_thread(lambda: t.app.connection_for_write().as_uri())\n"
        "            print('BROKER=' + uri)\n"
        "asyncio.run(run())\n"
    )
    env = {**os.environ, "REDIS_URL": _BROKER}
    env.pop("CELERY_BROKER_URL", None)
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=_BACKEND, env=env, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr[-800:]
    return next(ln[7:] for ln in result.stdout.splitlines() if ln.startswith("BROKER="))


@pytest.mark.parametrize(("module", "task"), _CALL_SITES, ids=[t for _, t in _CALL_SITES])
def test_api_process_binds_tasks_to_the_configured_broker(module: str, task: str) -> None:
    assert _broker_seen_by_the_api(module, task) == _BROKER
