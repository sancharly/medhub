---
id: ADD-014
type: architecture-doc
title: Module Host / Plugin Registry (SI-MODHOST)
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
links:
  - target: SR-016
    relation: implements
  - target: RISK-004
    relation: relates_to
  - target: SOUP-002
    relation: relates_to
tags:
  - software-item:SI-MODHOST
  - class:B
  - layer:backend
---

# ADD-014 — Module Host / Plugin Registry (SI-MODHOST)

## Responsibility

Module discovery/registration, platform-service injection, router mounting

## Software units (IEC 62304 §5.4.1)

- `U-MH-Discovery` — entry-point discovery & `ModuleManifest` validation (SR-016).
- `U-MH-PlatformServices` — `PlatformServices` facade injected into modules (SR-016.3).
- `U-MH-RouterMount` — mount module routers under `/api/v1/modules/{key}` (SR-016).
- `U-MH-ModuleSettings` — `backend/app/modules/module_settings.py`: the platform settings a module may read, one accessor per setting (today the DICOM stored and decoded size bounds); a module never imports `app.core.config` (SR-016 AC 3). The module boundary is checked by a name-level allow-list (`ALLOWED_PLATFORM_NAMES` in `backend/tests/modules/test_module_boundary.py`): a module may import only the listed names from the listed platform modules (`app.modules.contract`, `app.api.deps`, `app.api.errors`, `app.audit.actions`, `app.modules.module_settings`). A new name needs a design decision recorded here.

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-016.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0001](../../design/adr/), [ADR-0005](../../design/adr/).

## Risk relevance

Participates in RISK-004 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.0 (2026-10-21) — Created and self-approved.
- 1.1 (2026-11-14) — TASK-223 (CR-006, QA finding R2-3; Document Writer in TASK-225): unit `U-MH-ModuleSettings` (`backend/app/modules/module_settings.py`) named, and the name-level allow-list of `backend/tests/modules/test_module_boundary.py` recorded; the DICOM module no longer imports `app.core.config`. Content change on an approved record, so the 1.0 approval record is cleared and the record returns to review.
