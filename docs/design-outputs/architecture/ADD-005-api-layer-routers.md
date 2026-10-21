---
id: ADD-005
type: architecture-doc
title: API Layer / Routers (SI-API)
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 03e60d9718baa3c4e987c9defecd7f38a65c3745b814ea8954cf78a050d95f2d
approval_note: self-approved
links:
  - target: SR-001
    relation: implements
  - target: SR-008
    relation: implements
  - target: SR-026
    relation: implements
  - target: SR-031
    relation: implements
  - target: RISK-001
    relation: relates_to
  - target: RISK-005
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: SOUP-001
    relation: relates_to
  - target: SOUP-002
    relation: relates_to
  - target: SOUP-003
    relation: relates_to
  - target: SOUP-004
    relation: relates_to
  - target: SOUP-005
    relation: relates_to
  - target: SOUP-006
    relation: relates_to
  - target: SOUP-007
    relation: relates_to
  - target: SOUP-017
    relation: relates_to
  - target: SOUP-024
    relation: relates_to
tags:
  - software-item:SI-API
  - class:B
  - layer:backend
---

# ADD-005 — API Layer / Routers (SI-API)

## Responsibility

HTTP endpoints, request/response DTOs, validation, error formatting, AuthZ dependency wiring

## Software units (IEC 62304 §5.4.1)

- `U-API-Routers` — endpoint definitions per resource (auth, accounts, groups, appointments, clinical, attachments, consents, modules).
- `U-API-DTO` — Pydantic request/response schemas (camelCase, FHIR-traceable).
- `U-API-ErrorHandler` — RFC 7807 problem+json mapping (SR-027.3, api-design.md).
- `U-API-Deps` — DI providers: current session, current user, `authorize(...)` guard.

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-001, SR-008, SR-026, SR-031.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0003](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0008](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0010](../../design/adr/), [ADR-0011](../../design/adr/).

## Risk relevance

Participates in RISK-001, RISK-005, RISK-007 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
