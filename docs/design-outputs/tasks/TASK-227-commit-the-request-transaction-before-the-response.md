---
id: "TASK-227"
type: task
title: "Commit the request transaction before the response is sent"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-14"
links:
  - target: "SR-012"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "SR-008"
    relation: implements
  - target: "SR-013"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "RISK-006"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-080"
    relation: relates_to
  - target: "PRB-081"
    relation: relates_to
  - target: "ADD-016"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "SOUP-002"
    relation: relates_to
  - target: "TASK-136"
    relation: relates_to
  - target: "TASK-141"
    relation: relates_to
  - target: "TASK-217"
    relation: relates_to
tags: ["cr:CR-006", "transaction", "audit", "control:design"]
---

# TASK-227 — Commit the request transaction before the response is sent

- **Software items / units:** SI-PERSIST (ADD-016, `U-PER-Repos`: `db/repositories/session.py`),
  SI-API (ADD-005: every router and `api/deps.py` that depends on `get_db`), SI-ATTACH (ADD-012:
  `AttachmentService.open_stream`), SI-AUDIT (ADD-013, `audit/deps.py`, `AuditRepository.add_independent`).
- **PRB:** PRB-080 (resolved by this task). PRB-081 relates only (out of scope, D-27).
- **CR:** CR-006 D-27. **Decision:** [ADR-0023](../../design/adr/0023-request-transaction-commits-before-the-response.md) (Accepted, CR-006 D-28).
- **Order:** after TASK-136 (approved), **before TASK-141**. See "Ordering".
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** M. Files: `backend/app/db/repositories/session.py`, `backend/app/api/deps.py`,
  `backend/app/audit/deps.py`, the 12 router files with `Depends(get_db)` (`me`, `clinical`, `groups`,
  `anonymized_data`, `accounts`, `lifecycle`, `attachments`, `modules`, `auth`, `appointments` and the
  others the inventory test finds), `backend/app/attachments/service.py`,
  `backend/app/db/repositories/audit_repo.py` (only if the independent write needs the engine
  captured); tests under `backend/tests/`. The edit at each site is mechanical (one alias); the
  behaviour change is in one place.

## Objective

Every request's database transaction commits, or rolls back, before its response is sent (ADR-0023).

- **SR-012 AC 5 (new):** a 201 for a clinical entry or an attachment is sent only after the commit; a
  failed commit is a 5xx problem response, never the success status.
- **SR-023 AC 10 (new):** the SUCCESS audit rows of a request (`AUTHZ_ALLOWED`, `ATTACHMENT_ACCESS`)
  are committed before the response, and for a download before the first byte; an aborted pass 2
  adds a FAILURE row on its own transaction.
- **SR-008 AC 4 (restored):** once a revoke has been answered, the next request of that doctor is
  denied; a revoke whose commit fails is reported as a 5xx, not as done.
- **SR-013 AC 5 (kept):** the two-pass download's FAILURE path still works after the request session
  is closed.

## Implementation detail

- `session.py`: keep `get_db` unchanged; add the alias
  `DbSession = Annotated[Session, Depends(get_db, scope="function")]` (name may differ; one alias).
  Replace every `db: Session = Depends(get_db)` with it. No site may keep the default scope: a mix gives
  two sessions in one request (the cache key includes the scope, ADR-0023 "Context").
- `AttachmentService.open_stream`: capture `attachment.id`, `attachment.size`, `attachment.checksum` and
  `actor.id` as plain values before returning; `_verified()` and the FAILURE call inside it use only
  those values and the storage stream. `record_access_failure` takes the actor id (or the captured
  value) so it does not read an expired ORM instance.
- `AuditRepository.add_independent`: confirm that `self._session.get_bind()` works on a closed session
  (it should: the bind comes from the sessionmaker). If not, capture the engine at construction. Either
  way, a test proves it (below).
- No change to `get_db`'s commit/rollback logic, to the HTTP contract or to the OpenAPI document (the
  export must stay byte-identical). No new dependency.
- Out of scope: PRB-081 (concurrency cap), orphan-object clean-up after a failed upload commit (an
  unreferenced encrypted object, as after any rollback today), the erasure enqueue order (TASK-141).

## Tests (write first; the first three fail on HEAD)

1. **PRB-080 reproduction — response observed before commit**
   (`tests/db/test_request_commit_order.py::test_success_response_is_sent_after_commit`, SR-012 AC 5):
   wrap the session's `commit` with a recorder that notes whether the response's
   `http.response.start` has already gone out (an ASGI `send` wrapper on the app under test, or a
   real-uvicorn probe as in the QA probe of PRB-080). Create a clinical entry and upload an attachment;
   assert the commit was recorded **before** the response start. Also an immediate `GET` of the new
   entry with a second client returns it (real PostgreSQL). Fails on HEAD (the commit comes after).
