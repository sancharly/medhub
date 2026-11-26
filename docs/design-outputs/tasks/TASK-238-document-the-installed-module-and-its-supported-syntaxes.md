---
id: "TASK-238"
type: task
title: "Document the installed DICOM module and its supported transfer syntaxes"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-25"
links:
  - target: "SR-017"
    relation: implements
  - target: "SR-028"
    relation: implements
  - target: "RISK-003"
    relation: mitigates
  - target: "CR-008"
    relation: relates_to
  - target: "ADD-015"
    relation: relates_to
  - target: "ADD-022"
    relation: relates_to
  - target: "ADD-021"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "ADD-014"
    relation: relates_to
  - target: "TASK-240"
    relation: relates_to
tags: ["cr:CR-008", "control:information", "docs"]
---

# TASK-238 — Document the installed DICOM module and its supported transfer syntaxes

- **Role:** Document Writer (arc42 and operator documentation); records only, no code.
- **CR:** CR-008 (P-2, D-1, D-4, D-5; decision D-A).
- **Depends on:** TASK-233 to TASK-237 and TASK-240 (documents what they built; read their Implementation records).
- **Size:** M (five documentation files and one record).

## Objective

The narrative matches the built system: the module is installed as a workspace member and present in
the image, its frame path supports the D-3 (a) syntaxes only and returns `application/octet-stream`, and
no viewer entry point exists until #29.

## Steps

1. `docs/design/05-building-blocks.md`: SI-MOD-DICOM-BE — installation (workspace member, module-owned
   `numpy` and `pydicom`, ADR-0024), the frame-path check order and allow-list, the frame media type
   (link ADD-015, do not copy its table); `U-FEM-MyModules` — no consumer in code until #29
   (`AttachmentItem` no longer shows a viewer link).
2. `docs/design/07-deployment-view.md`: the backend image installs every module non-editable from the
   lock and does not ship `modules/`; the Docker Build job checks discovery (TS-013 TC-013.15).
3. `docs/design/12-interfaces.md`: `GET /api/v1/modules/dicom-viewer/studies/{attachment_id}` — 200
   `application/dicom` (whole object) or `application/octet-stream` (frame, layout in ADD-015); 400 rule
   `dicom_transfer_syntax_unsupported` added; the `useMyModules` row's consumer column updated.
4. `docs/design-outputs/architecture/ADD-021-frontend-module-registry.md` (approved 1.3 → 1.4, `in_review`,
   remove the approval record): `useMyModules` has no consumer in code after CR-008 D-5; TC-005.6 retired;
   version-history line.
5. `docs/design-outputs/architecture/ADD-015` (1.3, `in_review`): remove the "(planned)" marker from the
   CR-008 paragraph once TASK-233 to TASK-235 are approved; correct anything the implementation changed
   (e.g. the Big Endian byte-order finding of TASK-235); version-history line.
6. `infra/DEPLOY.md`, next to the "Module manifests" paragraph: one short paragraph (P-2): the DICOM
   viewer module is part of the image; per-frame decoding (`?frame=`) supports Implicit VR Little
   Endian, Explicit VR Little Endian, Deflated Explicit VR Little Endian, Explicit VR Big Endian and RLE
   Lossless; every other transfer syntax (JPEG, JPEG-LS, JPEG 2000, HTJ2K, video) is refused there with
   `dicom_transfer_syntax_unsupported` and stays downloadable whole; installing the module does not enable
   it (a system administrator enables it per group).
7. `docs/design-outputs/architecture/ADD-014-module-host-plugin-registry.md` (approved 1.1 → 1.2, `in_review`,
   remove the approval record): the new platform helper `app.modules.dicom_support` and its allow-listed
   names (TASK-234); `docs/design-outputs/architecture/ADD-012-attachment-service.md` (approved 1.9 → 1.10, same
   approval handling): `U-ATT-Upload` inflates a Deflated DICOM upload under `dicom_max_decoded_bytes` before
   validation (TASK-240, PRB-094); arc42 05 `U-MH-ModuleSettings` allow-list sentence and `U-ATT-Upload` line
   to match. Version-history lines.
8. arc42 sections 04, 08 and 11: check only; change them only if a statement is now false (e.g. section 11
   listing "module not installed"); list what was checked in the Implementation record.

## Verification

