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
    "AT_REST_ENCRYPTION_KEY_ID": "k1",
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
    placeholder = {
        "DATABASE_OWNER_URL": "postgresql://owner:changeme@h/db",
        "AT_REST_ENCRYPTION_RETIRED_KEYS": "old:changeme",
    }.get(name, "changeme")
    messages = check(_env(**{name: placeholder}))
    assert messages and all(name in m for m in messages)
    assert all("changeme" not in m for m in messages)


OTHER_KEY = base64.urlsafe_b64encode(bytes(range(1, 33))).decode()
THIRD_KEY = base64.urlsafe_b64encode(bytes(range(2, 34))).decode()
RETIRED = "AT_REST_ENCRYPTION_RETIRED_KEYS"


def test_each_retired_key_is_checked() -> None:
    """SR-022 AC 3: every ``id:key`` entry is validated."""
    assert check(_env(**{RETIRED: f"old:{OTHER_KEY},older:{THIRD_KEY}"})) == []
    messages = check(_env(**{RETIRED: f"old:{OTHER_KEY},older:changeme"}))
    assert messages and all(RETIRED in m for m in messages)
    assert all("changeme" not in m for m in messages)


# SR-022 AC 6: the key identifier is required and well formed
@pytest.mark.parametrize("value", [None, "", "  "])
def test_key_id_is_required(value: str | None) -> None:
    messages = check(_env(AT_REST_ENCRYPTION_KEY_ID=value))
    assert messages == ["AT_REST_ENCRYPTION_KEY_ID is not set"]


@pytest.mark.parametrize(
    "value", ["K1", "k_1", "k:1", "a" * 33, "k 1", "clé", " k1", "k1 ", "k1\n"]
)
def test_malformed_key_id_is_refused(value: str) -> None:
    messages = check(_env(AT_REST_ENCRYPTION_KEY_ID=value))
    assert messages and all("AT_REST_ENCRYPTION_KEY_ID" in m for m in messages)


@pytest.mark.parametrize("value", ["k1", "2026-11", "a" * 32, "0"])
def test_well_formed_key_id_is_accepted(value: str) -> None:
    assert check(_env(AT_REST_ENCRYPTION_KEY_ID=value)) == []


# SR-022 AC 6 / ADR-0018: duplicate ids, a retired key equal to the current one, bad entries
def test_retired_key_with_the_current_id_is_refused() -> None:
    messages = check(_env(**{RETIRED: f"k1:{OTHER_KEY}"}))
    assert len(messages) == 1 and RETIRED in messages[0] and "k1" in messages[0]


def test_duplicate_retired_ids_are_refused() -> None:
    messages = check(_env(**{RETIRED: f"old:{OTHER_KEY},old:{THIRD_KEY}"}))
    assert len(messages) == 1 and "repeats the key id" in messages[0]


def test_retired_key_equal_to_the_current_key_is_refused_without_the_value() -> None:
    messages = check(_env(**{RETIRED: f"old:{GOOD_KEY}"}))
    assert len(messages) == 1 and "same key as AT_REST_ENCRYPTION_KEY" in messages[0]
    assert GOOD_KEY not in messages[0]


@pytest.mark.parametrize(
    "entry", [OTHER_KEY, f":{OTHER_KEY}", f"Old:{OTHER_KEY}", f"old:{OTHER_KEY[:-4]}"]
)
def test_malformed_retired_entry_is_refused_without_the_value(entry: str) -> None:
    messages = check(_env(**{RETIRED: entry}))
    assert messages and all(RETIRED in m for m in messages)
    assert all(OTHER_KEY not in m and entry not in m for m in messages)


def test_retired_key_of_the_wrong_length_is_refused() -> None:
    short = base64.urlsafe_b64encode(bytes(range(31))).decode()
    messages = check(_env(**{RETIRED: f"old:{short}"}))
    assert len(messages) == 1 and "32 bytes" in messages[0]


# SR-022 AC 3: whitespace is refused, not stripped. The id is written into every ciphertext
# exactly as configured, so "k1 " would produce values that can never be read back.
WHITESPACE_FORMS = [" k1", "k1 ", "k1\n"]


