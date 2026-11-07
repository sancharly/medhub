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
    "DATABASE_URL": "postgresql://user:db-pw-8f3k2xq7@localhost:5432/medhub",
    "REDIS_URL": "redis://localhost:6379/0",
    "OBJECT_STORE_ENDPOINT": "http://localhost:9000",
    "OBJECT_STORE_ACCESS_KEY": "test-access-key",
    "OBJECT_STORE_SECRET_KEY": "test-secret-key-24-chars-xx",
    "OBJECT_STORE_BUCKET": "medhub",
    "SMTP_HOST": "localhost",
    "SMTP_USER": "test@example.com",
    "SMTP_PASSWORD": "testpassword",
    "AT_REST_ENCRYPTION_KEY": "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleTEyMzQ=",
    "AT_REST_ENCRYPTION_KEY_ID": "test",
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


@pytest.fixture(autouse=True)
def _restore_default_celery_app():
    """The API lifespan makes the configured Celery app the process default (PRB-071). A test that
    runs the lifespan must not leave it as the default for later tests, which would then dispatch
    ``.delay()`` calls to a broker that is not there."""
    from celery import _state

    saved = _state.default_app
    yield
    _state.default_app = saved
