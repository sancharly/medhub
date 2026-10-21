---
id: "ADD-008"
type: architecture-doc
title: "Identity & Account Lifecycle (SI-IDENTITY)"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "SR-003"
    relation: implements
  - target: "SR-004"
    relation: implements
  - target: "SR-024"
    relation: implements
  - target: "SR-032"
    relation: implements
  - target: "SR-033"
    relation: implements
  - target: "SR-034"
    relation: implements
  - target: "RISK-002"
    relation: relates_to
  - target: "RISK-008"
    relation: relates_to
  - target: "SOUP-014"
    relation: relates_to
tags: ["software-item:SI-IDENTITY", "class:B", "layer:backend"]
---

# ADD-008 — Identity & Account Lifecycle (SI-IDENTITY)

## Responsibility

Account CRUD, role-constrained creation, activation, deactivate/reactivate/delete, erasure

## Software units (IEC 62304 §5.4.1)

- `U-ID-AccountCrud` — create (role-constrained, min fields, unique email), read (SR-003, SR-004, SR-032).
- `U-ID-Activation` — single-use 72h token, password-set, activate, resend (SR-033).
- `U-ID-Lifecycle` — deactivate/reactivate (session kill ≤30s), delete+confirm, email release (SR-034).
- `U-ID-Erasure` — deletion as anonymization into a retained anonymized dataset; generates the user-held anonymization code, stores only its salted KDF hash, sets the 5-year retention deadline, and authorizes code-based retrieval (SR-024, ADR-0013).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-003, SR-004, SR-024, SR-032, SR-033, SR-034.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0002](../../design/adr/), [ADR-0004](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0011](../../design/adr/), [ADR-0012](../../design/adr/), [ADR-0013](../../design/adr/).

## Risk relevance

Participates in RISK-002, RISK-008 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
