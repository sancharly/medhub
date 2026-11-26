---
id: ADD-022
type: architecture-doc
title: DICOM Viewer Module (frontend) (SI-MOD-DICOM-FE)
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-26"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-26"
approved_digest: a31f884c7ae2b1eb906e83bacae646add9e71235e6f6d11f0c4ba8bc35957649
approval_note: self-approved
links:
  - target: SR-017
    relation: implements
  - target: SR-018
    relation: implements
  - target: SR-026
    relation: implements
  - target: RISK-003
    relation: relates_to
tags:
  - software-item:SI-MOD-DICOM-FE
  - class:B
  - layer:frontend
---

# ADD-022 — DICOM Viewer Module (frontend) (SI-MOD-DICOM-FE)

## Responsibility

Cornerstone3D viewport, window/level, zoom, pan, slice nav

## Software units (IEC 62304 §5.4.1)

- `U-DICOMFE-Viewport` — Cornerstone3D init, parse, LUT, slice ordering, default W/L (SR-017).
- `U-DICOMFE-Controls` — window/level, zoom, pan, slice navigation (SR-018).

**State on 2026-11-25 (CR-008).** Neither unit exists in code yet; they are built in the viewer phase
(GitHub #29, TASK-100 to TASK-103). Until then there is **no entry point** to the viewer: CR-008 D-5
removes the "Open in viewer" link from `AttachmentItem` (`frontend/src/core/clinical/AttachmentItem.tsx`;
TASK-237), which pointed at the core attachment download, and every attachment keeps its Download link
(SR-017 AC 11). The viewer phase adds the entry point, gated by `GET /me/modules` (ADD-021), and obtains
the study only through the module endpoint `GET /api/v1/modules/dicom-viewer/studies/{attachment_id}`
(ADD-015), the whole object for Cornerstone3D (ADR-0008), never the core attachment URL.

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-017, SR-018, SR-026.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0008](../../design/adr/), [ADR-0009](../../design/adr/).

## Risk relevance

Participates in RISK-003 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-11-25) — CR-008 Plan stage (Software Architect role): records that the units are not built yet and that there is no viewer entry point until the viewer phase (D-5, SR-017 AC 11; TASK-237), and that the viewer obtains the study only through the module endpoint. Content change, so the 1.0 approval record is cleared and the record returns to review.
