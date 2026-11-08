---
id: ADD-013
type: architecture-doc
title: Audit Service (SI-AUDIT)
status: in_review
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-08"
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

- `U-AUD-Writer` — append-only event writer (actor/action/target/outcome/ts/source address), no
  plaintext secrets (SR-023). It writes failure and refusal events (outcome FAILURE, and
  `ACCOUNT_LOCKOUT`) on an independent transaction, so they survive a request that ends in an
  error; every other event joins the request transaction (ADR-0016).
  - It records the originating client address of the request (SR-042) when the caller passes none,
    and no address outside a request (SR-023 AC 6). The address is derived by the
    [ADR-0019](../../design/adr/0019-originating-client-address-trusted-proxy-rule.md) rule, not
    validated by the writer.
  - It takes typed fields only (SR-023 AC 9), so no credential or secret can be stored under any
    field; anything else raises `AuditFieldError` before any row is written (the failed-login
    counter is incremented before the audit write, so a refusal cannot skip the count):
    - `action` is a member of `AuditAction`.
    - `target_type` is one of a closed set, and `target_id` has the shape of its `target_type`
      (the exact shapes are listed once, in
      [08 cross-cutting concepts](../../design/08-cross-cutting-concepts.md) section 8.4).
    - A module key has the shape `^[a-z][a-z0-9_-]{0,63}$` and nothing more: shape only, no
      registry lookup. The pattern is defined once in `backend/app/core/module_key.py` and shared
      with module discovery, which rejects a manifest that does not match.
    - The pattern scrub of credential-like text stays as a second line.
  - The runtime database role has `SELECT, INSERT` only on `audit_log`; `UPDATE`, `DELETE` and
    `TRUNCATE` fail with a permission error (SR-023 AC 8,
    [ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md)).
  - Module discovery logs a rejected manifest at WARNING and skips it; the registry sync then
    deletes the row of every module no longer discovered, and with a group enablement row that
    delete hits a foreign key and the backend does not start (PRB-075; arc42
    section 11 holds the open decision).

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
- 1.3 (2026-11-08) — TASK-201 (CR-004): unit text replaced with the unit as built. The typed-field wording names the shared module-key pattern and the refusal and counter order, and points to arc42 8.4 for the exact `target_id` shapes (TASK-192); the discovery defect recorded (round 2: corrected to the verified start-up failure). Arc42 sections 05 and 08 hold the narrative. Content change, so the 1.2 approval record is cleared and the record returns to review.
- 1.4 (2026-11-08) — TASK-201 round 2: `target_id` shapes kept only in arc42 8.4; the discovery note corrected (the backend does not start when the registry delete hits a foreign key). `in_review`.
