---
id: TS-018
type: test-specification
title: Performance budgets and data-access cost verification
status: in_review
version: "1.10"
author: Carlos Santiago Liceras
created: "2026-11-13"
updated: "2026-11-16"
links:
  - target: SR-026
    relation: verifies
tags:
  - level:unit
  - level:integration
  - level:system
  - class:B
  - cr:CR-006
---

# TS-018 — Performance budgets and data-access cost verification

## Scope

Software requirement covered: SR-026. This version holds the test cases for **SR-026 AC 5**
(20 concurrent clients on one API worker: no 5xx, the AC 1 and AC 2 budgets hold, a slow call does not
delay unrelated requests) and the part of **AC 1 and AC 2** that the same load test measures
(TC-018.3) (TASK-136), and the index-served lookups and the one-row activation of **SR-026 AC 6**
(TC-018.5, TC-018.6) (TASK-219), the group listing and the two remaining lookup indexes (TC-018.7, TC-018.8) (TASK-220), **AC 8** (TC-018.9) (TASK-222) and **AC 7** (TC-018.10) (TASK-145). The remaining acceptance criteria are added by the tasks that implement them and are not
yet mapped, so this specification is incomplete for SR-026 until then:

| SR-026 AC | Task that adds its test cases |
|---|---|
| AC 3 (DICOM first image within 10 s) | TASK-226 (TC-018.11: not executable, PRB-048 and PRB-046) |
| AC 4 (budgets verified by performance tests) | TASK-226 (TC-018.12) |

Software items under test: SI-API `U-API-Deps`, `api/routers/auth.py` and the lifespan (ADD-005);
SI-PERSIST engine (ADD-016); the Redis client of `api/deps.py` (SI-AUTH, ADD-006, no behaviour change).
SI-PERSIST migrations 0011 and 0012 and SI-IDENTITY activation (ADD-016, SOUP-009 PostgreSQL); SI-GROUPS `groups_of` (ADD-009); SI-FE-SHELL `app/App.tsx` and `scripts/check-bundle-budget.mjs` (ADD-018). Levels: unit (TC-018.1, TC-018.4, TC-018.9, TC-018.10), integration through the ASGI app (TC-018.2), integration against PostgreSQL (TC-018.5 to TC-018.8) and system (TC-018.3).

## Preconditions and environment

Branch `fix/review-2026-07-reliability`. Backend Python 3.12 with the dependencies locked in
`backend/uv.lock`; Starlette 1.3.1 and anyio 4.14.2 (SOUP-003), SQLAlchemy `QueuePool` (SOUP-008),
redis-py (SOUP-013). TC-018.1, TC-018.2 and TC-018.4 need no database, Redis or object store (the
session service and the database dependency are stubbed). TC-018.5 to TC-018.8 need Docker (a PostgreSQL container of the project image, `backend/tests/postgres_image.py`). TC-018.3 needs a started stack
(`infra/docker-compose.yml`, one Gunicorn worker) with the load-test accounts seeded, and a host that
has the same CPU for every compared run; the data set grows with every run (see TASK-136), so only
runs made in sequence on one stack are comparable in throughput.

## Test cases

