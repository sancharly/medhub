"""Tests for OpenAPI contract (TASK-068)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def schema(client):
    resp = client.get("/api/v1/openapi.json")
    assert resp.status_code == 200
    return resp.json()


class TestOpenAPISchema:
    def test_openapi_endpoint_returns_200(self, client):
        resp = client.get("/api/v1/openapi.json")
        assert resp.status_code == 200

    def test_schema_has_openapi_version(self, schema):
        assert "openapi" in schema
        # FastAPI generates 3.1.0 when customized
        assert schema["openapi"].startswith("3.")

    def test_schema_has_cookie_security_scheme(self, schema):
        schemes = schema.get("components", {}).get("securitySchemes", {})
        assert "cookieAuth" in schemes
        assert schemes["cookieAuth"]["in"] == "cookie"

    def test_schema_has_problem_detail_component(self, schema):
        schemas_comp = schema.get("components", {}).get("schemas", {})
        assert "ProblemDetail" in schemas_comp

    def test_schema_has_paths(self, schema):
        paths = schema.get("paths", {})
        assert len(paths) > 0

    def test_auth_login_path_exists(self, schema):
        paths = schema.get("paths", {})
        assert any("login" in p for p in paths)

    def test_schema_has_security_field(self, schema):
        assert "security" in schema


class TestOpenAPIExport:
    def test_export_script_produces_file(self):
        """Verify the export script can be run and creates a valid JSON file."""
        import subprocess
        import sys

        backend_dir = Path(__file__).parent.parent.parent
        script = backend_dir / "scripts" / "export_openapi.py"

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=str(backend_dir),
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        output_path = backend_dir / "openapi" / "openapi.json"
        assert output_path.exists()

        # Must be valid JSON
        schema = json.loads(output_path.read_text())
        assert "openapi" in schema
        assert "paths" in schema
