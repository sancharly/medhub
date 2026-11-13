---
id: ADD-015
type: architecture-doc
title: DICOM Module (backend) (SI-MOD-DICOM-BE)
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-13"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-13"
approved_digest: ab874956ddd2051c1b4a9d34f71f0bc7ef5d6cedea30ae10e858c05f866136c7
approval_note: self-approved
links:
  - target: SR-016
    relation: implements
  - target: SR-017
    relation: implements
  - target: SR-026
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
  **CR-006 (planned, D-2; TASK-218):** before any pixel data is decoded, the unit refuses an object over
  150 MiB stored (checked from the attachment record through `open(..., max_bytes=)`, ADD-012, before
  the store is read) or whose header-declared decoded size (rows × columns × frames × samples ×
  bytes per sample, read with `stop_before_pixels`, SOUP-015) exceeds 1 GiB, with an RFC 7807 problem;
  a decode that fails part-way returns a problem and no image (SR-017 AC 6; SR-026 AC 3; RISK-003,
  RISK-007). NumPy is not installed, so the decode itself cannot succeed until PRB-048 is resolved.

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-016, SR-017; SR-026 (AC 3, added by CR-006).
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

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect role): stored and decoded size bounds before decode (SR-017 AC 6) marked "CR-006 (planned)"; `implements` SR-026 added. Content change, so the 1.0 approval record is cleared and the record returns to review.
