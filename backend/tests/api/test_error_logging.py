"""TASK-206 slice A (PRB-068, SR-043 AC 4): the 500 record names the route, never the raw path."""

from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.errors import register_error_handlers

TOKEN = "SecretActivationToken-abc123_XYZ"


def _app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/api/v1/activation/{token}")
    async def activation(token: str) -> None:
        raise RuntimeError("boom")

    return app


def _records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == "app.api.errors"]


def test_unhandled_exception_logs_route_template_not_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = TestClient(_app(), raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR):
        response = client.get(f"/api/v1/activation/{TOKEN}")
    assert response.status_code == 500
    records = _records(caplog)
    assert len(records) == 1
    text = records[0].getMessage() + (records[0].exc_text or "")
    assert "/api/v1/activation/{token}" in text
    assert TOKEN not in text
    assert TOKEN not in caplog.text


def test_unhandled_exception_on_unmatched_path_logs_placeholder(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class Failing(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
            raise RuntimeError("middleware failure")

    app = _app()
    app.add_middleware(Failing)
    client = TestClient(app, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR):
        response = client.get(f"/api/v1/activation/{TOKEN}")
    assert response.status_code == 500
    message = _records(caplog)[0].getMessage()
    assert "<unmatched>" in message
    assert TOKEN not in caplog.text


def test_unhandled_exception_log_keeps_method_and_traceback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = TestClient(_app(), raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR):
        client.get(f"/api/v1/activation/{TOKEN}")
    record = _records(caplog)[0]
    assert record.getMessage().startswith("Unhandled exception for GET ")
    assert record.exc_info is not None
    assert record.exc_info[0] is RuntimeError


def test_problem_body_instance_still_echoes_the_path_to_the_client() -> None:
    client = TestClient(_app(), raise_server_exceptions=False)
    body = client.get(f"/api/v1/activation/{TOKEN}").json()
    assert body["instance"] == f"/api/v1/activation/{TOKEN}"


def test_real_app_500_logs_the_router_template(caplog: pytest.LogCaptureFixture) -> None:
    """TASK-207 (finding 3): through the real app the record names ``/activation/{token}``
    (the router prefix, not ``/api/v1``), identifies the endpoint and carries no token."""
    from unittest.mock import MagicMock  # noqa: PLC0415

    from app.api.routers.activation import _get_activation_service  # noqa: PLC0415
    from app.main import create_app  # noqa: PLC0415

    service = MagicMock()
    service.activate.side_effect = RuntimeError("boom")
    app = create_app()
    app.dependency_overrides[_get_activation_service] = lambda: service
    client = TestClient(app, raise_server_exceptions=False)
    body = {
        "accountId": "00000000-0000-0000-0000-000000000001",
        "password": "x",
        "confirmPassword": "x",
    }
    with caplog.at_level(logging.ERROR):
        response = client.post(f"/api/v1/activation/{TOKEN}", json=body)
    assert response.status_code == 500
    records = _records(caplog)
    assert len(records) == 1
    text = records[0].getMessage() + (records[0].exc_text or "")
    assert "/activation/{token}" in text
    assert TOKEN not in text
    assert TOKEN not in caplog.text
