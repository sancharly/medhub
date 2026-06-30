"""DICOM helpers — frame extraction and content-type validation."""

from __future__ import annotations

import io

from app.api.errors import ValidationProblem


def validate_dicom_content_type(content_type: str) -> None:
    """Raise ValidationProblem if content_type is not application/dicom."""
    if content_type != "application/dicom":
        raise ValidationProblem(f"Expected application/dicom content type, got {content_type!r}.")


def stream_dicom(data: bytes, frame: int | None) -> bytes:
    """Return DICOM bytes, optionally extracting a single frame.

    If frame is None, returns the raw data unchanged.
    If frame is specified, uses pydicom to extract that frame's pixel data.
    """
    if frame is None:
        return data

    import pydicom  # noqa: PLC0415

    ds = pydicom.dcmread(io.BytesIO(data))
    pixel_array = ds.pixel_array
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
