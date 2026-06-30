"""Tests for OpenAPI contract (TASK-068, TASK-068a)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.openapi import _PUBLIC_PATHS, _STATE_CHANGING_METHODS
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


class TestOpenAPISecurityRequirements:
    """TASK-068a: security model must be surfaced per-operation."""

    def test_protected_operations_declare_cookie_auth(self, schema):
        """Every non-public operation must reference cookieAuth."""
        failures: list[str] = []
        for path, path_item in schema.get("paths", {}).items():
            if path in _PUBLIC_PATHS:
                continue
            for method, operation in path_item.items():
                if not isinstance(operation, dict):
                    continue
                security = operation.get("security")
                if not security or not any("cookieAuth" in s for s in security):
                    failures.append(f"{method.upper()} {path}")
        assert (
            not failures
        ), "Protected operations missing cookieAuth security requirement:\n" + "\n".join(failures)

    def test_public_operations_do_not_declare_cookie_auth(self, schema):
        """Public operations must not require cookieAuth."""
        failures: list[str] = []
        for path, path_item in schema.get("paths", {}).items():
            if path not in _PUBLIC_PATHS:
                continue
            for method, operation in path_item.items():
                if not isinstance(operation, dict):
                    continue
                security = operation.get("security", [])
                if any("cookieAuth" in s for s in security):
                    failures.append(f"{method.upper()} {path}")
        assert not failures, "Public operations incorrectly declare cookieAuth:\n" + "\n".join(
            failures
        )

    def test_state_changing_protected_ops_document_csrf_header(self, schema):
        """POST/PUT/PATCH/DELETE on protected paths must document X-CSRF-Token."""
        failures: list[str] = []
        for path, path_item in schema.get("paths", {}).items():
            if path in _PUBLIC_PATHS:
                continue
            for method, operation in path_item.items():
                if method not in _STATE_CHANGING_METHODS:
                    continue
                if not isinstance(operation, dict):
                    continue
                params = operation.get("parameters", [])
                param_names = {p.get("name") for p in params if isinstance(p, dict)}
                if "X-CSRF-Token" not in param_names:
                    failures.append(f"{method.upper()} {path}")
        assert (
            not failures
        ), "State-changing protected operations missing X-CSRF-Token header:\n" + "\n".join(
            failures
        )


class TestOpenAPIExport:
    def test_export_module_produces_file(self):
        """Verify the canonical export module writes valid JSON."""
        import subprocess
        import sys

        backend_dir = Path(__file__).parent.parent.parent
        output_path = backend_dir / "openapi" / "openapi.json"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "app.export_openapi",
                "--output",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(backend_dir),
        )
        assert result.returncode == 0, f"Export failed: {result.stderr}"
        assert output_path.exists()

        schema = json.loads(output_path.read_text())
        assert "openapi" in schema
        assert "paths" in schema
