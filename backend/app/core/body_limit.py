"""Request-body guard for the attachment upload route (SR-013 AC 6, ADR-0021, TASK-135).

Pure ASGI. For ``POST /api/v1/clinical-entries/{id}/attachments`` only:

- a declared ``Content-Length`` above ``attachment_max_bytes + MULTIPART_ALLOWANCE`` is refused
  before any body byte is read;
- whatever the headers say, the ``http.request`` bytes are counted and the request is refused once
  the count passes that same bound. At most the maximum, plus the 64 KiB multipart allowance, plus
  the one received message that crosses the bound, is read.

The refusal is today's size refusal: HTTP 400, ``application/problem+json``, type
``validation-error`` (``ValidationProblem``), so the OpenAPI contract does not change.
"""

from __future__ import annotations

import re

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.errors import ValidationProblem, _problem_response
from app.core.config import get_settings

MULTIPART_ALLOWANCE = 65536  # 64 KiB: room for the multipart framing around the file

_UPLOAD_PATH = re.compile(r"^/api/v1/clinical-entries/[^/]+/attachments$")


class _BodyTooLarge(BaseException):  # noqa: N818
    """Raised out of ``receive`` into the application.

    A ``BaseException`` so that the form parser's and FastAPI's ``except Exception`` do not turn it
    into a generic "error parsing the body" 400; the guard catches it and answers.
    """


class AttachmentBodyLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] != "POST"
            or not _UPLOAD_PATH.match(scope["path"])
        ):
            await self.app(scope, receive, send)
            return

        maximum = get_settings().attachment_max_bytes
        bound = maximum + MULTIPART_ALLOWANCE

        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > bound:
            await self._refuse(scope, receive, send, maximum)
            return

        received = 0
        started = False

        async def counting_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > bound:
                    raise _BodyTooLarge
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, counting_receive, tracking_send)
        except _BodyTooLarge:
            if started:
                raise
            await self._refuse(scope, receive, send, maximum)

    @staticmethod
    async def _refuse(scope: Scope, receive: Receive, send: Send, maximum: int) -> None:
        problem = ValidationProblem(f"Attachment size exceeds maximum {maximum} bytes.")
        response = _problem_response(problem.to_dict(Request(scope)), problem.status)
        await response(scope, receive, send)
