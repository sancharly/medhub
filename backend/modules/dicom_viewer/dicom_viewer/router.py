"""DICOM Viewer API router."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import get_current_user, get_platform_services
from app.api.errors import AuthorizationError, ProblemDetail, ValidationProblem
from app.audit.actions import AuditAction
from app.modules.contract import AuditOutcome
from app.modules.module_settings import dicom_max_stored_bytes
from dicom_viewer.dicom import stream_dicom, validate_dicom_content_type


def build_router() -> APIRouter:
    """Build and return the DICOM viewer APIRouter. Services are injected per-request via DI."""
    router = APIRouter()

    @router.get(
        "/studies/{attachment_id}",
        responses={
            200: {
                "description": (
                    "Without `frame`: the stored DICOM object, byte for byte "
                    "(`application/dicom`). With `frame=N`: the samples of frame N "
                    "(`application/octet-stream`), exactly as pydicom's `pixel_array` returns "
                    "them, written with `ndarray.tobytes()` (C order, no header, no padding): "
                    "rows x columns x samples per pixel, samples interleaved per pixel whatever "
                    "the Planar Configuration, in the server's native byte order "
                    "(little-endian), each sample `ceil(BitsAllocated / 8)` bytes, unsigned when "
                    "Pixel Representation is 0 and two's-complement signed when 1. No rescale, "
                    "windowing or photometric conversion is applied: YCbCr samples (YBR_FULL, "
                    "YBR_FULL_422) are served as stored, not converted to RGB. A YBR_FULL_422 "
                    "object is upsampled to 3 samples per pixel (Y, Cb, Cr interleaved, the "
                    "chroma of each pixel pair repeated for both pixels). Read Rows, Columns, "
                    "Samples per Pixel, Bits Allocated, Pixel Representation and Photometric "
                    "Interpretation from the whole object."
                ),
                "content": {"application/dicom": {}, "application/octet-stream": {}},
            },
            400: {
                "description": (
                    "Not a DICOM object; stored size over the maximum (150 MiB, rule "
                    "dicom_stored_size_exceeded); transfer syntax not supported for frame "
                    "decoding, or none declared (rule dicom_transfer_syntax_unsupported); "
                    "inflated or declared decoded size over the maximum (1 GiB, rule "
                    "dicom_decoded_size_exceeded); "
                    "or the pixel data could not be decoded, or does not match the size and frame "
                    "count in the header (rule dicom_decode_failed). "
                    "No image is returned."
                ),
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                    }
                },
            },
            502: {
                "description": "Stored object failed its checksum verification.",
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                    }
                },
            },
        },
    )
    def get_study(
        attachment_id: uuid.UUID,
        frame: Annotated[int | None, Query(ge=0)] = None,
        actor: Any = Depends(get_current_user),
        services: Any = Depends(get_platform_services),
    ) -> Response:
        try:
            data, content_type, _filename = services.attachments.open(
                actor, attachment_id, max_bytes=dicom_max_stored_bytes()
            )
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
        except ValidationProblem as exc:  # the only one open() raises: stored size over the bound
            raise ValidationProblem(
                exc.detail,
                errors=[
                    ProblemDetail(
                        field="study", rule="dicom_stored_size_exceeded", message=exc.detail
                    )
                ],
            ) from exc

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
        media_type = "application/dicom" if frame is None else "application/octet-stream"
        return Response(content=result, media_type=media_type)

    return router
