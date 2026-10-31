---
id: ADD-005
type: architecture-doc
title: API Layer / Routers (SI-API)
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approved_digest: 9d344bebe46cd59d8b1b53c8937ae7627d32186a65d17e8ca5c75cad67c7a768
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
  - target: SR-042
    relation: implements
  - target: SR-043
    relation: implements
  - target: SR-023
    relation: implements
  - target: RISK-006
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
- `U-API-ClientAddress` (new, CR-004) — pure ASGI middleware, mounted first: applies the
  trusted-proxy rule of SR-042 AC 1 to AC 3 with the `TRUSTED_PROXIES` setting and publishes the
  originating client address in `request.state` and a `ContextVar` for the audit writer and the
  rate limit. Gunicorn's own forwarded-header handling is off ([ADR-0019](../../design/adr/0019-originating-client-address-trusted-proxy-rule.md)).
- `U-API-RateLimit` (new, CR-004) — anonymized-data retrieval limit keyed on the originating
  client address, atomic increment, fixed 3600 s window from the first counted attempt, refused
  before the code is evaluated (SR-042 AC 4, AC 5; ADR-0013 values).
- `U-API-Security` (CR-004 change) — CSRF exemptions are an exact set of paths, the activation
  route matched as one path segment; a route-inventory test keeps the set reviewed (SR-031 AC 3).
- The API process installs the shared log redaction filter (SR-043 AC 2; see ADD-017).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-001, SR-008, SR-026, SR-031; CR-004 adds SR-042, SR-043, SR-023 (AC 6, through `U-API-ClientAddress`).
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0003](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0008](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0010](../../design/adr/), [ADR-0011](../../design/adr/), [ADR-0019](../../design/adr/0019-originating-client-address-trusted-proxy-rule.md).

## Risk relevance

Participates in RISK-001, RISK-005, RISK-007 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): unit changes for the planned design added (marked "CR-004"), links added. Content change, so the approval record is cleared and the record returns to review. The implementing tasks confirm the unit text when they land.
