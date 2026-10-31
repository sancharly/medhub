"""TASK-005: Test that the app lifespan starts up without error."""

import logging

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app

VALID_ENV = {
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/medhub",
    "REDIS_URL": "redis://localhost:6379/0",
    "OBJECT_STORE_ENDPOINT": "http://localhost:9000",
    "OBJECT_STORE_ACCESS_KEY": "test-access-key",
    "OBJECT_STORE_SECRET_KEY": "test-secret-key-24-chars-xx",
    "OBJECT_STORE_BUCKET": "medhub",
    "SMTP_HOST": "smtp.example.com",
    "SMTP_USER": "noreply@example.com",
    "SMTP_PASSWORD": "smtppassword",
    "AT_REST_ENCRYPTION_KEY": "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleTEyMzQ=",
}


@pytest.mark.asyncio
async def test_lifespan_startup_logs_non_secret_config(monkeypatch, caplog) -> None:
    """Lifespan startup must complete and health endpoint must still respond."""
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)

    # Clear cache so fresh Settings are built from monkeypatched env
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        app = create_app()
        transport = ASGITransport(app=app)
        with caplog.at_level(logging.INFO, logger="app.main"):
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/healthz")
        assert response.status_code == 200
        # smtp_host must not leak into startup logs
        assert VALID_ENV["SMTP_HOST"] not in caplog.text
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_lifespan_refuses_a_placeholder_secret_before_starting(monkeypatch) -> None:
    """SR-041 AC 3: the API start-up stops on a placeholder and names the setting, not the value."""
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("SMTP_PASSWORD", "changeme")

    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        app = create_app()
        with pytest.raises(SystemExit) as exc:
            async with app.router.lifespan_context(app):
                pass
        assert "SMTP_PASSWORD" in str(exc.value)
        assert "changeme" not in str(exc.value)
    finally:
        get_settings.cache_clear()
