---
id: "ADD-019"
type: architecture-doc
title: "Frontend Auth/Session UI (SI-FE-AUTH)"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "SR-002"
    relation: implements
  - target: "SR-025"
    relation: implements
  - target: "SR-030"
    relation: implements
  - target: "SR-033"
    relation: implements
  - target: "RISK-005"
    relation: relates_to
  - target: "SOUP-025"
    relation: relates_to
  - target: "SOUP-027"
    relation: relates_to
  - target: "SOUP-028"
    relation: relates_to
tags: ["software-item:SI-FE-AUTH", "class:B", "layer:frontend"]
---

# ADD-019 — Frontend Auth/Session UI (SI-FE-AUTH)

## Responsibility

Login, activation, password, inactivity warning/extend

## Software units (IEC 62304 §5.4.1)

- `U-FEA-LoginForm`, `U-FEA-Activation`, `U-FEA-PasswordForm`, `U-FEA-IdleWarning` (SR-002, SR-025, SR-030.4, SR-033).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-002, SR-025, SR-030, SR-033.
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
