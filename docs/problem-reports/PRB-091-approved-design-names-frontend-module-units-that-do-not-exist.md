---
id: "PRB-091"
type: problem-report
title: "Approved design names frontend module units that were never built"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-15"
updated: "2026-11-16"
criticality: minor
links: []
tags: ["design", "frontend", "documentation", "found-in:TASK-225", "outside:CR-006"]
---

# PRB-091 — Approved design names frontend module units that were never built

## Observed

Found by QA in the TASK-225 review (2026-11-15). The approved design record ADD-021 (SI-FE-MODREG) lists the units `U-FEM-Registry` (module registry and lazy import, SR-016) and `U-FEM-NavGate` (navigation shown only when the module is enabled per `GET /me/modules`, SR-015). Arc42 section 05 repeats them and `docs/design/12-interfaces.md` (12.2, row `ModuleRegistry`, `register(FrontendModule)`) defines the interface and the `FrontendModule` type. None of this exists in `frontend/src`: there is no `ModuleRegistry`, no `register` call and no module navigation item. The only reader of the module list is `useMyModules` (`frontend/src/modules/useMyModules.ts`), used by `AttachmentItem` to show the DICOM viewer link.

## Impact

The design records describe a structure the product does not have. A reader of ADD-021 or section 12 would expect a registry through which a module is added with no edit to other items (SR-016 AC 1), and a gated navigation entry (SR-015). Neither is verifiable. The frontend DICOM viewer module (SI-MOD-DICOM-FE, ADD-022) is also not built (TS-019 scope note), so no module uses the registry yet.

## Investigation

`grep -rn "ModuleRegistry\|register(" frontend/src` finds no registry; `frontend/src/modules/` holds `index.ts`, `useMyModules.ts` and its test. The backend side of SR-016 (entry points, `ModuleManifest`, `PlatformServices`) is built and tested (TS-010). CR-007 investigated the open point (P-1, P-2). SR-015 AC 3 is verified on the server (TS-005 TC-005.2) and at the only client entry point, the viewer link of `AttachmentItem` (TC-005.6); it claims no frontend navigation, so it is met without the registry. SR-016 AC 2 (an enabled module is presented in the navigation/UI) is not met: no frontend module exists, and no test case cites it (TS-010 covers AC 1 and AC 3 only). CR-007 D-2 defers SR-016 AC 2 to PRB-048 with its wording unchanged (it stays unverified until then); D-3 leaves SR-015 AC 3 and SR-026 AC 7 unchanged.

## Safety evaluation

No data integrity, safety-related function or clinical decision is affected: the server enforces module access (`ModuleAccessGuard`, `AuthorizationService`), and the missing client navigation gate is defence in depth only. The gap is between an approved design and the code, so it is a traceability finding (IEC 62304 §5.3, §5.4). Criticality `minor`. Outside CR-006.

The decision on the registry and the navigation gate was taken in CR-007 (D-1): correct the design to what exists and record them as deferred to PRB-048.

## Resolution

Documentation correction under CR-007 D-1 (TASK-230); no code change. The design had described a structure the product does not have, and the build is already planned with the frontend DICOM viewer module (PRB-048, TASK-100, TASK-101), so the records now describe what exists and keep the target design as deferred.

- ADD-021 (1.2 to 1.3, `in_review`, approval record removed): the one built unit is `U-FEM-MyModules` (`useMyModules`, `frontend/src/modules/useMyModules.ts`, consumer `AttachmentItem`); `U-FEM-Registry` and `U-FEM-NavGate` moved to a "Deferred units" paragraph (ADR-0005 target design, built with PRB-048); SR-016 AC 2 deferred (D-2).
- `docs/design/05-building-blocks.md`: SI-FE-MODREG responsibility and unit list as in ADD-021; module boundary note says `SI-MOD-DICOM-FE` and the frontend registry are planned.
- `docs/design/12-interfaces.md`: the `ModuleRegistry` row and the `FrontendModule` type moved under a "Planned (not built)" note; rule 4 says "once built".
- `docs/specifications/diagram-building-blocks.puml`: unbuilt parts labeled "(planned)", dashed arrows.

Verification: `grep -rn "ModuleRegistry\|FrontendModule" frontend/src` finds nothing; the same grep over `docs/design` and ADD-021 hits only deferred or planned statements (and ADR-0005, which is the target design and out of scope); the diagram renders with `plantuml`. Status stays `open` until QA confirms the review and `traceability-check`; then `resolved` (CR-007 `resolves` this record).

QA confirmation (TASK-230 review, 2026-11-16, working tree): `grep -rn "ModuleRegistry\|FrontendModule" frontend/src` finds nothing; in ADD-021, `docs/design/05-building-blocks.md` and `docs/design/12-interfaces.md` every mention of `ModuleRegistry`, `FrontendModule`, `U-FEM-Registry` and `U-FEM-NavGate` is a deferred or planned statement; `useMyModules` and `AttachmentItem` exist and behave as ADD-021 states (TS-005 TC-005.5, TC-005.6 unchanged); `plantuml -checkonly` passes; `traceability-check` 0 errors. Residual outside the CR-007 scope (TASK-230 QA MEDIUM-1): `docs/design/06-runtime-views.md` 6.4 and `docs/specifications/diagram-seq-dicom-view.puml` still describe the module navigation item and lazy chunk without a "planned" mark; they are part of the unbuilt frontend DICOM viewer scenario (PRB-048) and are corrected with it or at the next change of section 06. `resolved` (CR-007 holds the `resolves` link).

## Version history

- 1.0 (2026-11-15) — Created from the TASK-225 QA review. `open`, `minor`, outside CR-006.
- 1.1 (2026-11-16) — TASK-230: investigation updated with CR-007 P-1, P-2 (D-2, D-3); resolution written. `open`.
- 1.2 (2026-11-16) — QA approved TASK-230: Resolution confirmed in the working tree; status `open` → `resolved` (CR-007 D-1). Criticality unchanged.