- Review against the code at the branch head: every statement in the changed sections is true there
  (`graphify query` for the module, discovery and Dockerfile; then the cited lines).
- Markdown links resolve (relative paths checked by hand or with the project's link check, if any).
- `traceability-check` on ADD-012, ADD-014, ADD-015, ADD-021, ADD-022, TASK-238, CR-008: 0 errors.

## Acceptance criteria

- [x] arc42 05, 07 and 12 and ADD-012, ADD-014, ADD-015 and ADD-021 describe the installed module, its check order,
  allow-list and frame media type, and the absence of a viewer entry point (SR-017 AC 7 to AC 11).
- [x] `infra/DEPLOY.md` names the supported syntaxes and the refusal of the others (P-2; RISK-003
  information-for-safety row).

## Definition of Done

- [x] Sections and records updated; `traceability-check` 0 errors

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
- 1.1 (2026-11-25) — CR-008 D-B: depends on TASK-240; ADD-012, ADD-014 and the matching arc42 05 lines added (shared helper, upload-path bound). `draft`.
- 1.2 (2026-11-25) — Implemented by the Document Writer role: sections, records and `DEPLOY.md` updated; orchestrator-requested corrections from the TASK-235 QA added (see the Implementation record). Handed to QA: `draft` to `in_review`.
- 1.2 (2026-11-25, QA) — Round 1 APPROVED (QA-1 to QA-6 LOW, not blocking); `traceability-check` 0 errors. Status `approved`. ADD-012 1.10, ADD-014 1.2, ADD-015 1.4 and ADD-021 1.4 stay `in_review` for the human's approval in MedTrace.

## Implementation record

Document Writer, 2026-11-25. Statements checked against the branch head (`backend/modules/dicom_viewer/dicom_viewer/{dicom.py,router.py}`, `backend/app/modules/dicom_support.py`, `backend/app/attachments/dicom_validation.py`, `backend/Dockerfile`, `backend/pyproject.toml`, `backend/scripts/check_image_modules.py`, `.github/workflows/ci.yml`).

**Files changed (steps 1 to 7).**

- arc42 05: `U-ATT-Upload` bounded inflation; `U-MH-ModuleSettings` allow-list sentence and new `U-MH-DicomSupport`; `U-DICOMBE-Studies` installation and frame-path check order (the "NumPy is not installed" sentence removed); `U-FEM-MyModules` has no consumer in code.
- arc42 07: new section "Backend image and installed modules (CR-008)".
- arc42 12: new "Module endpoint of CR-008" table (200 `application/dicom` and `application/octet-stream`, 400 `dicom_transfer_syntax_unsupported` and the other rules, 502); the `useMyModules` consumer column.
- ADD-021 1.3 to 1.4, ADD-014 1.1 to 1.2, ADD-012 1.9 to 1.10 (each `approved` to `in_review`, approval fields removed); ADD-015 1.3 to 1.4 (still `in_review`).
- `infra/DEPLOY.md`: paragraph "The DICOM viewer module", after the "Module manifests" paragraphs (P-2).

**Step 8 (checked).** arc42 04: no statement false. arc42 08: no statement false. arc42 11: the row "NumPy is not installed" was false and is removed; one row added for the accepted residual of Deflated inflation within the bound (RISK-007, CR-008 Q-2). Other statements in 11 unchanged.

**Added at the orchestrator's request (carried forward from the TASK-235 QA; not in the original steps).**

1. ADD-015 "Frame response" corrected: samples served as stored (YCbCr stays YCbCr, no photometric conversion); YBR_FULL_422 upsampled to 3 interleaved samples per pixel with each pixel pair's Cb and Cr repeated; interleaved whatever the Planar Configuration, in native byte order (Big Endian arrays converted); an array not matching the header's frame shape and count is `dicom_decode_failed`; trailing data smaller than one frame is ignored; a negative or out-of-range frame number is refused.
2. ADD-015 check order made exact (frame number, stored size, group 0002 allow-list, bounded inflation for Deflated only, declared decoded size, decode), with the upload path's bounded inflation (TASK-240) and its accepted residual (a Deflated upload within the bound is still inflated whole by pydicom, up to about 1 GiB; RISK-007; CR-008 Q-2).
3. CR-008 D-4 says samples "in the object's declared order"; ADD-015 and the code say interleaved per pixel whatever the Planar Configuration. ADD-015 now matches the code.

**For the human (CR-008 is not edited).**

- D-4 (a) wording "in the object's declared order" is inexact: the layout is interleaved (rows x columns x samples per pixel) whatever the Planar Configuration. Consider correcting it in CR-008 Decisions.
- D-3 (a) says the refusal names the UID; the code names it only when it is a well-formed UID of at most 64 characters, otherwise it says the UID is invalid (`dicom.py`, `_check_transfer_syntax`).
- The "trailing data under one frame is ignored" residual is documented in ADD-015 from the TASK-235 QA record; no test in `backend/modules/dicom_viewer/tests` names it.
- `traceability-check` was not run by this role; run it on ADD-012, ADD-014, ADD-015, ADD-021, ADD-022, TASK-238 and CR-008 before QA approval (Definition of Done item left unticked).

## QA review — round 1 (2026-11-25): APPROVED

QA Engineer. Every changed statement checked against the branch head (`dicom.py`, `router.py`, `dicom_support.py`,
`dicom_validation.py`, `test_module_boundary.py`, `Dockerfile`, both `pyproject.toml`, `check_image_modules.py`,
`ci.yml`, `smoke-test.sh`, `frontend/src`). Check order, allow-list, frame layout (as-stored YCbCr, YBR_FULL_422
upsampling, interleaving, native byte order, header-mismatch refusal), upload-path bound and its residual, install
mechanism and CI and smoke checks hold. No changed document still says NumPy is missing, the module is not installed
or a viewer link exists. arc42 11 rows match RISK-007; `U-MH-DicomSupport` in 05 matches ADD-014 and the allow-list
in `test_module_boundary.py`. ADR-0024, SR, RISK, SOUP, TS and TC ids resolve.

Points for the human: (1) CR-008 D-4 (a) "in the object's declared order" and (2) D-3 (a) "naming the UID" are
stated accurately. (3) Trailing data under one frame: the ADD-015 sentence is true. A QA probe served the exact
frame with 2 and 30 extra bytes and refused 32 (one frame) with `dicom_decode_failed`, for 1 and 3 frames. It cites
its source (TASK-235 QA), so it does not claim more than the evidence; no test pins it (QA-1). (4) `frame=-1`: 400
problem over HTTP (FastAPI `ge=0`, the 400 `validation-error` handler); the docs' "400 problem" wording matches.

- **QA-1 LOW — trailing-data residual not pinned by a test.** `ADD-015-dicom-module-backend.md:83`. Add a TS-019 case (2 extra bytes:
  exact frame; one frame extra: `dicom_decode_failed`) in TASK-239 or a later task.
- **QA-2 LOW — 07 "copies only" omits `alembic.ini`.** `docs/design/07-deployment-view.md:38`. Say "the virtual
  environment, `alembic.ini`, `app/`, `scripts/` and the entry script".
- **QA-3 LOW — DEPLOY.md contradicts itself.** `infra/DEPLOY.md:279`: "there is nothing to install. Installing it
  does not enable it". Write "Being in the image does not enable it".
- **QA-4 LOW — stale viewer-link clause in ADD-021.** `ADD-021-frontend-module-registry.md:44`: "never shows the viewer link". Drop it or say
  "keeps the last known list" only.
- **QA-5 LOW — check list omits the content-type check.** `ADD-015-dicom-module-backend.md:48`, `docs/design/05-building-blocks.md:120`: the route
  refuses a non-`application/dicom` attachment (`validate_dicom_content_type`) after the stored size and before the
  syntax. Name it, or say the list starts after the content-type check.
- **QA-6 LOW — 12 table lists no 401, 403 or 404.** `docs/design/12-interfaces.md:105-115`: the mount gate
  (`require_module_enabled`) and the authorization of `open()` answer these. Add a row "`401`/`403`/`404` as every
  module route" or state the table lists only what CR-008 changed.

Pre-existing (not blocking): `docs/design/06-runtime-views.md:37` says the shell shows a viewer nav item and loads the
module as a lazy chunk; neither exists (PRB-091, deferred units).

`traceability-check` (fallback parser; CR-008, the four ADDs, ADD-022, TASK-238, and every record linked to or from
them: 67 of 487 records): 0 errors, 65 warnings, none new to this task (62 W5 approved records linking records under
review in CR-008, W1 SR-018 no TS, W6 links to obsolete ADD-004). MedTrace's own Verify view was not run here.
