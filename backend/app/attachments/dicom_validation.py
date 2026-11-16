"""DICOM validation using pydicom (TASK-045)."""

from __future__ import annotations

from typing import BinaryIO

from app.api.errors import ValidationProblem


def validate_dicom(fp: BinaryIO) -> dict[str, object]:
    """Parse and validate a DICOM file read from ``fp``. Returns metadata dict.

    Only the header is read (``stop_before_pixels``); ``fp`` is rewound afterwards (SR-013 AC 6).
    Raises ValidationProblem if the data is not a valid DICOM file.
    """
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
