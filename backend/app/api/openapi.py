"""OpenAPI customization (TASK-068)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def customize_openapi(app: FastAPI) -> None:
    """Customize the OpenAPI schema: OpenAPI 3.1, cookie security scheme, Problem component."""

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

        # Add problem+json responses to all state-changing operations
        for path_item in schema.get("paths", {}).values():
            for method, operation in path_item.items():
                if method in ("post", "put", "patch", "delete") and isinstance(operation, dict):
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
                                        "schema": {
                                            "$ref": "#/components/schemas/ProblemDetail"
                                        }
                                    }
                                },
                            }

        # Root-level security: empty (no auth required by default; protected endpoints override)
        schema.setdefault("security", [])

        app.openapi_schema = schema
        return schema

    app.openapi = _generate  # type: ignore[method-assign]
