"""The narrow settings accessor a module uses instead of app.core.config (TASK-223, SR-016 AC 3)."""

from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.modules import module_settings


def test_accessor_returns_defaults() -> None:
    assert module_settings.dicom_max_stored_bytes() == 157286400
    assert module_settings.dicom_max_decoded_bytes() == 1073741824


def test_accessor_returns_the_configured_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DICOM_MAX_STORED_BYTES", "1234")
    monkeypatch.setenv("DICOM_MAX_DECODED_BYTES", "5678")
    get_settings.cache_clear()
    assert module_settings.dicom_max_stored_bytes() == 1234
    assert module_settings.dicom_max_decoded_bytes() == 5678


def test_accessor_exports_nothing_but_the_module_limits() -> None:
    assert set(module_settings.__all__) == {"dicom_max_stored_bytes", "dicom_max_decoded_bytes"}
