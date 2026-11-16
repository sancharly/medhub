---
id: ADD-012
type: architecture-doc
title: Attachment Service (SI-ATTACH)
status: approved
version: "1.9"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-16"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-16"
approved_digest: f4430eae153a450b49a7bd06f65eaa4096dd0269fdc0ac51e4bc535b8d4a4265
approval_note: self-approved
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
  - target: SOUP-036
    relation: relates_to
  - target: SOUP-003
    relation: relates_to
  - target: RISK-012
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
- **CR-006 (ADR-0021, implemented).** `U-ATT-Upload` (TASK-135): the maximum is 150 MiB (D-2); content is
  read from Starlette's spooled file in 64 KiB chunks, counted and hashed incrementally, refused once
  the count passes the maximum (the API guard refuses the body after the maximum plus one chunk);
  DICOM validation reads the header from the file; the object is sent with one `PutObject` whose body
  is the file (SR-013 AC 6). `U-ATT-Fetch` (TASK-217): `open_stream` hashes a first chunked read
  without keeping it and remembers the ETag; on a match a second read conditional on that ETag
  (`If-Match`, SOUP-036 behaviour 14) is opened before the response starts, a 412 becomes the SR-013
  AC 5 answer (502, FAILURE row), and the streamed second read is hashed as it is sent and aborted on
  a mismatch with a FAILURE row (SR-013 AC 5, D-6, D-10; RISK-012). `open(..., max_bytes=)` keeps the
  verified whole-object read for the DICOM module and refuses from the stored size before reading
  (SR-017 AC 6, ADD-015).
- **CR-006 (TASK-227, ADR-0023).** `U-ATT-Fetch`: the SUCCESS `ATTACHMENT_ACCESS` row and the
  `AUTHZ_ALLOWED` row are committed with the request transaction before the first byte is sent; when
  that commit fails nothing is served (SR-023 AC 10). The response generator runs after the request
  session is closed, so it follows a generator rule: `open_stream` captures the plain values it needs
  (attachment id, size, checksum, storage key, actor id) before it returns, and the pass-2 FAILURE row
  is written from those values on its own transaction (ADR-0016), never through the closed session or
  an ORM instance. An aborted pass 2 therefore leaves the SUCCESS row and one FAILURE row after it
  (SR-013 AC 5). The download holds no pooled connection during the transfer.

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
[ADR-0015](../../design/adr/0015-object-store-component-after-minio.md) (the object-store component this item talks to; its deployment is [ADD-025](ADD-025-object-store-deployment.md)),
[ADR-0021](../../design/adr/0021-bounded-attachment-io-and-bound-two-pass-download.md) (bounded IO and the bound two-pass download, CR-006).

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
- 1.7 (2026-11-13) — CR-006 Plan stage (Software Architect role): bounded upload and bound two-pass download (ADR-0021) marked "CR-006 (planned)"; links to SOUP-036 (conditional read), SOUP-003 (spooled upload file) and RISK-012 added. Content change, so the 1.6 approval record is cleared and the record returns to review.
- 1.8 (2026-11-13) — TASK-227 (CR-006, ADR-0023): `U-ATT-Fetch` commits its audit rows before the body and follows the generator rule (plain values, own-transaction FAILURE row). Content change, so the 1.7 approval record is cleared and the record returns to review.
- 1.9 (2026-11-14) — TASK-225 (Document Writer): the "CR-006 (planned, ADR-0021)" marker is removed; `U-ATT-Upload` (TASK-135) and `U-ATT-Fetch` (TASK-217) are implemented as described. Wording only. Content change on an approved record, so the 1.8 approval record is cleared and the record returns to review.
