"""Root test conftest.

Two responsibilities:
1. Prevent pydantic-settings from loading the local .env file (gitignored, only for dev).
2. Provide baseline env vars so unit tests that instantiate services don't need to
   set up the full environment themselves.  Individual tests may override specific vars
   via additional monkeypatch.setenv calls.
3. Clear the get_settings() LRU cache before/after each test so monkeypatched env vars
   are always picked up fresh.
"""

import pytest

_BASELINE_ENV = {
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/medhub",
    "REDIS_URL": "redis://localhost:6379/0",
    "OBJECT_STORE_ENDPOINT": "http://localhost:9000",
    "OBJECT_STORE_ACCESS_KEY": "minioadmin",
    "OBJECT_STORE_SECRET_KEY": "minioadmin",
    "OBJECT_STORE_BUCKET": "medhub",
    "SESSION_SIGNING_KEY": "test-signing-key-at-least-32-bytes-long!",
    "SMTP_HOST": "localhost",
    "SMTP_USER": "test@example.com",
    "SMTP_PASSWORD": "testpassword",
    "AT_REST_ENCRYPTION_KEY": "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGs=",
}


@pytest.fixture(autouse=True)
def _test_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch out .env file loading and provide baseline env vars for all tests."""
    from app.core.config import Settings, get_settings

    # Prevent the local .env file from being loaded
    monkeypatch.setitem(Settings.model_config, "env_file", None)

    # Provide required fields so services can call get_settings() without errors
    for key, value in _BASELINE_ENV.items():
        monkeypatch.setenv(key, value)

    # Clear the LRU cache so monkeypatched vars are picked up
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
