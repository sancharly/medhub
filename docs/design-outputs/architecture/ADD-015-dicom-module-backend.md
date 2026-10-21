---
id: ADD-015
type: architecture-doc
title: DICOM Module (backend) (SI-MOD-DICOM-BE)
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 932b347cbe0afa09864fc298c9b94e60f92a8d01d78a427227b7d6df34adaa14
approval_note: self-approved
links:
  - target: SR-016
    relation: implements
  - target: SR-017
    relation: implements
  - target: RISK-003
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: SOUP-015
    relation: relates_to
tags:
  - software-item:SI-MOD-DICOM-BE
  - class:B
  - layer:backend
---

# ADD-015 — DICOM Module (backend) (SI-MOD-DICOM-BE)

## Responsibility

Authorized DICOM byte/frame endpoints behind the module contract

## Software units (IEC 62304 §5.4.1)

- `U-DICOMBE-Studies` — authorized DICOM byte/frame endpoint via platform services (SR-016, SR-017).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-016, SR-017.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0001](../../design/adr/), [ADR-0005](../../design/adr/), [ADR-0008](../../design/adr/).

## Risk relevance

Participates in RISK-003, RISK-007 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.
