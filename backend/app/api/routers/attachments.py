"""Attachments API router (TASK-045/046, TASK-066a)."""

from __future__ import annotations

import errno
import logging
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import APIRouter, Depends, Request, Response, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.content_disposition import content_disposition
from app.api.deps import get_current_user
from app.api.errors import UploadStorageUnavailableProblem
from app.api.schemas.attachments import AttachmentResponse
from app.attachments.service import AttachmentService
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.db.models.account import Account
from app.db.repositories.attachment_repo import AttachmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.clinical_repo import ClinicalRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.session import DbSession

logger = logging.getLogger(__name__)


class _SpoolFailureRoute(APIRoute):
    """Answer a failed spool of the upload body as a logged 503 problem (TASK-232, PRB-092).

    FastAPI re-raises any non-HTTP error from ``request.form()`` as a 400 ``from`` the original
    error, so an ``OSError`` cause (scratch space full, I/O error) is the spool failing, not a
    malformed body. A genuine 400 has no ``OSError`` cause and passes through unchanged.
    """

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def spool_aware_handler(request: Request) -> Response:
            try:
                return await handler(request)
            except StarletteHTTPException as exc:
                err = exc.__cause__
                if exc.status_code != 400 or not isinstance(err, OSError):
                    raise
                # SR-043 AC 4: the route template, never the raw path, the file name or a field.
                route = request.scope.get("route")
                path = getattr(route, "path", None) or "<unmatched>"
                logger.error(
                    "Upload body could not be spooled for %s %s: %s (%s)",
                    request.method,
                    path,
                    errno.errorcode.get(err.errno or 0, "unknown"),
                    err.strerror,
                    exc_info=err,
                )
                raise UploadStorageUnavailableProblem() from err

        return spool_aware_handler


router = APIRouter(tags=["attachments"], route_class=_SpoolFailureRoute)


def _get_attachment_service(db: DbSession) -> AttachmentService:
    from app.authz.consent import ConsentService  # noqa: PLC0415
    from app.core.object_storage import ObjectStorageClient  # noqa: PLC0415

    audit_svc = AuditService(AuditRepository(db))
    consent_svc = ConsentService(ConsentRepository(db), audit_svc)
    authz_svc = AuthorizationService(consent_svc, audit_svc)
    return AttachmentService(
        AttachmentRepository(db),
        ClinicalRepository(db),
        audit_svc,
        authz_svc,
        ObjectStorageClient(),
    )


@router.post(
    "/clinical-entries/{entry_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
    responses={
        503: {
            "description": "The upload body could not be spooled to temporary storage; "
            "nothing was saved. Retry later.",
            "content": {
                "application/problem+json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        }
    },
)
async def upload_attachment(
    entry_id: uuid.UUID,
    file: UploadFile,
    actor: Account = Depends(get_current_user),
    svc: AttachmentService = Depends(_get_attachment_service),
) -> AttachmentResponse:
    """Upload an attachment via multipart/form-data.

    The form field must be named ``file``. DICOM files (.dcm) are validated
    and their modality metadata is persisted with the record.
    """
    filename = file.filename or "unknown"
    content_type = file.content_type or "application/octet-stream"
    # The spooled file (on disk beyond 1 MiB) is read in chunks by the service, never as one
    # bytes object (SR-013 AC 6); the blocking store runs off the event loop.
    attachment = await run_in_threadpool(
        svc.store, actor, entry_id, filename, content_type, file.file
    )
    return AttachmentResponse.model_validate(attachment)


@router.get(
    "/clinical-entries/{entry_id}/attachments",
    response_model=list[AttachmentResponse],
)
def list_attachments(
    entry_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: AttachmentService = Depends(_get_attachment_service),
) -> list[AttachmentResponse]:
    """List attachments for a clinical entry."""
    attachments = svc.list_attachments(actor, entry_id)
    return [AttachmentResponse.model_validate(a) for a in attachments]


@router.get(
    "/attachments/{attachment_id}",
    responses={
        502: {
            "description": "Stored object failed its checksum verification.",
            "content": {
                "application/problem+json": {
                    "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                }
            },
        }
    },
)
def fetch_attachment(
    attachment_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: AttachmentService = Depends(_get_attachment_service),
) -> StreamingResponse:
    # Two-pass, bounded read (SR-013 AC 5, AC 6): every byte sent was verified against the stored
    # SHA-256; a failure before the first byte is a 502 problem, one after the last aborts the
    # transfer.
    chunks, content_type, filename, size = svc.open_stream(actor, attachment_id)

    # SR-023 AC 2 / ADR-0016: the open succeeded but no content is served; the independent
    # FAILURE row is the record of the attempt.
    try:
        return StreamingResponse(
            chunks,
            media_type=content_type,
            headers={
                "Content-Disposition": content_disposition(filename),
                "Content-Length": str(size),
            },
        )
    except Exception:
        svc.record_access_failure(actor, attachment_id)
        raise
