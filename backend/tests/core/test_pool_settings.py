"""SR-026 AC 5, ADR-0022: thread and connection pools are sized together; a bad pair is refused."""

from __future__ import annotations

from typing import cast
from unittest.mock import patch

import anyio.to_thread
import pytest
from pydantic import ValidationError
from sqlalchemy.pool import QueuePool

from app.core.config import Settings, get_settings
from app.main import create_app


def test_defaults_satisfy_the_invariant() -> None:
    settings = get_settings()
    assert settings.api_threadpool_size <= settings.db_pool_size + settings.db_max_overflow


def test_startup_refuses_threadpool_larger_than_db_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    """The PRB-072 shape (40 threads, 15 connections) cannot be configured."""
    monkeypatch.setenv("API_THREADPOOL_SIZE", "40")
    monkeypatch.setenv("DB_POOL_SIZE", "5")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "10")
    with pytest.raises(ValidationError) as exc:
        Settings()  # type: ignore[call-arg]
    message = str(exc.value)
    assert "API_THREADPOOL_SIZE (40)" in message
    assert "15" in message


def test_threads_equal_to_connections_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_THREADPOOL_SIZE", "40")
    monkeypatch.setenv("DB_POOL_SIZE", "20")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "20")
    settings = Settings()  # type: ignore[call-arg]
    assert (settings.api_threadpool_size, settings.db_pool_timeout) == (40, 30)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("API_THREADPOOL_SIZE", "0"),
        ("DB_POOL_SIZE", "0"),
        ("DB_POOL_TIMEOUT", "0"),
        ("DB_MAX_OVERFLOW", "-1"),
    ],
)
def test_non_positive_pool_values_are_refused(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


@pytest.mark.asyncio
async def test_lifespan_refuses_to_start_with_threads_over_connections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_THREADPOOL_SIZE", "40")
    monkeypatch.setenv("DB_POOL_SIZE", "5")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "10")
    app = create_app()
    with pytest.raises(ValidationError):
        async with app.router.lifespan_context(app):
            pass


@pytest.mark.asyncio
async def test_lifespan_applies_the_thread_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_THREADPOOL_SIZE", "12")
    monkeypatch.setenv("DB_POOL_SIZE", "6")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "6")
    limiter = anyio.to_thread.current_default_thread_limiter()
    before = limiter.total_tokens
    app = create_app()
    try:
        with patch("app.modules.discovery.discover_modules", return_value=[]):
            async with app.router.lifespan_context(app):
                assert limiter.total_tokens == 12
    finally:
        limiter.total_tokens = before


def test_engine_pool_follows_the_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_THREADPOOL_SIZE", "8")
    monkeypatch.setenv("DB_POOL_SIZE", "4")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "4")
    monkeypatch.setenv("DB_POOL_TIMEOUT", "7")
    from app.db.repositories import session as session_module

    engine = session_module.get_engine.__wrapped__()
    try:
        pool = cast(QueuePool, engine.pool)
        assert pool.size() == 4
        assert pool._max_overflow == 4  # noqa: SLF001 - QueuePool exposes no public getter
        assert pool._timeout == 7  # noqa: SLF001
    finally:
        engine.dispose()


def test_redis_pool_is_bounded_by_the_thread_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_THREADPOOL_SIZE", "9")
    monkeypatch.setenv("DB_POOL_SIZE", "9")
    from app.api import deps

    deps._redis_client.cache_clear()  # noqa: SLF001
    try:
        client = deps.get_redis()
        assert client.connection_pool.max_connections == 9
        assert deps.get_redis() is client  # one client, one pool, not one per request
    finally:
        deps._redis_client.cache_clear()  # noqa: SLF001
