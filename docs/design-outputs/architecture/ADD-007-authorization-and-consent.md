---
id: ADD-007
type: architecture-doc
title: Authorization & Consent (SI-AUTHZ)
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approval_note: self-approved at the ship-feature plan gate (sancharly/medhub#27, CR-004)
links:
  - target: SR-004
    relation: implements
  - target: SR-005
    relation: implements
  - target: SR-006
    relation: implements
  - target: SR-007
    relation: implements
  - target: SR-008
    relation: implements
  - target: SR-009
    relation: implements
  - target: SR-011
    relation: implements
  - target: SR-015
    relation: implements
  - target: SR-036
    relation: implements
  - target: RISK-001
    relation: relates_to
  - target: RISK-004
    relation: relates_to
  - target: SR-023
    relation: implements
  - target: SR-032
    relation: implements
  - target: SR-034
    relation: implements
  - target: RISK-006
    relation: relates_to
tags:
  - software-item:SI-AUTHZ
  - class:B
  - layer:backend
---

# ADD-007 — Authorization & Consent (SI-AUTHZ)

## Responsibility

Deny-by-default decisions; per-source consent grants; module access guard

## Software units (IEC 62304 §5.4.1)

- `U-AUTHZ-Policy` — deny-by-default decision engine (user type + relationship + consent + module) (SR-005).
- `U-AUTHZ-Consent` — `ConsentGrant` create/revoke, per-source union evaluation (SR-008, SR-036).
- `U-AUTHZ-AdminProjection` — non-clinical field projection for admin personnel (SR-009).
- `U-AUTHZ-ModuleGuard` — module-enabled-for-group check (SR-015).
- `U-AUTHZ-ApptVisibility` — appointment visibility scoping (SR-011).
- `U-AUTHZ-Policy` (CR-004 change) — **the only place an access decision is taken**
  ([ADR-0006](../../design/adr/0006-authz-consent-model.md)). It now also decides, and audits with
  actor, action, target, outcome and source address (SR-023 AC 7): appointment list scope and
  single-appointment visibility (formerly in `AppointmentService` and `U-AUTHZ-ApptVisibility`,
  PRB-026), module access (with `U-AUTHZ-ModuleGuard`'s result as an input), and the account
  lifecycle, activation, unlock, consent and roster rules that identity services and routers
  compared themselves (PRB-027; SR-032 AC 1, AC 4, AC 5; SR-034 AC 1). A refusal that the
  contract answers with 404 (SR-011 AC 4) is still audited as `AUTHZ_DENIED`.
- `U-AUTHZ-ApptVisibility` and `U-AUTHZ-ModuleGuard` (CR-004 change) — inputs to
  `U-AUTHZ-Policy`, no longer called by services or dependencies to decide on their own.
- A static test fails when a `user_type` comparison that decides access appears outside
  `backend/app/authz/` (allow-list of the non-decision comparisons in PRB-027's Investigation).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-004, SR-005, SR-006, SR-007, SR-008, SR-009, SR-011, SR-015, SR-036; CR-004 adds SR-023 (AC 7), SR-032, SR-034.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0005](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0011](../../design/adr/), [ADR-0006](../../design/adr/0006-authz-consent-model.md).

## Risk relevance

Participates in RISK-001, RISK-004 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): unit changes for the planned design added (marked "CR-004"), links added. Content change, so the approval record is cleared and the record returns to review. The implementing tasks confirm the unit text when they land.
