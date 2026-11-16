---
id: "PRB-091"
type: problem-report
title: "Approved design names frontend module units that were never built"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-15"
updated: "2026-11-15"
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

`grep -rn "ModuleRegistry\|register(" frontend/src` finds no registry; `frontend/src/modules/` holds `index.ts`, `useMyModules.ts` and its test. The backend side of SR-016 (entry points, `ModuleManifest`, `PlatformServices`) is built and tested (TS-010). Whether SR-015 AC 3 and SR-016 AC 2 (frontend gating and lazy loading) are met by other means was not established here.

## Safety evaluation

No data integrity, safety-related function or clinical decision is affected: the server enforces module access (`ModuleAccessGuard`, `AuthorizationService`), and the missing client navigation gate is defence in depth only. The gap is between an approved design and the code, so it is a traceability finding (IEC 62304 §5.3, §5.4). Criticality `minor`. Outside CR-006.

**Open decision for a human:** build the registry and the navigation gate, or remove the two units and the interface from ADD-021 and section 12 (and decide how SR-015 AC 3 and SR-016 AC 2 are then verified). This record does not take that decision.

## Resolution

Not fixed here. Arc42 sections 05 and 12 cite this record instead of describing the units as built.
