"""Fail unless this image discovers the DICOM viewer module as an installed package.

Run inside the production image by the CI job "Docker Build" (SR-017 AC 7, SR-028; TASK-236):

    python scripts/check_image_modules.py /app

The one argument is the application directory (default /app). Exit 0 when:
- the `medhub.modules` entry points are exactly `dicom-viewer`;
- `dicom_viewer.manifest`, `numpy` and `pydicom` import;
- `<app>/modules` does not exist (the source tree is not shipped, ADR-0024);
- `dicom_viewer` is imported from `<app>/.venv/lib/python3.X/site-packages/`.
Otherwise print each failed check and exit 1.
"""

from __future__ import annotations

import importlib
import sys
from importlib.metadata import entry_points
from pathlib import Path


def failures(app: Path) -> list[str]:
    problems: list[str] = []

    names = sorted(e.name for e in entry_points(group="medhub.modules"))
    if names != ["dicom-viewer"]:
        problems.append(f"medhub.modules entry points are {names}, expected ['dicom-viewer']")

    for module in ("dicom_viewer.manifest", "numpy", "pydicom"):
        try:
            importlib.import_module(module)
        except Exception as exc:  # any import failure is a failed check
            problems.append(f"import {module} failed: {exc!r}")

    if (app / "modules").exists():
        problems.append(
            f"{app / 'modules'} exists; the module source tree must not be in the image"
        )

    site = (
        app
        / ".venv"
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
    )
    package = sys.modules.get("dicom_viewer")
    origin = getattr(package, "__file__", None)
    if origin is None:
        problems.append("dicom_viewer has no __file__ (not imported)")
    elif not str(origin).startswith(f"{site}/"):
        problems.append(f"dicom_viewer is imported from {origin}, expected under {site}/")

    return problems


def main() -> int:
    app = Path(sys.argv[1] if len(sys.argv) > 1 else "/app")
    problems = failures(app)
    for problem in problems:
        print(f"FAIL: {problem}", file=sys.stderr)
    if not problems:
        print("ok: dicom-viewer is discovered from the installed package")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
