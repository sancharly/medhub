---
id: "ADD-021"
type: architecture-doc
title: "Frontend Module Registry (SI-FE-MODREG)"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "SR-015"
    relation: implements
  - target: "SR-016"
    relation: implements
  - target: "RISK-004"
    relation: relates_to
  - target: "SOUP-025"
    relation: relates_to
  - target: "SOUP-027"
    relation: relates_to
tags: ["software-item:SI-FE-MODREG", "class:B", "layer:frontend"]
---

# ADD-021 — Frontend Module Registry (SI-FE-MODREG)

## Responsibility

Dynamic module registration, gated nav, lazy chunk loading

## Software units (IEC 62304 §5.4.1)

- `U-FEM-Registry` — module registry + lazy import (SR-016).
- `U-FEM-NavGate` — render nav only if enabled per `GET /me/modules` (SR-015).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-015, SR-016.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0001](../../design/adr/), [ADR-0005](../../design/adr/).

## Risk relevance

Participates in RISK-004 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
