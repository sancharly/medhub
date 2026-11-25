---
id: "TASK-238"
type: task
title: "Document the installed DICOM module and its supported transfer syntaxes"
status: draft
version: "1.1"
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

- [ ] arc42 05, 07 and 12 and ADD-012, ADD-014, ADD-015 and ADD-021 describe the installed module, its check order,
  allow-list and frame media type, and the absence of a viewer entry point (SR-017 AC 7 to AC 11).
- [ ] `infra/DEPLOY.md` names the supported syntaxes and the refusal of the others (P-2; RISK-003
  information-for-safety row).

## Definition of Done

- [ ] Sections and records updated; `traceability-check` 0 errors

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
- 1.1 (2026-11-25) — CR-008 D-B: depends on TASK-240; ADD-012, ADD-014 and the matching arc42 05 lines added (shared helper, upload-path bound). `draft`.
