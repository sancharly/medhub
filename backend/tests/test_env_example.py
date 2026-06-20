"""TASK-003: Verify infra/.env.example covers all required Settings fields."""
import re
from pathlib import Path

from pydantic_settings import BaseSettings

from app.core.config import Settings


def _required_fields(model: type[BaseSettings]) -> list[str]:
    """Return field names that have no default value."""
    required = []
    for name, field_info in model.model_fields.items():
        if field_info.default is None and field_info.default_factory is None:  # type: ignore[misc]
            # PydanticUndefined means no default
            from pydantic_core import PydanticUndefinedType

            if isinstance(field_info.default, PydanticUndefinedType):
                required.append(name)
        # A simpler check: no default at all
    return required


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
        assert env_key in defined_keys, (
            f"Settings field '{field_name}' is missing from infra/.env.example"
        )
