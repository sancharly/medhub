---
id: "ADD-023"
type: architecture-doc
title: "Frontend API Client (SI-FE-APICLIENT)"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "SR-031"
    relation: implements
  - target: "RISK-005"
    relation: relates_to
  - target: "SOUP-028"
    relation: relates_to
  - target: "SOUP-033"
    relation: relates_to
tags: ["software-item:SI-FE-APICLIENT", "class:B", "layer:frontend"]
---

# ADD-023 — Frontend API Client (SI-FE-APICLIENT)

## Responsibility

Typed client generated from OpenAPI; session/CSRF handling

## Software units (IEC 62304 §5.4.1)

- `U-FEAPI-Client` — generated typed client; cookie/CSRF handling (SR-031.3).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-031.
Non-functional requirements constraining this item: NFR-006.

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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: —.

## Risk relevance

Participates in RISK-005 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
