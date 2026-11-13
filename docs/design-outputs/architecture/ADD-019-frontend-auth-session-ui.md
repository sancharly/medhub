---
id: ADD-019
type: architecture-doc
title: Frontend Auth/Session UI (SI-FE-AUTH)
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-13"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-13"
approved_digest: f02a5c57a63e519848957b5c1f3eac67ef64c665faa4f5e01f2dca0484eea471
approval_note: self-approved
links:
  - target: SR-026
    relation: implements
  - target: SR-002
    relation: implements
  - target: SR-025
    relation: implements
  - target: SR-030
    relation: implements
  - target: SR-033
    relation: implements
  - target: RISK-005
    relation: relates_to
  - target: SOUP-025
    relation: relates_to
  - target: SOUP-027
    relation: relates_to
  - target: SOUP-028
    relation: relates_to
tags:
  - software-item:SI-FE-AUTH
  - class:B
  - layer:frontend
---

# ADD-019 — Frontend Auth/Session UI (SI-FE-AUTH)

## Responsibility

Login, activation, password, inactivity warning/extend

## Software units (IEC 62304 §5.4.1)

- `U-FEA-LoginForm`, `U-FEA-Activation`, `U-FEA-PasswordForm`, `U-FEA-IdleWarning` (SR-002, SR-025, SR-030.4, SR-033).
- **CR-006 (planned).** `U-FEA-Me` (TASK-144): `useMe()` is the only reader of the `me` query
  (`retry: false`); a 401 clears the cache and redirects once. `U-FEA-IdleWarning` (TASK-144): the
  deadline is the receipt time of the `me` or extend response plus the session seconds the server
  reports (`sessionExpiresInSeconds`, `expiresInSeconds`; relative, so the client clock does not move
  it); no client timeout constant (SR-030 AC 8, AC 4). `U-FEA-IdleTimer` (TASK-222): activity re-arms
  the timers at most once per second, leading and trailing edge (SR-026 AC 8). Server enforcement of
  SR-030 AC 1 to AC 3 is unchanged (RISK-005).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-002, SR-025, SR-030, SR-033; SR-026 (AC 8, added by CR-006).
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0011](../../design/adr/), [ADR-0012](../../design/adr/).

## Risk relevance

Participates in RISK-005 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect role): one `me` query, client deadline from the server-reported session seconds, and throttled activity tracking marked "CR-006 (planned)"; `implements` SR-026 added. Content change, so the 1.0 approval record is cleared and the record returns to review.
