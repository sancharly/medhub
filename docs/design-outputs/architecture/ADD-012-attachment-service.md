---
id: ADD-012
type: architecture-doc
title: Attachment Service (SI-ATTACH)
status: approved
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-10"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-10"
approval_note: approved by the human in chat at the close of CR-004
links:
  - target: SR-013
    relation: implements
  - target: SR-022
    relation: implements
  - target: SR-026
    relation: implements
  - target: RISK-002
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: RISK-011
    relation: relates_to
  - target: SOUP-015
    relation: relates_to
  - target: SOUP-017
    relation: relates_to
  - target: SOUP-019
    relation: relates_to
tags:
  - software-item:SI-ATTACH
  - class:B
  - layer:backend
---

# ADD-012 — Attachment Service (SI-ATTACH)

## Responsibility

Upload/fetch attachment binaries via object storage, authorized

## Software units (IEC 62304 §5.4.1)

- `U-ATT-Upload` — validate, store object (SSE), bind to entry/patient transactionally (SR-013). It refuses a
  file name longer than 255 UTF-8 bytes with a 400 problem (`filename_max_bytes`) before anything is written;
  the name is never truncated, as it is part of the clinical record (TASK-206, PRB-069). The display name and the storage key are one value, so a name with dot segments reaches the object store, which refuses it, and the upload answers 500 (PRB-073, open).
- `U-ATT-Fetch` — authorized stream / scoped pre-signed URL (SR-005, SR-013.3). Before any byte is
  served it compares the SHA-256 of the content read from the store with the stored checksum
  (constant-time). On a mismatch it serves nothing, records an `ATTACHMENT_ACCESS` audit event with
  outcome FAILURE, and answers HTTP 502 (TASK-173). The `Content-Disposition` value it sends is bounded
  for any stored name (`filename*` at most 255 bytes of the name, the ASCII fallback at most 150 characters,
  extension kept; about 1 KB) and bidi control characters are mapped to `_` (TASK-206, PRB-069).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-013, SR-022, SR-026.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0008](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0010](../../design/adr/), [ADR-0011](../../design/adr/),
[ADR-0015](../../design/adr/0015-object-store-component-after-minio.md) (the object-store component this item talks to; its deployment is [ADD-025](ADD-025-object-store-deployment.md)).

## Risk relevance

Participates in RISK-002, RISK-007, RISK-011 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-10-30): TASK-175. Approval record cleared; the link to SOUP-023 (`mc`) removed.
- 1.2 (2026-10-30): TASK-176. The link to SOUP-022 (MinIO) removed.
- 1.3 (2026-10-30): TASK-180. `U-ATT-Fetch` verifies the stored checksum and refuses with an audit
  FAILURE (TASK-173); ADR-0015 named among the governing decisions. Still `in_review`, not approved.
- 1.4 (2026-11-06): TASK-204 (PRB-063). `U-ATT-Fetch` records an `ATTACHMENT_ACCESS` FAILURE on every server-side
  failure after authorization, not only a checksum mismatch. Approval record cleared; `in_review`.
- 1.5 (2026-11-07): TASK-206 (PRB-069). `U-ATT-Upload` validates the name length (255 UTF-8 bytes, 400); `U-ATT-Fetch` bounds the header. Approval record cleared; `in_review`.
- 1.6 (2026-11-08) — TASK-201: `U-ATT-Upload` notes the open dot-segment defect (PRB-073). No other change.
