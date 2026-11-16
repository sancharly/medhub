---
id: "PRB-080"
type: problem-report
title: "Request database transaction commits after the response is sent"
status: resolved
version: "1.3"
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

In CR-006 scope (D-27, human decision 2026-11-13), resolved by TASK-227 under ADR-0023 (approved by the
human 2026-11-13, decisions P-10 to P-15): every use of `get_db` goes through one alias,
`DbSession = Annotated[Session, Depends(get_db, scope="function")]`, so the commit runs before the response is
sent and a failed commit is a 5xx. The streamed download's generator runs after the session is closed, so
`open_stream` captures plain values (actor id, attachment id, size, checksum, storage key) and the pass-2
FAILURE row is written on its own transaction from them (ADR-0016); an aborted pass 2 now leaves the SUCCESS rows
and one FAILURE row after them (P-12). RISK-002 assessed as not affected (CR-006 change analysis).

Evidence (TASK-227, branch `fix/review-2026-07-reliability`, HEAD c69d7dc plus the working tree), real
PostgreSQL where stated:

- Reproduction on HEAD behaviour: the recorded events of `POST` clinical entry were `['response_start', 'commit']`
  (`test_success_response_is_sent_after_commit`); a failing `Session.commit` gave 201
  (`test_commit_failure_is_a_5xx_not_a_success`); the three download cases failed (`test_download_audit_order.py`: audit rows and pool probe at the first body
  chunk, commit failure, aborted pass 2). With the fix: commit before
  `response_start`, 5xx problem with no row stored, both SUCCESS rows visible and `pool.checkedout() == 0`.
- Scope inventory (`tests/api/test_db_dependency_scope.py`): every `get_db` dependant of every route has scope
  `function`, one cache key per route, with two planted negative controls.
- OpenAPI export byte-identical to `backend/openapi/openapi.json`.
- Verified by TS-007 TC-007.14 and TC-007.15, TS-009 TC-009.13, TS-002 TC-002.10 (`in_review`).

QA verification (TASK-227 round 1, 2026-11-13): reproduced independently in a scratch copy (plain `Depends(get_db)` alias: 7 of 8 new tests fail; HEAD `open_stream`: `DetachedInstanceError`); with the fix the backend suite (1653 passed), the DICOM module suite, `mypy` and `ruff check` are green and the OpenAPI export is byte-identical. Fixed and verified in the working tree, so `resolved`; `closed` once confirmed through a shipped release.

## Version history

- 1.0 (2026-11-13) — Created from TASK-136 QA round 1 (download 4xx note). `open`, `major`.
- 1.1 (2026-11-13) — Added to CR-006 by D-27; Resolution names TASK-227 and ADR-0023. Still `open`.
- 1.2 (2026-11-13) — TASK-227 implemented: Resolution names the implementation and its evidence. Still `open` until the human's decision.
- 1.3 (2026-11-13) — QA review of TASK-227 (round 1): APPROVED; fix verified, `open → resolved` (CR-006 holds the `resolves` link).
