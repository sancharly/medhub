"""DICOM Viewer API router."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import get_current_user, get_platform_services
from app.api.errors import AuthorizationError
from app.audit.actions import AuditAction
from app.modules.contract import AuditOutcome
from dicom_viewer.dicom import stream_dicom, validate_dicom_content_type


def build_router() -> APIRouter:
    """Build and return the DICOM viewer APIRouter. Services are injected per-request via DI."""
    router = APIRouter()

    @router.get("/studies/{attachment_id}")
    def get_study(
        attachment_id: uuid.UUID,
        frame: Annotated[int | None, Query(ge=0)] = None,
        actor: Any = Depends(get_current_user),
        services: Any = Depends(get_platform_services),
    ) -> Response:
        try:
            data, content_type, _filename = services.attachments.open(actor, attachment_id)
        except AuthorizationError:
            services.audit.record(
                actor=actor.id,
                action=AuditAction.DICOM_STUDY_READ,
                target_type="attachment",
                target_id=str(attachment_id),
                outcome=AuditOutcome.FAILURE,
                ip=None,
            )
            raise

        validate_dicom_content_type(content_type)
        result = stream_dicom(data, frame)

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
