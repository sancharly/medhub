---
id: "TASK-135"
type: task
title: "True streaming attachment upload and download"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-013"
    relation: implements
  - target: "SR-031"
    relation: relates_to
  - target: "NFR-008"
    relation: relates_to
  - target: "TASK-125"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:high", "remediation-of:TASK-125"]
---

- **Phase:** Review 2026-07 — backend security/robustness
- **Implements / restores:** SR-013; remediates TASK-125
- **Depends on:** —
- **Branch:** `fix/attachment-streaming`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — finding A (High)

## Objective

Attachment upload buffers the entire request body in RAM before any size check:
`app/api/routers/attachments.py` `upload_attachment` does `data = await file.read()` and only then
`AttachmentService.store()` validates `len(data)` against the limit. A client can exhaust worker
memory with an oversized body (memory-DoS). Download is symmetric: `svc.open()` returns the whole
object as `bytes`, which `fetch_attachment` re-chunks from memory through `StreamingResponse` —
streaming in name only. TASK-125 was closed **Completed** although its streaming acceptance
criterion was not met; this task restores it.

## Implementation detail

- Upload: read the `UploadFile` in bounded chunks, aborting with 413 as soon as the cumulative size
  exceeds `max_attachment_bytes` — never materialize the full body. Spool to a temp file (or stream
  directly to MinIO multipart upload) for DICOM validation, which needs a seekable handle.
- Download: replace `svc.open()`-returns-`bytes` with a generator over the boto3
  `StreamingBody.iter_chunks()` so object bytes flow client-ward without full buffering.
- Enforce a reverse-proxy `client_max_body_size` as defense-in-depth (`infra/reverse-proxy`).
- Keep SSE-AES256 and DICOM validation behavior unchanged.

## Acceptance criteria

- [ ] An upload exceeding the size limit is rejected with 413 after reading at most one chunk past
  the limit; process RSS does not grow with request size (test with a body ≫ limit).
- [ ] Downloading a large attachment holds at most one chunk in memory at a time.
- [ ] DICOM validation and modality persistence still pass existing tests.
- [ ] Reverse proxy rejects oversized bodies before they reach the app.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Integration tests through `POST /clinical-entries/{id}/attachments` and
  `GET /attachments/{id}` prove bounded memory (size-limit rejection + chunked download)
- [ ] Traceability row updated (SR-013 → TASK-135 → tests)
- [ ] AUDIT-LEDGER note added correcting the TASK-125 verdict
