"""Attachments API router (TASK-045/046)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas.attachments import AttachmentResponse
from app.attachments.service import AttachmentService
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.db.models.account import Account
from app.db.repositories.attachment_repo import AttachmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.clinical_repo import ClinicalRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.session import get_db

router = APIRouter(tags=["attachments"])


def _get_attachment_service(db: Session = Depends(get_db)) -> AttachmentService:
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
)
async def upload_attachment(
    entry_id: uuid.UUID,
    request: Request,
    actor: Account = Depends(get_current_user),
    svc: AttachmentService = Depends(_get_attachment_service),
) -> AttachmentResponse:
    """Upload an attachment. Reads raw body; caller must set Content-Type and
    X-Filename headers for filename and content_type respectively.
    """
    filename = request.headers.get("X-Filename", "unknown")
    content_type = request.headers.get("Content-Type", "application/octet-stream")
    data = await request.body()
    attachment = svc.store(actor, entry_id, filename, content_type, data)
    return AttachmentResponse.model_validate(attachment)


@router.get("/attachments/{attachment_id}")
def fetch_attachment(
    attachment_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: AttachmentService = Depends(_get_attachment_service),
) -> StreamingResponse:
    data, content_type, filename = svc.open(actor, attachment_id)
    return StreamingResponse(
        iter([data]),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
