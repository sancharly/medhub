"""Settings fixture for the DICOM module tests; the module is an installed package (CR-008)."""

from __future__ import annotations

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
    from app.core.config import Settings, get_settings

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for key, value in _BASELINE_ENV.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