| ID | Verifies (SR / AC) | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-018.1 | SR-026 AC 5 (NFR-008) | `backend/tests/api/test_no_blocking_in_async.py`: `test_no_async_def_calls_blocking_client`, `test_the_scan_covers_the_async_handlers_it_is_meant_to_guard`, `test_planted_blocking_call_in_async_def_is_found` (four planted shapes: session service, SQLAlchemy `execute`, Redis `setex`, object store `put_object`), `test_the_sanctioned_shapes_are_not_flagged`. Negative control: run against the pre-TASK-136 `app/api` | No `async def` under `app/api` calls a blocking client or service method on the event loop; the scan sees the async functions that exist; each planted shape is found; a plain `def`, `run_in_threadpool(svc.store, ...)` and an awaited call are not flagged | All listed tests pass; on `8028685` the first test fails and names seven calls (`get_session`, `get_current_user`, `_dependency`, `upload_attachment`, `logout` twice, `extend_session`) |
| TC-018.2 | SR-026 AC 5 | `backend/tests/api/test_no_blocking_in_async.py::test_slow_db_call_does_not_block_unrelated_request` (the session lookup is patched to sleep 2 s while a concurrent `GET /healthz` is timed from the moment it was due). Negative control: same test on `8028685` | With a dependency call blocked for 2 s, an unrelated request completes in under 200 ms | The test passes; on `8028685` it fails with `/healthz waited 1.73 s` |
| TC-018.3 | SR-026 AC 5, AC 1, AC 2 | `backend/scripts/load_test.py` (seed, then run): 20 clients, 5 min, mix of `GET /me`, list appointments, list clinical entries, create clinical entry, 1 MiB upload and download, plus a 10 Hz `GET /healthz` probe; started stack, one worker. Results and the before/after table: TASK-136 "Load test". The final run with the approved pool values is TASK-226 | No 5xx and no transport error; no gunicorn `WORKER TIMEOUT` and no `QueuePool limit` line in the server log; p95 of every routine operation within 3 s (AC 1) and of the clinical-entry create within 3 s (AC 2, upload time excluded) | **Executed 2026-11-15 (TASK-226), PASS.** Branch head `0130394`, project `medhub-verify` (empty database, migrations 0001 to 0012, test accounts only), through the reverse proxy (`https://127.0.0.1:18443`, `--insecure`), one Gunicorn worker, pools as deployed (`API_THREADPOOL_SIZE=20`, `DB_POOL_SIZE=20`, `DB_MAX_OVERFLOW=20`, `DB_POOL_TIMEOUT=10`), 20 clients, 300 s: 29 601 requests, **0 × 5xx, 0 transport errors**, 0 `WORKER TIMEOUT` and 0 `QueuePool limit` lines **in the captured backend log, which was empty (0 bytes: `docker logs --since` returned nothing), so these counts rest on the client side, the 0 × 5xx and 0 transport errors, and not on the server log**; p95 (s): GET /me 0.281, list appointments 0.332, list clinical entries 0.370, create clinical entry 0.371, 1 MiB upload 1.009, download 1.051, `/healthz` probe 0.116; slowest single request 5.04 s (an upload, excluded from AC 2). Before (`8028685`, TASK-136 step 1, backend port, no proxy): 456 requests, 210 transport errors, 10 worker kills, p95 about 2.2 s for the answered requests. Evidence: TASK-226 "Implementation record". Earlier TASK-136 evidence: 0 × 5xx, 0 transport errors, 0 worker timeouts, every p95 under 1.2 s, on four pool configurations; the pre-TASK-136 build fails the same test (210 transport errors, 10 worker kills) |
| TC-018.4 | SR-026 AC 5 (ADR-0022) | `backend/tests/core/test_pool_settings.py`: `test_startup_refuses_threadpool_larger_than_db_pool`, `test_lifespan_refuses_to_start_with_threads_over_connections`, `test_threads_equal_to_connections_is_accepted`, `test_non_positive_pool_values_are_refused`, `test_defaults_satisfy_the_invariant`, `test_lifespan_applies_the_thread_limit`, `test_engine_pool_follows_the_settings`, `test_redis_pool_is_bounded_by_the_thread_limit` | Settings with more threads than `DB_POOL_SIZE + DB_MAX_OVERFLOW` (the 40 against 15 of PRB-072) are refused, also at lifespan start; the lifespan sets anyio's thread limiter; the engine and the Redis client are built with the configured sizes, one client per process | All listed tests pass |
| TC-018.5 | SR-026 AC 6 (PRB-021) | `backend/tests/db/test_migration_0011_indexes.py`: `test_upgrade_downgrade_0011_empty_and_populated`, `test_authorization_lookups_use_index`, `test_without_the_indexes_the_same_lookups_scan` (negative control) | Migration 0011 upgrades and downgrades on an empty database and on one with 10 000 rows in each of `appointment`, `consent_grant`, `clinical_entry`, `attachment`, creating and dropping `ix_appointment_scheduled_at`, `ix_consent_grant_appointment_id`, `ix_clinical_entry_patient_id`, `ix_attachment_patient_id` with row counts unchanged; after `ANALYZE` with `enable_seqscan` on, `EXPLAIN` of the lookup by patient (clinical entries, attachments), by a one-hour appointment-time window and by consent appointment names the new index and has no `Seq Scan`; at revision 0010 the clinical-entry lookup is a `Seq Scan` | All listed tests pass; `test_migration.py` (no ORM/migration drift) still passes |
| TC-018.6 | SR-026 AC 6 (PRB-022 regression) | `backend/tests/identity/test_activation_one_row.py::test_activation_reads_one_account_row`. Negative control: `AccountRepository.get_by_id` replaced by a `list()` scan fails with `assert 1001 == 1` | `ActivationService.activate` against PostgreSQL with 1 and with 1 001 accounts issues the same number of statements on `account` and fetches exactly one account row | The test passes |
| TC-018.7 | SR-026 AC 6 (PRB-024) | `backend/tests/groups/test_groups_of.py::test_groups_of_query_count_constant` (the PRB-024 case) and `::test_module_gate_query_count_constant` (the module-gating case: `ModuleAccessGuard.is_module_enabled` and the two repository calls of `GET /me/modules`) (`before_cursor_execute` counter; identity map expired before each count). Negative control: the same test on `c69d7dc` (`groups_of` calling `GroupRepository.get` per membership) | `GroupService.groups_of`, `ModuleAccessGuard.is_module_enabled` and the `/me/modules` repository pair each issue the same number of statements for an account with 1, 10 and 100 memberships; the returned set is unchanged (characterisation in TC-005.4) | The tests pass; on `c69d7dc` the `groups_of` test fails with `{1: 3, 10: 12, 100: 102}`; with an N+1 planted in the guard the module-gating test fails with `{1: 4, 10: 13, 100: 103}` (`groups_of` has no caller; module gating already used a constant 3 queries) |
| TC-018.8 | SR-026 AC 6 (PRB-021, CR-006 D-29) | `backend/tests/db/test_migration_0012_indexes.py`: `test_upgrade_downgrade_0012_empty_and_populated`, `test_remaining_lookups_use_index`, `test_without_the_0012_indexes_the_same_lookups_scan` (negative control), `test_orm_drift_at_head_and_at_0011` | Migration 0012 upgrades and downgrades on an empty database and on one with 10 000 attachments, 10 000 consent grants (50 doctors, a quarter revoked) and 10 000 patient accounts, creating and dropping `ix_attachment_clinical_entry_id` and `ix_consent_grant_doctor_id_active` with row counts unchanged; after `ANALYZE` with `enable_seqscan` on, `EXPLAIN` of `AttachmentRepository.list_for_clinical_entry` and `ConsentRepository.list_patients_for_doctor` (statements captured from the repositories) names the new index and has no `Seq Scan` on `attachment` or `consent_grant` (`account` may be seq-scanned: at 10 000 accounts the planner hash-joins about 150 rows, at 210 000 it uses `account_pkey`, so the assertion is limited to those two tables); at revision 0011 both are a `Seq Scan` on their table; ORM metadata and migrations agree at head and differ at 0011 by exactly the two `add_index` diffs | All listed tests pass; `test_migration.py` still passes |
| TC-018.9 | SR-026 AC 8 (PRB-025, TASK-222) | `frontend/src/auth/useIdleTimer.test.ts`: `no listeners registered for activity events` (`window.addEventListener` is called for none of `mousemove`, `keydown`, `click`, `touchstart`, `scroll`), `activity events do not move the deadline` (the five events dispatched at 10 minutes of a 15-minute deadline; warning and expiry still fire at the reported time minus 2 minutes and at the reported time). Negative control: one activity listener that re-arms the timers | User input events (mouse, keyboard, touch, scroll) cause no session-timer work (SR-026 AC 8 as reworded in 1.7, CR-006 D-36): no listener is registered for them, and dispatching them neither re-arms nor extends the deadline or the warning | Both tests pass; with a re-arming `mousemove`/`keydown` listener added both fail (the second also fails `reading without requests is warned at 13 min and signed out at 15 min` in `SessionActivityProvider.test.tsx`, TC-001.13) |
| TC-018.10 | SR-026 AC 7 (PRB-020, TASK-145) | `frontend/scripts/check-bundle-budget.test.mjs`: `counts the entry chunk and its static imports, not the lazy chunks`, `fails when the initial payload is over the budget`, `fails when a lazy chunk is pulled into the static graph`, `the budget is the approved 165 kB gzip`, and on a real `vite build` (production mode, temporary output): `landing route does not import admin pages or any other lazy page`, `admin pages share one chunk`, `initial JavaScript is within 165 kB gzip`, `a lazy page imported eagerly fails the check` (real build with `PatientListPage` imported statically, which Rollup merges into the entry chunk); synthetic cases also cover a lazy group missing as a chunk, a group's modules inside the entry chunk, and `--clean` removing `dist/.vite` after a pass only; `frontend/src/app/App.lazy.test.tsx`: `an unauthenticated deep link loads no page chunk`, `landing route does not import the other pages`, `a lazy page is requested on first navigation and renders`. `npm run build` runs the same check (`scripts/check-bundle-budget.mjs --clean`) after `vite build`: it requires each lazy group (change-password, patients, clinical, appointments, consent, admin) to be its own dynamic chunk with none of its modules in the initial chunks, then removes `dist/.vite` (manifest, chunk-module list) so it is not published. Negative control: `App.tsx` with static page imports | Initial JavaScript (entry chunk plus its static imports, from the Vite manifest) is at most 165 kB gzip (1 kB = 1000 bytes, zlib default level); each of the change-password page, patients, clinical, appointments, consent and the admin pages (one chunk) is its own dynamic chunk outside that graph; a page chunk is requested only after sign-in succeeded and the route was navigated to | All listed tests pass and `npm run build` ends with "within the budget": 160.06 kB gzip (504.51 kB raw) against 172.68 kB gzip (558.87 kB raw) before; with static imports the build measures 173.00 kB gzip, the budget test and all three `App.lazy` tests fail; with only `PatientListPage` imported statically the size stays under budget (160.4 kB) and the lazy-group check is what fails |
| TC-018.11 | SR-026 AC 3 | System level: open a typical DICOM study in the viewer on a started stack and time the first rendered image | The first image is rendered within 10 s | **Not executed (2026-11-15, TASK-226): not possible.** The started stack has no `dicom_viewer` package and no `medhub.modules` entry point, so the viewer route is not mounted (PRB-048), and NumPy is not installed, so a pixel decode cannot succeed (PRB-046). No real render and no timing exist; AC 3 stays unverified until both problems are resolved. TS-019 TC-019.4 covers the bounds at the 150 MiB / 1 GiB limit with the decode stubbed |
| TC-018.12 | SR-026 AC 4 | TC-018.3 (AC 1, AC 2, AC 5 under load), TC-018.10 (AC 7, `npm run build` 2026-11-15: 160.06 kB gzip of 165) and TC-018.5 to TC-018.8 (AC 6) | The budgets of AC 1, AC 2, AC 5, AC 6 and AC 7 are each verified by a performance or system test that was executed | **PASS for AC 1, 2, 5, 6, 7 (2026-11-15, TASK-226); AC 3 not executable (TC-018.11); AC 8 by unit test TC-018.9** |

