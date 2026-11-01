"""TASK-197: the secret-setting rule (SR-041 AC 3, SR-022 AC 3, CR-004 Q-5, TS-015 TC-015.3)."""

from __future__ import annotations

import base64
import logging
import subprocess
import sys

import pytest

from app.core import secret_settings
from app.core.secret_settings import KNOWN_PLACEHOLDERS, SECRET_SETTINGS, check, enforce

GOOD_KEY = base64.urlsafe_b64encode(bytes(range(32))).decode()
GOOD = {
    "DATABASE_URL": "postgresql://medhub:Zx9Qw3Lm7Rt2Vb5N@postgres:5432/medhub",
    "SMTP_USER": "noreply@example.com",
    "SMTP_PASSWORD": "Kd83hf02Lqz9Pw41",
    "AT_REST_ENCRYPTION_KEY": GOOD_KEY,
    "OBJECT_STORE_ACCESS_KEY": "a1b2c3d4e5f6a1b2c3d4e5f6",
    "OBJECT_STORE_SECRET_KEY": "Zx9Qw3Lm7Rt2Vb5Nk8Hy4Jd6Fg1Sa0Pc",
}
HISTORICAL = [
    "changeme",
    "change-me-to-a-random-32-byte-secret",
    "change-me-to-a-random-32-byte-key!",
    "minioadmin",
]
PLACEHOLDERS = ["changeme", "CHANGEME", "change-me", "change-me-to-anything", *HISTORICAL]


def _env(**changes: str | None) -> dict[str, str | None]:
    env: dict[str, str | None] = dict(GOOD)
    env.update(changes)
    return env


def _with_secret(name: str, value: str | None) -> dict[str, str | None]:
    """GOOD with one secret setting replaced; the database one is a URL password."""
    if name == "DATABASE_URL":
        return _env(DATABASE_URL=None if value is None else f"postgresql://medhub:{value}@h/db")
    return _env(**{name: value})


def test_good_environment_passes() -> None:
    assert check(GOOD) == []


def test_every_historical_template_value_is_a_known_placeholder() -> None:
    # TASK-197 item 3: the template once shipped these.
    for value in HISTORICAL:
        assert value in KNOWN_PLACEHOLDERS


# SR-041 AC 3: unset, empty or placeholder -> one message naming the setting, never the value
@pytest.mark.parametrize(
    "name",
    [
        "DATABASE_URL",
        "SMTP_PASSWORD",
        "AT_REST_ENCRYPTION_KEY",
        "OBJECT_STORE_ACCESS_KEY",
        "OBJECT_STORE_SECRET_KEY",
    ],
)
@pytest.mark.parametrize("value", [None, "", "   ", *PLACEHOLDERS])
def test_missing_or_placeholder_secret_is_refused_by_name(name: str, value: str | None) -> None:
    messages = check(_with_secret(name, value))
    assert len(messages) >= 1
    assert all(name in m for m in messages)
    if value and value.strip():
        assert all(value not in m for m in messages)


def test_database_url_without_a_password_is_refused() -> None:
    messages = check(_env(DATABASE_URL="postgresql://medhub@postgres:5432/medhub"))
    assert len(messages) == 1 and "DATABASE_URL" in messages[0]


@pytest.mark.parametrize(
    "name", ["DATABASE_OWNER_URL", "OBJECT_STORE_SSE_KEY", "AT_REST_ENCRYPTION_RETIRED_KEYS"]
)
def test_optional_secret_is_checked_only_when_present(name: str) -> None:
    assert check(_env(**{name: None})) == []
    assert check(_env(**{name: ""})) == []
    placeholder = "postgresql://owner:changeme@h/db" if name == "DATABASE_OWNER_URL" else "changeme"
    messages = check(_env(**{name: placeholder}))
    assert messages and all(name in m for m in messages)
    assert all("changeme" not in m for m in messages)


def test_each_retired_key_is_checked() -> None:
    other = base64.urlsafe_b64encode(bytes(range(1, 33))).decode()
    assert check(_env(AT_REST_ENCRYPTION_RETIRED_KEYS=f"{other},{GOOD_KEY}")) == []
    messages = check(_env(AT_REST_ENCRYPTION_RETIRED_KEYS=f"{other},changeme"))
    assert messages and all("AT_REST_ENCRYPTION_RETIRED_KEYS" in m for m in messages)


# SR-022 AC 3 / SR-041 AC 3: the key decodes to exactly 32 bytes
@pytest.mark.parametrize("size", [31, 33])
def test_wrong_length_at_rest_key_is_refused(size: int) -> None:
    key = base64.urlsafe_b64encode(bytes(range(size))).decode()
    messages = check(_env(AT_REST_ENCRYPTION_KEY=key))
    assert len(messages) == 1 and "AT_REST_ENCRYPTION_KEY" in messages[0]
    assert key not in messages[0]


