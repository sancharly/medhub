---
id: "ADD-017"
type: architecture-doc
title: "Async Worker (SI-WORKER)"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "SR-024"
    relation: implements
  - target: "SR-033"
    relation: implements
  - target: "SR-034"
    relation: implements
  - target: "SR-035"
    relation: implements
  - target: "RISK-008"
    relation: relates_to
  - target: "RISK-009"
    relation: relates_to
tags: ["software-item:SI-WORKER", "class:B", "layer:backend"]
---

# ADD-017 — Async Worker (SI-WORKER)

## Responsibility

Celery tasks: send activation & appointment emails, session-revocation propagation

## Software units (IEC 62304 §5.4.1)

- `U-WK-Email` — render & send activation/appointment emails via SMTP (SR-033, SR-035).
- `U-WK-SessionRevoke` — propagate deactivation session-kill within 30s (SR-034.2).
- `U-WK-RetentionErase` — scheduled job that permanently erases anonymized datasets past their 5-year retention deadline (SR-024.4, ADR-0013).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-024, SR-033, SR-034, SR-035.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0002](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0011](../../design/adr/), [ADR-0012](../../design/adr/), [ADR-0013](../../design/adr/).

## Risk relevance

Participates in RISK-008, RISK-009 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
