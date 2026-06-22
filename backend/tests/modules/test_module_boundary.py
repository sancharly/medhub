"""Tests that the DICOM module does not import from forbidden host internals (TASK-071)."""

from __future__ import annotations

from pathlib import Path

DICOM_SRC = Path(__file__).parent.parent.parent / "modules" / "dicom_viewer" / "dicom_viewer"

FORBIDDEN_PATTERNS = [
    "app.db",
    "app.core.object_storage",
]


def _all_imports(pattern: str) -> list[str]:
    """Return file:line matches for pattern anywhere in module source."""
    matches = []
    for py_file in DICOM_SRC.rglob("*.py"):
        for i, line in enumerate(py_file.read_text().splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if pattern in stripped and ("import" in stripped or "from" in stripped):
                matches.append(f"{py_file.name}:{i}: {stripped}")
    return matches


class TestModuleBoundary:
    def test_dicom_module_does_not_import_app_db(self) -> None:
        hits = _all_imports("app.db")
        assert hits == [], "DICOM module imports from app.db (forbidden):\n" + "\n".join(hits)

    def test_dicom_module_does_not_import_object_storage(self) -> None:
        hits = _all_imports("app.core.object_storage")
        assert hits == [], "DICOM module imports from app.core.object_storage:\n" + "\n".join(hits)
