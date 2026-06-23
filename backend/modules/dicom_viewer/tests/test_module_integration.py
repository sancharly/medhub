"""Integration tests for DICOM module manifest and boundary (TASK-073)."""

from __future__ import annotations

from unittest.mock import MagicMock

from dicom_viewer.manifest import DICOMViewerManifest, manifest


class TestManifestIntegration:
    def test_module_manifest_singleton(self) -> None:
        assert isinstance(manifest, DICOMViewerManifest)

    def test_register_calls_mount_with_router(self) -> None:
        m = DICOMViewerManifest()
        mock_registry = MagicMock()
        mock_services = MagicMock()
        m.register(mock_registry, mock_services)
        assert mock_registry.mount.called
        call_args = mock_registry.mount.call_args
        assert call_args[0][0] == "dicom-viewer"

    def test_required_permissions_is_list(self) -> None:
        m = DICOMViewerManifest()
        assert isinstance(m.required_permissions, list)

    def test_version_is_semver_like(self) -> None:
        import re

        m = DICOMViewerManifest()
        assert re.match(r"^\d+\.\d+\.\d+", m.version)
