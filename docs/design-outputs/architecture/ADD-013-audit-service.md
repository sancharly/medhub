---
id: ADD-013
type: architecture-doc
title: Audit Service (SI-AUDIT)
status: approved
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approval_note: self-approved at the ship-feature plan gate (sancharly/medhub#27, CR-004)
links:
  - target: SR-023
    relation: implements
  - target: RISK-006
    relation: relates_to
  - target: SOUP-008
    relation: relates_to
  - target: SR-042
    relation: implements
  - target: SOUP-020
    relation: relates_to
tags:
  - software-item:SI-AUDIT
  - class:B
  - layer:backend
---

# ADD-013 — Audit Service (SI-AUDIT)

## Responsibility

Append-only audit log of security-relevant events

## Software units (IEC 62304 §5.4.1)

- `U-AUD-Writer` — append-only event writer (actor/action/target/outcome/ts), no plaintext secrets (SR-023). It writes failure and refusal events (outcome FAILURE, and `ACCOUNT_LOCKOUT`) on an independent transaction, so they survive a request that ends in an error; every other event joins the request transaction (ADR-0016).
- `U-AUD-Writer` (CR-004 change) —
  - records the originating client address of the request (SR-042) when the caller passes none,
    and no address outside a request (SR-023 AC 6);
  - takes typed fields only: `action` an `AuditAction`, `target_type` from a closed set,
    `target_id` one or two UUIDs or a UUID plus a registered module key; anything else is refused
    before storage, so no credential or secret can be stored under any field (SR-023 AC 9). The
    pattern scrub stays as a second line;
  - the runtime database role has `SELECT, INSERT` only on `audit_log`; `UPDATE`, `DELETE` and
    `TRUNCATE` fail with a permission error (SR-023 AC 8,
    [ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md)).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-023; CR-004 adds SR-042 (address rule).
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0011](../../design/adr/), [ADR-0016](../../design/adr/0016-failure-audit-events-on-own-transaction.md), [ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md), [ADR-0019](../../design/adr/0019-originating-client-address-trusted-proxy-rule.md).

## Risk relevance

Participates in RISK-006 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.2 (2026-10-31) — CR-004 Plan stage (Software Architect role): unit changes for the planned design added (marked "CR-004"), links added. Content change, so the approval record is cleared and the record returns to review. The implementing tasks confirm the unit text when they land.
