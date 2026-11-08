---
id: ADD-018
type: architecture-doc
title: Frontend App Shell (SI-FE-SHELL)
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-08"
links:
  - target: SR-001
    relation: implements
  - target: SR-019
    relation: implements
  - target: SR-020
    relation: implements
  - target: SR-027
    relation: implements
  - target: RISK-002
    relation: relates_to
  - target: SOUP-024
    relation: relates_to
  - target: SOUP-025
    relation: relates_to
  - target: SOUP-026
    relation: relates_to
  - target: SOUP-027
    relation: relates_to
  - target: SOUP-029
    relation: relates_to
  - target: SOUP-030
    relation: relates_to
  - target: SOUP-031
    relation: relates_to
  - target: SOUP-032
    relation: relates_to
  - target: SOUP-034
    relation: relates_to
  - target: SOUP-035
    relation: relates_to
  - target: SR-005
    relation: implements
  - target: SR-009
    relation: implements
  - target: RISK-001
    relation: relates_to
tags:
  - software-item:SI-FE-SHELL
  - class:B
  - layer:frontend
---

# ADD-018 — Frontend App Shell (SI-FE-SHELL)

## Responsibility

Layout, routing, responsive frame, navigation, module mounting, error/confirmation UX

## Software units (IEC 62304 §5.4.1)

- `U-FE-Layout` — responsive layout/breakpoints (SR-020).
- `U-FE-Nav` — consistent navigation/terminology (SR-027.1).
- `U-FE-Confirm` — confirmation dialogs for destructive actions (SR-027.2).
- `U-FE-Error` — clear, actionable error surfaces (SR-027.3).
- `U-FE-RouteGuard` — `RequireRole` route wrapper: a route whose role list does not contain the
  signed-in user's role is not mounted and redirects to `/profile`. The role table is
  `frontend/src/core/nav/routeRoles.ts`; `navConfig.ts` derives its role lists from it, so the two
  cannot diverge. Every `<Route>` in `App.tsx` has an entry. Defence in depth only: the server stays the control
  (SR-005, SR-009, SR-031 AC 5; PRB-014).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-001, SR-019, SR-020, SR-027; CR-004 adds SR-005, SR-009 (defence in depth, route guard).
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0003](../../design/adr/), [ADR-0010](../../design/adr/), [ADR-0011](../../design/adr/).

## Risk relevance

Participates in RISK-002 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): unit changes for the planned design added (marked "CR-004"), links added. Content change, so the approval record is cleared and the record returns to review. The implementing tasks confirm the unit text when they land.
- 1.2 (2026-11-08) — TASK-201 (CR-004), from the TASK-142 QA review: `U-FE-RouteGuard` names `routeRoles.ts` as the role table and `navConfig.ts` as its consumer (it named `navConfig.ts` as the table). Content change, so the 1.1 approval record is cleared and the record returns to review.
