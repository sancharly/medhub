"""DICOM Viewer module manifest."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.contract import PlatformServices, RouterRegistry


class DICOMViewerManifest:
    module_key = "dicom-viewer"
    name = "DICOM Viewer"
    version = "0.1.0"
    required_permissions = ["clinical:read"]

    def register(self, registry: RouterRegistry, services: PlatformServices) -> None:
        from dicom_viewer.router import build_router  # noqa: PLC0415

        router = build_router(services)
        registry.mount(self.module_key, router)


manifest = DICOMViewerManifest()