@pytest.mark.parametrize("value", WHITESPACE_FORMS)
def test_key_id_with_surrounding_whitespace_is_refused_by_name(value: str) -> None:
    messages = check(_env(AT_REST_ENCRYPTION_KEY_ID=value))
    assert len(messages) == 1 and "AT_REST_ENCRYPTION_KEY_ID" in messages[0]


@pytest.mark.parametrize("value", WHITESPACE_FORMS)
def test_settings_refuse_a_key_id_with_surrounding_whitespace(monkeypatch, value: str) -> None:
    from pydantic import ValidationError  # noqa: PLC0415

    from app.core.config import Settings  # noqa: PLC0415

    monkeypatch.setenv("AT_REST_ENCRYPTION_KEY_ID", value)
    with pytest.raises(ValidationError, match="AT_REST_ENCRYPTION_KEY_ID"):
        Settings()


@pytest.mark.parametrize("kid", WHITESPACE_FORMS)
def test_retired_key_id_with_surrounding_whitespace_is_refused_by_name(kid: str) -> None:
    messages = check(_env(**{RETIRED: f"{kid}:{OTHER_KEY}"}))
    assert len(messages) == 1 and RETIRED in messages[0]
    assert OTHER_KEY not in messages[0]


@pytest.mark.parametrize("kid", WHITESPACE_FORMS)
def test_settings_refuse_a_retired_key_id_with_surrounding_whitespace(
    monkeypatch, kid: str
) -> None:
    from pydantic import ValidationError  # noqa: PLC0415

    from app.core.config import Settings  # noqa: PLC0415

    monkeypatch.setenv(RETIRED, f"{kid}:{OTHER_KEY}")
    with pytest.raises(ValidationError, match=RETIRED) as exc:
        Settings()
    assert OTHER_KEY not in str(exc.value)


def test_retired_key_equal_to_the_current_key_in_the_other_alphabet_is_refused() -> None:
    """The comparison is on decoded bytes: ``openssl rand -base64`` output (standard alphabet)
    and the same key in the URL-safe alphabet are one key."""
    raw = bytes([0xFB, 0xFF] * 16)
    url_safe = base64.urlsafe_b64encode(raw).decode()
    standard = base64.b64encode(raw).decode()
    assert url_safe != standard
    for current, retired in ((url_safe, standard), (standard, url_safe)):
        messages = check(_env(AT_REST_ENCRYPTION_KEY=current, **{RETIRED: f"old:{retired}"}))
        assert len(messages) == 1 and "same key as AT_REST_ENCRYPTION_KEY" in messages[0]
        assert url_safe not in messages[0] and standard not in messages[0]


def test_settings_env_reads_the_key_settings_from_settings_not_the_process_environment(
    monkeypatch,
) -> None:
    """Carried requirement C3: the key id and retired keys come from Settings."""
    from app.core.config import get_settings  # noqa: PLC0415

    monkeypatch.setenv("AT_REST_ENCRYPTION_KEY_ID", "from-settings")
    monkeypatch.setenv(RETIRED, f"old:{OTHER_KEY}")
    get_settings.cache_clear()
    env = secret_settings.settings_env()
    assert env["AT_REST_ENCRYPTION_KEY_ID"] == "from-settings"
    assert env[RETIRED] == f"old:{OTHER_KEY}"


def test_settings_refuse_a_bad_key_ring_at_start_up(monkeypatch) -> None:
    """SR-022 AC 3: the application itself refuses, naming the setting and not the key."""
    from pydantic import ValidationError  # noqa: PLC0415

    from app.core.config import Settings  # noqa: PLC0415

    monkeypatch.setenv(RETIRED, f"test:{OTHER_KEY}")  # the id the baseline environment uses
    with pytest.raises(ValidationError) as exc:
        Settings()
    assert RETIRED in str(exc.value) and OTHER_KEY not in str(exc.value)
    monkeypatch.delenv(RETIRED)
    monkeypatch.delenv("AT_REST_ENCRYPTION_KEY_ID")
    with pytest.raises(ValidationError, match="at_rest_encryption_key_id"):
        Settings()


def test_secret_values_returns_the_retired_keys_without_their_ids() -> None:
    from app.core.secret_settings import secret_values  # noqa: PLC0415

    values = secret_values(_env(**{RETIRED: f"old:{OTHER_KEY}"}))
    assert OTHER_KEY in values and f"old:{OTHER_KEY}" not in values


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
