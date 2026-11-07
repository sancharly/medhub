---
id: "PRB-069"
type: problem-report
title: "Attachment file names have no length limit, so a long name makes the proxy answer 502"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-07"
updated: "2026-11-07"
criticality: minor
links: []
tags: ["attachments", "hazard:availability", "found-in:TASK-204-qa"]
---

# PRB-069 — Attachment file names have no length limit, so a long name makes the proxy answer 502

## Observed

Found by QA while reviewing TASK-204 (committed as 33daae8), finding 1. An attachment whose name is
400 CJK characters, or 255 × U+FDFA, uploads with 201 but its download through the reverse proxy answers
**502 "upstream sent too big header"**. The backend answered 200 and committed an `ATTACHMENT_ACCESS`
SUCCESS row. 255 CJK characters (header 2,592 bytes) and 255 emoji (3,357 bytes) still pass; the limit
measured was a `Content-Disposition` of about 4,042 bytes.

## Impact

The uploader can store an attachment that nobody can download through the application (SR-013 AC 3),
and the audit trail records a successful access that the user never received (SR-023 AC 2). Names
taken from real file systems are at most 255 characters and pass today, so only unusual or
API-crafted names are affected. The object itself is intact.

## Investigation

- `backend/app/api/routers/attachments.py:60` takes `file.filename` as given; `AttachmentService.store`
  (`backend/app/attachments/service.py`) validates size and DICOM content but not the name, and
  `Attachment.filename` (`backend/app/db/models/attachment.py:21`) is an unbounded string.
- `backend/app/api/content_disposition.py:21-31` builds the ASCII fallback from the NFKD form. NFKD can
  expand one character into up to 18 (U+FDFA becomes 18 ASCII-range characters), and the fallback has no
  length cap. `:34-38` percent-encodes the whole name into `filename*` (up to 3 bytes of output per UTF-8
  byte), also without a cap. 255 × U+FDFA gives a 6,927-byte header value.
- `infra/reverse-proxy/nginx.conf:31-37` sets no `proxy_buffer_size`, so nginx 1.31.8 uses its default of
  one memory page (4 KB). All upstream response headers must fit in it; otherwise nginx answers 502.
- The SUCCESS row is committed by the backend before nginx rejects the response; the backend cannot see
  the proxy's failure.
- The storage key also embeds the name (`attachments/service.py:78`); S3 limits a key to 1,024 bytes, so
  a very long name can also fail at upload. Not observed; noted for the fix.
- Root cause: no bound on the stored name and no budget on the header built from it.

## Safety evaluation

Availability of one attachment, for names that real file systems do not produce; the content is not lost
or altered and can be recovered from the object store. The misleading SUCCESS audit row weakens the
audit trail slightly (RISK-006). Criticality **minor**. No release exists (CR-004 A-1), so no notification
is needed. The human sets the final criticality.

## Resolution

Fixed by TASK-206 (CR-004 D-14, D-16); status `resolved` on QA approval (D-8).

- Upload: a name over 255 UTF-8 bytes is refused with a 400 `application/problem+json`
  (`errors[0].rule = filename_max_bytes`); nothing is stored (`backend/app/attachments/service.py`). The
  upload control shows the reason (`frontend/src/core/clinical/AttachmentUpload.tsx`).
- Download: the `Content-Disposition` value is bounded for any stored name (`filename*` at most 255 bytes of
  the name, the fallback at most 150 characters, extension kept; about 1 KB, 957 bytes measured for 255 x
  U+FDFA through the proxy), so a name stored before the limit still downloads
  (`backend/app/api/content_disposition.py`). Bidi control characters are also mapped to `_` (TASK-204 QA
  finding 3).
- Tests: `backend/tests/api/test_content_disposition.py`, `backend/tests/attachments/test_attachment_upload.py`,
  `backend/tests/api/test_attachments_router.py`, `frontend/src/core/clinical/AttachmentUpload.test.tsx`;
  started stack: 256-byte and 259-byte names answer 400, a 255-byte name answers 201 and downloads.
- Accepted residual (human, D-16): names legal on Windows and macOS of more than 255 bytes (for example more
  than 85 CJK characters) are refused.

## Source

TASK-204 QA review, finding 1 (`docs/design-outputs/tasks/TASK-204-safe-download-file-names-and-failed-download-audit.md`);
human decision 2026-11-07.

## Version history

- 1.0 (2026-11-07) — Created from the TASK-204 QA review. `open`, `minor`.
- 1.1 (2026-11-07) — Resolution written by the Software Developer role (TASK-206). Left `open` (CR-004 D-8).
- 1.2 (2026-11-07) — QA approved TASK-206: status `resolved` (CR-004 D-8).
