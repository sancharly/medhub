---
id: "PRB-063"
type: problem-report
title: "Attachment download answers 500 when the file name has a character outside Latin-1"
status: resolved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-11-01"
updated: "2026-11-06"
criticality: major
links: []
tags: ["attachments", "hazard:availability", "found-in:TASK-196-rehearsal"]
---

# PRB-063 — Attachment download answers 500 when the file name has a character outside Latin-1

## Observed

Found by the Software Developer during the TASK-196 rehearsal (2026-11-01, scratch project `task196`).
An attachment uploaded with the file name `résumé 患者 #1.txt` is accepted (201) and stored, but
`GET /api/v1/attachments/<id>` answers HTTP 500 on every attempt, on the tree of commit `f7d79fc` and on
the current tree alike. The backend log shows `UnicodeEncodeError: 'latin-1' codec can't encode
characters in position 29-30` raised while the response headers are built:
`backend/app/api/routers/attachments.py:110` writes the stored file name into
`Content-Disposition: attachment; filename="{filename}"`, and HTTP header values are encoded as Latin-1.
The object itself is intact: the migration tool read it from the old store, compared its SHA-256 with
`attachment.checksum` and wrote and verified it on the new one. Only the download endpoint fails.

## Impact

**Any** character outside Latin-1 in the file name makes the download fail, not only CJK or Arabic
scripts. QA reproduced it with `report’s summary.pdf` (U+2019, the apostrophe that macOS and Office
insert); `–` (U+2013) and `€` (U+20AC) fail the same way, and such names are common in files from macOS
and Microsoft Office. A clinician can upload the document and can never download it again through the
application; the data is not lost (it is in the object store and the checksum is recorded). A failed
download writes **no audit event** (only `ATTACHMENT_UPLOAD|SUCCESS` exists for that id), so the access
attempt is also not recorded. A file name containing a double quote would break the header too.
Contributes to RISK-007 (clinical information unavailable). Not related to the SSE key or to key
rotation (TASK-196, TASK-195): the failure is identical before and after both. The exception is raised
from `StreamingResponse` (`backend/app/api/routers/attachments.py:107`) with the header built at `:110`.

## Safety evaluation

Criticality **major**: clinical information is stored and not retrievable by the user who stored it, and
nothing tells the uploader at upload time. No occurrence outside the rehearsal is known. The class of
the defect is availability, not integrity or confidentiality. The human sets the final criticality.

## Investigation

Survey of every place that builds a `Content-Disposition` header (TASK-204, 2026-11-06):

- `backend/app/api/routers/attachments.py` (`fetch_attachment`) was the only builder, from the stored
  file name. `starlette.responses.StreamingResponse` encodes header values as Latin-1, so any character
  above U+00FF raised `UnicodeEncodeError` (reproduced on the unfixed code with `résumé 患者 #1.txt` and
  `report’s summary.pdf`: HTTP 500). A `"` or `\` produced a malformed header; a CR or LF would have been
  a header-injection vector.
- The DICOM route (`/studies/{id}`) builds a plain `Response` and discards the name; it is not affected,
  though the frontend's "Open in viewer" link goes through the attachments route, so DICOM files with such
  names failed there too.
- No export endpoint sets the header, `FileResponse` is not used, and no frontend code parses it
  (`AttachmentItem.tsx` is a plain link, so the browser applies the header).
- The 500 left no audit evidence: `AttachmentService.open` wrote the SUCCESS `ATTACHMENT_ACCESS` row in
  the request transaction, and `get_db` rolled it back on the exception (ADR-0016: only FAILURE rows are
  independent).

## Resolution

TASK-204 (CR-004 D-9; commit pending QA approval). New helper `backend/app/api/content_disposition.py`
(standard library only, never raises): `attachment; filename="<ASCII fallback>"; filename*=UTF-8''<percent-encoded>`
per RFC 6266/5987, control characters and lone surrogates mapped to `_`; `fetch_attachment` is its only
user and a static test fails if anything else builds the header. New
`AttachmentService.record_access_failure` writes an independent `ATTACHMENT_ACCESS` FAILURE row on a storage
error, a missing object, a checksum mismatch and a failure while the response is built. Verified by
TS-007 TC-007.9 and TC-007.10 and on a started stack (scratch project `task204`). Status stays `open`
until QA approves TASK-204, then `resolved` (CR-004 D-8). QA approved TASK-204 on 2026-11-06; `resolved`. Not covered: very long names can exceed the reverse proxy's 4 KB response-header buffer (TASK-204 QA finding 1, carried).

## Source

TASK-196 rehearsal; backend log of the `backend` container.

## Version history

- 1.0 (2026-11-01) — Created from TASK-196. `open`, `major`.
- 1.1 (2026-11-02) — TASK-196 QA round 1: Impact widened (any non-Latin-1 character, no audit event on a failed download); folded into CR-004 (D-9). `open`, `major`.
- 1.2 (2026-11-06) — TASK-204: Investigation and Resolution written; frontmatter version corrected (it said 1.0 while this history records 1.1). `open`, `major`.
- 1.3 (2026-11-06) — TASK-204 QA approval: `resolved` (CR-004 D-8). `major`.
