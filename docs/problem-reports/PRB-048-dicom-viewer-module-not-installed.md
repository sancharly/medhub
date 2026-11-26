---
id: "PRB-048"
type: problem-report
title: "DICOM viewer module is not installed in any environment"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-11-26"
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

## Resolution

Resolved in CR-008 (the `resolves` link is on CR-008), verified in the working tree on 2026-11-26 (TASK-239, branch `bug/dicom-module-install`, head 5bd10e7 plus the task's working-tree changes).

What changed:
- **TASK-233** (D-1, D-7): `medhub-dicom-viewer` is a uv workspace member and a dependency of `medhub-backend` (`backend/pyproject.toml`, `backend/uv.lock`); the production image installs it non-editable (`backend/Dockerfile`, `uv sync --frozen --no-dev --no-editable`) and no longer ships `modules/` source; the module suite runs with `--import-mode=importlib` against the installed package (ADR-0024).
- **TASK-236** (D-6): `backend/scripts/check_image_modules.py` and a Docker Build step fail the build when the image does not discover the module; `infra/smoke-test.sh` checks 401, not 404, on the module route.
- **TASK-237** (D-5): the "Open in viewer" link, which opened the raw download, is removed; Download stays.
- **TASK-238**: arc42, ADD, DEPLOY.md and SR-017 updated.

Verification (2026-11-26):
- Fresh clone of the branch (head 5bd10e7), `cd backend && uv sync --frozen --python 3.12`, then the CR-008 entry-point command prints `['dicom-viewer']`.
- Image built from the branch with the project's Compose file: `entry_points(group='medhub.modules')` is `['dicom-viewer']` and `python scripts/check_image_modules.py /app` exits 0. The same check run against the pre-TASK-233 image `infra-backend:latest` exits 1 (no entry point, no `dicom_viewer`, no NumPy, `/app/modules` present). A stand-in install whose entry-point target is `dicom_viewer.manifest:nope` also exits 1 (a name-only check would have passed).
- Started stack (a scratch Compose project, branch image): `GET /api/v1/modules/dicom-viewer/studies/<uuid>` unauthenticated answers 401; a doctor of a group without the module enabled answers 403; after a system administrator enabled `dicom-viewer` for the group, the doctor reaches the route (smoke test: `[PASS]` for the 401 check, TS-010 TC-010.9).
- Module guard tests (TS-010 TC-010.8) pass; negative control: with `medhub-dicom-viewer` uninstalled the three guard tests fail, reinstalled they pass.
- Frontend (TS-019 TC-019.12): suite 412 passed on Node 20.19.0, lint, typecheck and build clean.
- Hosted CI: the Docker Build job (including the TASK-236 image check) and the full workflow run only after the human approves a push; their result is verified on hosted CI after push and is not claimed here.
- Not part of this resolution: the viewer itself (#29) and the "first rendered image within 10 s" case (SR-026 AC 3), which stay with the viewer phase.

## Source

Found by the QA review of TASK-154 (CR-001, 2026-10-22), while checking PRB-046 and SOUP-015.
Verified statically by the Software Architect role: manifests, lock, Dockerfile and the cited
source lines.

## Note (2026-11-15, CR-006 TASK-226)

SR-026 AC 3 (the first rendered DICOM image within 10 s) is not verified by CR-006 and stays unverified until this problem report and PRB-046 are both resolved: on a started stack the viewer route is not mounted and the decode cannot run (TS-018 TC-018.11, TS-019 TC-019.5). CR-006 verifies the stored and decoded size bounds only (TASK-218, TS-019 TC-019.1 to TC-019.4); the deferral follows D-20 and is for the human to confirm.

## Version history

- 1.2 (2026-11-26) — Resolved (TASK-239, CR-008): fix and verification recorded in "Resolution". The human closes the PRB in MedTrace after the merge.
