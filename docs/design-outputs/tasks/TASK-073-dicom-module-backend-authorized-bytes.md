---
id: "TASK-073"
type: task
title: "DICOM module backend (authorized bytes)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-016"
    relation: implements
  - target: "SR-017"
    relation: implements
  - target: "TASK-072"
    relation: relates_to
  - target: "TASK-046"
    relation: relates_to
tags: ["fix-branch:phase-5-audit", "phase:5-module-host-dicom-backend"]
---

- **Phase:** 5 — Module host + DICOM backend
- **Software item / unit:** SI-MOD-DICOM-BE / U-DICOMBE-Studies
- **Implements:** SR-016 (data via platform services only), SR-017 (AC-5 only enabled + authorized users can open; bytes for CT/MRI/X-ray); ADR-0008, ADR-0005
- **Depends on:** TASK-072 (router mount + module gating), TASK-046 (`AttachmentService.open`) — must be merged first
- **Branch:** `feature/dicom-backend`
- **Status:** Completed (fix/phase-5-audit 2026-06-30)

## Objective

Deliver the DICOM viewer module **backend** — the first module proving the plugin mechanism (SR-016). It exposes one authorized endpoint that streams DICOM Part-10 bytes (and, where beneficial, frames) for a given attachment, obtaining those bytes **only** through `PlatformServices.attachments` after the enablement gate (TASK-072) and the per-request authorization. It is a separate installable package under `backend/modules/dicom_viewer/`, designed so new modalities add with minimal effort. Traces to SR-016 and SR-017 AC-5.

## Interfaces to honor

This module implements the **Module Contract** (`ModuleManifest`, [12-interfaces.md](../../design/12-interfaces.md) §12.1) and consumes `PlatformServices` **verbatim**:

```python
class ModuleManifest:  # the module provides an instance
    module_key = "dicom-viewer"
    name = "DICOM Viewer"
    version = "..."                       # semver
    required_permissions = [...]
    def register(self, registry: RouterRegistry, services: PlatformServices) -> None: ...
```

- `register` mounts an `APIRouter` via `registry.mount("dicom-viewer", router)` → host serves it at `/api/v1/modules/dicom-viewer/...` (TASK-072, ADR-0005).
- The byte endpoint obtains DICOM bytes/frames **only** via `services.attachments.open(actor, attachment_id)` (TASK-046) — the module **must not** touch object storage, the DB, or `SI-PERSIST` directly (§12.1 invariant, SR-016.3). Every request therefore passes `ModuleAccessGuard` (enablement, TASK-072) then `AuthorizationService` (consent, inside `attachments.open`) per runtime view 6.4.
- The module records its own access via `services.audit` where it adds module-specific context; the underlying clinical-data access is already audited by `attachments.open` (SR-023).

## Implementation detail

- Files to create (installable package — entry point `medhub.modules`, discovered by TASK-070):
  - `backend/modules/dicom_viewer/pyproject.toml` — declares `[project.entry-points."medhub.modules"]` → the manifest; depends on the host contract package.
  - `backend/modules/dicom_viewer/dicom_viewer/__init__.py`
  - `backend/modules/dicom_viewer/dicom_viewer/manifest.py` — the `ModuleManifest` instance + `register(...)`.
  - `backend/modules/dicom_viewer/dicom_viewer/router.py` — the `APIRouter` with the studies endpoint.
  - `backend/modules/dicom_viewer/dicom_viewer/dicom.py` — modality-agnostic helpers: stream the Part-10 object; optional frame extraction via **`pydicom`** (`dcmread`, `pixel_array` / per-frame access). Modality-handling table is data-driven (CT/MRI/X-ray registered) so a new modality is an entry, not a re-architecture (ADR-0008 low-effort extension).
  - `backend/modules/dicom_viewer/tests/` — module tests.