TS-001 and TS-002 (authorization and session decisions, RISK-001 and RISK-005) run unchanged as the guard
for this task: the dependencies changed from `async def` to `def`, their decisions did not.

## Acceptance criteria (class B unit level)

Unit acceptance (§5.5.3): the invariant check is a pure function of the four settings and is applied when
`Settings` is built, so no start-up path (API lifespan, worker, migration job) can use a pair that
violates it; the thread limit is set once per process in the lifespan; the Redis pool size equals the
thread limit, so a worker thread never finds the pool empty.

## Verification results

2026-11-15, TASK-226 (branch head `0130394`): the final load run (TC-018.3), the build budget (TC-018.10: 160.44 kB gzip in the production image build on Node 24.22.2, budget 165; 160.06 kB on the host's Node 18.17.1) and the full backend and frontend suites, all green; AC 3 not executable (TC-018.11). Details in TASK-226 "Implementation record".

Earlier: see TASK-136 "Implementation record" (2026-11-13): backend suite, ruff, mypy, the load-test table for the
pre-TASK-136 build and the working tree, and the two infra tests, green since the pool values were approved
(CR-006 D-24) and wired in `infra/`.

## Version history

- 1.0 (2026-11-13): TASK-136. Created for SR-026 AC 5 (TC-018.1 to TC-018.4); AC 3, 4, 6, 7, 8 are added by
  TASK-226, TASK-219, TASK-220, TASK-145 and TASK-222. `in_review`.
- 1.1 (2026-11-13): Pool values approved (CR-006 D-24); verification note updated. `in_review`.
- 1.1 (2026-11-13): QA review of TASK-136 (round 1): `approved` (status only; content unchanged).
- 1.2 (2026-11-13): TASK-219. Added TC-018.5 (indexes of migration 0011) and TC-018.6 (activation reads one account row) for SR-026 AC 6; AC 6 group listing stays with TASK-220. Content change, so the approval record is removed. `in_review`.
- 1.2 (2026-11-13): QA review of TASK-219 (round 1): `approved` (status only; content unchanged).
- 1.3 (2026-11-14): TASK-220. Added TC-018.7 (`groups_of` constant query count) and TC-018.8 (migration 0012 indexes) for SR-026 AC 6; the AC 6 row is removed from the pending table. Content change, so the approval record is removed. `in_review`.
- 1.3 (2026-11-14, round 2): TC-018.7 adds the module-gating case; TC-018.8 explains why `account` may be scanned. Still `in_review`.
- 1.3 (2026-11-14): QA review of TASK-220 (round 2): `approved` (status only; content unchanged).
- 1.4 (2026-11-14): TASK-222. Added TC-018.9 (no activity listener, no timer work, SR-026 AC 8); the AC 8 row is removed from the pending table. Content change, so the 1.3 approval record was removed and the status returned to `in_review`; the human approved 1.4 afterwards (corrected in 1.7).
- 1.5 (2026-11-14): TASK-145. Added TC-018.10 (initial JavaScript within 165 kB gzip, lazy route chunks, SR-026 AC 7); the AC 7 row is removed from the pending table. The task text named TC-018.8, which TASK-220 had already used. Content change, so the approval record is removed. `in_review`.
- 1.5 (2026-11-14): QA review of TASK-145 (round 1): `approved` (status only; content unchanged).
- 1.6 (2026-11-14): TASK-145 QA round 1 fixes. TC-018.10: lazy-group check (a page made eager is merged into the entry chunk and no longer a chunk of its own), real-build negative control, manifest removed after the check. Content change, so the approval record is removed. `in_review`.
- 1.6 (2026-11-14): QA review of TASK-145 (round 2): `approved` (status only; content unchanged).
- 1.7 (2026-11-14): TASK-225 correction of the 1.4 line. It said "no approval record on the file", which was true when written but is not the history: the 1.3 approval record was removed by the TASK-222 change and the human approved 1.4 afterwards (the 1.5 line removes that approval record in turn). Wording of the history only. Content change on an approved record, so the 1.6 approval record is removed. `in_review`.
- 1.7 (2026-11-15): QA review of TASK-225 (round 2): `approved` (status only; content unchanged).
- 1.8 (2026-11-15): TASK-226. TC-018.3 result recorded (final run, approved pools, through the proxy: 0 × 5xx, p95 at most 1.05 s); TC-018.11 (SR-026 AC 3, not executable: PRB-048, PRB-046) and TC-018.12 (SR-026 AC 4) added; pending table updated. Content change on an approved record, so the approval record is cleared: `in_review`.
- 1.9 (2026-11-15): TASK-226 round 2 (QA L-1, L-4). AC 7 evidence is the production image build, 160.44 kB; TC-018.3 states that the backend log capture was empty. Still `in_review`.
- 1.9 (2026-11-15): QA review of TASK-226 (round 2): `approved` (status only; content unchanged).
- 1.10 (2026-11-16): CR-006 D-36 (human decision on P-20). TC-018.9 expected result follows the reworded SR-026 AC 8 ("user input events cause no session-timer work"); the note that the wording was left to the human is removed. Same tests, same pass criteria. Content change on an approved record, so the approval is cleared: `in_review`.
