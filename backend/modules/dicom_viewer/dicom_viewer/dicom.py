"""DICOM helpers — frame extraction and content-type validation."""

from __future__ import annotations

import io

from app.api.errors import ProblemDetail, ValidationProblem
from app.modules.module_settings import dicom_max_decoded_bytes


def validate_dicom_content_type(content_type: str) -> None:
    """Raise ValidationProblem if content_type is not application/dicom."""
    if content_type != "application/dicom":
        raise ValidationProblem(f"Expected application/dicom content type, got {content_type!r}.")


def _problem(rule: str, message: str) -> ValidationProblem:
    return ValidationProblem(
        message, errors=[ProblemDetail(field="study", rule=rule, message=message)]
    )


def _check_declared_decoded_size(data: bytes) -> None:
    """Refuse, from the header alone, an object whose decoded size is missing or too large."""
    import pydicom  # noqa: PLC0415

    maximum = dicom_max_decoded_bytes()
    try:
        header = pydicom.dcmread(io.BytesIO(data), stop_before_pixels=True)
        rows = int(header["Rows"].value)
        columns = int(header["Columns"].value)
        frames = int(header.get("NumberOfFrames", 1) or 1)
        samples = int(header.get("SamplesPerPixel", 1) or 1)
        bits = int(header["BitsAllocated"].value)
    except Exception as exc:
        raise _problem(
            "dicom_decode_failed", "The DICOM header does not declare the image size."
        ) from exc
    if min(rows, columns, frames, samples, bits) <= 0:
        raise _problem("dicom_decode_failed", "The DICOM header declares an invalid image size.")
    declared = rows * columns * frames * samples * ((bits + 7) // 8)
    if declared > maximum:
        raise _problem(
            "dicom_decoded_size_exceeded",
            f"The declared decoded size is larger than the maximum of {maximum} bytes.",
        )


def stream_dicom(data: bytes, frame: int | None) -> bytes:
    """Return DICOM bytes, optionally extracting a single frame.

    If frame is None, returns the raw data unchanged.
    If frame is specified, uses pydicom to extract that frame's pixel data, after the
    header-declared decoded size has been checked against the configured maximum (SR-017 AC 6).
    A decode that fails raises a problem; no partial bytes are returned.
    """
    if frame is None:
        return data

    import pydicom  # noqa: PLC0415

    _check_declared_decoded_size(data)
    try:
        ds = pydicom.dcmread(io.BytesIO(data))
        pixel_array = ds.pixel_array
    except Exception as exc:
        raise _problem("dicom_decode_failed", "The DICOM pixel data could not be decoded.") from exc
    # pixel_array shape: (frames, rows, cols) for multi-frame or (rows, cols) for single
    if pixel_array.ndim == 2:
        if frame != 0:
            raise ValidationProblem(f"Frame {frame} out of range; this DICOM has 1 frame.")
        frame_data = pixel_array.tobytes()
    else:
        num_frames = pixel_array.shape[0]
        if frame >= num_frames:
            raise ValidationProblem(
                f"Frame {frame} out of range; this DICOM has {num_frames} frames."
            )
        frame_data = pixel_array[frame].tobytes()

    return frame_data