def test_32_byte_at_rest_key_is_accepted() -> None:
    assert check(_env(AT_REST_ENCRYPTION_KEY=GOOD_KEY)) == []


def test_non_base64_at_rest_key_is_refused_without_the_value() -> None:
    value = "not base64 !!! with spaces"
    messages = check(_env(AT_REST_ENCRYPTION_KEY=value))
    assert messages and all("AT_REST_ENCRYPTION_KEY" in m and value not in m for m in messages)


# CR-004 Q-5: SMTP without authentication starts; with a user and no password it is refused
@pytest.mark.parametrize("password", [None, "", "changeme"])
def test_smtp_user_set_requires_a_real_password(password: str | None) -> None:
    messages = check(_env(SMTP_PASSWORD=password))
    assert messages and all("SMTP_PASSWORD" in m for m in messages)


@pytest.mark.parametrize("user", [None, "", "  "])
def test_smtp_without_user_needs_no_password(user: str | None) -> None:
    assert check(_env(SMTP_USER=user, SMTP_PASSWORD=None)) == []
    assert check(_env(SMTP_USER=user, SMTP_PASSWORD="changeme")) == []


def test_enforce_raises_system_exit_naming_the_setting_not_the_value(caplog) -> None:
    secret = "change-me-to-a-random-32-byte-secret"
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(SystemExit) as exc:
            enforce(_env(OBJECT_STORE_SECRET_KEY=secret))
    assert "OBJECT_STORE_SECRET_KEY" in str(exc.value)
    assert secret not in str(exc.value) and secret not in caplog.text


def test_enforce_accepts_good_environment() -> None:
    enforce(GOOD)


def test_enforce_without_argument_checks_the_configured_settings(monkeypatch) -> None:
    from app.core.config import get_settings  # noqa: PLC0415

    monkeypatch.setenv("SMTP_PASSWORD", "changeme")
    get_settings.cache_clear()
    with pytest.raises(SystemExit, match="SMTP_PASSWORD"):
        enforce()


def test_object_store_rule_shares_the_placeholder_list() -> None:
    """The preflight and the start-up check use one list (TASK-197 item 1)."""
    from app.core import object_store_credentials  # noqa: PLC0415

    assert object_store_credentials.KNOWN_DEFAULTS is secret_settings.KNOWN_DEFAULTS
    assert object_store_credentials.check("change-me-to-anything", GOOD["OBJECT_STORE_SECRET_KEY"])


def test_secret_settings_list_names_every_checked_setting() -> None:
    assert set(SECRET_SETTINGS) >= {
        "DATABASE_URL",
        "DATABASE_OWNER_URL",
        "SMTP_PASSWORD",
        "AT_REST_ENCRYPTION_KEY",
        "AT_REST_ENCRYPTION_RETIRED_KEYS",
        "OBJECT_STORE_SSE_KEY",
        "OBJECT_STORE_ACCESS_KEY",
        "OBJECT_STORE_SECRET_KEY",
    }


def test_preflight_module_runs_without_application_settings() -> None:
    """The preflight imports the shared rule with no application settings in its environment."""
    env = {"PATH": "/usr/bin:/bin", "OBJECT_STORE_ACCESS_KEY": "x", "OBJECT_STORE_SECRET_KEY": ""}
    proc = subprocess.run(
        [sys.executable, "-m", "app.core.object_store_credentials"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1 and "OBJECT_STORE_SECRET_KEY" in proc.stderr


# TASK-191 / ADR-0017: the runtime role and the owner role differ in name and in password
OWNER = "postgresql://medhub:Hy4Jd6Fg1Sa0PcZx@postgres:5432/medhub"
RUNTIME = "postgresql://medhub_app:Zx9Qw3Lm7Rt2Vb5N@postgres:5432/medhub"


def test_distinct_owner_and_runtime_roles_pass() -> None:
    assert check(_env(DATABASE_URL=RUNTIME, DATABASE_OWNER_URL=OWNER)) == []


def test_runtime_url_naming_the_owner_user_is_refused() -> None:
    messages = check(
        _env(
            DATABASE_URL=OWNER.replace("Hy4Jd6Fg1Sa0PcZx", "Zx9Qw3Lm7Rt2Vb5N"),
            DATABASE_OWNER_URL=OWNER,
        )
    )
    assert any("same database user" in m for m in messages)


def test_runtime_password_equal_to_the_owner_password_is_refused_without_the_value() -> None:
    messages = check(_env(DATABASE_URL=RUNTIME, DATABASE_OWNER_URL=RUNTIME.replace("_app", "")))
    assert any("same password" in m for m in messages)
    assert not any("Zx9Qw3Lm7Rt2Vb5N" in m for m in messages)


def test_owner_url_placeholder_is_refused() -> None:
    owner = "postgresql://medhub:change-me@postgres:5432/medhub"
    assert any(
        "DATABASE_OWNER_URL" in m
        for m in check(_env(DATABASE_URL=RUNTIME, DATABASE_OWNER_URL=owner))
    )
