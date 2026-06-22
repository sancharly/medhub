"""DICOM Viewer API router."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import get_current_user
from app.audit.actions import AuditAction
from dicom_viewer.dicom import stream_dicom, validate_dicom_content_type

if TYPE_CHECKING:
    pass


def build_router(services: Any) -> APIRouter:
    """Build and return the DICOM viewer APIRouter bound to platform services."""
    router = APIRouter()

    @router.get("/studies/{attachment_id}")
    def get_study(
        attachment_id: uuid.UUID,
        frame: Annotated[int | None, Query(ge=0)] = None,
        actor: Any = Depends(get_current_user),
    ) -> Response:
        data, content_type, _filename = services.attachments.open(actor, attachment_id)

        validate_dicom_content_type(content_type)

        result = stream_dicom(data, frame)

        # Import AuditOutcome at call time to avoid module-level db import
        from app.db.models.audit import AuditOutcome  # noqa: PLC0415

        services.audit.record(
            actor=actor.id,
            action=AuditAction.DICOM_STUDY_READ,
            target_type="attachment",
            target_id=str(attachment_id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

        return Response(content=result, media_type="application/dicom")

    return router
