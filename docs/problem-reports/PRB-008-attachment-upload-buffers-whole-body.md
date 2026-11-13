---
id: "PRB-008"
type: problem-report
title: "Attachment upload and download buffer the whole object in memory"
status: investigating
version: "1.1"
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
Download half: TASK-217 (bound two-pass read), not yet done. This report therefore stays open
(`investigating`) until TASK-217 is verified.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding A.

## Version history

- 1.0 (2026-09-17) — Created from the July 2026 code review.
- 1.1 (2026-11-13) — TASK-135: upload half implemented and verified in the working tree; `investigating`
  until the download half (TASK-217) is done.
