"""The platform settings a module may read (SR-016 AC 3, ADD-014).

A module does not import ``app.core.config``: ``Settings`` carries the database URL and the storage
and encryption keys. Each setting a module needs gets one accessor here, which reads the value on
every call so a changed configuration (or a test) is seen.
"""

from __future__ import annotations

from app.core.config import get_settings

__all__ = ["dicom_max_decoded_bytes", "dicom_max_stored_bytes"]


def dicom_max_stored_bytes() -> int:
    """Largest stored DICOM object the DICOM viewer opens (SR-017)."""
    return get_settings().dicom_max_stored_bytes


def dicom_max_decoded_bytes() -> int:
    """Largest decoded size the DICOM viewer accepts from a header (SR-017)."""
    return get_settings().dicom_max_decoded_bytes
