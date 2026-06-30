"""Tests for DICOM validation (TASK-045)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.api.errors import ValidationProblem
from app.attachments.dicom_validation import validate_dicom


def test_invalid_dicom_raises_validation_problem() -> None:
    """Non-DICOM bytes raise ValidationProblem."""
    with pytest.raises(ValidationProblem):
        validate_dicom(b"not a dicom file")


def test_valid_dicom_returns_metadata() -> None:
    """Valid DICOM returns dict with modality, patient_id, study_date."""
    mock_dataset = MagicMock()
    mock_dataset.Modality = "CT"
    mock_dataset.PatientID = "P001"
    mock_dataset.StudyDate = "20240101"

    with patch("pydicom.dcmread", return_value=mock_dataset):
        result = validate_dicom(b"fake dicom bytes")

    assert result["modality"] == "CT"
    assert result["patient_id"] == "P001"
    assert result["study_date"] == "20240101"


def test_dicom_with_none_attributes_returns_none_for_absent_fields() -> None:
    """DICOM whose optional tags are None returns None for those fields."""
    mock_dataset = MagicMock()
    mock_dataset.Modality = None
    mock_dataset.PatientID = None
    mock_dataset.StudyDate = None

    with patch("pydicom.dcmread", return_value=mock_dataset):
        result = validate_dicom(b"fake bytes")

    assert "modality" in result
    assert result["modality"] is None
    assert result["patient_id"] is None
    assert result["study_date"] is None
