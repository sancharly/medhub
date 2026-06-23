"""Configure sys.path so both dicom_viewer and app are importable in DICOM module tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add backend/ (for app.*) and backend/modules/dicom_viewer/ (for dicom_viewer.*)
_backend = Path(__file__).parent.parent.parent.parent  # backend/
_dicom_pkg = Path(__file__).parent.parent  # backend/modules/dicom_viewer/

for _p in [str(_backend), str(_dicom_pkg)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

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
    from app.core.config import Settings, get_settings

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for key, value in _BASELINE_ENV.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
