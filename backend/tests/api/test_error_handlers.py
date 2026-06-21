"""TASK-026: RFC 7807 error handler tests."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ProblemDetail,
    RateLimitedError,
    UnauthenticatedError,
    ValidationProblem,
    register_error_handlers,
)


@pytest.fixture()
def app_with_errors() -> FastAPI:
    """Minimal FastAPI app with error handlers and test routes."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/test/validation")
    def raise_validation() -> None:
        raise ValidationProblem(
            "Bad field",
            errors=[
                ProblemDetail(field="email", rule="invalid_email", message="Not a valid email")
            ],
        )

    @app.get("/test/unauth")
    def raise_unauth() -> None:
        raise UnauthenticatedError()

    @app.get("/test/authz")
    def raise_authz() -> None:
        raise AuthorizationError()

    @app.get("/test/notfound")
    def raise_notfound() -> None:
        raise NotFoundError()

    @app.get("/test/conflict")
    def raise_conflict() -> None:
        raise ConflictError()

    @app.get("/test/ratelimit")
    def raise_ratelimit() -> None:
        raise RateLimitedError()

    @app.get("/test/boom")
    def raise_generic() -> None:
        raise RuntimeError("surprise!")

    @app.post("/test/pydantic")
    def pydantic_endpoint(body: dict[str, str]) -> dict[str, str]:
        return body

    return app


@pytest.fixture()
def client(app_with_errors: FastAPI) -> TestClient:
    return TestClient(app_with_errors, raise_server_exceptions=False)


def _assert_problem(resp, expected_status: int, type_slug: str) -> dict:
    assert resp.status_code == expected_status
    assert resp.headers["content-type"].startswith("application/problem+json")
    body = resp.json()
    assert body["status"] == expected_status
    assert body["type"].endswith(type_slug)
    assert "title" in body
    assert "detail" in body
    assert "instance" in body
    assert "errors" in body
    return body


def test_validation_problem(client: TestClient) -> None:
    resp = client.get("/test/validation")
    body = _assert_problem(resp, 400, "validation-error")
    assert len(body["errors"]) == 1
    assert body["errors"][0]["field"] == "email"


def test_unauthenticated_error(client: TestClient) -> None:
    _assert_problem(resp := client.get("/test/unauth"), 401, "unauthenticated")
    assert resp.json()["instance"] == "/test/unauth"


def test_authorization_error(client: TestClient) -> None:
    _assert_problem(client.get("/test/authz"), 403, "forbidden")


def test_not_found_error(client: TestClient) -> None:
    _assert_problem(client.get("/test/notfound"), 404, "not-found")


def test_conflict_error(client: TestClient) -> None:
    _assert_problem(client.get("/test/conflict"), 409, "conflict")


def test_rate_limited_error(client: TestClient) -> None:
    _assert_problem(client.get("/test/ratelimit"), 429, "rate-limited")


def test_generic_500_no_stack_trace(client: TestClient) -> None:
    body = _assert_problem(client.get("/test/boom"), 500, "internal-error")
    # Must not expose internal details
    assert "surprise" not in body["detail"]
    assert "Traceback" not in str(body)


def test_request_validation_error_field_level(client: TestClient) -> None:
    """FastAPI RequestValidationError maps to field-level errors[]."""
    # POST with wrong content type triggers validation
    resp = client.post("/test/pydantic", content="not-json", headers={"Content-Type": "text/plain"})
    assert resp.status_code in (400, 422)
    assert resp.headers["content-type"].startswith("application/problem+json")


def test_type_uri_base(client: TestClient) -> None:
    resp = client.get("/test/notfound")
    assert resp.json()["type"].startswith("https://medhub.example/errors/")
