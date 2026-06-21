"""RFC 7807 Problem Details error handling (TASK-026).

All HTTP errors returned by MedHub use application/problem+json with:
  type, title, status, detail, instance, errors[]
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_BASE_URI = "https://medhub.example/errors/"


class ProblemDetail(BaseModel):
    field: str
    rule: str
    message: str


class ProblemError(Exception):
    """Base RFC 7807 problem error."""

    status: int = 500
    title: str = "Internal Server Error"
    type_slug: str = "internal-error"

    def __init__(
        self,
        detail: str = "An unexpected error occurred.",
        *,
        errors: list[ProblemDetail] | None = None,
        instance: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.errors = errors or []
        self.instance = instance

    def to_dict(self, request: Request) -> dict[str, Any]:
        return {
            "type": f"{_BASE_URI}{self.type_slug}",
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": self.instance or str(request.url.path),
            "errors": [e.model_dump() for e in self.errors],
        }


class ValidationProblem(ProblemError):
    status = 400
    title = "Validation Error"
    type_slug = "validation-error"

    def __init__(
        self,
        detail: str = "Request validation failed.",
        *,
        errors: list[ProblemDetail] | None = None,
    ) -> None:
        super().__init__(detail, errors=errors)


class UnauthenticatedError(ProblemError):
    status = 401
    title = "Unauthenticated"
    type_slug = "unauthenticated"

    def __init__(self, detail: str = "Authentication is required.") -> None:
        super().__init__(detail)


class AuthorizationError(ProblemError):
    status = 403
    title = "Forbidden"
    type_slug = "forbidden"

    def __init__(self, detail: str = "You do not have permission to perform this action.") -> None:
        super().__init__(detail)


class NotFoundError(ProblemError):
    status = 404
    title = "Not Found"
    type_slug = "not-found"

    def __init__(self, detail: str = "The requested resource was not found.") -> None:
        super().__init__(detail)


class ConflictError(ProblemError):
    status = 409
    title = "Conflict"
    type_slug = "conflict"

    def __init__(
        self,
        detail: str = "A conflict occurred with the current state of the resource.",
    ) -> None:
        super().__init__(detail)


class RateLimitedError(ProblemError):
    status = 429
    title = "Too Many Requests"
    type_slug = "rate-limited"

    def __init__(self, detail: str = "Too many requests. Please try again later.") -> None:
        super().__init__(detail)


def _problem_response(problem: dict[str, Any], status: int) -> JSONResponse:
    return JSONResponse(
        content=problem,
        status_code=status,
        media_type="application/problem+json",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all RFC 7807 error handlers on the FastAPI app."""

    @app.exception_handler(ProblemError)
    async def problem_error_handler(request: Request, exc: ProblemError) -> JSONResponse:
        return _problem_response(exc.to_dict(request), exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = err.get("loc", ())
            field = ".".join(str(p) for p in loc if p != "body")
            errors.append(
                ProblemDetail(
                    field=field or "unknown",
                    rule=err.get("type", "invalid"),
                    message=err.get("msg", "Invalid value"),
                ).model_dump()
            )
        problem = {
            "type": f"{_BASE_URI}validation-error",
            "title": "Validation Error",
            "status": 400,
            "detail": "Request validation failed.",
            "instance": str(request.url.path),
            "errors": errors,
        }
        return _problem_response(problem, 400)

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
        problem = {
            "type": f"{_BASE_URI}internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred.",
            "instance": str(request.url.path),
            "errors": [],
        }
        return _problem_response(problem, 500)
