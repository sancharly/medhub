"""The DICOM viewer module is an installed package, not a test-setup path (CR-008)."""

from __future__ import annotations

import importlib
import json
from importlib.metadata import distribution, entry_points, requires
from pathlib import Path
from urllib.parse import urlparse

from packaging.requirements import Requirement

from app.modules.discovery import discover_modules


def test_entry_point_is_discovered() -> None:
    eps = entry_points(group="medhub.modules")
    assert [ep.name for ep in eps] == ["dicom-viewer"]
    ep = next(iter(eps))
    assert ep.value == "dicom_viewer.manifest:manifest"
    assert ep.load().module_key == "dicom-viewer"
    assert "dicom-viewer" in [m.module_key for m in discover_modules()]


def test_distribution_declares_its_runtime_dependencies() -> None:
    names = {Requirement(r).name for r in requires("medhub-dicom-viewer") or []}
    assert {"numpy", "pydicom"} <= names
    # The lock is the authority on the NumPy version; only the import is asserted here.
    importlib.import_module("numpy")


def test_module_is_imported_from_the_installed_distribution() -> None:
    import dicom_viewer

    dist = distribution("medhub-dicom-viewer")
    module_file = Path(dicom_viewer.__file__).resolve()
    direct_url = json.loads(dist.read_text("direct_url.json") or "{}")
    if direct_url.get("dir_info", {}).get("editable"):
        # uv workspace members are editable installs: the source directory is the installed one.
        source = Path(urlparse(direct_url["url"]).path).resolve()
        assert source in module_file.parents
    else:
        assert module_file in {Path(str(f.locate())).resolve() for f in dist.files or []}
