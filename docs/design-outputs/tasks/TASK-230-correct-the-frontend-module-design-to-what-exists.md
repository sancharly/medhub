---
id: "TASK-230"
type: task
title: "Correct the frontend module design records to the units that exist"
status: approved
version: "1.1"
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

- [x] ADD-021, arc42 05 and 12 name as built only units and interfaces that exist in `frontend/src`.
- [x] The registry and the navigation gate are recorded as deferred to PRB-048 with TASK-100 and
  TASK-101, so the target design is not lost.
- [x] ADD-021 is `in_review` 1.3 with its approval record removed and a version-history line.

## Definition of Done

- [x] Records consistent; PRB-091 Resolution written; `traceability-check` no error for these records

## Implementation record

- ADD-021 1.3 `in_review` (approval record removed, version-history line); P-1 answered (a), D-2: SR-016 AC 2 deferred to PRB-048, no SR change (D-3).
- `docs/design/05-building-blocks.md`, `docs/design/12-interfaces.md`, `docs/specifications/diagram-building-blocks.puml` corrected; PRB-091 1.1 Investigation and Resolution written (status left `open` for QA).
- Checks: `grep ModuleRegistry|FrontendModule frontend/src` no hit; same grep on docs/design and ADD-021 hits only deferred/planned text and ADR-0005 (target design, out of scope); `plantuml` renders the diagram; built unit paths exist (`useMyModules.ts`, `AttachmentItem.tsx`); TS-005 TC-005.5 and TC-005.6 unchanged. `traceability-check` not run by the document writer: left to QA.

## QA review round 1 (qa-engineer, 2026-11-16) — APPROVED

0 CRITICAL, 0 HIGH, 1 MEDIUM, 3 LOW (not blocking).

- **MEDIUM-1** — `docs/design/06-runtime-views.md:37` and
  `docs/specifications/diagram-seq-dicom-view.puml:7,17-18` still describe the unbuilt navigation gate
  and registry as the runtime ("The shell shows the viewer nav item only if the module is enabled ...
  (SR-015.3, SR-016.2); the module loads as a lazy chunk"; participant "SPA Shell + Module Registry"),
  with no "planned" mark, and ADD-021 1.3 sends the reader to section 06 for its runtime
  interactions. The whole 6.4 scenario is the unbuilt frontend DICOM viewer (PRB-048), and CR-007
  limits the correction to ADD-021, 05 and 12, so this is outside the approved scope and does not
  block. Fix (next change of section 06, or a follow-up under PRB-048): one line under 6.4 and a
  note in the sequence diagram, "Planned (PRB-048, PRB-091): the frontend module, its navigation
  item and lazy chunk are not built; today the only client entry point is the viewer link of
  `AttachmentItem`". `docs/design/04-solution-strategy.md:11,13` and
  `docs/design/08-cross-cutting-concepts.md:53` state the ADR-0005 strategy and concept, not built
  units: acceptable as target design. Recorded in PRB-091's QA confirmation.
- **LOW-1** — `docs/specifications/diagram-building-blocks.puml:12,40-43`: `FEModReg` is drawn only
  with planned (dashed) edges; the built relations are missing (`AttachmentItem` in SI-FE-CORE uses
  `useMyModules`, which calls `apiClient.listMyModules()`). Fix: add `FECore --> FEModReg : useMyModules`
  and `FEModReg --> FEApi : GET /me/modules`.
- **LOW-2** — The diagram labels SI-FE-MODREG "Module List Reader" while ADD-021, 05 and 12 keep the
  item name "Frontend Module Registry". Fix: use one name (for example keep "Module Registry" with
  the "(registry and nav gate planned)" line) the next time the diagram or ADD-021 is changed.
- **LOW-3** — CR-007 Verification and the TASK verification grep `register(` over `frontend/src`
  match `unregister()` in `frontend/src/api/queryClient.test.tsx:53,61` (a false positive, not a
  registry). Fix: grep `\bregister(` or `ModuleRegistry\|FrontendModule` only, as PRB-091 does.
- Observations (not findings): ADD-021 keeps `implements SR-016` while its SR-016 part is deferred;
  this keeps SR-016 covered by an ADD (class B) and the Requirements section states the deferral.
  ADR-0005 and `api-design.md` left as target design: matches CR-007 Out of scope. The house PlantUML
  rules (bare `@startuml`, no colour on the system's own elements) are not met by this file
  (`@startuml building-blocks`, `#lightblue` throughout); that is the project's established diagram
  convention and pre-existing, not changed here.

Verification (working tree): `grep -rn "ModuleRegistry\|FrontendModule" frontend/src` no hit;
`register(` hits only `unregister()` (LOW-3). `grep` of `ModuleRegistry|register(|FrontendModule|U-FEM-Registry|U-FEM-NavGate`
over `docs/design` and ADD-021: every hit is a deferred/planned statement, the backend
`register(RouterRegistry, ...)` (12:36) or ADR-0005. `useMyModules.ts` and `AttachmentItem.tsx` exist;
`useMyModules` is the only reader of `listMyModules`, its only consumer is `AttachmentItem` (`:18-33`,
link gated on `dicom-viewer`), and `GroupModules.tsx:34`, `GroupMembers.tsx:29,37` invalidate
`queryKeys.myModules`, as ADD-021 states; "fail closed" matches TS-005 line 51 and TC-005.6. TS-005,
ADR-0005, `api-design.md`, TASK-100 to TASK-102 and every SR unchanged (`git status`).
`plantuml -checkonly docs/specifications/diagram-building-blocks.puml` exit 0; no rendered SVG/PNG
tracked or left in the tree. ADD-021: 1.3 `in_review`, the four approval fields removed,
version-history line present. `traceability-check` on CR-007, TASK-230, ADD-021, PRB-091, SR-015,
SR-016, PRB-048, TASK-100, TASK-101: 474 records, 9 scoped, 0 errors, 0 warnings before the status
change; after it, 0 errors and 3 expected W5 warnings (approved TASK-230 → ADD-021 `in_review`, awaiting
the human; → TASK-100, TASK-101 `draft`, the deferred build).

## Version history

- 1.0 (2026-11-16) — Created at the CR-007 Plan stage (Software Architect role), D-1 (PRB-091 by documentation correction). `draft`.
- 1.1 (2026-11-16) — Implemented; `in_review`.
- 1.1 (2026-11-16) — QA review round 1: APPROVED, `in_review` to `approved`; acceptance criteria and Definition of Done already ticked. PRB-091 1.2 `resolved`; ADD-021 1.3 stays `in_review` for the human.
