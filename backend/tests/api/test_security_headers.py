"""Tests for security headers middleware (TASK-069)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client():
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


class TestSecurityHeaders:
    def test_csp_header_present(self, client):
        resp = client.get("/healthz")
        assert "content-security-policy" in resp.headers

    def test_x_content_type_options_header(self, client):
        resp = client.get("/healthz")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options_header(self, client):
        resp = client.get("/healthz")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy_header(self, client):
        resp = client.get("/healthz")
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_headers_on_api_endpoints(self, client):
        resp = client.get("/api/v1/openapi.json")
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
