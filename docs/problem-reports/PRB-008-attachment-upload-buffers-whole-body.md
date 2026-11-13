---
id: "PRB-008"
type: problem-report
title: "Attachment upload and download buffer the whole object in memory"
status: resolved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-13"
criticality: major
links: []
tags: ["performance", "hazard:availability"]
---

# PRB-008 — Attachment upload and download buffer the whole object in memory

## Observed

`api/routers/attachments.py` awaits `file.read()` into memory before the size check, and the download path loads the whole object then re-chunks it from RAM.

## Impact

Concurrent large DICOM transfers exhaust process memory and blow the SR-026 performance budget; the size limit is enforced after the damage.

## Safety evaluation

Contributes to RISK-007 (clinical information unavailable).

## Resolution

Upload half: TASK-135 (in review, 2026-11-13), CR-006 D-2, ADR-0021. The router no longer calls
`await file.read()`: `AttachmentService.store` reads the spooled file in 64 KiB chunks, counts and hashes
incrementally, and refuses (400 `validation-error`, unchanged) as soon as the count passes the maximum,
now 150 MiB (`attachment_max_bytes`, default in `Settings`). A pure-ASGI guard
(`backend/app/core/body_limit.py`, upload route only) refuses a declared `Content-Length` over the
maximum plus 64 KiB before any body byte is read, and stops reading once 64 KiB past that bound. DICOM
validation reads the header from the file; the object is sent with one `PutObject` whose body is the file.
Verified in the working tree: TC-007.12 in TS-007 1.9 (service and ASGI tests, 20 MiB and 60 MiB peak
allocation under 4 MiB, exactly 150 MiB accepted with the right SHA-256, over-limit refused after at most
the maximum plus 64 KiB plus one chunk); OpenAPI export byte-identical. Not verified: an upload of a real
large file through the started stack to the real object store (TASK-226 load test).
Download half: TASK-217 (in review, 2026-11-13), CR-006 D-6 and D-10, ADR-0021. `AttachmentService.open`
no longer serves the router. `open_stream` reads the object twice through
`ObjectStorageClient.get_object_stream` (boto3 `Body.iter_chunks(65536)`, the response opened before any
byte is sent). Pass 1 hashes the chunks, keeps nothing and records the ETag; on a SHA-256 match pass 2
re-reads with `IfMatch=<ETag>` and the router streams the chunks (`Content-Length` from the stored size)
while hashing again. A mismatch in pass 1, or an object replaced between the passes (the store answers
412, `ObjectChangedError`), gives the existing 502 `attachment-integrity-failure` problem with no
content and one FAILURE `ATTACHMENT_ACCESS` row; a digest that differs at the end of pass 2 records a
FAILURE row and ends the response without completing it. `open()` stays for the DICOM module and gains
`max_bytes` (refusal before any read, for TASK-218). Verified in the working tree: TC-007.13 in TS-007
1.10 (peak allocation of a 20 MiB and a 60 MiB download under 4 MiB; second read conditional on the first
ETag; replaced object; second-pass mismatch; `max_bytes`); the conditional read on the pinned SeaweedFS
4.51 with SSE-S3 on (TASK-217 "Step 1 evidence"); mutation check (removing `IfMatch` or the final digest
check fails three tests); full backend suite and OpenAPI export byte-identical. Not verified: a large
download through the started stack (TASK-226 load test).
Both halves are implemented and verified; QA approved TASK-135 and TASK-217 (2026-11-13), so the report is
`resolved` (CR-006 `resolves` PRB-008) and becomes `closed` when CR-006 closes.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding A.

## Version history

- 1.0 (2026-09-17) — Created from the July 2026 code review.
- 1.1 (2026-11-13) — TASK-135: upload half implemented and verified in the working tree; `investigating`
  until the download half (TASK-217) is done.
- 1.2 (2026-11-13) — TASK-217: download half implemented and verified in the working tree; `## Resolution`
  covers both halves. Still `investigating` until QA approves TASK-135 and TASK-217.
- 1.3 (2026-11-13) — QA review of TASK-217 (round 3): both halves approved; `investigating → resolved`.
