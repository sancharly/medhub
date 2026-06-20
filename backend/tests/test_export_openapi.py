"""TASK-005: Test the export_openapi module."""
import json
import sys


def test_export_openapi_writes_file(tmp_path, monkeypatch) -> None:
    """export_openapi.main() writes valid OpenAPI JSON to the given path."""
    output = tmp_path / "openapi.json"
    monkeypatch.setattr(sys, "argv", ["export_openapi", "--output", str(output)])
    from app.export_openapi import main

    main()
    assert output.exists()
    data = json.loads(output.read_text())
    assert data["openapi"].startswith("3.")
    assert "paths" in data


def test_export_openapi_default_filename(tmp_path, monkeypatch) -> None:
    """Default output file is openapi.json in the current directory."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["export_openapi"])
    from app.export_openapi import main

    main()
    output = tmp_path / "openapi.json"
    assert output.exists()
