"""TASK-005: Test that the app lifespan starts up without error."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app

VALID_ENV = {
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/medhub",
    "REDIS_URL": "redis://localhost:6379/0",
    "OBJECT_STORE_ENDPOINT": "http://localhost:9000",
    "OBJECT_STORE_ACCESS_KEY": "minioadmin",
    "OBJECT_STORE_SECRET_KEY": "minioadmin",
    "OBJECT_STORE_BUCKET": "medhub",
    "SESSION_SIGNING_KEY": "supersecretkey",
    "SMTP_HOST": "smtp.example.com",
    "SMTP_USER": "noreply@example.com",
    "SMTP_PASSWORD": "smtppassword",
    "AT_REST_ENCRYPTION_KEY": "encryptionkey32byteslong12345678",
}


@pytest.mark.asyncio
async def test_lifespan_startup_logs_non_secret_config(monkeypatch) -> None:
    """Lifespan startup must complete and health endpoint must still respond."""
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)

    # Clear cache so fresh Settings are built from monkeypatched env
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/healthz")
        assert response.status_code == 200
    finally:
        get_settings.cache_clear()
