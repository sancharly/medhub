---
id: ADD-010
type: architecture-doc
title: Appointments & Notifications (SI-APPT)
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 9f8da8dc7f3ff770a1963d0fb35eed4d6b3049af6da2ff0b76b7348dd7a1a365
approval_note: self-approved
links:
  - target: SR-010
    relation: implements
  - target: SR-011
    relation: implements
  - target: SR-035
    relation: implements
  - target: SR-036
    relation: implements
  - target: RISK-009
    relation: relates_to
  - target: RISK-004
    relation: relates_to
  - target: SOUP-014
    relation: relates_to
tags:
  - software-item:SI-APPT
  - class:B
  - layer:backend
---

# ADD-010 — Appointments & Notifications (SI-APPT)

## Responsibility

Appointment CRUD, state machine, confirmation, notification dispatch

## Software units (IEC 62304 §5.4.1)

- `U-APPT-Crud` — create (validate refs/datetime), list scoped (SR-010, SR-011).
- `U-APPT-State` — PENDING/CONFIRMED/DECLINED transitions, patient-only confirm/decline (SR-035).
- `U-APPT-Notify` — enqueue in-app + email notification via the `Notification` abstraction (best-effort send, `status` field + post-send hook as the extension point for future delivery/read tracking) (SR-035.2/3, section 8.12).
- `U-APPT-ConsentLink` — on confirm create / on decline revoke `APPOINTMENT:{id}` grant (SR-036).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-010, SR-011, SR-035, SR-036.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0006](../../design/adr/).

## Risk relevance

Participates in RISK-009, RISK-004 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
