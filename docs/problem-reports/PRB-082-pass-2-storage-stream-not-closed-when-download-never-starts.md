---
id: "PRB-082"
type: problem-report
title: "Pass-2 storage stream is not closed when the download never starts"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["reliability","hazard:availability","found-in:TASK-227-qa"]
---

# PRB-082 — Pass-2 storage stream is not closed when the download never starts

## Observed

Found by QA in the TASK-227 review (2026-11-14). `AttachmentService.open_stream` opens the pass-2 object
stream (`chunks`, a boto3 `StreamingBody` behind the storage port) and returns the `_verified()` generator
(`backend/app/attachments/service.py:206-232`). The only `chunks.close()` is in that generator's `finally`
(`service.py:230-232`). A generator that was created but never started does not run its `finally`.

## Impact

Two paths leave the pass-2 stream unclosed until it is garbage-collected:

- the SUCCESS audit commit fails after `open_stream` returned (reachable since TASK-227 / ADR-0023, which
  commits the request transaction before the response is sent);
- the `StreamingResponse` cannot be built (`backend/app/api/routers/attachments.py:109-116`; since TASK-217), so
  the router's `except Exception` (`attachments.py:117-119`) records the FAILURE row and re-raises, but does not
  close the stream.

No data or audit effect; a storage connection is held until garbage collection.

## Investigation

`_verified()` owns the close, and a generator's `finally` runs only if iteration started (or `close()` is called
on a started generator). Both paths above end before Starlette iterates the body, so nothing calls
`chunks.close()`. The pass-2 stream is opened before the SUCCESS audit record (`service.py:187-190`, the SUCCESS audit row at 197-204), so it
exists whenever those paths are taken. Not reproduced with a real object store; derived from the code and the
TASK-227 QA review. Candidate fix: a closer that works whether or not the generator started (it closes `chunks`
itself, idempotently), called on the route's error path and registered on the request's function-scope exit
stack for the commit-failure path.

## Safety evaluation

Availability only (RISK-007): no data is disclosed or altered, no audit row is lost or wrong, and no content is
served on these paths. A storage connection is held briefly until garbage collection; the load needed is
repeated commit failures or response-construction failures, which are not a normal condition. Criticality
**minor**. No release exists (CR-004 A-1), so no notification is needed. The human sets the final criticality.

## Resolution

Not started; outside CR-006 unless the human adds it. Opened on the human's decision (2026-11-14) after the
TASK-227 QA review; CR-006 does not link it.

## Version history

- 1.0 (2026-11-14) — Created from TASK-227 QA review. `open`, `minor`.
