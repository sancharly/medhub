---
id: ADD-009
type: architecture-doc
title: Groups & Module Enablement (SI-GROUPS)
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-15"
links:
  - target: SR-014
    relation: implements
  - target: SR-015
    relation: implements
  - target: SR-026
    relation: implements
  - target: RISK-004
    relation: relates_to
tags:
  - software-item:SI-GROUPS
  - class:B
  - layer:backend
---

# ADD-009 — Groups & Module Enablement (SI-GROUPS)

## Responsibility

Group CRUD, auto/manual membership, per-group module enablement

## Software units (IEC 62304 §5.4.1)

- `U-GRP-Crud` — group create/list (SR-014).
- `U-GRP-Membership` — auto-by-type + manual add/remove (SR-014.2/3). **CR-006 (TASK-220, implemented):**
  `groups_of` reads a user's groups with one joined query, a constant number of queries for any number
  of memberships (SR-026 AC 6); its result set is fixed by a characterisation test written before the
  rewrite (RISK-004).
- `U-GRP-ModuleEnable` — enable/disable module per group (SR-015).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-014, SR-015; SR-026 (AC 6, added by CR-006).
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0005](../../design/adr/), [ADR-0006](../../design/adr/).

## Risk relevance

Participates in RISK-004 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect role): constant-query `groups_of` (SR-026 AC 6) marked "CR-006 (planned)"; `implements` SR-026 added. Content change, so the 1.0 approval record is cleared and the record returns to review.
- 1.2 (2026-11-15) — TASK-225 (QA round 1, MEDIUM 3): the "CR-006 (planned; TASK-220)" marker of `U-GRP-Membership` is removed; `groups_of` is implemented as described (one joined query, `GroupRepository.groups_for_account`). Wording only. Content change on an approved record, so the 1.1 approval record is cleared and the record returns to review.
