"""DICOM validation using pydicom (TASK-045)."""

from __future__ import annotations

from typing import BinaryIO

from pydicom.uid import DeflatedExplicitVRLittleEndian

from app.api.errors import ProblemDetail, ValidationProblem
from app.modules.dicom_support import (
    DeflateStreamError,
    InflatedSizeExceeded,
    check_inflated_size,
    read_transfer_syntax,
)
from app.modules.module_settings import dicom_max_decoded_bytes


def validate_dicom(fp: BinaryIO) -> dict[str, object]:
    """Parse and validate a DICOM file read from ``fp``. Returns metadata dict.

    Only the header is read (``stop_before_pixels``); ``fp`` is rewound afterwards (SR-013 AC 6).
    A Deflated object is first inflated under ``dicom_max_decoded_bytes`` and refused above it
    (TASK-240); every other transfer syntax is accepted as before.
    Raises ValidationProblem if the data is not a valid DICOM file.
    """
    _check_deflated_size(fp)
    try:
        import pydicom  # noqa: PLC0415

        dataset = pydicom.dcmread(fp, stop_before_pixels=True)
        fp.seek(0)
        return {
            "modality": getattr(dataset, "Modality", None),
            "patient_id": getattr(dataset, "PatientID", None),
            "study_date": getattr(dataset, "StudyDate", None),
        }
    except Exception as exc:
        msg = f"Invalid DICOM file: {exc}"
        raise ValidationProblem(msg) from exc


def _check_deflated_size(fp: BinaryIO) -> None:
    """Refuse a Deflated object that inflates above the decoded bound, before pydicom reads it."""
    if read_transfer_syntax(fp) != DeflatedExplicitVRLittleEndian:
        return
    limit = dicom_max_decoded_bytes()
    try:
        check_inflated_size(fp, limit)
    except InflatedSizeExceeded as exc:
        msg = f"The DICOM file inflates to more than {limit} bytes."
        raise ValidationProblem(
            msg,
            errors=[ProblemDetail(field="file", rule="dicom_decoded_size_exceeded", message=msg)],
        ) from exc
    except DeflateStreamError as exc:
        msg = f"Invalid DICOM file: {exc}"
        raise ValidationProblem(msg) from exc
