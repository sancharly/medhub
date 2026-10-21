---
id: ADD-011
type: architecture-doc
title: Clinical Records (SI-CLINICAL)
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 511518ee6f119ef6615f6efdb1e4e9e566635dbea32a5f55424ef77f44d4d48c
approval_note: self-approved
links:
  - target: SR-006
    relation: implements
  - target: SR-007
    relation: implements
  - target: SR-012
    relation: implements
  - target: RISK-002
    relation: relates_to
  - target: SOUP-016
    relation: relates_to
tags:
  - software-item:SI-CLINICAL
  - class:B
  - layer:backend
---

# ADD-011 — Clinical Records (SI-CLINICAL)

## Responsibility

Clinical-entry CRUD with required fields & attribution

## Software units (IEC 62304 §5.4.1)

- `U-CLIN-EntryCrud` — create entry with required fields, author from session, list for patient (SR-012).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-006, SR-007, SR-012.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0004](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0007](../../design/adr/).

## Risk relevance

Participates in RISK-002 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
