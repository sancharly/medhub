---
id: "PRB-073"
type: problem-report
title: "An attachment file name with dot segments answers 500 at upload"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-07"
updated: "2026-11-07"
criticality: minor
links: []
tags: ["attachments", "input-validation", "found-in:TASK-206-qa"]
---

# PRB-073 — An attachment file name with dot segments answers 500 at upload

## Observed

Found by QA while reviewing TASK-206 (2026-11-07). An upload whose multipart file name is
`../../etc/passwd` answers 500: the name reaches the storage key and the object store refuses it with
`InvalidRequest`.

## Impact

The upload fails with a generic error instead of a validation message. Nothing is stored. Browsers send a
base name only, so this needs an API client or a crafted request; an ordinary user is not expected to
meet it. The application's containment relies on the object store's refusal: the key is built from
client input, with `..` able to point outside the attachment's own prefix.

## Investigation

- `backend/app/api/routers/attachments.py:60` passes `file.filename` unchanged.
- `backend/app/attachments/service.py:79` checks the name's length only (PRB-069, TASK-206).
- `service.py:100` builds `f"attachments/{entry.patient_id}/{uuid.uuid4()}/{filename}"`, so `/` and `..` in the
  name become key segments. `service.py:104` calls `put_object`
  (`backend/app/core/object_storage.py:33-41`), which raises; nothing handles it, so it reaches the generic
  500 handler. The object is not written and no row is created (`service.py:107` onwards is not reached).
- Not verified: which names the store refuses. `report..final.pdf` (dots inside a segment) and a name with
  `/` but no `..` were not tried. A name with `/` and no `..` is expected to be accepted, as a nested key.
- Root cause: the client's file name is used as part of a storage path. The display name and the storage
  key are one value.

**Should the name be normalised at upload?** Not the stored name: it is part of the clinical record (SR-013
AC 2, the reason PRB-069 refuses rather than truncates). Two options for the CR that takes this PRB:

1. Stop embedding the name in the key (`attachments/{patient_id}/{uuid}`). The name stays verbatim in
   `Attachment.filename`, the 500 goes away, and the key no longer depends on client input. Existing keys
   stay valid, as the column holds the full key. Recommended; it also closes TASK-202's carried item on the
   raw name in the key.
2. Refuse `/`, `\` and dot segments with a 400 (`ValidationProblem`, SR-013 AC 1). Smaller, but it keeps the
   name in the key.

## Safety evaluation

No data is disclosed, altered or lost, and the store refuses the key, so no traversal was observed. It
affects one upload from a crafted request. Criticality **minor**. No release exists (CR-004 A-1), so no
notification is needed. The human sets the final criticality.

## Resolution

Not fixed. Known anomaly outside CR-004 (D-18). It has no `resolves` link yet.

## Source

TASK-206 QA review, "Pre-existing issues"; human decision 2026-11-07 (CR-004 D-18).

## Version history

- 1.0 (2026-11-07) — Created from the TASK-206 QA review. `open`, `minor`.