- Endpoint ([api-design.md](../../specifications/api-design.md) "Module endpoints"): `GET /api/v1/modules/dicom-viewer/studies/{attachmentId}` → authorized DICOM bytes/frames. Default: stream the whole Part-10 object (Cornerstone3D parses client-side, ADR-0008). Optional `?frame=` for per-frame bytes where beneficial (ADR-0008 "and, where beneficial, frames").
- Response: `application/dicom` (whole object) with appropriate `Content-Type`/`Content-Length`; bytes are produced by `attachments.open`'s stream — the module does not re-encode pixel data (rendering is client-side, ADR-0008). Initial-render budget (10 s, SR-026) is met by streaming bytes only and lazy/progressive client loading.
- Audit: the module emits a `module.dicom.studies.read` event via `services.audit` with attachment id and outcome (in addition to the `attachment.read` audit from TASK-046).
- Error cases (RFC 7807): module not enabled → `403 /errors/forbidden` (from TASK-072 gate, before the handler); not authorized to the underlying attachment → `403 /errors/forbidden` (from `attachments.open`, SR-017 AC-5); unknown attachment → `404 /errors/not-found`; attachment is not a DICOM object → `400 /errors/validation-error` (or `404` if treated as not-a-DICOM-study) — document the chosen code in OpenAPI.
- Edge cases: a user with the module enabled but **without** consent to the patient is denied at `attachments.open` (enablement ≠ data authorization — both gates required, SR-015 + SR-005, SR-017 AC-5). A user authorized to the data but **without** the module enabled is denied at the gate. CT/MRI/X-ray are in MVP scope (SR-017 AC-2, ADR-0008); other modalities are out of MVP but enter via the same data-driven path with minimal change.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/modules/dicom_viewer/tests/test_studies_endpoint.py`):
  - the manifest is a valid `ModuleManifest` with `module_key == "dicom-viewer"` and registers a router at the module prefix (SR-016 AC-4).
  - authorized + enabled user `GET .../studies/{attachmentId}` → DICOM bytes streamed; bytes came from `services.attachments.open` (assert the facade was the source; no direct storage/DB access) (SR-016.3, SR-017 AC-1).
  - `?frame=` returns the requested frame for a multi-frame DICOM (volumetric handling, SR-017 AC-3 byte side).
  - enabled but **not authorized** to the attachment → `403`, no bytes, denied access audited (SR-017 AC-5, SR-005, SR-023).
  - authorized but module **not enabled** → `403` at the gate, handler not entered (SR-015, SR-017 AC-5).
  - non-DICOM / unknown attachment → `400`/`404`.
  - CT, MRI, and X-ray sample objects all stream successfully (SR-017 AC-2).
  - module emits its `module.dicom.studies.read` audit event (SR-023).
- Module-boundary test (reuse `backend/tests/modules/test_module_boundary.py`, TASK-071): the package imports only the contract/facade — no `app.db`, no object-storage client (§12.1 invariant, SR-016 AC-3).
- Integration (`backend/modules/dicom_viewer/tests/test_module_integration.py`): installed via its entry point, discovered (TASK-070), mounted + gated (TASK-072); end-to-end authorized fetch and the two denial paths.

## Acceptance criteria

- [x] The DICOM viewer is delivered as a module via the plugin mechanism — separate package, entry point, no edits to core or other modules (SR-016 AC-1/AC-4).
- [x] `GET /api/v1/modules/dicom-viewer/studies/{attachmentId}` returns authorized DICOM bytes/frames (api-design, SR-017 AC-1).
- [x] Bytes are obtained **only** through `PlatformServices.attachments` after authorization — no direct storage/DB access (SR-016.3).
- [x] Both gates apply: only a user with the module enabled (SR-015) **and** authorized to the source data (SR-005) can open an image (SR-017 AC-5).
- [x] CT, MRI, and X-ray objects are served; the modality table is data-driven for low-effort extension (SR-017 AC-2, ADR-0008).
- [x] Module-specific and underlying clinical-data access are audited (SR-023).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration + module-boundary tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (module studies endpoint under the module prefix)
- [x] Audit events emitted for security-relevant actions (SR-023)
- [x] Traceability matrix row updated (SR-016, SR-017 → TASK-073 → tests)
- [x] Security review completed (authorized PHI byte access via module boundary — SR-031.6)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-070a. Dead code `SUPPORTED_MODALITIES` removed; module reachability unblocked by wiring `sync_installed` in TASK-070a.

## Fix verdict (2026-06-30)

- **Verdict:** PASS
- Implemented in `fix/phase-5-audit`. Dead code `SUPPORTED_MODALITIES = {"CT", "MRI", "XR"}` removed from `backend/modules/dicom_viewer/dicom_viewer/dicom.py`. Module reachability restored by TASK-070a: `sync_installed` now wired into startup, so the DICOM viewer entry point is persisted to `module_registry` and can be enabled.
