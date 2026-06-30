#!/usr/bin/env python
"""Thin shim — delegates to the canonical export module (TASK-068a).

Usage (from backend/):
    python scripts/export_openapi.py

The canonical command referenced in CLAUDE.md is:
    uv run python -m app.export_openapi --output openapi/openapi.json
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend/ is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.export_openapi import main  # noqa: E402

if __name__ == "__main__":
    # Default output when called as a script without --output
    if "--output" not in sys.argv:
        backend_dir = Path(__file__).parent.parent
        sys.argv += ["--output", str(backend_dir / "openapi" / "openapi.json")]
    main()
