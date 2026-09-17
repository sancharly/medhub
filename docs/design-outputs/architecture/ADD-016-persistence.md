---
id: "ADD-016"
type: architecture-doc
title: "Persistence (SI-PERSIST)"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "SR-003"
    relation: implements
  - target: "SR-004"
    relation: implements
  - target: "SR-021"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "SR-031"
    relation: implements
  - target: "RISK-002"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "RISK-011"
    relation: relates_to
tags: ["software-item:SI-PERSIST", "class:B", "layer:backend"]
---

# ADD-016 — Persistence (SI-PERSIST)

## Responsibility

SQLAlchemy models, repositories, Alembic migrations, encryption-at-rest config

## Software units (IEC 62304 §5.4.1)

- `U-PER-Models` — SQLAlchemy ORM models (FHIR-aligned, SR-021).
- `U-PER-Repos` — repositories with parameterized queries (SR-031.1).
- `U-PER-Migrations` — Alembic migrations (NFR-006).
- `U-PER-Crypto` — at-rest encryption config / pgcrypto where needed (SR-022).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-003, SR-004, SR-021, SR-022, SR-031.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0004](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0007](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0010](../../design/adr/), [ADR-0011](../../design/adr/).

## Risk relevance

Participates in RISK-002, RISK-007, RISK-011 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
