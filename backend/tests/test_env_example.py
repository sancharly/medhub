"""TASK-003: Verify infra/.env.example covers all required Settings fields."""

import re
from pathlib import Path

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
    for default in KNOWN_DEFAULTS - {"admin", "password", "secret"}:
        assert default not in text.replace("postgresql://medhub:changeme@", "").replace(
            "smtp_password=changeme", ""
        )
