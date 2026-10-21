---
id: ADD-020
type: architecture-doc
title: Frontend Core Views (SI-FE-CORE)
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: fcdca7c7a01b9aa510d16a15c6748876c486bd0271b42eb42c634b14311cad02
approval_note: self-approved
links:
  - target: SR-003
    relation: implements
  - target: SR-004
    relation: implements
  - target: SR-005
    relation: implements
  - target: SR-006
    relation: implements
  - target: SR-007
    relation: implements
  - target: SR-008
    relation: implements
  - target: SR-009
    relation: implements
  - target: SR-010
    relation: implements
  - target: SR-011
    relation: implements
  - target: SR-012
    relation: implements
  - target: SR-013
    relation: implements
  - target: SR-014
    relation: implements
  - target: SR-015
    relation: implements
  - target: SR-016
    relation: implements
  - target: SR-035
    relation: implements
  - target: SR-036
    relation: implements
  - target: RISK-002
    relation: relates_to
  - target: RISK-001
    relation: relates_to
  - target: SOUP-025
    relation: relates_to
  - target: SOUP-028
    relation: relates_to
  - target: SOUP-029
    relation: relates_to
tags:
  - software-item:SI-FE-CORE
  - class:B
  - layer:frontend
---

# ADD-020 — Frontend Core Views (SI-FE-CORE)

## Responsibility

Profile, patients, clinical entries, appointments, consent, admin (accounts/groups/modules)

## Software units (IEC 62304 §5.4.1)

- `U-FEC-Profile`, `U-FEC-Patients`, `U-FEC-ClinicalEntries`, `U-FEC-Appointments`, `U-FEC-Consent`, `U-FEC-AdminAccounts`, `U-FEC-AdminGroupsModules`.

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-003, SR-004, SR-005, SR-006, SR-007, SR-008, SR-009, SR-010, SR-011, SR-012, SR-013, SR-014, SR-015, SR-016, SR-035, SR-036.
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

Participates in RISK-002, RISK-001 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
