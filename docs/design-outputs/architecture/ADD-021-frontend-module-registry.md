---
id: ADD-021
type: architecture-doc
title: Frontend Module Registry (SI-FE-MODREG)
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
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

Dynamic module registration, gated nav, lazy chunk loading

## Software units (IEC 62304 §5.4.1)

- `U-FEM-Registry` — module registry + lazy import (SR-016).
- `U-FEM-NavGate` — render nav only if enabled per `GET /me/modules` (SR-015). **CR-006 (D-4;
  TASK-221, `frontend/src/modules/useMyModules.ts`):** one `useMyModules()` hook serves every module-dependent view (the attachment viewer link
  of ADD-020 included): stale after 30 s, refetched every 50 s (the interval restarts when a response arrives, so the 60 s bound of SR-015 AC 5 keeps 10 s for the round trip and one retry), on window focus and on mount (next
  navigation), keeping the last known list when a refetch fails; admin group and module mutations
  (module toggle, member add and remove) invalidate it. A change reaches every affected user within 60 s or the next navigation (SR-015 AC 5);
  the server guard stays the authority (SR-015 AC 3; RISK-004).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-015, SR-016.
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
