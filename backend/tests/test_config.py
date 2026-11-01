"""TASK-003: Settings and secrets management tests."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings

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
    "AT_REST_ENCRYPTION_KEY_ID": "test",
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
    assert "test-secret-key-24-chars-xx" not in r
    assert "supersecretkey" not in r
    assert "smtppassword" not in r
    assert "dGVzdGtleXRl" not in r


def test_get_settings_is_cached(monkeypatch) -> None:
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    get_settings.cache_clear()


def test_settings_builds_without_session_signing_key(monkeypatch) -> None:
    """TASK-140 SR-030: sessions are opaque, so no signing key is required (AC 5)."""
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("SESSION_SIGNING_KEY", raising=False)
    assert "session_signing_key" not in Settings.model_fields
    Settings()


def test_stale_session_signing_key_is_ignored(monkeypatch, tmp_path) -> None:
    """TASK-140 SR-030: an operator's leftover SESSION_SIGNING_KEY, in the environment or in
    the .env file, does not stop the app from starting."""
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("SESSION_SIGNING_KEY", "leftover-from-an-old-deployment")
    Settings()

    env_file = tmp_path / ".env"
    env_file.write_text("session_signing_key=leftover-from-an-old-deployment\n")
    monkeypatch.delenv("SESSION_SIGNING_KEY")
    Settings(_env_file=str(env_file))
    # case-insensitive, as environment variables are
    env_file.write_text("SESSION_SIGNING_KEY=leftover-from-an-old-deployment\n")
    Settings(_env_file=str(env_file))


def test_mistyped_key_in_env_file_is_refused(monkeypatch, tmp_path) -> None:
    """TASK-197 item 2: only the retired key is dropped; a typo such as TRUSTED_PROXIE fails."""
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    env_file = tmp_path / ".env"
    env_file.write_text("TRUSTED_PROXIE=10.0.0.0/8\n")
    with pytest.raises(ValidationError, match="(?i)trusted_proxie"):
        Settings(_env_file=str(env_file))


def test_smtp_without_user_starts_without_password(monkeypatch) -> None:
    """CR-004 Q-5: SMTP without authentication is supported."""
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("SMTP_USER")
    monkeypatch.delenv("SMTP_PASSWORD")
    s = Settings()
    assert s.smtp_user == "" and s.smtp_password is None


def test_smtp_user_without_password_is_refused_without_echoing_values(monkeypatch) -> None:
    """CR-004 Q-5: a user needs a password; the error names the setting, not a secret value."""
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("SMTP_PASSWORD")
    with pytest.raises(ValidationError) as exc:
        Settings()
    text = str(exc.value)
    assert "SMTP_PASSWORD" in text
    assert VALID_ENV["DATABASE_URL"] not in text and VALID_ENV["AT_REST_ENCRYPTION_KEY"] not in text


def test_validation_error_never_echoes_a_rejected_value(monkeypatch) -> None:
    """SR-041 AC 3, TS-015 TC-015.3: `hide_input_in_errors=True` keeps a rejected value out of text.

    A DATABASE_URL with the wrong scheme is rejected by the field type; with the flag off the
    error text would carry the whole input, password included. (``errors()`` keeps the input
    whatever the flag says; the start-up path prints the exception text, never ``errors()``.)
    """
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("DATABASE_URL", "mysql://u:SENTINEL@h:5432/d")
    with pytest.raises(ValidationError) as exc:
        Settings()
    assert "DATABASE_URL" in str(exc.value) or "database_url" in str(exc.value)
    assert "SENTINEL" not in str(exc.value)
