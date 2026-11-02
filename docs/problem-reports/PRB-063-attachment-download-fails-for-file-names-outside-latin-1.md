---
id: "PRB-063"
type: problem-report
title: "Attachment download answers 500 when the file name has a character outside Latin-1"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-01"
updated: "2026-11-01"
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

## Resolution

Not fixed. Folded into CR-004 by the human on 2026-11-02 (D-9, Scope row PRB-063 to TASK-204; the task is
written by the Software Architect). A fix would, for example, send
`filename*=UTF-8''<percent-encoded name>` (RFC 6266) and an ASCII-safe `filename=` fallback, with a test
that downloads an attachment whose name is `résumé 患者 #1.txt` and one that contains a double quote.

## Source

TASK-196 rehearsal; backend log of the `backend` container.

## Version history

- 1.0 (2026-11-01) — Created from TASK-196. `open`, `major`.
- 1.1 (2026-11-02) — TASK-196 QA round 1: Impact widened (any non-Latin-1 character, no audit event on a failed download); folded into CR-004 (D-9). `open`, `major`.
