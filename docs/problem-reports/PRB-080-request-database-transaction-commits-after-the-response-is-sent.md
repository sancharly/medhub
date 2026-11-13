---
id: "PRB-080"
type: problem-report
title: "Request database transaction commits after the response is sent"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
criticality: major
links: []
tags: ["data-integrity","audit","hazard:data-integrity","found-in:TASK-136-qa"]
---

# PRB-080 — Request database transaction commits after the response is sent

## Observed

Found by QA in round 1 of TASK-136 (2026-11-13), from one download answering 4xx among 1 463 in the last
load-test run (`backend/scripts/load_test.py`, 20 clients, 300 s). The script downloads only the attachment its
own client uploaded and deletes nothing, so no other client can race it. The 4xx was not captured (no access
log), so its status and cause are unproven; the commit order below is the only path that fits.

QA probe on a real uvicorn server, FastAPI 0.138, the `get_db` shape of MedHub
(`/private/tmp/claude-501/-Users-carlos-santiago--claude-spares-spare-VaVpDG/8f1dc588-ebf1-4b95-82da-0fbffafee938/scratchpad/commit_order_probe.py`,
session scratchpad, not in the repository): POST 201, then an immediate GET sees the committed row: False; 0.3 s
later: True.

## Impact

1. A client can receive the 201 of a write before the row is committed, so an immediate read-back (the
   frontend after an upload, a script, another client) answers 404 or shows stale data.
2. A commit that fails after the 201 loses a write the user saw acknowledged (clinical entry, attachment
   metadata); the response cannot be changed any more.
3. A download's SUCCESS audit row is committed only after the transfer ends, and a failure of that commit is
   not visible in the response.

## Investigation

`get_db` is a dependency with `yield` that commits after the handler. FastAPI 0.138 runs the teardown of such a
dependency (default scope `"request"`) after `await response(...)` (`fastapi/routing.py:131-137`), i.e. after the
body was sent. Present since TASK-001 (FastAPI 0.138 throughout); not caused by TASK-136. The installed
FastAPI's `Depends` has a `scope` parameter (`fastapi/params.py:749`, `"function"` or `"request"`), so the
fix below is available. Root cause confirmed by the probe; the 4xx in the load test is not.

Candidate fixes (a design decision for the human, with the same behaviour for rollback on error):

- `Depends(get_db, scope="function")`: the teardown, and the commit, run when the endpoint function returns,
  before the response is sent. Check it with streaming responses (the session is closed before the stream is
  read, so a download must not read from the session in the generator) and with `get_current_user` and other
  dependencies that share the session.
- An explicit `commit()` in the service or handler before it returns.

## Safety evaluation

Affects data integrity of clinical writes and the order of audit rows: RISK-007 (information unavailable when
needed: a just-acknowledged write is not readable), RISK-006 (incomplete audit trail: the SUCCESS audit row of a
download is committed after the transfer, and a failing commit is not reported) and RISK-002 (clinical data
misattribution: a write the user saw acknowledged may not exist). No wrong data is shown to another patient and
the window is milliseconds in normal operation, but a commit failure after a 201 is silent data loss in a clinical
record. Criticality **major**: it can lose an acknowledged clinical write and weakens the audit order; not
`critical` because no wrong clinical information is displayed and the loss needs a commit failure. No release
exists (CR-004 A-1), so no notification is needed. The human sets the final criticality.

## Resolution

Not started. Out of CR-006 scope until the human decides; needs its own CR or a decision to add it.

## Version history

- 1.0 (2026-11-13) — Created from TASK-136 QA round 1 (download 4xx note). `open`, `major`.