2. **Commit failure gives 5xx, not 201**
   (`test_commit_failure_is_a_5xx_not_a_success`, SR-012 AC 5): make `Session.commit` raise
   (`OperationalError`) for a `POST` of a clinical entry and a consent revoke (SR-008 AC 4); assert a
   5xx problem response, no 201/200, and that the row is absent. Fails on HEAD (the client gets 201).
3. **Download audit ordering** (`tests/attachments/test_download_audit_order.py`, SR-023 AC 10,
   SR-013 AC 5, real PostgreSQL):
   - (a) when the first body chunk is produced, the `ATTACHMENT_ACCESS` SUCCESS and `AUTHZ_ALLOWED`
     rows are already committed (read on a separate connection from inside the storage stub's first
     chunk). Fails on HEAD.
   - (b) the commit of the SUCCESS row fails → 5xx, no body byte, and a FAILURE row is not required
     (the access did not start).
   - (c) pass-2 mismatch after the response started: the transfer is aborted, the SUCCESS row stays
     and one FAILURE row is committed after it (the request session is closed by then; no
     `DetachedInstanceError`).
   - (d) the download does not hold a pooled connection during the transfer
     (`engine.pool.checkedout()` is 0 while the stub is yielding).
4. **Scope inventory** (`tests/api/test_db_dependency_scope.py`, ADR-0023): for every route of the
   assembled app (core and installed modules), every dependant whose call is `get_db` has scope
   `"function"`, and each route resolves at most one `get_db` cache key. A planted route using plain
   `Depends(get_db)` makes the test fail (negative control).
5. **Regression:** TS-007 TC-007.6 to TC-007.8 and the TASK-217 cases unchanged; TS-009 TC-009.4 to
   TC-009.8 (independent FAILURE rows) unchanged; TS-002 (consent and authorization) unchanged; full
   backend suite; OpenAPI export byte-identical.

Recorded as new cases in TS-007 (tests 1-3), TS-009 (test 3, TC for SR-023 AC 10) and TS-002 (the
revoke case of test 2), per the CR-006 rule for a TS changed by several tasks.

## Acceptance criteria

- [x] SR-012 AC 5: tests 1 and 2 pass; both fail on HEAD (recorded with the HEAD commit).
- [x] SR-023 AC 10: test 3 (a) to (c) pass; (a) fails on HEAD.
- [x] SR-008 AC 4: the revoke case of test 2 passes; TS-002 unchanged.
- [x] SR-013 AC 5: TC-007.6 to TC-007.8 and test 3 (c) pass.
- [x] Every `get_db` dependency has scope `"function"` (test 4 with its negative control).
- [x] No contract change, no new dependency.

## Definition of Done

- [x] `uv run pytest -q` (backend, coverage ≥ 85 %), `modules/` suites, `ruff check`, `ruff format --check`,
  `mypy app` green; OpenAPI export byte-identical
- [x] TS-007, TS-009, TS-002 updated; ADD-016 (`U-PER-Repos`: request transaction ends before the response),
  ADD-005 and ADD-012 (generator rule) updated with a "CR-006" marker; SOUP-002 relied-on behaviour gains
  `Depends(scope="function")` (teardown before the response; cache key includes the scope)
