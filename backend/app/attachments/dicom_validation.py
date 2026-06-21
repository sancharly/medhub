"""DICOM validation using pydicom (TASK-045)."""

from __future__ import annotations

import io

from app.api.errors import ValidationProblem


def validate_dicom(data: bytes) -> dict[str, object]:
    """Parse and validate a DICOM file. Returns metadata dict.

    Raises ValidationProblem if the data is not a valid DICOM file.
    """
    try:
        import pydicom  # noqa: PLC0415

        dataset = pydicom.dcmread(io.BytesIO(data), stop_before_pixels=True)
        return {
            "modality": getattr(dataset, "Modality", None),
            "patient_id": getattr(dataset, "PatientID", None),
            "study_date": getattr(dataset, "StudyDate", None),
        }
    except Exception as exc:
        msg = f"Invalid DICOM file: {exc}"
        raise ValidationProblem(msg) from exc
