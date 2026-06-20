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
