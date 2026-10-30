---
id: ADD-012
type: architecture-doc
title: Attachment Service (SI-ATTACH)
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-30"
links:
  - target: SR-013
    relation: implements
  - target: SR-022
    relation: implements
  - target: SR-026
    relation: implements
  - target: RISK-002
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: RISK-011
    relation: relates_to
  - target: SOUP-015
    relation: relates_to
  - target: SOUP-017
    relation: relates_to
  - target: SOUP-019
    relation: relates_to
tags:
  - software-item:SI-ATTACH
  - class:B
  - layer:backend
---

# ADD-012 — Attachment Service (SI-ATTACH)

## Responsibility

Upload/fetch attachment binaries via object storage, authorized

## Software units (IEC 62304 §5.4.1)

- `U-ATT-Upload` — validate, store object (SSE), bind to entry/patient transactionally (SR-013).
- `U-ATT-Fetch` — authorized stream / scoped pre-signed URL (SR-005, SR-013.3).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-013, SR-022, SR-026.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0008](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0010](../../design/adr/), [ADR-0011](../../design/adr/).

## Risk relevance

Participates in RISK-002, RISK-007, RISK-011 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
