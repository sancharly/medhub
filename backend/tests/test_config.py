"""TASK-003: Settings and secrets management tests."""
import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings

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


def test_settings_loads_with_complete_env(monkeypatch) -> None:
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    settings = Settings()
    assert settings.environment == "local"
    assert settings.smtp_port == 587


def test_missing_required_field_raises_validation_error(monkeypatch) -> None:
    """Missing DATABASE_URL must raise ValidationError (fail-fast)."""
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("DATABASE_URL")
    with pytest.raises(ValidationError):
        Settings()


def test_secret_str_not_revealed_in_repr(monkeypatch) -> None:
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    settings = Settings()
    r = repr(settings)
    # SecretStr values must not appear in repr
    assert "minioadmin" not in r
    assert "supersecretkey" not in r
    assert "smtppassword" not in r
    assert "encryptionkey" not in r


def test_get_settings_is_cached(monkeypatch) -> None:
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    get_settings.cache_clear()
