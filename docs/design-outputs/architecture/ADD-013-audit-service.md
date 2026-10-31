---
id: ADD-013
type: architecture-doc
title: Audit Service (SI-AUDIT)
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approved_digest: 08008cc6b2e14b8f691cf6c04199de2995a4d000b96b09669a5bb74a227bfd85
approval_note: self-approved
links:
  - target: SR-023
    relation: implements
  - target: RISK-006
    relation: relates_to
  - target: SOUP-008
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

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-023.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0011](../../design/adr/), [ADR-0016](../../design/adr/0016-failure-audit-events-on-own-transaction.md).

## Risk relevance

Participates in RISK-006 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
