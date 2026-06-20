"""Dump the OpenAPI schema to openapi.json.

Usage:
    uv run python -m app.export_openapi
    uv run python -m app.export_openapi --output path/to/openapi.json
"""
import argparse
import json
from pathlib import Path

from app.main import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Export OpenAPI schema to JSON file")
    parser.add_argument(
        "--output",
        default="openapi.json",
        help="Output file path (default: openapi.json)",
    )
    args = parser.parse_args()

    app = create_app()
    schema = app.openapi()
    output = Path(args.output)
    output.write_text(json.dumps(schema, indent=2))
    print(f"OpenAPI schema written to {output}")


if __name__ == "__main__":
    main()
