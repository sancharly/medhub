---
id: "TASK-230"
type: task
title: "Correct the frontend module design records to the units that exist"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-16"
updated: "2026-11-16"
links:
  - target: "SR-015"
    relation: implements
  - target: "SR-016"
    relation: implements
  - target: "CR-007"
    relation: relates_to
  - target: "PRB-091"
    relation: relates_to
  - target: "ADD-021"
    relation: relates_to
  - target: "PRB-048"
    relation: relates_to
  - target: "TASK-100"
    relation: relates_to
  - target: "TASK-101"
    relation: relates_to
  - target: "RISK-004"
    relation: relates_to
tags: ["cr:CR-007", "design", "frontend", "documentation"]
---

# TASK-230 — Correct the frontend module design records to the units that exist

- **Software item:** SI-FE-MODREG (ADD-021).
- **PRB:** PRB-091. **CR:** CR-007 (D-1).
- **Depends on:** none. Parallel with TASK-229 and TASK-231. If the human answers P-1 with option (b),
  the SR-016 change is a separate Product Owner step before this task closes.
- **Branch:** `fix/cr-007-review-followups`.
- **Size:** S (records only: `docs/design-outputs/architecture/ADD-021-frontend-module-registry.md`,
  `docs/design/05-building-blocks.md`, `docs/design/12-interfaces.md`,
  `docs/specifications/diagram-building-blocks.puml`, PRB-091). No code change.

## Objective

ADD-021, arc42 05 and 12 describe what is built in `frontend/src`. The built unit is `useMyModules`
(`frontend/src/modules/useMyModules.ts`), the one reader of `GET /me/modules`, whose consumer is
`AttachmentItem` (the DICOM viewer link, gated on the user's module list). `U-FEM-Registry`,
`U-FEM-NavGate`, `ModuleRegistry` and `register(FrontendModule)` are not built; they are recorded as
deferred to the frontend DICOM viewer module (PRB-048), planned in TASK-100 and TASK-101 (`draft`), not
as existing units.

## Steps

1. **ADD-021** (approved 1.2 → 1.3; `in_review`; remove `approved_by`, `approved_on`, `approved_digest`,
   `approval_note`):
   - Responsibility: "the signed-in user's module list for module-dependent views; module registration,
     gated navigation and lazy module chunks deferred (PRB-048)".
   - Software units: one built unit, `U-FEM-MyModules` — `useMyModules`, with the existing CR-006 text
     (refresh within 60 s, invalidation, fail closed; SR-015 AC 3, AC 5). A "Deferred units" paragraph:
     `U-FEM-Registry` and `U-FEM-NavGate` are the target design of ADR-0005, not built; built with
     their first consumer, the frontend DICOM viewer module (PRB-048, TASK-100, TASK-101, TASK-102);
     TASK-100 then adds the module chunk to `LAZY_GROUPS` of the budget check (SR-026 AC 7, CR-007
     P-2).
   - Requirements implemented: SR-015 (AC 3 client gate, AC 5); SR-016 as decided at P-1 (option (a):
     AC 2 deferred to PRB-048).
   - Version-history line naming CR-007, PRB-091 and the removed approval.
2. **`docs/design/05-building-blocks.md`:** level-1 row SI-FE-MODREG responsibility as in ADD-021; the
   SI-FE-MODREG unit list as in ADD-021 (the PRB-091 "not built" sentence is replaced by the deferred
   paragraph); the "Module boundary note" says `SI-MOD-DICOM-FE` and the frontend registry are planned,
   not built (PRB-048).
3. **`docs/design/12-interfaces.md`:** 12.2: the `ModuleRegistry` row and the `FrontendModule` block
   moved under a "Planned (not built; PRB-048, TASK-100)" note; the `useMyModules()` row stays. 12.3
   rule 4: "Modules depend only on `PlatformServices` (backend) and, once built, `ModuleRegistry`
   (frontend)".
4. **`docs/specifications/diagram-building-blocks.puml`:** the SI-FE-MODREG and SI-MOD-DICOM-FE
   rectangles labelled "(planned)" where they show unbuilt parts; keep the house PlantUML style.
5. **PRB-091** (1.0 → 1.1): Resolution (what changed, why: D-1; how verified: the grep and review
   below); `resolved` once QA confirms. The Investigation's open point on SR-015 AC 3 and SR-016 AC 2
   cites CR-007 P-1 and P-2.
6. Not changed (out of scope, CR-007): ADR-0005, `docs/specifications/api-design.md`, TASK-100 to
   TASK-102, TS-005, TS-010, any SR.

## Verification

- `grep -rn "ModuleRegistry\|register(\|FrontendModule\|U-FEM-Registry\|U-FEM-NavGate" docs/design docs/design-outputs/architecture/ADD-021-*.md`
  → every hit is inside a "deferred" or "planned" statement; `grep -rn "ModuleRegistry\|FrontendModule" frontend/src`
  → no hit (nothing built is described as missing, nothing missing as built).
- Every unit ADD-021 names as built exists at the path given, and its verification is unchanged
  (TS-005 TC-005.5, TC-005.6).
- The PlantUML diagram compiles (`plantuml -checkonly` or the project's renderer).
- `traceability-check` on ADD-021, PRB-091, TASK-230, CR-007: 0 errors.

## Acceptance criteria

- [ ] ADD-021, arc42 05 and 12 name as built only units and interfaces that exist in `frontend/src`.
- [ ] The registry and the navigation gate are recorded as deferred to PRB-048 with TASK-100 and
  TASK-101, so the target design is not lost.
- [ ] ADD-021 is `in_review` 1.3 with its approval record removed and a version-history line.

## Definition of Done

- [ ] Records consistent; PRB-091 Resolution written; `traceability-check` no error for these records

## Version history

- 1.0 (2026-11-16) — Created at the CR-007 Plan stage (Software Architect role), D-1 (PRB-091 by documentation correction). `draft`.
