"""DICOM helpers — frame extraction and content-type validation."""

from __future__ import annotations

import io
import re
from typing import Any

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


def _native_bytes(samples: Any) -> bytes:
    """The samples as ``tobytes()`` writes them, in the server's native byte order (ADD-015).

    pydicom returns the array of an Explicit VR Big Endian object with a big-endian dtype, so the
    order is normalised; for every other syntax this is a no-copy view.
    """
    native: bytes = samples.astype(samples.dtype.newbyteorder("="), copy=False).tobytes()
    return native


def stream_dicom(data: bytes, frame: int | None) -> bytes:
    """Return DICOM bytes, optionally extracting a single frame.

    If frame is None, returns the raw data unchanged.
    If frame is specified, uses pydicom to extract that frame's pixel data, after the
    transfer syntax has been checked against the allow-list (SR-017 AC 10), the inflated size of a
    Deflated object and the header-declared decoded size against the configured maximum (AC 6).
    A decode that fails raises a problem; no partial bytes are returned. The frame is returned as
    ``ndarray.tobytes()`` in native byte order, the layout of ADD-015 "Frame response".
    """
    if frame is None:
        return data
    if frame < 0:
        raise ValidationProblem(f"Frame {frame} out of range; the first frame is 0.")

    import pydicom  # noqa: PLC0415

    if _check_transfer_syntax(data) == str(DeflatedExplicitVRLittleEndian):
        _check_inflated_size(data)
    _check_declared_decoded_size(data)
    try:
        ds = pydicom.dcmread(io.BytesIO(data))
        # The samples as stored: no YCbCr to RGB conversion (pydicom converts YBR_FULL and
        # YBR_FULL_422 by default); a YBR_FULL_422 object is still upsampled to 3 samples per pixel.
        ds.pixel_array_options(as_rgb=False)
        pixel_array = ds.pixel_array
        rows = int(ds["Rows"].value)
        columns = int(ds["Columns"].value)
        samples = int(ds.get("SamplesPerPixel", 1) or 1)
        num_frames = int(ds.get("NumberOfFrames", 1) or 1)
    except Exception as exc:
        raise _problem("dicom_decode_failed", "The DICOM pixel data could not be decoded.") from exc
    # The frame shape comes from the header; the decoded array must be exactly one frame of it, or
    # exactly NumberOfFrames of them (absent means 1). Anything else is refused, never guessed.
    frame_shape = (rows, columns) if samples == 1 else (rows, columns, samples)
    shape = tuple(pixel_array.shape)
    single = num_frames == 1 and shape == frame_shape
    multiple = shape[1:] == frame_shape and shape[0] == num_frames
    frame_bytes = rows * columns * samples * pixel_array.dtype.itemsize
    if not (single or multiple) or pixel_array.nbytes != num_frames * frame_bytes:
        raise _problem(
            "dicom_decode_failed", "The DICOM pixel data does not match the size in the header."
        )
    if frame >= num_frames:
        noun = "frame" if num_frames == 1 else "frames"
        raise ValidationProblem(f"Frame {frame} out of range; this DICOM has {num_frames} {noun}.")
    return _native_bytes(pixel_array if single else pixel_array[frame])