- [x] PRB-080 Resolution filled with the evidence (stays `open` until the human's decision)
- [x] `traceability-check` no error for this record and its neighbours

## Ordering

TASK-136 (event loop and pools) is approved; TASK-227 follows it and goes **before TASK-141**:

- TASK-141's D-11 test ("an erasure whose code e-mail cannot be queued is rolled back as a whole, 503")
  depends on where the request transaction ends. Writing it against the final transaction shape avoids
  re-verifying it. With `scope="function"` the rollback still runs before the response, so the D-11
  behaviour is unchanged, but its test should assert it on the new shape.
- TASK-227 touches every router once; doing it before TASK-141 (erasure router, OpenAPI regeneration),
  TASK-143 and TASK-144 keeps those diffs small.
- It shares `attachments/service.py` with TASK-217 (approved) and no file with TASK-219 (migration 0011,
  in progress) or TASK-220. It can run in parallel with TASK-219 and TASK-220.

## Risk notes

- **Mixed scopes** (cause 12 of the CR-006 analysis): two sessions per request if one site is missed →
  test 4.
- **Generator after close** (cause 13): `DetachedInstanceError` or a lost FAILURE row in an aborted
  download (RISK-012 audit part, RISK-006) → test 3 (c).
- **Audit reading of an aborted download** changes from "FAILURE only" to "SUCCESS then FAILURE"
  (ADR-0023, ADR-0016 note amended): a decision for the human (CR-006 finding P-12).

## Implementation record (Software Developer role, 2026-11-13)

Handoff `draft → in_review`; the checkboxes above are for QA.

- **Code.** `session.py` gains `DbSession = Annotated[Session, Depends(get_db, scope="function")]`;
  all 30 `Depends(get_db)` sites in 14 files under `backend/app` use it (a parameter without a default
  cannot follow one with a default, so `db: DbSession` moved to the front of 12 signatures; FastAPI
  resolves by name, the OpenAPI export is unchanged). `AttachmentService.open_stream` captures actor
  id, attachment id, storage key, checksum, size, content type and file name before returning, and a
  new private `_record_failure(actor_id, attachment_id)` writes the FAILURE row from plain values;
  `record_access_failure(actor, id)` keeps its signature and delegates. `AuditRepository.add_independent`
  is unchanged: `get_bind()` works on a closed session (test 3 (c) writes the row after the close).
  Four existing test overrides of the attachment/DICOM service dependency now declare
  `db: DbSession` (the production shape); their assertions are unchanged.
- **Tests.** `tests/db/test_request_commit_order.py` (tests 1, 2; real PostgreSQL),
  `tests/attachments/test_download_audit_order.py` (test 3 (a) to (d); real PostgreSQL, runtime role),
  `tests/api/test_db_dependency_scope.py` (test 4 and two planted negative controls). FastAPI 0.138
  keeps included routers lazy (`_IncludedRouter`), so the scope test walks routes with
  `fastapi.routing.iter_route_contexts`; `app.routes` alone yields no API route.
- **Fails on HEAD behaviour.** With the alias temporarily set to plain `Depends(get_db)` (every site then
  behaves as on c69d7dc): 7 of 8 new tests fail (events `['response_start', 'commit']`, 201 on a failed
  commit, the three download cases, the scope walk and the mixed-scope control; only the default-scope
  control passes, by design). With the alias at `scope="function"` but `open_stream` restored from HEAD,
  download cases (a) and (c) fail with `DetachedInstanceError` on the closed session.
- **Records.** ADD-016 1.4, ADD-005 1.4, ADD-012 1.8, SOUP-002 1.2 (approval fields removed, `in_review`);
  TS-007 1.11 (TC-007.14, TC-007.15), TS-009 1.12 (TC-009.13), TS-002 1.8 (TC-002.10), all `in_review`;
  PRB-080 1.2 Resolution with evidence (stays `open`).
- **Observation, not changed.** When the commit of the SUCCESS rows fails (case (b)), or the response
  cannot be built, the `_verified()` generator is never iterated, so its `finally: chunks.close()` does
  not run and the pass-2 object stream is released only by garbage collection. The same holds on HEAD
  for a failure between `open_stream` and the first iteration. A candidate for a separate PRB; out of
  this task's scope.

## QA review round 1 (qa-engineer, 2026-11-13) — APPROVED

Verdict: **APPROVED**, no CRITICAL, HIGH or MEDIUM finding; 5 LOW findings (non-blocking, for the
orchestrator to schedule) and one pre-existing issue.

Checked independently:

- **Scope inventory.** `git grep "Depends(get_db)" HEAD -- backend/app` gives 30 sites in 14 files; the working
  tree has 30 `db: DbSession` in the same 14 files and no `Depends(get_db)` left in `backend/app` or
  `backend/modules` outside tests. The remaining `get_db` callers are the Celery tasks (`next(get_db())`, not
  FastAPI dependencies). The DICOM router (`modules/dicom_viewer/dicom_viewer/router.py:53-54`) reaches `get_db`
  only through `get_current_user` and `get_platform_services`, both `DbSession`, so one cache key and one
  session; the scope walk covers it through its separate module app. Mutation: one site of
  `api/routers/me.py` back to plain `Depends(get_db)` (scratch copy) makes
  `test_every_route_resolves_get_db_with_function_scope` fail with "scope 'request'" and "two sessions".
- **Post-teardown hazards.** In FastAPI 0.138 the endpoint result is serialised inside `f(request)`, i.e. inside
  the `function_stack` (`fastapi/routing.py:134-136`, `serialize_response` at 711), so every response model built
  from ORM objects is serialised before the commit and `expire_on_commit`. The only response whose body is produced
  after the teardown is `StreamingResponse` in `api/routers/attachments.py:109`; no route uses `BackgroundTasks`,
  `FileResponse` or another generator (the DICOM route returns `Response(content=bytes)`; no export streams).
  The pass-2 FAILURE row written from the generator keeps the client address (probe: all three rows carry
  `203.0.113.9`).
- **Fails on HEAD behaviour, reproduced** in a scratch copy: alias set to plain `Depends(get_db)` gives 7 of 8 new
  tests failing (only the default-scope negative control passes); `open_stream` restored from HEAD with the fixed
  alias gives `DetachedInstanceError` in download cases (a) and (c).
- **OpenAPI:** export from HEAD (`git archive`) and from the working tree are byte-identical, and equal to
  `backend/openapi/openapi.json`.
- **Adjusted tests:** the four overrides only change `db: Session = Depends(get_db)` to `db: DbSession` (and drop
  the now-unused imports); no assertion changed. Without the change each would build a second, request-scoped
  session next to the function-scoped one, so the change is required to keep them on the production shape.
- Records: TS-007 TC-007.14/.15, TS-009 TC-009.13, TS-002 TC-002.10 match the tests; PRB-080 Resolution matches the
  evidence; ADR-0023 is Accepted (CR-006 D-28). `traceability-check` (scope 198 records, one hop): 0 errors.

Findings:

1. **[LOW] Unstarted download generator leaks the pass-2 stream until garbage collection** —
   `backend/app/attachments/service.py:206-232`, `backend/app/api/routers/attachments.py:104-121`. When the commit of
   the SUCCESS rows fails (case (b), newly reachable with `scope="function"`) or the `StreamingResponse` cannot be
   built (pre-existing since TASK-217), `_verified()` is never started, so its `finally: chunks.close()` never runs
   (closing an unstarted generator does not execute its `finally`); the storage response is released only when its
   last reference goes. No data or audit effect; transient storage-connection use. → Raise a separate PRB
   (minor, resource handling, SR-013 AC 6 context): the fix needs a closer that does not depend on the generator
   having started (for example an iterator object whose `close()` closes the storage stream, closed by the route on
   its error path and registered on the request's function-scope exit stack for the commit-failure path).
2. **[LOW] TC-002.10 overstates its evidence** — `TS-002` TC-002.10: "observed in TC-007.14 for every write route";
   TC-007.14 observes the order for two routes, and it is the scope walk that proves every route uses the same
   mechanism. Coverage of SR-008 AC 4 is acceptable (uniform mechanism + TC-002.1 to .9 for the denial), but → say
   "the scope walk of TC-007.14 shows every route commits the same way", or add the consent revoke to
   `test_success_response_is_sent_after_commit` (assert `commit` before `response_start` for `DELETE /consents/{id}`).
3. **[LOW] `monkeypatch.undo()` in the middle of a test** — `backend/tests/attachments/test_download_audit_order.py`
   (`test_failed_commit_of_the_success_row_serves_no_byte`): undoes every patch of the test, including the `world`
   fixture's `get_engine`, `CHUNK` and `ObjectStorageClient`; it works only because the remaining code uses the owner
   engine. → Use `pytest.MonkeyPatch.context()` for the `Session.commit` patch, as `failing_commit()` does.
4. **[LOW] TC-009.8 planted route not on the production shape** —
   `backend/tests/audit/test_failure_audit_persistence.py:248` still declares `db: Session = Depends(get_db)` (request
   scope). The rollback it tests behaves the same in both scopes, but → use `db: DbSession` so the test exercises the
   shape ADR-0023 mandates.
5. **[LOW] Record drift** — this record's header says "ADR-0023 (Proposed)" (Accepted at CR-006 D-28); CR-006 scope
   row of PRB-080 says "31 `Depends(get_db)` sites in 15 files" (HEAD has 30 in 14). → Correct both at the next
   edit of these records (TASK-225 or the CR close-out).

Pre-existing (not blocking): `ruff format --check` reports 3 files untouched by this task
(`tests/api/test_openapi_contract.py`, `tests/auth/test_session_service.py`, `tests/test_env_example.py`).

Verification run: backend `uv run pytest -q --cov=app` 1653 passed, 10 skipped, coverage 94.81 %;
`modules/dicom_viewer/tests` 31 passed; `ruff check` clean; `mypy app` clean (135 files);
`python3 -m unittest discover -s infra/tests` 178 OK; OpenAPI byte-identical; traceability 0 errors.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (D-27).
- 1.1 (2026-11-13) — Build stage (Software Developer): implementation record, `draft → in_review`. QA review round 1:
  APPROVED (5 LOW, see "QA review round 1"); checkboxes ticked; `in_review → approved`. PRB-080 set `resolved`.
- 1.2 (2026-11-14) — TASK-225 (QA finding 5 of round 1): the header names ADR-0023 as Accepted (CR-006 D-28), not "Proposed". Wording only. Content change on an approved record, so the 1.1 approval record is cleared and the record returns to review.
- 1.2 (2026-11-15) — QA review (TASK-225 round 2): `approved` (status only; the 1.2 change against the previous approved version is wording only).
