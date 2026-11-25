"""DICOM helpers — frame extraction and content-type validation."""

from __future__ import annotations

import io
import re

from pydicom.uid import (
    DeflatedExplicitVRLittleEndian,
    ExplicitVRBigEndian,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    RLELossless,
)

from app.api.errors import ProblemDetail, ValidationProblem
from app.modules.dicom_support import (
    DeflateStreamError,
    InflatedSizeExceeded,
    check_inflated_size,
    read_transfer_syntax,
)
from app.modules.module_settings import dicom_max_decoded_bytes

# The transfer syntaxes NumPy decodes without a decoder plugin (CR-008 D-3 (a), ADD-015); all are
# lossless. Every other syntax is refused on the frame path.
SUPPORTED_FRAME_TRANSFER_SYNTAXES = frozenset(
    str(uid)
    for uid in (
        ImplicitVRLittleEndian,
        ExplicitVRLittleEndian,
        DeflatedExplicitVRLittleEndian,
        ExplicitVRBigEndian,
        RLELossless,
    )
)

_UID = re.compile(r"[0-9]+(\.[0-9]+)*")


def validate_dicom_content_type(content_type: str) -> None:
    """Raise ValidationProblem if content_type is not application/dicom."""
    if content_type != "application/dicom":
        raise ValidationProblem(f"Expected application/dicom content type, got {content_type!r}.")


def _problem(rule: str, message: str) -> ValidationProblem:
    return ValidationProblem(
        message, errors=[ProblemDetail(field="study", rule=rule, message=message)]
    )


def _check_transfer_syntax(data: bytes) -> str:
    """Return the transfer syntax from the file meta information, or refuse the object.

    Nothing beyond group 0002 is parsed; a missing syntax is refused, never guessed (SR-017 AC 10).
    """
    uid = read_transfer_syntax(io.BytesIO(data))
    if uid is None:
        raise _problem(
            "dicom_transfer_syntax_unsupported",
            "The DICOM object declares no transfer syntax; it cannot be decoded as a frame.",
        )
    if uid not in SUPPORTED_FRAME_TRANSFER_SYNTAXES:
        # The value is untrusted input: name it only when it is a UID (PS3.5 section 9.1).
        if len(uid) > 64 or not _UID.fullmatch(uid):
            message = "The DICOM transfer syntax UID is invalid; frame decoding is not supported."
        else:
            message = f"The DICOM transfer syntax {uid} is not supported for frame decoding."
        raise _problem("dicom_transfer_syntax_unsupported", message)
    return uid


def _check_inflated_size(data: bytes) -> None:
    """Refuse a Deflated object inflating above the decoded bound, without inflating it in full."""
    maximum = dicom_max_decoded_bytes()
    try:
        check_inflated_size(io.BytesIO(data), maximum)
    except InflatedSizeExceeded as exc:
        raise _problem(
            "dicom_decoded_size_exceeded",
            f"The inflated size is larger than the maximum of {maximum} bytes.",
        ) from exc
    except DeflateStreamError as exc:
        raise _problem("dicom_decode_failed", "The DICOM pixel data could not be decoded.") from exc


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
    transfer syntax has been checked against the allow-list (SR-017 AC 10), the inflated size of a
    Deflated object and the header-declared decoded size against the configured maximum (AC 6).
    A decode that fails raises a problem; no partial bytes are returned.
    """
    if frame is None:
        return data

    import pydicom  # noqa: PLC0415

    if _check_transfer_syntax(data) == str(DeflatedExplicitVRLittleEndian):
        _check_inflated_size(data)
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
