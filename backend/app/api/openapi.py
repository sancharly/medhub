"""OpenAPI customization (TASK-068, TASK-068a)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# Paths that do NOT require authentication (no cookieAuth requirement).
# All other paths are protected.
_PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/api/v1/auth/login",
        "/api/v1/activation/{token}",
        "/healthz",
    }
)

_CSRF_HEADER_PARAM: dict[str, Any] = {
    "name": "X-CSRF-Token",
    "in": "header",
    "required": True,
    "description": "CSRF token — must match the `medhub_csrf` cookie value.",
    "schema": {"type": "string"},
}

_STATE_CHANGING_METHODS: frozenset[str] = frozenset({"post", "put", "patch", "delete"})


def _is_protected(path: str) -> bool:
    """Return True if the path requires cookieAuth."""
    return path not in _PUBLIC_PATHS


def customize_openapi(app: FastAPI) -> None:
    """Customize the OpenAPI schema.

    - OpenAPI 3.1
    - cookieAuth security scheme applied to all protected operations
    - X-CSRF-Token header documented on state-changing protected operations
    - ProblemDetail shared component
    - problem+json error responses on state-changing operations
    """

    def _generate() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version="3.1.0",
            routes=app.routes,
            servers=app.servers,
        )

        # Cookie-based session security scheme
        schema.setdefault("components", {})
        schema["components"].setdefault("securitySchemes", {})
        schema["components"]["securitySchemes"]["cookieAuth"] = {
            "type": "apiKey",
            "in": "cookie",
            "name": "medhub_session",
        }

        # Shared Problem Details component
        schema["components"].setdefault("schemas", {})
        schema["components"]["schemas"]["ProblemDetail"] = {
            "type": "object",
            "properties": {
                "type": {"type": "string", "format": "uri"},
                "title": {"type": "string"},
                "status": {"type": "integer"},
                "detail": {"type": "string"},
                "instance": {"type": "string"},
                "errors": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["type", "title", "status", "detail"],
        }

        # Per-operation security + CSRF header + error responses
        for path, path_item in schema.get("paths", {}).items():
            protected = _is_protected(path)
            for method, operation in path_item.items():
                if not isinstance(operation, dict):
                    continue

                # Apply cookieAuth to protected operations
                if protected:
                    operation["security"] = [{"cookieAuth": []}]

                # Document X-CSRF-Token on state-changing protected operations
                if method in _STATE_CHANGING_METHODS and protected:
                    operation.setdefault("parameters", [])
                    existing_names = {
                        p.get("name") for p in operation["parameters"] if isinstance(p, dict)
                    }
                    if "X-CSRF-Token" not in existing_names:
                        operation["parameters"].append(_CSRF_HEADER_PARAM)

                # Add problem+json error responses on state-changing operations
                if method in _STATE_CHANGING_METHODS:
                    operation.setdefault("responses", {})
                    for code in ("400", "401", "403", "422"):
                        if code not in operation["responses"]:
                            operation["responses"][code] = {
                                "description": {
                                    "400": "Validation Error",
                                    "401": "Unauthenticated",
                                    "403": "Forbidden",
                                    "422": "Unprocessable Entity",
                                }.get(code, "Error"),
                                "content": {
                                    "application/problem+json": {
                                        "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                                    }
                                },
                            }

        # Root-level security: empty (per-operation overrides apply)
        schema["security"] = []

        app.openapi_schema = schema
        return schema

    app.openapi = _generate  # type: ignore[method-assign]
