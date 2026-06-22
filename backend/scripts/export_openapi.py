#!/usr/bin/env python
"""Export OpenAPI schema to backend/openapi/openapi.json (TASK-068)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the backend directory is on the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import create_app  # noqa: E402


def main() -> None:
    app = create_app()
    schema = app.openapi()
    output_path = backend_dir / "openapi" / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2))
    print(f"OpenAPI schema written to {output_path}")


if __name__ == "__main__":
    main()
