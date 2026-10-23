---
id: "PRB-048"
type: problem-report
title: "DICOM viewer module is not installed in any environment"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
criticality: major
links: []
tags: ["configuration-management", "modules", "dicom"]
---

# PRB-048 — DICOM viewer module is not installed in any environment

## Observed

- The DICOM viewer is a plugin module. `backend/modules/dicom_viewer/pyproject.toml:7-8` declares
  its entry point `dicom-viewer = "dicom_viewer.manifest:manifest"` in the group
  `medhub.modules`.
- Nothing installs that package:
  - `backend/pyproject.toml` neither lists it in `[project] dependencies` nor declares it as a uv
    source or workspace member (there is no `[tool.uv]` table).
  - `backend/uv.lock` has no `dicom-viewer` entry.
  - `backend/Dockerfile:6` and `:13` only copy the `modules/` folder into the image.
- **Effect at start-up:** `discover_modules()` (`backend/app/modules/discovery.py:40`, called from
  `backend/app/main.py:42`) reads `importlib.metadata.entry_points(group="medhub.modules")`
  (`discovery.py:46`). That finds nothing, so the module's router, including
  `GET /studies/{attachment_id}` (`backend/modules/dicom_viewer/dicom_viewer/router.py:22`), is
  never mounted.
- **QA evidence:** in the production image `medhub-backend:ci` and in the dev venv (`uv run`), the
  entry-point query returns `[]` and `find_spec("dicom_viewer")` is `False`.
- **Frontend effect:** the module is never registered or enabled, so `dicomModuleEnabled`
  (`frontend/src/core/clinical/AttachmentItem.tsx:24`) is never true, and the DICOM "view" link
  (`:32`) never renders. The core "Download" link is unaffected.
- **The "view" link does not use the module either:** it is built from the same core
  `/attachments/{id}` URL as "Download" (`AttachmentItem.tsx:32-34`,
  `frontend/src/api/client.ts:166-167`), and nothing in the frontend calls the module's `/studies/`
  endpoint. Installing the module alone would only show a second link to the raw download.
- **Why the tests pass:** the module's tests put `modules/dicom_viewer` on `sys.path` themselves
  (`backend/modules/dicom_viewer/tests/conftest.py:1-16`).
- [ADR-0005](../design/adr/0005-plugin-module-mechanism.md):41 requires a plugin to be
  "build/deploy-time installed (package present in the image)".

## Impact

- SR-017 (DICOM image opening and rendering) is not available in any environment built from the
  manifests. The module endpoint returns 404, and the in-app viewer cannot be reached.
- The RISK-003 controls that live in the module (the frame endpoint, and the fail-loud behaviour
  of PRB-006 and TASK-135) are verified only by tests that bypass installation. No deployed system
  exercises them.
- PRB-046 (NumPy not declared) is masked: the frame path becomes reachable, and fails, only once
  this report is resolved.

## Safety evaluation

Nothing wrong is shown to a clinician. The DICOM "view" link is absent. A DICOM attachment can
still be downloaded through the core attachment endpoint and opened in an external viewer, so the
information is not lost or misattributed. This affects no data integrity and no clinical decision
beyond the unavailability of the in-app viewer (RISK-007 at most). RISK-003 is not re-scored:
an absent viewer cannot render a wrong image.

The criticality is `major`, following the PRB-002 precedent: a core SR function is unavailable in
a real deployment, and the test suite does not detect it. The human may change it at approval.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

In a separate CR (outside CR-001):

- Install the module in every environment by declaring it a dependency of `medhub-backend`. That
  can be done as a uv workspace member, or as a path dependency through `[tool.uv.sources]`. Either
  way, `uv sync --frozen --no-dev` then installs its entry point in the production image.
- Refresh `backend/uv.lock`.
- Add a test that the built production image discovers the module, for example
  `entry_points(group="medhub.modules")` contains `dicom-viewer`. Add it to the Docker Build job,
  like TS-013 TC-013.8.
- Run the module tests against the installed package, not a `sys.path` insertion.
- Wire the "view" link to the module's `/studies/{id}` endpoint, or record that the viewer module
  has no frontend and remove the link.
- Plan PRB-046 (NumPy and transfer syntaxes) and PRB-006 (decode bound) in the same change, since
  installing the module makes their path reachable.

## Source

Found by the QA review of TASK-154 (CR-001, 2026-10-22), while checking PRB-046 and SOUP-015.
Verified statically by the Software Architect role: manifests, lock, Dockerfile and the cited
source lines.
