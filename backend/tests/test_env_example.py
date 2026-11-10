"""TASK-003: Verify infra/.env.example covers all required Settings fields."""

import re
from pathlib import Path

import pytest

from app.core.config import Settings


def test_env_example_covers_all_settings_fields() -> None:
    env_example = Path(__file__).parents[2] / "infra" / ".env.example"
    assert env_example.exists(), f"Missing {env_example}"
    content = env_example.read_text()
    # Extract keys defined in .env.example (lines like KEY=value or KEY=)
    defined_keys = {
        match.group(1).upper()
        for line in content.splitlines()
        if (match := re.match(r"^([A-Z_][A-Z0-9_]*)=", line))
    }
    for field_name in Settings.model_fields:
        env_key = field_name.upper()
        assert (
            env_key in defined_keys
        ), f"Settings field '{field_name}' is missing from infra/.env.example"


def _env_example_values() -> dict[str, str]:
    env_example = Path(__file__).parents[2] / "infra" / ".env.example"
    return {
        m.group(1): m.group(2)
        for line in env_example.read_text().splitlines()
        if (m := re.match(r"^([A-Z_][A-Z0-9_]*)=(.*)$", line))
    }


def test_env_example_object_store_keys_are_empty() -> None:
    """TASK-174 / SR-040 AC 2: no object-store default credential in the template."""
    values = _env_example_values()
    assert values["OBJECT_STORE_ACCESS_KEY"] == ""
    assert values["OBJECT_STORE_SECRET_KEY"] == ""


def test_env_example_has_no_object_store_default_strings() -> None:
    from app.core.object_store_credentials import KNOWN_DEFAULTS

    env_example = Path(__file__).parents[2] / "infra" / ".env.example"
    values = _env_example_values()
    for name in ("OBJECT_STORE_ACCESS_KEY", "OBJECT_STORE_SECRET_KEY"):
        assert values[name].lower() not in KNOWN_DEFAULTS
    text = env_example.read_text().lower()
    # TASK-203: no exception list; "admin", "password" and "secret" are ordinary words in the
    # comments, the rest of the default set must not appear anywhere in the file.
    for default in KNOWN_DEFAULTS - {"admin", "password", "secret"}:
        assert default not in text


# Secret settings of the deployment (SR-041, DEPLOY.md "Secret settings"). POSTGRES_PASSWORD is
# the database image's password, which is not an application setting.
_TEMPLATE_SECRETS = (
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "SMTP_PASSWORD",
    "AT_REST_ENCRYPTION_KEY",
    "OBJECT_STORE_SSE_KEY",
    "OBJECT_STORE_ACCESS_KEY",
    "OBJECT_STORE_SECRET_KEY",
)


def test_env_example_secret_settings_are_present_and_empty() -> None:
    """TASK-203 / SR-041 AC 4: the template holds no value for any secret setting."""
    values = _env_example_values()
    for name in _TEMPLATE_SECRETS:
        assert name in values, f"{name} is missing from infra/.env.example"
        assert values[name] == "", f"{name} must be empty in infra/.env.example"


def test_env_example_secret_list_covers_the_application_rule() -> None:
    """Every secret setting the application refuses is either in the template or optional."""
    from app.core import secret_settings as rule

    optional_not_in_template = {
        rule.DATABASE_OWNER_URL,
        rule.AT_REST_ENCRYPTION_RETIRED_KEYS,
    }
    assert set(rule.SECRET_SETTINGS) - optional_not_in_template <= set(_TEMPLATE_SECRETS)
    # An optional secret that is in the template must be empty too.
    for name, value in _env_example_values().items():
        if name in rule.SECRET_SETTINGS:
            assert value == "", name


def test_env_example_holds_no_placeholder_value() -> None:
    """TASK-203 / SR-041 AC 4: no value of the shared placeholder list, in any case, anywhere."""
    from app.core.secret_settings import KNOWN_PLACEHOLDERS, PLACEHOLDER_PREFIX, is_placeholder

    env_example = Path(__file__).parents[2] / "infra" / ".env.example"
    for name, value in _env_example_values().items():
        assert not is_placeholder(value), f"{name} is a placeholder"
    text = env_example.read_text().lower()
    # The generic words occur in comments; every other entry (including the old template values)
    # and the prefix must not appear at all.
    for placeholder in KNOWN_PLACEHOLDERS - {"admin", "password", "secret"}:
        assert placeholder not in text, placeholder
    assert PLACEHOLDER_PREFIX not in text


# PRB-056 / D-6: the template itself loads, and CORS_ORIGINS takes every plausible form
_THROWAWAY = {
    "POSTGRES_PASSWORD": "Zx9Qw3Lm7Rt2Vb5N",
    "DATABASE_URL": "postgresql://medhub_app:Zx9Qw3Lm7Rt2Vb5N@postgres:5432/medhub",
    "OBJECT_STORE_ACCESS_KEY": "a1b2c3d4e5f6a1b2c3d4e5f6",
    "OBJECT_STORE_SECRET_KEY": "Zx9Qw3Lm7Rt2Vb5Nk8Hy4Jd6Fg1Sa0Pc",
    "AT_REST_ENCRYPTION_KEY": "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=",
    "AT_REST_ENCRYPTION_KEY_ID": "k1",
    "OBJECT_STORE_SSE_KEY": "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA=",
}


def test_env_example_loads_through_settings_with_the_secrets_filled(monkeypatch) -> None:
    """Every other value in the template is used as shipped, including the empty CORS_ORIGINS."""
    from app.core.config import Settings, get_settings  # noqa: PLC0415

    for name, value in {**_env_example_values(), **_THROWAWAY}.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    settings = Settings()
    assert settings.cors_origins == []
    assert settings.at_rest_encryption_key_id == "k1"
    assert not settings.at_rest_encryption_retired_keys  # empty means none


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("  ", []),
        ("[]", []),
        ('["https://a.example"]', ["https://a.example"]),
        ('["https://a.example", "https://b.example"]', ["https://a.example", "https://b.example"]),
        ("https://a.example", ["https://a.example"]),
        ("https://a.example,https://b.example", ["https://a.example", "https://b.example"]),
        (" https://a.example , https://b.example, ", ["https://a.example", "https://b.example"]),
    ],
)
def test_cors_origins_accepts_empty_json_and_comma_separated(monkeypatch, raw, expected) -> None:
    from app.core.config import Settings  # noqa: PLC0415

    monkeypatch.setenv("CORS_ORIGINS", raw)
    assert Settings().cors_origins == expected


def test_cors_origins_unset_is_empty(monkeypatch) -> None:
    from app.core.config import Settings  # noqa: PLC0415

    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert Settings().cors_origins == []


@pytest.mark.parametrize("raw", ["[not json", "[1, 2]"])
def test_cors_origins_refuses_a_malformed_list(monkeypatch, raw) -> None:
    from pydantic import ValidationError  # noqa: PLC0415

    from app.core.config import Settings  # noqa: PLC0415

    monkeypatch.setenv("CORS_ORIGINS", raw)
    with pytest.raises((ValidationError, ValueError)):
        Settings()
