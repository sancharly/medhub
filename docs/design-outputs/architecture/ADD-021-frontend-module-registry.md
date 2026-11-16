---
id: ADD-021
type: architecture-doc
title: Frontend Module Registry (SI-FE-MODREG)
status: in_review
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-16"
links:
  - target: SOUP-028
    relation: relates_to
  - target: SR-015
    relation: implements
  - target: SR-016
    relation: implements
  - target: RISK-004
    relation: relates_to
  - target: SOUP-025
    relation: relates_to
  - target: SOUP-027
    relation: relates_to
tags:
  - software-item:SI-FE-MODREG
  - class:B
  - layer:frontend
---

# ADD-021 — Frontend Module Registry (SI-FE-MODREG)

## Responsibility

The signed-in user's module list for module-dependent views. Module registration, gated navigation and
lazy module chunks are deferred to the frontend DICOM viewer module (PRB-048).

## Software units (IEC 62304 §5.4.1)

- `U-FEM-MyModules` — `useMyModules` (`frontend/src/modules/useMyModules.ts`), the one reader of
  `GET /me/modules`; its consumer is `AttachmentItem` (`frontend/src/core/clinical/AttachmentItem.tsx`,
  the DICOM viewer link of ADD-020, shown only when `dicom-viewer` is in the list). **CR-006 (D-4;
  TASK-221):** one `useMyModules()` hook serves every module-dependent view: stale after 30 s, refetched every 50 s (the interval restarts when a response arrives, so the 60 s bound of SR-015 AC 5 keeps 10 s for the round trip and one retry), on window focus and on mount (next
  navigation), keeping the last known list when a refetch fails (fail closed: an unknown or failed list never shows the viewer link); admin group and module mutations
  (module toggle, member add and remove) invalidate it. A change reaches every affected user within 60 s or the next navigation (SR-015 AC 5);
  the server guard stays the authority (SR-015 AC 3; RISK-004). Verified by TS-005 TC-005.5 and TC-005.6.

**Deferred units.** `U-FEM-Registry` (module registry and lazy import, SR-016) and `U-FEM-NavGate`
(navigation entry shown only when the module is enabled, SR-015) are the target design of
[ADR-0005](../../design/adr/0005-plugin-module-mechanism.md) and are **not built**: there is no
`ModuleRegistry`, no `register(FrontendModule)` and no module navigation item in `frontend/src`
(PRB-091). They are built with their first consumer, the frontend DICOM viewer module (PRB-048;
TASK-100, TASK-101, TASK-102). TASK-100 then adds the module chunk to `LAZY_GROUPS` of the bundle
budget check (SR-026 AC 7; CR-007 D-3).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-015 (AC 3 client gate, AC 5); SR-016 AC 2 is deferred to PRB-048 (CR-007 D-2: the wording is unchanged and AC 2 stays unverified until the frontend DICOM viewer module is built).
Non-functional requirements constraining this item: —.

## Interfaces

Provided and consumed interfaces are specified in
[12-interfaces.md](../../design/12-interfaces.md); the runtime interactions this item takes part in
are in [06-runtime-views.md](../../design/06-runtime-views.md) and the sequence diagrams under
[`../../specifications/`](../../specifications/).

## Architecture narrative

This record is a summary and traceability anchor, not the narrative. The design itself is in the
arc42 sections — [05 building blocks](../../design/05-building-blocks.md) for the decomposition,
[04 solution strategy](../../design/04-solution-strategy.md),
[08 cross-cutting concepts](../../design/08-cross-cutting-concepts.md) and, for deployment,
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0001](../../design/adr/), [ADR-0005](../../design/adr/).

## Risk relevance

Participates in RISK-004 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect role): module-list refresh for every affected user (SR-015 AC 5) marked "CR-006 (planned)"; `relates_to` SOUP-028 (TanStack Query, refetch behaviour) added. Content change, so the 1.0 approval record is cleared and the record returns to review.
- 1.2 (2026-11-14) — TASK-221 implemented: "planned" removed, hook location and the member add and remove invalidation recorded. Content change, so the approval record is removed. `in_review`.
- 1.2 (2026-11-14) — TASK-221 round 2: refetch interval 50 s (was 60 s); the polling request is served without extending the session (ADD-006, SR-030 AC 1, AC 2). Still `in_review`.
- 1.3 (2026-11-16) — CR-007 TASK-230 (PRB-091, D-1): the design is corrected to the unit that exists, `U-FEM-MyModules` (`useMyModules`); `U-FEM-Registry` and `U-FEM-NavGate` recorded as deferred to PRB-048 (TASK-100, TASK-101). Content change, so the 1.2 approval record is removed. `in_review`.
