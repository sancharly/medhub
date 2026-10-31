"""TASK-197: the worker and beat refuse placeholder secrets at start-up (SR-041 AC 3)."""

from __future__ import annotations

import pytest


def _module():
    # Imported inside the tests: importing celery_app at collection time makes later tests that
    # dispatch tasks try to reach the Redis broker.
    from app.workers import celery_app  # noqa: PLC0415

    return celery_app


def test_worker_init_and_beat_init_run_the_secret_rule() -> None:
    from celery.signals import beat_init, worker_init  # noqa: PLC0415

    handler = _module()._enforce_secret_settings
    for signal in (worker_init, beat_init):
        receivers = [r() for _, r in signal.receivers]
        assert handler in receivers


def test_worker_init_handler_stops_on_a_placeholder(monkeypatch) -> None:
    from app.core.config import get_settings  # noqa: PLC0415

    monkeypatch.setenv("OBJECT_STORE_SECRET_KEY", "changeme")
    get_settings.cache_clear()
    with pytest.raises(SystemExit) as exc:
        _module()._enforce_secret_settings(sender=None)
    assert "OBJECT_STORE_SECRET_KEY" in str(exc.value) and "changeme" not in str(exc.value)


def test_worker_init_handler_accepts_good_settings() -> None:
    _module()._enforce_secret_settings(sender=None)
