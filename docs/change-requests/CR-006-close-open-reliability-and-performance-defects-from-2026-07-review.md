---
id: CR-006
type: change-request
title: Close the open reliability and performance defects from the 2026-07 review and audit
status: in_progress
version: "1.14"
author: Carlos Santiago Liceras
created: "2026-11-13"
updated: "2026-11-14"
branch: fix/review-2026-07-reliability
risk_impact: affects_controls
links:
  - target: PRB-006
    relation: resolves
  - target: PRB-008
    relation: resolves
  - target: PRB-009
    relation: resolves
  - target: PRB-012
    relation: resolves
  - target: PRB-013
    relation: resolves
  - target: PRB-015
    relation: resolves
  - target: PRB-016
    relation: resolves
  - target: PRB-017
    relation: resolves
  - target: PRB-019
    relation: resolves
  - target: PRB-020
    relation: resolves
  - target: PRB-021
    relation: resolves
  - target: PRB-022
    relation: resolves
  - target: PRB-024
    relation: resolves
  - target: PRB-025
    relation: resolves
  - target: PRB-030
    relation: resolves
  - target: PRB-031
    relation: resolves
  - target: PRB-032
    relation: resolves
  - target: PRB-078
    relation: resolves
  - target: PRB-079
    relation: relates_to
  - target: PRB-080
    relation: resolves
  - target: PRB-081
    relation: relates_to
  - target: PRB-072
    relation: resolves
  - target: PRB-083
    relation: resolves
  - target: PRB-084
    relation: resolves
  - target: PRB-087
    relation: resolves
  - target: PRB-089
    relation: resolves
  - target: PRB-090
    relation: resolves
  - target: SR-008
    relation: relates_to
  - target: SR-012
    relation: relates_to
  - target: SR-013
    relation: relates_to
  - target: SR-014
    relation: relates_to
  - target: SR-015
    relation: relates_to
  - target: SR-016
    relation: relates_to
  - target: SR-017
    relation: relates_to
  - target: SR-023
    relation: relates_to
  - target: SR-024
    relation: relates_to
  - target: SR-026
    relation: relates_to
  - target: SR-027
    relation: relates_to
  - target: SR-030
    relation: relates_to
  - target: SR-031
    relation: relates_to
  - target: SR-033
    relation: relates_to
  - target: SR-034
    relation: relates_to
  - target: SR-035
    relation: relates_to
  - target: NFR-006
    relation: relates_to
  - target: NFR-008
    relation: relates_to
  - target: RISK-001
    relation: relates_to
  - target: RISK-003
    relation: relates_to
  - target: RISK-004
    relation: relates_to
  - target: RISK-005
    relation: relates_to
  - target: RISK-006
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: RISK-008
    relation: relates_to
  - target: RISK-009
    relation: relates_to
  - target: RISK-012
    relation: relates_to
  - target: TASK-135
    relation: relates_to
  - target: TASK-136
    relation: relates_to
  - target: TASK-141
    relation: relates_to
  - target: TASK-143
    relation: relates_to
  - target: TASK-144
    relation: relates_to
  - target: TASK-145
    relation: relates_to
  - target: TASK-146
    relation: relates_to
  - target: TASK-207
    relation: relates_to
  - target: TASK-217
    relation: relates_to
  - target: TASK-218
    relation: relates_to
  - target: TASK-219
    relation: relates_to
  - target: TASK-220
    relation: relates_to
  - target: TASK-221
    relation: relates_to
  - target: TASK-222
    relation: relates_to
  - target: TASK-223
    relation: relates_to
  - target: TASK-224
    relation: relates_to
  - target: TASK-225
    relation: relates_to
  - target: TASK-226
    relation: relates_to
  - target: TASK-227
    relation: relates_to
  - target: TASK-228
    relation: relates_to
  - target: SOUP-019
    relation: relates_to
  - target: SOUP-036
    relation: relates_to
  - target: CR-004
    relation: relates_to
  - target: CR-005
    relation: relates_to
tags:
  - reliability
  - performance
  - issue:sancharly/medhub#28
---

## Reason

The 2026-07 code review (`docs/reports/CODE-REVIEW-2026-07.md`) and the audit
(`docs/implementation-plan/AUDIT-FINDINGS.md`) left seventeen reliability, performance and
test-coverage problem reports open. None is `critical`. Sixteen are defects that make the MVP miss
the SR-026 performance budgets or weaken a control that RISK-003, RISK-004, RISK-005, RISK-007,
RISK-008 or RISK-009 relies on; one (PRB-017) is a verification gap against the class B
unit-verification expectation (IEC 62304 §5.5). Verification on 2026-11-13 found two of them already
fixed (PRB-022, PRB-031) and two partly fixed (PRB-013, PRB-017), see "Scope":

- **Memory and event loop (RISK-007, RISK-003):** attachment upload and download hold the whole
  object in memory and enforce the size limit afterwards (PRB-008), the DICOM frame endpoint decodes
  any object with no size bound (PRB-006), and `async` dependencies perform synchronous IO on the
  event loop of every authenticated request (PRB-009).
- **Data-access cost (RISK-007):** four authorization lookups have no index (PRB-021), one path
  scans a whole table (PRB-022) and group membership issues one query per row (PRB-024).
- **Workers (RISK-007, RISK-008, RISK-009):** the retention sweep leaks a session per failing
  dataset and never retries (PRB-012); an enqueue failure was swallowed without a log (PRB-013).
- **Frontend (RISK-004, RISK-005):** the module list is never invalidated (PRB-015), the `me` query
  is issued from nine places with a hard-coded session TTL (PRB-016), upload bypasses the shared
  request helper (PRB-019), the bundle is not split (PRB-020), the idle timer is not debounced
  (PRB-025); the destructive dialog focus (PRB-031) was fixed meanwhile.
- **Verification (RISK-006, RISK-005):** security-relevant frontend units have no unit tests
  (PRB-017), the module boundary test is too narrow (PRB-030) and the JSON logger promises a
  request id it does not emit (PRB-032).

One CR bundles them because they come from the same review, share the same records (SR-026,
RISK-007) and one verification run (backend and frontend suites, a started stack and
`traceability-check`). Several share code: PRB-008 and PRB-009 both touch the attachment router;
PRB-015, PRB-016 and PRB-017 are in the same frontend session and gating units; PRB-021, PRB-022
and PRB-024 are one query-cost theme. This CR does not duplicate CR-004 (security, closed) or
CR-005 (build and deployment, closed).

Source: GitHub issue sancharly/medhub#28.

## Scope

### In scope

Each PRB, its state on the current branch (verified 2026-11-13 against the code), the requirement
its fix restores and its TASK. "New" marks a requirement criterion drafted in this CR (the SR is
back in `in_review`, see "Requirements decision"). TASKs marked "new at Plan stage" are created by
the architect. Line numbers are those found on 2026-11-13.

| PRB | Crit. | State on this branch (evidence) | Requirement restored (AC) | TASK |
|---|---|---|---|---|
| PRB-006 DICOM frame endpoint has no size or decode bound | major | Still open: `backend/modules/dicom_viewer/dicom_viewer/dicom.py:27-28` calls `dcmread` and `pixel_array` with no limit | **SR-017 AC 6 (new)**; SR-026 AC 3; RISK-007, RISK-003 | New at Plan stage (or folded into TASK-135, see Q-2) |
| PRB-008 Attachment upload and download buffer the whole object | major | Still open: `api/routers/attachments.py:62` `await file.read()`; `attachments/service.py:69-74` checks `len(data)` afterwards; `service.py:158` loads the whole object on download | **SR-013 AC 6 (new)**, AC 5 must still hold (Q-6); SR-026 AC 5 (new) | TASK-135 |
| PRB-009 Async handlers perform sync IO on the event loop | major | Still open: `api/deps.py:43,70,138` and `api/routers/attachments.py:49` are `async def` over sync Redis, SQLAlchemy and boto3 (the PRB's `:126,198` sites no longer exist) | **SR-026 AC 5 (new)**; NFR-008 | TASK-136 |
| PRB-012 Retention sweep leaks sessions and never retries | major | Still open: `workers/retention_tasks.py:92` reassigns `db = next(get_db())` without closing the previous one; `:22-26` declares `max_retries=3` with no `autoretry_for` and no `self.retry()` | **SR-024 AC 5 (new)**; RISK-007, RISK-008 | TASK-141 |
| PRB-013 Task enqueue failures are swallowed without a log | major | **Partly fixed** by TASK-207: all three sites now log one WARNING (`identity/lifecycle.py:73-76`, `appointments/service.py:73-75`, and `identity/erasure.py:141-142`, which PRB-013 1.1 still lists as unlogged). Remaining: surfacing beyond a log line, failing the request where the side effect is security-relevant (Q-5) | SR-035 AC 2, AC 3; SR-034 AC 2 (30 s session kill); SR-024 AC 1 (erasure code e-mail); no new AC unless Q-5 decides to fail the request | TASK-141 (narrowed) |
| PRB-015 Module list query never invalidated | major | Still open: `core/clinical/AttachmentItem.tsx:18-19` reads `["myModules"]`; no other reference to that key exists, so nothing invalidates it | **SR-015 AC 5 (new)**; RISK-004 | TASK-144 |
| PRB-016 `me` query from nine places; hard-coded session TTL | major | Still open: `auth/SessionActivityProvider.tsx:18-20` seeds `Date.now() + 15 * 60 * 1000`; `["me"]` is read in ten non-test files (`RequireAuth`, `RequireRole`, `ForcedPasswordGate`, `ChangePasswordPage`, `useLogin`, `ProfilePage`, `AccountsPage`, `AppointmentsPage`, `App`, `SessionActivityProvider`). The server already reports `expires_at` (`api/schemas/auth.py:49`) | **SR-030 AC 8 (new)**; SR-030 AC 1, AC 2, AC 4; RISK-005 | TASK-144 |
| PRB-017 Security-relevant frontend units have no unit tests | major | **Partly fixed**: `core/clinical/AttachmentUpload.test.tsx` now exists (TASK-206). Still without a test file: `SessionActivityProvider`, `AttachmentItem`; `api/csrf.ts` has no dedicated test (`client.test.ts` touches the CSRF cookie only as a fixture) | NFR-006 AC 3, AC 4 and IEC 62304 §5.5 (class B unit verification); SR-030 AC 1 to AC 4, SR-015 AC 3 and AC 4, SR-031 AC 3 | TASK-146 (narrowed to the three remaining units) |
| PRB-019 Upload bypasses the request helper; `ProblemError` hand-written in a generated file | minor | Still open: `api/client.ts:136-160` own `fetch` with no 401 handling; `api/generated/types.ts:17` exports `ProblemError` | SR-031 (error contract); SR-027 AC 3 (clear failure message); SR-030 (401 ends the session) | TASK-143 |
| PRB-020 No route-level code splitting | minor | Still open: no `lazy(` or `Suspense` anywhere in `frontend/src` | **SR-026 AC 7 (new)**; SR-020 | TASK-145 |
| PRB-021 Authorization lookups have no supporting indexes | major | Still open: no index on `appointment.scheduled_at`, `consent_grant.appointment_id`, `clinical_entry.patient_id` or `attachment.patient_id` in the models (`db/models/{appointment,consent,clinical,attachment}.py`) or in migrations 0001 to 0010 | **SR-026 AC 6 (new)**; RISK-007 | TASK-219 (migration 0011); TASK-220 (migration 0012, D-29: the two lookups the code issues that 0011 left unindexed) |
| PRB-022 Activation token validation scans the account table | major | **Already fixed**: `identity/activation.py:67` loads one row with `get_by_id(account_id)` and `_validate_token` (`:162-168`) checks only that row; no `list()` scan remains in `app/identity/` for activation (last change 2026-10-31, TASK-188 / PRB-070 route change). See Q-1 | SR-026 AC 6 (new, kept as the regression guard); SR-033 | None: PRB-022 `rejected` (D-1); SR-026 AC 6 gets a regression test |
| PRB-024 Group membership N+1 query | minor | Still open: `groups/service.py:131-138` `groups_of` calls `self._group_repo.get(m.group_id)` per membership | **SR-026 AC 6 (new)**; SR-014 AC 4 | New at Plan stage |
| PRB-025 Idle timer resets on every mouse and scroll event | minor | Still open: `auth/useIdleTimer.ts` registers `resetDeadline` directly on each activity event; no debounce or throttle | **SR-026 AC 8 (new)**; SR-030 AC 1 to AC 4 (timings unchanged) | New at Plan stage |
| PRB-030 Module boundary test denies only two import substrings | minor | Still open: `backend/tests/modules/test_module_boundary.py:9-12` lists `app.db` and `app.core.object_storage` only | SR-016 AC 3 (a module obtains data only through the platform's authorized interfaces) | New at Plan stage |
| PRB-031 Destructive dialog focuses Confirm instead of Cancel | minor | **Already fixed**: `core/confirm/ConfirmDialog.tsx:46,51` focus Cancel when `destructive`, and `ConfirmDialog.test.tsx:120` asserts it (fixed by the phase-6 audit remediations, commit 24240f8). See Q-1 | **SR-027 AC 5 (new)**; SR-027 AC 2; SR-034 AC 6 | None: PRB-031 to be `rejected` (D-1) |
| PRB-032 JSON logger drops the request-id field | minor | Still open: `core/logging.py` has no request-id field and no `request_id` exists anywhere in `backend/app` | None exists; see Q-7 (emit it, or drop the promise from the docstring) | New at Plan stage |
| PRB-080 Request database transaction commits after the response is sent (added by D-27) | major | Open: `db/repositories/session.py:34-45` commits in a `yield` dependency of default scope `"request"`, which FastAPI 0.138 tears down after `await response(...)` (`fastapi/routing.py:131-137`); 31 `Depends(get_db)` sites in 15 files | **SR-012 AC 5 (new)**, **SR-023 AC 10 (new)**; SR-008 AC 4, SR-013 AC 5 (restored); RISK-007, RISK-006, RISK-001 | TASK-227 |
| PRB-078 Reverse proxy rejects uploads larger than 1 MiB (added at the Plan gate, D-18) | major | Open: `infra/reverse-proxy/nginx.conf` sets no `client_max_body_size`, so nginx's 1 MiB default refuses larger bodies before the backend | SR-013 AC 1, AC 6; RISK-007 | TASK-135 |
| PRB-083 Erasure e-mail is sent for an erasure that did not commit (added by D-30) | minor | Open since TASK-141: `identity/erasure.py:128` enqueues before `invalidate_all`, the audit rows and the commit; `workers/email_tasks.py:142-173` sends without reading the database | SR-024 AC 6; RISK-008 | TASK-228 |
| PRB-084 Concurrent retention sweeps write a duplicate audit row (added by D-30) | minor | Open (predates TASK-141): `workers/retention_tasks.py:67-81` reads the dataset without a lock; the second sweep's 0-row delete still records `ANONYMIZED_DATASET_ERASED` | SR-024 AC 3, AC 5; RISK-006 | TASK-228 |
| PRB-087 Client idle timer re-arms on activity while the server slides only on requests (added by D-33) | minor | Open (predates CR-006): `auth/useIdleTimer.ts` re-arms the deadline to now + the reported length on every activity event, which the server never sees | SR-030 AC 8, AC 4 (the warning follows the server-reported expiry) | TASK-222 |
| PRB-089 Client inactivity timeout neither ends the server session nor clears the cached clinical data (added by D-33) | major | Open (predates CR-006): `auth/SessionActivityProvider.tsx:39-42` `handleExpired` only navigates; no `apiClient.logout()`, no `qc.clear()` | SR-030 AC 1, AC 2 (the session ends at the timeout), AC 8 (one redirect) | TASK-222 |
| PRB-090 Idle warning dialog redirects to sign-in without clearing the cached clinical data (added by D-34) | major | Open (found in TASK-222): `auth/IdleWarningDialog.tsx` navigates to `/login?timeout=1` itself, on the countdown reaching 0 and on an extend answered 401, with no logout and no cache clear | SR-030 AC 1, AC 2 (the session ends at the timeout), AC 8 (one redirect) | TASK-222 |

Existing TASKs whose records will need updating at the Plan stage: TASK-141 (narrow PRB-013 to the
remaining policy, add the retention requirement SR-024 AC 5), TASK-146 (narrow PRB-017), TASK-136
(add `implements` SR-026 AC 5 and decide on PRB-072, Q-1), TASK-135 (add `implements` SR-017 if it
absorbs PRB-006, Q-2), TASK-144 (add `implements` SR-015). All seven are `draft`.

### Requirements decision

Where an existing requirement already states the expected behaviour, the fix restores it and no
requirement changes: SR-014, SR-016, SR-031, SR-033, SR-034, SR-035, NFR-006 and the existing
criteria of SR-026 (AC 1 to AC 3), SR-027 (AC 2, AC 3) and SR-030 (AC 1 to AC 4).

Where no requirement stated it, the Product Owner drafted the smallest criterion that makes the
fix verifiable. Each changed SR is back in `in_review` with its approval cleared, version bumped
and a version-history line (the human re-approves):

| SR | New version | New criterion | Drives |
|---|---|---|---|
| SR-013 | 1.4 | AC 6: bounded memory on upload and download; size limit enforced while reading | PRB-008 |
| SR-015 | 1.1 | AC 5: enablement changes reach the UI without a reload (60 s proposed) | PRB-015 |
| SR-017 | 1.4 | AC 6: stored-size and decoded-size bound before decoding; a failed decode never renders | PRB-006 |
| SR-024 | 1.4 | AC 5: retention sweep isolates failures, releases sessions, retries at most 3 times | PRB-012 |
| SR-026 | 1.4 | AC 5: no 5xx and budgets hold at 20 concurrent clients; AC 6: data-access cost does not grow with data; AC 7: route-level splitting; AC 8: bounded inactivity tracking | PRB-008, 009, 020, 021, 022, 024, 025 |
| SR-027 | 1.2 | AC 5: destructive confirmation starts on Cancel | PRB-031 |
| SR-030 | 1.4 | AC 8: client deadline from the server-reported expiry; one redirect on an expired session | PRB-016 |

No new SR, UN, NFR or RR was needed: every changed SR keeps its existing `satisfies` or
`derives_from` links. Numeric values written in the criteria (100 MiB, 512 MiB, 20 clients, 60 s,
1 s) are proposals and are listed in the open questions. No SR was added for PRB-032 (Q-7) or
PRB-030 (SR-016 AC 3 already covers it).

### Out of scope

- The security defects of the same review (CR-004, closed) and the build and deployment defects
  (CR-005, closed).
- PRB-079 (anonymized-data retrieval verifies the code against every dataset), raised at the Plan
  gate (D-23): a `relates_to` link only; it needs its own CR with a decision on the retrieval-code
  format.
- PRB-081 (concurrent requests beyond threads plus connections per worker answer 500), raised by TASK-136
  QA: a `relates_to` link only (D-27). It is availability only and beyond SR-026 AC 5; it needs its own CR
  with a decision on a per-worker concurrency cap. TASK-227 removes only its streaming contribution.
- PRB-072 (concurrent writes collapse the API) unless the human adds it (Q-1). It is investigated
  in TASK-136's area and its hypothesis is a consequence of PRB-009 and the pool sizes.
- Moving the object store, the DICOM viewer UI and Cornerstone3D integration. PRB-020 only makes
  the bundle able to absorb them.
- Changing a PRB to `resolved`, `closed` or `rejected`, or a record to `approved`. Only the human
  approves; PRB status changes follow verification.

### Boundaries

- **Ask first:** any new runtime dependency (for example a streaming multipart parser); any change
  to the HTTP contract of upload, download or the DICOM frame endpoint, which needs a regenerated
  OpenAPI schema and frontend types; a pool-size or timeout change in the deployed configuration;
  an Alembic migration applied to an existing database (the four indexes).
- **Never:** put a secret or personal data in a log line added by these fixes; set a record
  `approved`; edit an `approved` record without bumping its version and clearing its approval;
  hand-edit a generated file.

### Risk impact (§7.4)

Preliminary classification: **`affects_controls`**, class B unchanged. Each fix restores a
control that RISK-007 (information unavailable) and RISK-003 (incorrect DICOM rendering) already
rely on, or removes a defect in a RISK-004, RISK-005, RISK-008 or RISK-009 control. No new hazard
is expected. Three changes can reach RISK-007 or RISK-003 if they go wrong and need a fail-safe
at the Risk stage: the size bounds (a legitimate 150 MB study must not be refused, Q-2); streaming
download versus the checksum rule of SR-013 AC 5 (Q-6); and the sync/async change of
`get_current_user`, which is on every authenticated request (PRB-009). The Risk stage confirms or
revises this, and revisits the residual scores of RISK-003, RISK-007, RISK-008 and RISK-009, as the
issue asks.

## Verification approach

IEC 62304 §8.2.1 (change approval), §8.2.3 (verification of changes) and §5.5 (unit verification,
class B). Every fix has a regression test written first that fails on the defect.

- **Attachment memory and size (SR-013 AC 6; PRB-008):** an API test that uploads a body larger
  than the limit and asserts the refusal and that the bytes read stay within limit plus one chunk;
  a memory-bounded download test of an object larger than the chunk size; the existing checksum
  tests of SR-013 AC 5 still pass. Recorded in TS-007.
- **DICOM bound (SR-017 AC 6; PRB-006):** tests with an object over the stored bound, an object
  whose header declares a decoded size over the bound while the stored bytes are small, and a
  truncated pixel stream; each returns an RFC 7807 error and no image. A valid reference study
  still renders. Recorded in TS-010 or a new TS.
- **Concurrency (SR-026 AC 5; PRB-009, PRB-072 if added):** a load test on a started stack with
  20 concurrent mixed read and write clients asserting no 5xx and the SR-026 AC 1 and AC 2
  budgets; a before and after measurement is recorded in the TR. A static test that no dependency
  or handler declared `async def` calls a blocking client.
- **Data-access cost (SR-026 AC 6; PRB-021, PRB-022, PRB-024):** a query-count test (constant
  queries for `groups_of` at 1, 10 and 100 memberships), a test that activation reads one account
  row, and an `EXPLAIN` check on a seeded database for the four lookups, plus a migration test on
  an empty and on a populated database (upgrade and downgrade).
- **Workers (SR-024 AC 5; PRB-012, PRB-013):** unit tests with a failing dataset that assert every
  opened session is closed and the task retries; log-capture tests of the three enqueue failure
  paths (already present for two, TASK-207) and the decision of Q-5.
- **Frontend (SR-015 AC 5, SR-030 AC 8, SR-026 AC 7 and AC 8, SR-027 AC 5; PRB-015, 016, 019, 020,
  025, 031):** Vitest and Testing Library unit tests per fix (invalidation after a mutation,
  expiry taken from the server value, a single redirect on a 401, upload through `request()` with
  its 401 branch, debounce timing with fake timers, cancel focus); a bundle-size assertion in the
  build; the generated-types drift check for PRB-019; the full frontend suite and type check.
- **Unit verification (PRB-017):** unit tests for `SessionActivityProvider`, `AttachmentItem` and
  `api/csrf.ts` with the acceptance criteria written in the TS, and coverage of the three units
  reported in the TR.
- **Module boundary (PRB-030):** a test that lists every `app.*` import in the DICOM module and
  fails on any outside the allow-list, and a negative case with a planted forbidden import.
- **Logger (PRB-032):** a log-capture test, per Q-7.
- **Whole change:** backend and frontend suites green, `ruff` and type checks, `openapi-lint` if
  the schema changes, `traceability-check` with no errors for the records of this CR, and the
  hosted CI run recorded as in CR-005.

## Assumptions

- A-1. The scope is the seventeen PRBs listed in issue #28. PRB-072 is not in the issue and is
  treated as out of scope until Q-1 is answered.
- A-2. Class B is unchanged (`docs/medtrace.yml` and `CLAUDE.md` agree). The defects do not add a
  hazard; the Risk stage confirms this.
- A-3. "Normal load" in SR-026 is undefined today. The 20 concurrent clients in AC 5 is the
  smallest figure that the PRB-072 report shows to fail (8 clients pass, 20 fail); decision D-3
  fixes it, it is not a measured user count.
- A-4. The default maximum attachment size is 100 MiB (`attachments/service.py:70`) while the design
  record puts a typical study at 50 to 150 MB (`docs/design/10-quality-requirements.md:41`).
  Decision D-2 sets the DICOM stored bound at 150 MiB and raises the attachment maximum to match.
- A-5. The server-reported `expires_at` (`api/schemas/auth.py:49`) is the source of truth for the
  client deadline, so PRB-016 needs no API change. To be confirmed at the Plan stage.
- A-6. PRB-013 has no remaining silent site, so its remaining scope is a policy decision.
- A-7. The line numbers in the PRB bodies are stale in several places (PRB-009, PRB-013); the
  evidence above supersedes them.

## Open questions

All nine are resolved by the decision with the same number (Q-n to D-n) in "Decisions". The text
below is kept as the record of what was asked and of the Product Owner's recommendation.

- **Q-1. Which PRBs are already fixed, and is PRB-072 in scope?** PRB-022 (activation reads one
  row) and PRB-031 (focus on Cancel, with a test) are fixed on this branch; PRB-013 is partly
  fixed; PRB-017 is partly fixed. PRB-072 (also referencing TASK-136) is not in issue #28.
  *Recommendation:* reject PRB-022 and PRB-031 as already fixed, citing the evidence in the table
  (only the human changes PRB status); narrow PRB-013 and PRB-017; add PRB-072 to this CR as a
  `resolves` link only if TASK-136's measurement shows it is a consequence of PRB-009, and
  otherwise leave it for its own CR.
- **Q-2. What are the DICOM bounds, and does TASK-135 absorb PRB-006?** AC 6 of SR-017 proposes
  100 MiB stored and 512 MiB decoded. The design record puts studies at 50 to 150 MB and a 512x512
  slice at about 0.5 MiB, so a decoded bound that large allows about 1,000 slices.
  *Recommendation:* 150 MiB stored and 1 GiB decoded, a separate attachment-size decision from the
  100 MiB upload limit (or raise that to 150 MiB), and a new task rather than folding PRB-006 into
  TASK-135, because TASK-135 is attachment-router work and PRB-006 is in the module.
- **Q-3. What is "normal load" for SR-026?** AC 5 proposes 20 concurrent clients on one worker.
  *Recommendation:* accept 20 and state it in NFR-008's next revision; a different figure changes
  only the load test.
- **Q-4. How stale may the module gating be?** AC 5 of SR-015 proposes 60 seconds or the next
  navigation. TASK-144 as drafted only invalidates the module query in the administrator's own
  browser, which does not reach the affected user. *Recommendation:* accept 60 seconds and use a
  short stale time plus refetch on focus in the module query.
- **Q-5. Should an enqueue failure fail the request?** All three sites now log a WARNING and the
  request succeeds. The retrieval code at `identity/erasure.py:140` has no recovery if the e-mail is
  lost, and a missed session-kill propagation leaves a session alive (RISK-005).
  *Recommendation:* keep best effort for the appointment notification (SR-035 AC 3 also shows
  it in the application) and for the session kill (synchronous invalidation already ran); fail the
  erasure request with a retryable error when the e-mail cannot be queued; no new SR beyond the
  existing SR-024 AC 1.
- **Q-6. How can a streaming download keep the checksum rule of SR-013 AC 5?** The SHA-256 must be
  verified before the first byte is served, but a true streaming download sends bytes as they are
  read. *Recommendation:* keep AC 5 as the stronger rule: a first pass hashes the object in chunks
  without keeping it, a second pass streams it, accepting two object-store reads; the alternative
  (hash while sending and abort the stream on mismatch) breaks "content is not served" and needs an
  SR-013 AC 5 change and a RISK-012 review.
- **Q-7. Emit the request id or drop the promise (PRB-032)?** There is no request-id concept in the
  backend today. *Recommendation:* drop the promise from the docstring, as it has a weak
  RISK-006 contribution and needs a new middleware, a context variable and an SR to be verifiable;
  reopen if incident analysis needs correlation. If the human prefers to emit it, an SR criterion
  is needed first.
- **Q-8. What initial bundle budget (SR-026 AC 7)?** The AC states the rule (landing route code
  only) without a number. *Recommendation:* measure the current bundle first at the Plan stage and
  set the budget at the current size minus the code that moves to lazy chunks, rounded down.
- **Q-9. Is PRB-017 verified by unit tests alone?** NFR-006 requires traceability to a system test
  before release. *Recommendation:* yes for the unit level (class B §5.5); the system-level
  evidence for SR-030 and SR-015 stays in TS-001 and TS-005.

## Decisions

The human (Carlos Santiago Liceras) answered "Approve as recommended" in chat on 2026-11-13, at the
Specify gate, to the question whether to approve CR-006 and the seven SR amendments with the
Product Owner's recommended answers. That reply is recorded here as the decision on the open
questions (content). It is not the MedTrace approval of the records, which is made by the human in
MedTrace after this content is final; CR-006 and the seven SRs stay `in_review` until then. The
decisions were relayed by the coordinating agent; the human's own MedTrace approval confirms them.

- **D-1 (Q-1):** PRB-022 and PRB-031 are rejected as already fixed before CR-006. Evidence:
  `identity/activation.py:67` and `:162-168` (one-row lookup, no scan); `ConfirmDialog.tsx:46,51`
  and `ConfirmDialog.test.tsx:120`. Their `resolves` links stay on this CR and their Scope entries
  are marked rejected. PRB-013 and PRB-017 are narrowed to the remaining gap (their Investigation
  text is updated) and stay `open`. PRB-072 stays `relates_to`; it joins the scope only if
  TASK-136's measurement shows it follows from PRB-009.
- **D-2 (Q-2):** DICOM bounds are 150 MiB stored and 1 GiB decoded (SR-017 AC 6, now 1.5); the
  attachment upload maximum of SR-013 is raised to 150 MiB to match. PRB-006 gets its own new
  task and is not absorbed by TASK-135.
- **D-3 (Q-3):** "normal load" for SR-026 AC 5 is 20 concurrent clients on one API worker.
- **D-4 (Q-4):** a module enablement change reaches the affected user's UI within 60 seconds or
  the next navigation, not only in the administrator's browser (SR-015 AC 5). TASK-144 uses a short
  stale time and refetch on focus.
- **D-5 (Q-5):** an enqueue failure fails the erasure request only, with a retryable error.
  Activation and appointment paths stay best effort with the WARNING log. No new SR beyond
  SR-024 AC 1.
- **D-6 (Q-6):** two-pass download: verify the checksum in a first chunked pass, then stream.
  SR-013 AC 5 is unchanged.
- **D-7 (Q-7):** PRB-032 is resolved by removing the request-id promise from the logger docstring.
  No SR.
- **D-8 (Q-8):** the initial bundle budget is measured at the Plan stage and then written into
  SR-026 AC 7 (a placeholder says so until then).
- **D-9 (Q-9):** unit tests are sufficient for PRB-017 at the unit level; system-level evidence
  stays in TS-001 and TS-005.

Risk gate (2026-11-13): asked whether to accept R-1 to R-5 of the change analysis as recommended,
the human answered "Accept as recommended" in chat (relayed by the coordinating agent). The
records stay `in_review` until the human's MedTrace approval.

- **D-10 (R-1, human decision 2026-11-13):** the two-pass download binds its second read to the
  first: a conditional read on the ETag (or version) seen in the hashing pass, refused on change
  with the SR-013 AC 5 response and a FAILURE audit row, and the streaming pass hashes as it sends
  and aborts on mismatch. SeaweedFS support for the conditional read is confirmed in SOUP-036 at
  the Plan stage. If it is not supported, the fallback is an SR-013 AC 5 change and RISK-012 back
  to 4 × 2 → alarp.
- **D-11 (R-2, human decision 2026-11-13):** the D-5 behaviour gets its own criterion, SR-024
  AC 6: an erasure whose retrieval-code e-mail cannot be queued fails with a retryable error and is
  rolled back as a whole. This revises D-5's "no new SR"; the Product Owner adds the criterion.
- **D-12 (R-3, human decision 2026-11-13):** the four missing `mitigates` links are added: SR-013,
  SR-017 and SR-024 → RISK-007, and SR-015 → RISK-004 (Product Owner; the SRs are re-approved).
- **D-13 (R-4, human decision 2026-11-13):** the human accepts RISK-003, 004, 005, 007, 008, 009
  and 012 with their expected residuals (RISK-003, 004 and 007 `alarp`); the acceptance is
  recorded by approving each record in MedTrace.
- **D-14 (R-5, human decision 2026-11-13):** the thread-pool and connection-pool sizes are
  proposed at the Plan stage with the load-test evidence, and the human approves them before the
  deployed configuration changes.

Plan gate (2026-11-13): asked whether to approve the plan and findings P-1 to P-9 as recommended,
the human answered "Aprobar como se recomienda" (approve as recommended) in chat, relayed by the
coordinating agent. The records stay `in_review` until the human's MedTrace approval.

- **D-15 (P-1):** the SeaweedFS `If-Match` behaviour is confirmed by a run as TASK-217 step 1, before any
  CR-006 code; if it fails, the D-10 fallback applies (SR-013 AC 5 change, RISK-012 4 × 2 → alarp).
- **D-16 (P-2):** SR-026 AC 7 budget: initial JavaScript (entry chunk plus its static imports) at most
  165 kB gzip. The Product Owner writes it into SR-026 (re-approval).
- **D-17 (P-3):** pool and thread values come from the TASK-136 load test; the human approves them before
  `infra/` changes.
- **D-18 (P-4):** the missing nginx body limit is recorded as PRB-078 (major), resolved by this CR
  through TASK-135.
- **D-19 (P-5):** the additive response fields `sessionExpiresInSeconds` (`GET /me`) and `expiresInSeconds`
  (session extend) are accepted (TASK-144).
- **D-20 (P-6):** TASK-218 tests the bounds and the error path with the decode stubbed; a real render
  needs NumPy and stays with PRB-048.
- **D-21 (P-7):** the additive 503 response on the erasure route is accepted (TASK-141).
- **D-22 (P-8):** the RISK control rows name their TASKs (RISK-003, 004, 005, 007, 012; RISK-008 and
  009 already did).
- **D-23 (P-9):** RISK-007 gets a control row for a failed lazy chunk (TASK-145); RISK-009's row names
  TS-004 instead of TS-006; the retrieval scan is recorded as PRB-079, out of CR-006 scope.
- **D-24 (approved 2026-11-13, Carlos Santiago Liceras, with the TASK-136 load-test evidence):** deployed
  values `API_THREADPOOL_SIZE=20`, `DB_POOL_SIZE=20`, `DB_MAX_OVERFLOW=20`, `DB_POOL_TIMEOUT=10` s; the Redis pool
  `max_connections` equals the thread limit. Rationale: 20 threads cover the 20 SR-026 AC 5 clients and 40
  measured no better; 40 connections = 2x threads because a FAILURE audit row uses a second connection
  (ADR-0016); a 10 s pool timeout fails before Gunicorn's 30 s worker kill. The start-up invariant bounds
  threads, not requests: a connection belongs to the request, so one worker serves about threads + connections
  concurrent requests (59 pass, 60 fail with 20 / 40) and answers 500 beyond that; recorded as PRB-081, outside
  CR-006 scope until the human decides. Evidence: baseline `8028685`, 456
  requests, 210 transport errors, 10 worker kills; working tree 0 errors, 0 kills, p95 0.17-1.12 s across
  configurations.
- **D-25:** code defaults 15 threads / pool 5 + overflow 10 / 30 s timeout, per ADR-0022 (today's effective
  database behaviour; the invariant caps threads at 15 outside Compose).
- **D-26:** PRB-072 is added to CR-006 and resolved by TASK-136 (the 8-ok / 16-and-20-fail pattern reproduces on
  `8028685` and disappears with the event-loop fix alone; `POST /accounts` was not exercised directly).

- **D-27 (human decision 2026-11-13, "PRB-080 sí, 081 aparte", relayed by the coordinating agent):**
  PRB-080 (request transaction commits after the response, major) joins CR-006 with a `resolves` link and
  is resolved by TASK-227 (design: ADR-0023, Proposed). PRB-081 stays outside CR-006, `open`, with a
  `relates_to` link, for a later CR. Reason for PRB-081: availability only (a bounded burst of 500s with
  self-recovery; no data disclosed or altered), and the load needed (more than 59 concurrent requests on one
  deployed worker) is beyond SR-026 AC 5 (20 clients, D-3). The content consequences (SR-012 AC 5, SR-023
  AC 10, the RISK rows, the order of TASK-227) are proposed below as P-10 to P-15 for the human's approval.

D-27 follow-up (2026-11-13): asked whether to approve P-10 to P-15 as recommended and to add the missing
indexes inside TASK-220, the human answered "Aprobar todo" (approve all) in chat, relayed by the coordinating
agent. The records stay `in_review` until the human's MedTrace approval.

- **D-28 (P-10 to P-15, human decision 2026-11-13):** accepted as recommended. P-10: the new criteria are
  SR-012 AC 5 and SR-023 AC 10 (no new SR). P-11: `get_db` uses `scope="function"` at every site through one
  alias, with a route-inventory test (ADR-0023, now Accepted). P-12: an aborted download records SUCCESS then
  FAILURE once the response has started, amending ADR-0016's "Unchanged" note for that case. P-13: RISK-001,
  RISK-006 and RISK-007 get the control rows; RISK-002 and RISK-012 stay unchanged (the human confirmed the
  assessment). P-14: TASK-227 is step 4b, after TASK-136 and before TASK-141, parallel with TASK-219 and
  TASK-220. P-15: ADD-016, ADD-005, ADD-012 and SOUP-002 are updated by TASK-227 when it lands.
- **D-29 (human decision 2026-11-13, from the TASK-219 QA review, finding 1, MEDIUM):** of the four 0011
  indexes only `clinical_entry.patient_id` serves a current query (`ClinicalRepository.list_for_patient`);
  the consent decision itself is served by the existing `ix_consent_grant_patient_doctor_active`. Two lookups
  the code issues have no index and still scan after 0011: `attachment.clinical_entry_id`
  (`AttachmentRepository.list_for_clinical_entry`, `backend/app/attachments/service.py:332`) and
  `consent_grant(doctor_id, active)` (`ConsentRepository.list_patients_for_doctor`,
  `backend/app/clinical/service.py:106`; the existing composite index starts with `patient_id`). Both are
  added to TASK-220 as migration 0012 (1.1, `ask first` on existing databases, same verification as
  TASK-219). The three unused 0011 indexes stay, as SR-026 AC 6 names them. Consequences: SR-026 AC 6 names
  the two lookups (1.6, `in_review`, approval cleared), so the 0012 query-plan check traces to a criterion;
  PRB-021's Observed text is corrected (1.1, stays `open`); RISK-007's data-access row names 0012 (1.15);
  TASK-225 confirms ADD-016 for 0011 and 0012 (TASK-219 QA finding 5) and indexes ADR-0021 to ADR-0023.
  Change analysis: cause 4 now also covers 0012 (writes to `attachment` and `consent_grant` blocked while
  the two indexes build; same "ask first" control and migration test); no new hazard, class B unchanged.
- **D-30 (human decision 2026-11-14, "Arreglarlos ahora", relayed by the coordinating agent, from the TASK-141
  QA review, LOW 1 and LOW 3):** both findings are fixed inside CR-006. LOW 1 is PRB-083 (the erasure e-mail is
  sent although the erasure did not commit) and LOW 3 is PRB-084 (two overlapping retention sweeps write a
  duplicate audit row). Both are `minor`, linked `resolves`, and planned as TASK-228 (Checkpoint B). Design: the
  worker sends the e-mail only once the erasure's `anonymized_dataset` row is visible (up to 14 re-checks,
  2 s doubling to 60 s, about 10 minutes; dropped on a positive "never committed", sent when the check
  cannot be made). The sweep locks the row with `SELECT ... FOR UPDATE` and re-checks the deadline in the same
  statement (not `SKIP LOCKED`). TASK-141 LOW 2 (no FAILURE audit row for a rolled-back erasure) and LOW 4 (dead
  test assignment) are not in D-30 and stay with the human. LOW 5 (TS-004 Notes) is folded into TASK-228,
  which edits TS-004. Change analysis below.
- **D-31 (human decision 2026-11-14, "Aprobar y construir", relayed by the coordinating agent):** P-16 accepted
  as recommended (the ~10-minute commit re-check window is the accepted residual of cause 14; bounding the erasure
  transaction itself is left to a later CR); P-17 accepted as recommended (no SR-024 change; the e-mail gate traces
  to AC 6); PRB-083 and PRB-084 confirmed `minor`. TASK-228 built and QA-approved (round 1).
- **D-32 (human decision 2026-11-14, "Opción (a)", relayed by the coordinating agent, from the TASK-221 QA
  review round 1, HIGH 1 and MEDIUM 2):** QA option (a) is taken. `GET /me/modules` checks the session
  without extending it, through its own dependency (a non-sliding `SessionService.resolve(..., slide=False)`
  behind a dedicated `get_current_user` variant that keeps the active-account re-check). Every other route keeps
  the sliding check. A backend test proves that `remaining_seconds` (and the Redis TTL) does not grow after
  `GET /me/modules`. The poll interval drops to about 50 s, with `staleTime` no larger, so SR-015 AC 5's
  60-second bound holds including the round trip and one retry (MEDIUM 2). Option (b), polling only after user
  activity plus a client-side logout on expiry, is not taken. The pre-existing gap that `handleExpired` neither
  logs out on the server nor clears the cache is not in D-32 and stays with the human (P-18). Change analysis
  below.
- **D-33 (human decisions 2026-11-14, relayed by the coordinating agent, on PRB-087 and on P-18):**
  - **PRB-087, "Server responses only".** The client inactivity deadline is re-armed only from server
    responses: `sessionExpiresInSeconds` from `GET /me` and `expiresInSeconds` from extend. Mouse, keyboard and
    scroll activity alone no longer re-arms or extends anything. To keep the session, the user makes a request
    or presses Extend in the warning dialog. PRB-087 comes into CR-006 (`resolves`) and is fixed in TASK-222.
  - **P-18, "Major, in CR-006".** The `handleExpired` gap is raised as PRB-089 (`major`, `open`), linked
    `resolves` and fixed in TASK-222. `handleExpired` calls `apiClient.logout()` (best effort) and `qc.clear()`,
    as the `AuthError` handler already does.
  - Consequence for TASK-222: its debounce (SR-026 AC 8, PRB-025) has nothing left to throttle. TASK-222 1.1
    removes the activity listeners instead, which also resolves PRB-025. SR-026 AC 8 and SR-030 AC 1 and AC 2
    need wording decisions (P-20, P-21). Change analysis below.
- **D-34 (human decision 2026-11-14, "Into CR-006, in 222", relayed by the coordinating agent, from the
  TASK-222 QA review round 1, HIGH 1):** PRB-090 (`major`, raised by the developer) comes into CR-006
  (`resolves`) and is fixed in TASK-222. `IdleWarningDialog` stops navigating on its own. It takes an
  `onExpired` prop and calls it on the countdown reaching 0 and on an extend answered 401. The provider passes
  `handleExpired`, which returns early once `sessionEnded` is set, so the session is ended once: cache cleared,
  logout attempted, one redirect. QA reproduced the defect: after a clock jump, the dialog's 500 ms tick runs
  before `handleExpired`, the session is left open, and the cached PHI is reachable with Back. Change analysis
  below.

## Change analysis (Risk stage, §7.4, 2026-11-13)

The Software Architect role ran this analysis. Scales and matrix: `docs/medtrace.yml` (5 × 5
`risk_matrix`) and PLAN-005. The architecture records touched (ADD) are named at the Plan stage.

- **Records consulted:** RISK-001, 003, 004, 005, 006, 007, 008, 009, 012; SR-013, 015, 017, 024,
  026, 027, 030 (as approved on 2026-11-13, not edited here), SR-016, 031, 034, 035; the 17 PRBs and
  PRB-048, 057, 072, 074; SOUP-003, 015, 017, 019, 025, 027, 028, 036; TS-001 to TS-007, TS-010.
- **Code read:** the evidence cited in "Scope"; also
  `backend/modules/dicom_viewer/dicom_viewer/dicom.py` (`dcmread` then `pixel_array` on the whole
  object) and `backend/app/identity/erasure.py:135-142` (the retrieval-code e-mail is enqueued
  inside the request's transaction, before commit).

**Conclusion.** `risk_impact: affects_controls` is **confirmed**.

- **No new hazard; class B unchanged (§7.4.1).** Every harm a change can reach is already in
  RISK-001, 003, 004, 005, 007, 008, 009 or 012. The highest severity reached is 4 (RISK-003 and
  RISK-012: a wrong image or a substituted study), which the class B rationale in
  `docs/medtrace.yml` already covers; no change adds a path to serious injury, and no change
  removes a control that a lower class would depend on. The class cannot rise from this change.
- **RISK-012 and RISK-005 are added to the analysis** (the CR text listed RISK-003 to RISK-009):
  the two-pass download changes how the checksum control of SR-013 AC 5 is realised (RISK-012),
  and PRB-016, PRB-019 and PRB-025 change the client side of the session controls (RISK-005).
- **RISK-003's record was wrong:** its row "Size and decompression limits on the frame endpoint"
  named SR-031, TASK-135, TS-008 and TS-011, but no bound was ever implemented (PRB-006 is open,
  `dicom.py` decodes without a limit). The row now names SR-017 AC 6 and planned verification.
- **New causes introduced by the change itself**, each with a control to plan:
  1. **Size bounds refuse a legitimate study** (RISK-007, delay; RISK-003 if a partly decoded image
     were shown): bounds of 150 MiB stored and 1 GiB decoded (D-2) sit above the design record's 50
     to 150 MB study; the refusal is an RFC 7807 error that names the limit, never a partial image;
     the header is read before any pixel data (pydicom `stop_before_pixels`, SOUP-015); a 150 MiB
     reference study is in the test set.
  2. **Two-pass download serves bytes that were not verified** (RISK-012, SR-013 AC 5): the object
     can be replaced between the hashing pass and the streaming pass. Control: the second read is
     bound to the first (a conditional read on the ETag or version seen in pass 1, refused on
     change with the AC 5 response and FAILURE audit), and the streaming pass hashes as it sends
     and aborts the connection on mismatch. SeaweedFS support for the conditional read is a
     relied-on requirement to confirm in SOUP-036 at the Plan stage. The two passes double
     object-store reads for a 150 MiB study (RISK-007, SR-026 AC 3: measured in the load test).
     See R-1.
  3. **Moving `get_current_user` and the attachment dependency off the event loop** (PRB-009) puts
     every authenticated request on a worker thread. A thread pool larger than the database or
     Redis pool makes requests queue on the pool and time out, the shape of PRB-072 (RISK-007).
     Control: thread-pool and connection-pool sizes set together and verified by the SR-026 AC 5
     load test; a static test that no `async def` dependency or handler calls a blocking client.
     The authorization and session decision must not change in the move: TS-001 and TS-002 run
     unchanged (RISK-001, RISK-005). A pool-size change is an "ask first" step (R-5).
  4. **Index migration 0011 on a populated database** (PRB-021) blocks writes to the four tables
     while the indexes build (RISK-007, deployment time). Control: "ask first" (Boundaries);
     migration test on an empty and a populated database, upgrade and downgrade.
  5. **Rewriting `groups_of`** (PRB-024) can return too few groups (an enabled module denied,
     RISK-004) or too many (a module shown that is not enabled, RISK-001). Control: a
     characterisation test of `groups_of` results written before the rewrite and unchanged after
     it (as CR-004 cause 3); the server-side module guard (SR-015 AC 3) is not touched.
  6. **Failing the erasure request on an enqueue failure** (D-5). Because the enqueue sits inside
     the request's transaction, raising there rolls the erasure back: the account and its data
     stay as they were and the operator retries. That is the safe direction (RISK-008); the
     control must keep the anonymization and the code e-mail in one outcome, never a committed
     erasure with a lost code. The converse case (enqueued, then the commit fails) sends a code
     that matches no dataset: harmless, noted for the Plan stage. See R-2. *(Corrected 2026-11-14,
     D-30: not harmless; the subject is told the account was erased when it was not. PRB-083,
     TASK-228.)*
  7. **Retention retries** (SR-024 AC 5): a retried run must be idempotent per dataset and must
     delete only datasets past their deadline, so a retry cannot erase too much (RISK-008).
     Control: a test with a dataset that fails once and then succeeds, and a test that a dataset
     before its deadline survives every retry.
  8. **Module gating refetch** (SR-015 AC 5): a failed refetch must keep the last known value, not
     hide an enabled module (RISK-004). The server stays the authority (SR-015 AC 3), so a stale
     "enabled" shows a link the server refuses (RISK-001 unaffected).
  9. **Client deadline from the server's expiry** (SR-030 AC 8): a skewed client clock moves the
     client countdown if the absolute `expires_at` is compared with the client's clock (RISK-005
     if late). Control: derive the remaining time relative to the response, and the server keeps
     enforcing idle and absolute expiry (SR-030 AC 1 to AC 3), so the client deadline only drives
     the warning and the redirect.
  10. **Debounced activity tracking** (SR-026 AC 8): the client deadline can be up to 1 s late;
      server enforcement is unchanged (RISK-005 not raised). *Superseded by D-33: no activity tracking
      remains, so this cause no longer exists; see causes 19 and 20.*
  11. **Lazy routes** (PRB-020, SR-026 AC 7): a chunk that fails to load leaves a route blank
      (RISK-007, minor). Control: an error boundary with a retry and a clear message (SR-027 AC 3).
- **PRB-022 and PRB-031 (rejected, D-1): no impact.** The fixes predate CR-006 and keep their
  tests; SR-026 AC 6 adds an activation regression test. No RISK record is touched for them.
- **PRB-017, PRB-030, PRB-032: verification and documentation only.** No behaviour changes. The
  new unit tests and the wider boundary test add evidence to existing controls (RISK-005,
  RISK-004; RISK-001 through SR-016 AC 3). PRB-032 removes a docstring promise that no RISK-006
  control relied on. RISK-001 and RISK-006 are not edited.
- **SOUP: no new item expected.** Streaming uses Starlette's upload file and python-multipart
  (SOUP-003, SOUP-017) and the boto3 streaming body (SOUP-019); the DICOM header read uses pydicom
  (SOUP-015); lazy routes use React and React Router (SOUP-025, SOUP-027). A new streaming parser
  is "ask first" and would need a SOUP record and a RISK-010 review.

| Change (PRB) | Software items | §7.4.1 contribution | §7.4.2 controls affected | §7.4.3 verification (planned; TASKs at Plan stage) |
|---|---|---|---|---|
| DICOM stored and decoded bound; a failed decode never renders (PRB-006) | SI-MOD-DICOM-BE, SOUP-015 | Removes an unbounded decode (process memory) and a partial-decode path. New: cause 1 | RISK-007 (new control), RISK-003 (row corrected and re-based on SR-017 AC 6) | TS-010 or a new TS: over the stored bound, over the declared decoded bound with small stored bytes, truncated pixel stream: each RFC 7807 and no image; a 150 MiB reference study renders |
| Streaming upload and download, limit enforced while reading, two-pass checksum (PRB-008) | SI-API, SI-ATTACH, SOUP-003, 017, 019, 036 | Removes whole-object buffering. New: cause 2 | RISK-007 (new control), RISK-012 (checksum control kept, under condition R-1) | TS-007: over-limit upload refused within limit plus one chunk; memory-bounded download; TC-007.6 to TC-007.8 unchanged; new case: object replaced between the passes gives 502 and a FAILURE audit row |
| No blocking IO on the event loop (PRB-009; PRB-072 if added, D-1) | SI-API, SI-AUTH, SI-ATTACH | Removes event-loop stalls on every authenticated request. New: cause 3 | RISK-007 (new control); RISK-001, RISK-005 (decision unchanged) | Load test on a started stack, 20 clients, no 5xx, SR-026 AC 1 and AC 2 budgets; static test; TS-001 and TS-002 unchanged |
| Indexes; `groups_of` N+1; activation regression (PRB-021, PRB-024, PRB-022) | SI-PERSIST, SI-GROUPS, SI-AUTHZ, SI-IDENTITY | Removes cost growth with data. New: causes 4, 5 | RISK-007 (new control), RISK-004, RISK-001 (characterisation) | Query-count test at 1, 10, 100 memberships; one-row activation test; `EXPLAIN` on a seeded database; migration test, populated, up and down; `groups_of` characterisation (TS-005) |
| Retention sweep isolation, session release, retries (PRB-012) | SI-WORKER, SI-PERSIST | Removes a pool-exhausting session leak (RISK-007) and a silent skip (RISK-008). New: cause 7 | RISK-008, RISK-007 (existing rows realised) | TS-004: failing dataset, every session closed, at most 3 retries, later datasets erased, early datasets kept; failed-count log without personal data (TS-017) |
| Enqueue-failure policy (PRB-013, D-5) | SI-IDENTITY, SI-APPT, SI-WORKER | An erasure no longer completes with a lost retrieval code. New: cause 6 | RISK-008 (new control); RISK-009 (logging row realised; best effort unchanged); RISK-005 (session kill: synchronous invalidation already ran) | TS-004 new case: broker unreachable gives a retryable error, no dataset, account unchanged; TS-017 TC-017.6 and TS-003 TC-003.7 (existing, TASK-207) |
| Module gating refresh (PRB-015) | SI-FE-CORE, SI-FE-MODREG | Removes a stale module state in the affected user's UI. New: cause 8 | RISK-004 (new control) | Vitest: refetch on focus and short stale time, failed refetch keeps the last value; TS-005 at system level |
| Session: server-reported deadline, one `me` source, upload through the request helper, debounced tracking (PRB-016, PRB-019, PRB-025) | SI-FE-AUTH, SI-FE-APICLIENT, SI-FE-SHELL | Client timers follow the server; a 401 during upload ends the session like any request; one redirect, no request loop. New: causes 9, 10 | RISK-005 (new control; server enforcement unchanged), RISK-007 | Vitest with fake timers; upload 401 branch; generated-types drift check; TS-001 |
| Route-level code splitting (PRB-020) | SI-FE-SHELL | No hazard. New: cause 11 | RISK-007 (minor) | Bundle-size assertion; error-boundary test for a failed chunk |
| Unit tests, boundary test, logger docstring (PRB-017, PRB-030, PRB-032) | SI-FE-AUTH, SI-FE-CORE, SI-FE-APICLIENT, SI-MODHOST, SI-API | None (verification and documentation) | Evidence for RISK-005, RISK-004, RISK-001; none for RISK-006 | Unit tests with coverage in the TR; boundary test with a planted forbidden import |
| PRB-022, PRB-031 (rejected, D-1) | none | None (fixed before CR-006) | none | Activation regression test (SR-026 AC 6); `ConfirmDialog.test.tsx:120` kept |

**Residual scores per record.** Not changed now: the scores depend on the fixes landing and are
re-scored from the evidence at the CR's verification checkpoint. Each record touched (`in_review`)
states its expected residual:

| RISK | Current (S × P → acceptability) | Expected after CR-006 | Why |
|---|---|---|---|
| RISK-003 | 4 × 2 → alarp | 4 × 2 → alarp | The bound realises a control the residual already assumed; the viewer is still not deployed (PRB-048) and its reference-image controls are unverified |
| RISK-004 | 3 × 2 → alarp | 3 × 2 → alarp | New refresh and characterisation controls hold the probability; ALARP argument unchanged |
| RISK-005 | 3 × 1 → acceptable | 3 × 1 → acceptable | Server enforcement unchanged; client timers now follow it |
| RISK-007 | 3 × 2 → alarp | 3 × 2 → alarp | Removes several causes, but the residual is set by the single-host decision (ADR-0010) and PRB-057, both untouched; not 3 × 1 |
| RISK-008 | 2 × 2 → acceptable | 2 × 2 → acceptable | Retention and erasure-code causes removed; PRB-074 (accepted known anomaly, CR-004 D-18, D-21) and TASK-116 remain |
| RISK-009 | 2 × 2 → acceptable | 2 × 2 → acceptable | Best effort by design (D-5); the in-app channel keeps it acceptable |
| RISK-012 | 4 × 1 → acceptable | 4 × 1 → acceptable **only if** the second read is bound to the first (cause 2); otherwise the substitution path re-opens and the record is 4 × 2 → alarp | R-1 |

Acceptability is the `risk_matrix` cell, not a judgement. Accepting a residual is the human's
decision, through approval of each RISK record.

**Safety-relevant SRs and their RISK coverage.** SR-013 → RISK-002, 003, 012 (`mitigates`), and
RISK-007's control table relies on AC 5 and AC 6 without a link; SR-015 → no `mitigates` link,
RISK-004 now relies on AC 5; SR-017 → RISK-003, and RISK-007 relies on AC 6 without a link; SR-024
→ RISK-008, and RISK-007 relies on AC 5 without a link; SR-026 → RISK-007; SR-030 → RISK-005.
SR-027 AC 5 (Cancel focus) is a use-error control for destructive actions (RISK-008 erase-too-much,
RISK-004 revoked access) that is already implemented; no record change. The missing links are
finding R-3; the D-5 control has no acceptance criterion of its own (R-2).

**Findings for the human (Risk stage):**

- **R-1. Two-pass download and RISK-012.** Recommendation: bind the second read to the first
  (conditional read on the ETag or version from pass 1) and hash during the second pass as well,
  aborting on mismatch. With the binding, SR-013 AC 5 holds as written; without it, the bytes
  served are not the bytes verified, RISK-012 goes back to 4 × 2 → alarp, and SR-013 AC 5 would
  need a change. SeaweedFS support for the conditional read is confirmed in SOUP-036 at the Plan
  stage.
- **R-2. The D-5 control has no SR criterion (§5.2.3).** "An erasure whose retrieval-code e-mail
  cannot be queued fails with a retryable error and is not committed" is a RISK-008 control, but
  SR-024 AC 1 does not state it, so the TS has no acceptance criterion to trace it to. D-5 decided
  "no new SR"; confirm that, or add it as SR-024 AC 6 (an SR change, so a re-approval).
- **R-3. Missing `mitigates` links on approved SRs:** SR-013 → RISK-007, SR-017 → RISK-007, SR-024
  → RISK-007, SR-015 → RISK-004. The RISK tables cite these ACs as controls. Adding the links
  changes the approved records (new digest). Recommendation: add them at the SRs' next revision,
  or now with re-approval.
- **R-4. Residual acceptance.** RISK-003, 004, 005, 007, 008, 009 and 012 are back in `in_review`
  with their expected residuals unchanged; RISK-003, 004 and 007 stay `alarp` and need the
  human's renewed acceptance.
- **R-5. Thread-pool and connection-pool sizes** (cause 3) are a deployed-configuration change
  ("ask first"); the Plan stage proposes the values with the load-test evidence.

### Change analysis for PRB-080 (§7.4, D-27, 2026-11-13)

Software Architect role. Code read: `backend/app/db/repositories/session.py:34-45`; the 31
`Depends(get_db)` sites; `api/routers/attachments.py` and `AttachmentService.open_stream`
(`attachments/service.py:144-226`); `audit/service.py` and `AuditRepository.add_independent`; FastAPI
0.138 `routing.py:120-137`, `dependencies/utils.py:318-329, 664-672`, `dependencies/models.py:63-71`.

- **No new hazard; class B unchanged (§7.4.1).** The fix moves the commit earlier; it removes a path to
  harm already in RISK-007 (a write acknowledged then lost, or not yet readable), RISK-006 (content
  disclosed before its audit row is committed; a failed audit commit invisible) and RISK-001 (a consent
  revoke acknowledged before it takes effect, or lost on a commit failure, while SR-008 AC 4 requires the
  next request to be denied). The highest severity reached is 3 (RISK-007); nothing approaches the class C
  boundary.
- **RISK-002 (misattribution): not affected.** PRB-080 lists it, but a lost or late write is missing
  information (RISK-007), not information attributed to the wrong patient or author; no path changes the
  subject or author of a record. No row added (P-13).
- **RISK-012 (two-pass download): control kept, record unchanged.** Today the streamed download holds its
  request session and connection through the whole transfer, and the SUCCESS `ATTACHMENT_ACCESS` row is
  committed after the transfer (a pass-2 mismatch rolls it back, leaving only the FAILURE row). With
  ADR-0023 the SUCCESS row commits before the first byte and the generator runs after the session is
  closed. The SR-013 AC 5 control (bytes served are bytes verified; abort on mismatch; FAILURE row) is
  unchanged in substance, but its FAILURE write now happens after the close: that is cause 13 below, and
  TS-007 TC-007.6 to TC-007.8 plus TASK-227 test 3 (c) verify it. RISK-012's scores and rows stay.
- **Where the SUCCESS row commits (SR-013 AC 5, ADR-0021, SR-023 AC 2).** Decision proposed: **before
  the response is sent and before the first byte** (SR-023 AC 10). Alternatives rejected: after the
  transfer (today; content disclosed with no committed record, a disconnect or a commit failure leaves
  none, and the connection is held through the transfer), and on its own transaction at stream end
  (same disclosure gap, and a SUCCESS for a transfer that may still be aborted). Consequence: an aborted
  pass 2 leaves SUCCESS then FAILURE, which is accurate (all but the held last chunk was sent) and amends
  ADR-0016's "Unchanged" note for failures after the response started (P-12).
- **Upload:** the body is parsed before the handler, so the scope changes nothing in the upload path;
  the 201 follows the commit. A commit failure after the object was stored leaves an unreferenced,
  encrypted object, as any rollback does today (no record points to it; no new hazard).
- **New causes introduced by the change itself:**
  12. **Mixed dependency scopes** (RISK-007, RISK-006): FastAPI's dependency cache key includes the scope,
      so one site left on the default scope gives a request two sessions; part of its unit of work (for
      example the audit row) would still commit after the response, or separately from the business
      write. Control: one alias for every `get_db` use and a route-inventory test with a negative
      control (TASK-227 test 4).
  13. **Response generator after the session is closed** (RISK-012 audit part, RISK-006): the commit
      expires the ORM instances and the close detaches them; a generator reading `attachment.size` or
      `actor.id` raises, and a FAILURE row written through the closed session could be lost. Control:
      `open_stream` captures plain values; the independent write is bound to the engine; TASK-227 test 3 (c)
      on real PostgreSQL.
- **SOUP:** no new item. SOUP-002 (FastAPI 0.138) gains a relied-on behaviour: `Depends(scope="function")`
  tears down before the response is sent, and the cache key includes the scope (recorded by TASK-227).
  SOUP-008 (session expiry on commit) as recorded.
- **SR coverage of the controls (§5.2.3):** no SR stated the commit order. Two criteria are proposed, in
  existing SRs (P-10): **SR-012 AC 5** (a save is acknowledged only after its commit; a failed commit is
  a 5xx) and **SR-023 AC 10** (a SUCCESS audit entry is committed before the response and before any
  content). SR-008 AC 4 (revocation effective for the next request) and SR-013 AC 5 already state the rest
  and are not changed. SR-012 gains `mitigates` RISK-007. SR-012 1.3 and SR-023 1.5 are `in_review`, their
  approval cleared.

| Change (PRB) | Software items | §7.4.1 contribution | §7.4.2 controls affected | §7.4.3 verification (TASK-227) |
|---|---|---|---|---|
| Request transaction ends before the response; one dependency scope; streamed download uses captured values (PRB-080) | SI-PERSIST, SI-API, SI-ATTACH, SI-AUDIT; SOUP-002 | Removes acknowledged-but-uncommitted writes, silent commit failures and content-before-audit. New: causes 12, 13 | RISK-007, RISK-006, RISK-001 (new rows); RISK-012 (control kept, verified again); RISK-002 none | Commit before response start (fails on `9109267`); commit failure gives 5xx, not 201, for an entry and a revoke; SUCCESS rows committed at the first chunk; pass-2 abort gives SUCCESS then FAILURE; no pooled connection during a download; scope inventory with a negative control; TS-007, TS-009, TS-002 regression |

**Residual scores:** unchanged in every touched record (RISK-001 2 × 2 → acceptable; RISK-006 2 × 2 →
acceptable; RISK-007 3 × 2 → alarp, set by ADR-0010 and PRB-057). The window was milliseconds and a lost
write needed a commit failure, so the fix lowers no score on its own. RISK-001 1.5, RISK-006 1.6 and
RISK-007 1.14 are `in_review` with the approval record cleared.

### Change analysis for PRB-083 and PRB-084 (§7.4, D-30, 2026-11-14)

Software Architect role. Code read: `backend/app/identity/erasure.py:85-157`,
`backend/app/workers/email_tasks.py:134-173`, `backend/app/workers/retention_tasks.py`,
`backend/app/workers/celery_app.py:58`, `backend/app/api/deps.py:25-35`, `backend/app/auth/session.py:233-240`.

- **No new hazard; class B unchanged (§7.4.1).** Both changes act inside RISK-008 (personal data lifecycle)
  and RISK-006 (audit trail). The highest severity reached is 2. Nothing approaches the class C boundary.
- **Controls affected (§7.4.2).** RISK-008: the D-5 control ("an erasure never completes with a lost code")
  is kept as TASK-141 built it, and the e-mail is bound to the commit. RISK-006: one audit row per retention
  erasure. RISK-009 (notification not delivered): no row changes. A dropped e-mail belongs to an erasure that
  did not happen, and SMTP retries stay at 3.
- **New causes introduced by the change itself:**
  14. **False drop** (RISK-008): the erasure commits after the last re-check (about 10 minutes after the
      enqueue). The code of a committed erasure would then be lost, which is what SR-024 AC 6 forbids. Control:
      the window is more than twenty times the Gunicorn worker timeout, and the drop happens only on a positive
      "row absent". Residual: nothing bounds the request transaction itself (the Redis client has no
      `socket_timeout`), so the window is a margin, not a guarantee. See P-16.
  15. **Worker cannot read the database** (RISK-008): the gate cannot decide. Control: the e-mail is sent after
      the last re-check, which in the worst case gives PRB-083's misleading e-mail, never a lost code.
  16. **Lock wait** (RISK-007, negligible): an overlapping sweep waits for one per-dataset transaction.
      `SKIP LOCKED` was rejected because a skipped dataset whose holder rolls back would be neither erased
      nor counted in that pass.
- **SOUP:** no new item. SOUP-014 (Celery) is relied on for `self.retry(countdown=, kwargs=)` with an ETA under
  the Redis `visibility_timeout`. SOUP-020 (PostgreSQL) is relied on for `FOR UPDATE` re-evaluation under READ
  COMMITTED. TASK-228 records both.
- **SR coverage (§5.2.3):** the e-mail gate traces to SR-024 AC 6 ("the request never reports success"; the
  e-mail is a report of success to the subject), and the single audit row to SR-024 AC 3. No SR is changed
  here. See P-17.

| Change (PRB) | Software items | §7.4.1 contribution | §7.4.2 controls affected | §7.4.3 verification (TASK-228) |
|---|---|---|---|---|
| Erasure e-mail sent only once the dataset row is committed (PRB-083) | SI-WORKER, SI-IDENTITY; SOUP-014 | Removes the misleading e-mail. New: causes 14, 15 | RISK-008 (new row; "harmless" corrected) | Sent when committed; re-checked then dropped when it never commits; sent when unconfirmed; SMTP retries still 3; real-PostgreSQL visibility test; TS-004 TC-004.6, TS-017 TC-017.9 |
| Retention row locked, deadline re-checked under the lock (PRB-084) | SI-WORKER; SOUP-020 | Removes the duplicate audit row. New: cause 16 | RISK-006 (new row) | Real PostgreSQL: a blocked second sweep writes no row; after a rollback of the first it erases once; TS-004 TC-004.7 |

**Residual scores:** unchanged (RISK-008 2 × 2 → acceptable; RISK-006 2 × 2 → acceptable). RISK-008 1.5 and
RISK-006 1.7 are `in_review` with the approval record cleared.

**Findings for the human (D-30):**

- **P-16. Bound of the e-mail gate.** Recommendation: accept the 10-minute margin. Alternative: also bound the
  erasure transaction (a Redis `socket_timeout` and PostgreSQL `SET LOCAL statement_timeout` /
  `idle_in_transaction_session_timeout` in `_erase`), so a commit after the window is impossible. That changes
  shared client configuration, so it belongs to a later CR or an extension of TASK-228.
- **P-17. SR wording.** Recommendation: no SR change; TC-004.6 traces to SR-024 AC 6. Alternative: the Product
  Owner adds "the retrieval-code e-mail is sent only once the erasure is committed" to AC 6. SR-024 is
  approved, so this needs re-approval.

### Change analysis for the non-sliding module poll (§7.4, D-32, 2026-11-14)

Software Architect role. Code read: `backend/app/api/deps.py:55-95`, `backend/app/auth/session.py:168-205`,
`backend/app/api/routers/me.py:40-50`, `frontend/src/modules/useMyModules.ts`,
`frontend/src/auth/SessionActivityProvider.tsx:25-60`. `useMyModules` is the only `refetchInterval` in
`frontend/src`.

- **No new hazard; class B unchanged (§7.4.1).** The defect QA found (a background poll that keeps an
  unattended session alive) is a cause of the existing RISK-005 hazard: someone else rides an authenticated
  session at an unattended workstation. D-32 removes that cause. The change adds a read-only session check,
  which can only end a session earlier, never keep it longer. The highest severity reached is 3 (RISK-005). Nothing
  approaches the class C boundary.
- **Controls affected (§7.4.2).**
  - RISK-005: the idle-expiry control (SR-030 AC 1, AC 2) is restored for the poll. A new control row says
    background polls do not extend the session. The client-session row's claim "Server enforcement of SR-030
    AC 1 to AC 3 is unchanged" is corrected: it now names the one non-sliding route.
  - RISK-004: the module-refresh row and its "risks introduced by controls" line name the ~50 s interval and the
    non-sliding check. SR-015 AC 5 is met with a margin, not exactly at 60 s.
  - RISK-001: not touched. The poll returns only module keys, never PHI.
- **New causes introduced by the change itself:**
  17. **Wrong dependency on a route** (RISK-005): a route that serves user actions given the non-sliding check
      would end a working user's session early (an availability effect), never extend one. Control: only
      `GET /me/modules` uses it, and the backend test pins both sides: no TTL growth there, and growth on a
      normal route.
  18. **Non-sliding path skips a check** (RISK-005): the non-sliding resolve must still apply the absolute
      lifetime and the missing or ended session result, and the dependency must still re-check that the
      account is active. Control: the same `resolve` body with only the write skipped; tests for an expired,
      ended and inactive account on `GET /me/modules`.
  - The ~50 s interval adds about 20% more requests than 60 s (about 0.4 requests per second at 20 clients,
    D-3). That is negligible against SR-026 AC 5.
- **SOUP:** no new item. SOUP-028 (TanStack Query) is relied on for `refetchInterval` restarting on each query
  update, which is why 50 s rather than 60 s is chosen. That is recorded with TASK-221 (QA LOW 6).
- **SR coverage (§5.2.3):** the non-sliding check traces to SR-030 AC 1 and AC 2 (inactivity means no user
  request, so a background poll is not activity), and the interval to SR-015 AC 5. No SR is changed. TASK-221
  implements SR-015 only today. It should also `implements` SR-030 and `mitigates` RISK-005 (see P-19).

| Change | Software items | §7.4.1 contribution | §7.4.2 controls affected | §7.4.3 verification (planned, TASK-221) |
|---|---|---|---|---|
| `GET /me/modules` checks the session without extending it (QA HIGH 1) | SI-AUTH `U-AUTH-Session`, SI-API (`deps.py`, `me.py`) | Removes the cause "background poll keeps the session alive". New: causes 17, 18 | RISK-005 (new row; row "client session timers" corrected) | Backend: `remaining_seconds` and the Redis TTL do not grow after `GET /me/modules`, and still grow after a sliding route; expired, ended and inactive cases still 401. New TS-001 case |
| Poll about 50 s, `staleTime` no larger (QA MEDIUM 2) | SI-FE-MODREG (`useMyModules.ts`) | None new. The SR-015 AC 5 bound holds with a round trip | RISK-004 (row and introduced-risk line) | Vitest with MSW `delay()`: the link is gone 60 s after a change that lands just after the server read. TS-005 TC-005.5 |

**Residual scores:** unchanged (RISK-005 3 × 1 → acceptable; RISK-004 3 × 2 → alarp). The defect was found
before merge, so the approved residuals never rested on it. With D-32 they rest again on the server's idle
expiry. RISK-005 1.9 and RISK-004 1.6 are `in_review` with the approval record cleared.

**Findings for the human (D-32):**

- **P-18. `handleExpired` leaves the server session and the cache in place** (pre-existing; not covered by
  PRB-087, TASK-222 or TASK-146). At the client timeout, `SessionActivityProvider.tsx:39-42` only navigates
  to `/login?timeout=1`. Unlike the `AuthError` handler a few lines below, it calls neither
  `apiClient.logout()` nor `qc.clear()`. With D-32, the server session has already ended by then (corrected
  in 1.13: not when requests followed the last `me` or extend response, see D-33). But the
  query cache still holds the clinical data shown before, and Back re-renders it until a request answers 401.
  Recommendation: raise a new PRB (proposed `minor`, or `major` if you read a cached PHI view on an
  unattended workstation as a disclosure under RISK-001 and RISK-005), resolved by calling logout and clearing
  the cache in `handleExpired`. Not created here.
- **P-19. TASK-221 links.** Add `implements` SR-030 and `mitigates` RISK-005 to TASK-221 (the developer is
  editing it now), so the new RISK-005 row traces to its task.

### Change analysis for the server-driven client deadline and the timeout session end (§7.4, D-33, 2026-11-14)

Software Architect role. Code read: `frontend/src/auth/useIdleTimer.ts`, `SessionActivityProvider.tsx`,
`useMe.ts` (`staleTime` 30 s, refetch on mount when stale; `refetchOnWindowFocus: false` app-wide in `api/queryClient.ts:30`), `RequireAuth.tsx`, `api/client.ts:110`
(`logout`), `backend/app/auth/session.py:168-205`.

- **The two clocks after D-33.** The server slides the session on every request except `GET /me/modules`
  (D-32). The client re-arms only on a `me` or extend response. Each of those is itself a sliding request, and
  the client deadline is the receipt time plus the server's remaining seconds. So the client deadline is never
  later than the server's. It is earlier when the user made other requests (saves, or views that do not
  refetch `me`) after the last `me` or extend response. Before D-33 the client could run
  *later* than the server (PRB-087: activity with no request).
- **No new hazard; class B unchanged (§7.4.1).** Every effect falls inside RISK-005 (session at an unattended
  workstation), RISK-001 (PHI shown to the wrong person) and RISK-004 or RISK-007 (a legitimate user signed out
  early). The highest severity reached is 3 (RISK-005). Nothing approaches the class C boundary.
- **RISK-005 (§7.4.2).** The warning now rests on server truth (SR-030 AC 4, AC 8). It always appears at least
  2 minutes before the server would end the session, never after. The PRB-089 fix makes the client timeout end
  the server session. The earlier of the two deadlines is therefore the one that applies, and an unattended
  workstation is closed at the client deadline at the latest.
  - Without the PRB-089 fix, D-33's server-only re-arming would make a live server session after the client
    redirect the normal case: going Back gives the next person a working session. The two fixes must land
    together, in one TASK and one commit (TASK-222).
  - New row: "the client timeout ends the session". The client-session row is corrected: activity no longer
    re-arms, and no debounce exists.
- **RISK-001 (§7.4.2), PRB-089 disclosure aspects.** After a client timeout, Back re-renders the cached
  clinical views. `RequireAuth` sees a successful `me` in the cache.
  - If the server session has ended, the person at the workstation sees the PHI the clinician last loaded. It
    stays on screen until a refetch answers 401, or indefinitely if the refetch fails for another reason
    (PRB-067 keeps the app mounted).
  - If the server session is alive, they reach anything that session can reach. That case is RISK-005's harm.
  - `qc.clear()` before the redirect removes the first path and `logout` removes the second. New RISK-001 row.
    The residual stays 2 × 2: no score was ever based on the client cache.
- **RISK-004 (§7.4.2).** A clinician who reads without making requests now gets the warning at 13 minutes
  (clinical roles) and must press Extend. Ignoring it signs them out at 15 minutes, now also on the server.
  This is the SR-030 AC 1 behaviour, with "inactivity" read as "no request", which D-32 already uses. It
  replaces a client that silently ran past the server's expiry.
  - The availability effect is a sign-in and the loss of any unsaved form input. RISK-004 already covers
    delayed access, and the sign-in recovers it. No score changes.
  - One line is added under "Risks introduced by controls". The module-refresh row is unchanged.
- **New causes introduced by the change itself:**
  19. **Client earlier than the server** (RISK-004, RISK-007): a user who works through requests that do not
      refetch `me` gets the warning although the server would keep the session. Extend recovers it.
      Navigation to a view that reads `useMe` re-arms in practice, because it refetches on mount when older than
      30 s. Window focus does not (`refetchOnWindowFocus: false`).
      Control: the warning dialog and Extend (SR-030 AC 4), tested.
  20. **Logout at the timeout fails or 401s** (RISK-005, RISK-007): the server session may already have ended
      (401) or the network may be down. Control: logout is best effort, and its error is ignored, not sent to
      the `AuthError` handler. The cache is cleared and the single redirect happens whatever the result (SR-030
      AC 8). If logout failed, the server session still ends on its own idle expiry, no later than the server
      deadline. Tested.
  - `qc.clear()` with mounted observers must not start a second session check or a second redirect (SR-030
    AC 8). The cache is cleared and the navigation made in the same handler, and the test counts `me`
    requests.
- **SOUP:** no new item. SOUP-028 (TanStack Query) is relied on for `QueryClient.clear()` removing every cached
  query. TASK-222 checks whether SOUP-028's functional requirements need that line (it is close to "caching
  and invalidation").
- **SR coverage (§5.2.3):** server-only re-arming traces to SR-030 AC 8 and AC 4; the session end at the timeout
  to SR-030 AC 1, AC 2 and AC 5 (logout invalidates the token); the cache clear to SR-030 AC 1 and AC 2. No SR
  is changed here. See P-20 and P-21.

| Change | Software items | §7.4.1 contribution | §7.4.2 controls affected | §7.4.3 verification (planned, TASK-222) |
|---|---|---|---|---|
| Client deadline re-armed only from `me` and extend responses; activity listeners removed (PRB-087, PRB-025) | SI-FE-AUTH `U-FEA-IdleTimer`, `U-FEA-IdleWarning` | Removes "client runs later than the server". New: cause 19 | RISK-005 (client-session row corrected), RISK-004 (introduced-risk line) | Vitest with fake timers: mouse, key, scroll and touch events leave the deadline and the timers unchanged; a new `me` or extend response re-arms; warning at reported − 2 min; TS-001 TC-001.5 and TC-001.11 updated |
| `handleExpired` logs out (best effort), clears the cache, redirects once (PRB-089) | SI-FE-AUTH (`SessionActivityProvider`), SI-FE-APICLIENT | Removes "Back after timeout shows cached PHI or a live session". New: cause 20 | RISK-005 (new row), RISK-001 (new row) | Vitest: at expiry `logout` called once, cache empty, one redirect, no extra `me` request; logout 401 or network error still clears and redirects; Back after expiry renders no clinical data. System level: the session cookie is refused after a client timeout (TS-001 new case) |

**Residual scores:** unchanged (RISK-005 3 × 1 → acceptable; RISK-001 2 × 2 → acceptable; RISK-004 3 × 2 →
alarp). Both defects predate CR-006, and no approved residual counted on the client cache or on activity
re-arming. The server's idle and absolute expiry stay the basis. RISK-005 1.10, RISK-001 1.6 and RISK-004 1.7
are `in_review` with the approval record cleared.

**Findings for the human (D-33):**

- **P-20. SR-026 AC 8 is moot.** It requires the inactivity tracking to re-arm "at most once per second of
  continuous user activity". With no activity tracking, the criterion is met vacuously (zero re-arms), and its
  second clause holds trivially. Recommendation: the Product Owner retires AC 8 or rewords it, for example "user
  input events cause no session-timer work". SR-026 is approved, so either change needs re-approval. TS-018's
  pending AC 8 row (TASK-222) follows the decision. Until then, TASK-222 traces AC 8 through a test that input
  events do no timer work.
- **P-21. SR-030 AC 1 and AC 2, meaning of "inactivity".** AC 4 still fits as written: the warning comes
  2 minutes before the timeout the client enforces, which is never later than the server's. AC 1 and AC 2 say
  "after 15 (30) minutes of inactivity" without defining it. D-32 and D-33 read it as "no request by the user
  (excluding background polls) and no Extend". The client may warn earlier when requests did not refresh `me`.
  Recommendation: the Product Owner adds that definition to AC 1 and AC 2, or records it in the SR's
  rationale. SR-030 is approved, so this needs re-approval. Not blocking: TASK-222 can be built and verified
  against today's wording.

### Change analysis for the warning dialog's own redirect (§7.4, D-34, 2026-11-14)

- **Same hazard as PRB-089, by another route; no new hazard.** The dialog's two redirects (countdown at 0,
  extend 401) bypass `handleExpired`. After either, the server session may still be open (the countdown
  case) or the cache still holds PHI (both cases), and Back re-renders it.
  - RISK-001: PHI shown to the person at the workstation.
  - RISK-005: a live session taken over.
  - The D-33 control rows in RISK-001 and RISK-005 now name the dialog route. Their verification adds a Back
    test after each dialog route.
- **The change itself.** The session end has one owner (`handleExpired`), guarded by `sessionEnded`, so the
  deadline timer and the dialog's tick cannot both end the session. That keeps one redirect and no repeated
  session check (SR-030 AC 8). A missed guard would cause a second logout call or a second redirect
  (availability only). This is covered by cause 20's control and the redirect-count assertion.
- **Class B unchanged.** The highest severity is still 3 (RISK-005). No SOUP or SR change. Residuals unchanged
  (RISK-001 2 × 2, RISK-005 3 × 1, acceptable). RISK-001 1.7 and RISK-005 1.11 stay `in_review`.

## Plan

Plan stage, 2026-11-13, Software Architect role. The plan is the TASK records below (overlay: no
`docs/plans/<feature>.md`). Nothing is built until the human approves the plan, ADR-0021 and
ADR-0022, the changed ADD and SOUP records, and the findings P-1 to P-9.

- All tasks on `fix/review-2026-07-reliability`, one commit per QA-approved task with its records.
- An `approved` TS that several tasks change is bumped, and its approval cleared, once by the first
  task that changes it; later tasks add to the same version (CR-002 rule): TS-007 (TASK-135), TS-005
  (TASK-220), TS-004 (TASK-141), TS-011 (TASK-143), TS-001 (TASK-144), TS-012 (TASK-145), TS-010
  (TASK-223), TS-017 (TASK-141). New: TS-018 "Performance budgets and data-access cost" (`verifies`
  SR-026; TASK-136 creates it), TS-019 "DICOM image opening and rendering" (`verifies` SR-017;
  TASK-218). No TS verifies SR-026 or SR-017 today.
- **"Ask first" steps** (Boundaries): the pool and thread values in the deployed configuration
  (TASK-136, D-14: proposed with the load-test evidence, approved before `infra/` changes); migrations
  0011 and 0012 on an existing database (TASK-219, TASK-220); the additive HTTP contract changes of TASK-144 (`GET /me`
  `sessionExpiresInSeconds`, extend `expiresInSeconds`) and TASK-141 (erasure 503), each with a
  regenerated OpenAPI document and frontend types. No new runtime dependency is planned (no NumPy,
  no streaming parser, no load-test package).
- **First Build-stage steps, before any CR-006 code:** TASK-217 step 1 (SeaweedFS conditional read on
  the pinned digest; a failure stops the plan for the D-10 fallback) and TASK-136 step 1 (load-test
  baseline on the plan-time head).

### Plan-stage open items (resolved here)

- **D-10 / R-1, SeaweedFS conditional read: supported in the published 4.51 source; a confirming run is
  TASK-217 step 1.** At tag `4.51`, `GetObjectHandler` and `HeadObjectHandler`
  (`weed/s3api/s3api_object_handlers.go`) call `processConditionalHeaders`;
  `validateConditionalHeadersForReads` (`weed/s3api/s3api_object_handlers_put.go`) checks `If-Match`
  first against `getObjectETag(entry)` and returns `ErrPreconditionFailed`, mapped to HTTP 412 in
  `weed/s3api/s3err/s3api_errors.go`. boto3 sends it as `get_object(IfMatch=...)`. Recorded as
  relied-on behaviour 14 in SOUP-036 1.4 and in SOUP-019 1.4. Not yet run against the pinned image with
  SSE-S3 on: SOUP-036 lists it as unconfirmed by a run.
- **D-8, bundle budget: measured, value proposed (P-2).** `npm run build` on the plan-time head (vite
  5.4.21): one JavaScript chunk, 559.07 kB minified, **172.55 kB gzip**; CSS 7.25 kB (3.36 kB gzip);
  fonts are separate `woff2` files. Source-map attribution: libraries about 470 kB minified (MUI
  material 200.6 kB, react-dom 126.9 kB, TanStack query-core 37.5 kB, react-router 36.6 kB, MUI system
  34.7 kB), route code that can move to lazy chunks about 20 kB minified (admin 8.9, clinical 4.1,
  appointments 2.9, consent 1.9, password 1.6, patients 0.8). Recommended SR-026 AC 7 value: **initial
  JavaScript (entry chunk plus its static imports) at most 165 kB gzip**, the current 172.55 kB less the
  route code (about 6.5 kB gzip), rounded down to 5 kB. TASK-145 checks it at build time and records the
  after-split size; if the measured entry is above 165 kB because shared MUI components stay in it,
  TASK-145 reports the measured value instead of loosening the check.
- **D-14 / R-5, pool sizes:** defaults today are AnyIO 40 threads, SQLAlchemy `QueuePool` 5 + 10 with a
  30 s `pool_timeout`, redis-py unbounded; 40 threads against 15 connections is the PRB-072 shape.
  Candidate for the measurement: 40 threads, pool 20 + 20, timeout 10 s, Redis `max_connections` 40,
  with a start-up check that threads ≤ pool + overflow (ADR-0022). TASK-136 records the before and after
  load tests and proposes the values; the human approves them before the deployed configuration
  changes; TASK-226 runs the final measurement with the approved values.

### Tasks

| Order | Task | PRB | SR (AC) | RISK (`mitigates`) | Size | Depends on | Status |
|---|---|---|---|---|---|---|---|
| 1 | [TASK-135](../design-outputs/tasks/TASK-135-true-streaming-attachment-upload-and-download.md) Bounded-memory upload, limit enforced while reading, 150 MiB, proxy body limit | 008, 078 | SR-013 AC 6, AC 1; SR-026 AC 5 | 007 | M | — (after TASK-136 step 1 baseline) | updated |
| 2 | [TASK-217](../design-outputs/tasks/TASK-217-bound-two-pass-attachment-download.md) Bound two-pass download (step 1: SeaweedFS `If-Match` run, first of all) | 008 | SR-013 AC 5, AC 6; SR-026 AC 5 | 012, 007 | M | 135 | new |
| 3 | [TASK-218](../design-outputs/tasks/TASK-218-dicom-stored-and-decoded-size-bounds.md) DICOM stored and decoded bounds before decode | 006 | SR-017 AC 6; SR-026 AC 3 | 003, 007 | S | 217 | new |
| — | **Checkpoint A** | | | | | 1–3 | |
| 4 | [TASK-136](../design-outputs/tasks/TASK-136-align-async-handlers-with-sync-io-stack.md) Blocking IO off the event loop; pool settings; load test before/after; values proposed (**ask first** for deployed values) | 009 (072 relates) | SR-026 AC 5, AC 1, AC 2; NFR-008 | 007 | M | 217 (step 1 first of the CR) | updated |
| 5 | [TASK-219](../design-outputs/tasks/TASK-219-indexes-for-authorization-lookups-migration-0011.md) Indexes, migration 0011 (**ask first** on existing DBs); activation one-row guard | 021, 022 (regression) | SR-026 AC 6 | 007 | S | — (parallel with 1–4) | new |
| 6 | [TASK-220](../design-outputs/tasks/TASK-220-constant-query-group-membership-lookup.md) Constant-query `groups_of`, characterisation first; migration 0012 indexes (attachments by entry, consents by doctor; **ask first** on existing DBs, D-29) | 024, 021 (remaining) | SR-026 AC 6; SR-014 AC 4 | 004, 007 | M | 219 (0012 revises 0011; parallel otherwise) | new (1.1, D-29) |
| 7 | [TASK-141](../design-outputs/tasks/TASK-141-worker-reliability-retention-sessions-retries-silent-failures.md) Retention isolation and retries; erasure rolled back on enqueue failure (PRB-013 folded in) | 012, 013 | SR-024 AC 5, AC 6, AC 1; SR-043 | 007, 008, 009 | M | — (parallel) | updated |
| 4b | [TASK-227](../design-outputs/tasks/TASK-227-commit-the-request-transaction-before-the-response.md) Request transaction commits before the response (`scope="function"` on every `get_db`); download audit order (D-27, ADR-0023) | 080 (081 relates) | SR-012 AC 5; SR-023 AC 10; SR-008 AC 4; SR-013 AC 5 | 007, 006, 001 | M | 136; before 141 (parallel with 219, 220) | new (`in_review`) |
| 7b | [TASK-228](../design-outputs/tasks/TASK-228-erasure-e-mail-after-commit-and-locked-retention-row.md) Erasure e-mail sent only once the erasure is committed; retention row locked (D-30) | 083, 084 | SR-024 AC 6, AC 3, AC 5; SR-043 | 008, 006 | S–M | 141 | `approved` (QA round 1) |
| — | **Checkpoint B** | | | | | 4–7, 4b, 7b | |
| 8 | [TASK-143](../design-outputs/tasks/TASK-143-unify-frontend-api-client-upload-and-problem-types.md) Upload through `request()`; `ProblemError` from the schema | 019 | SR-030 AC 8; SR-031; SR-027 AC 3 | 005 | S | — (parallel; frontend) | updated |
| 9 | [TASK-144](../design-outputs/tasks/TASK-144-shared-useme-hook-session-ttl-reconciliation-module-cache-invalidation.md) One `me` query; client deadline from the server-reported expiry (additive API field) | 016 | SR-030 AC 8, AC 4 | 005 | M | — (parallel) | updated |
| 10 | [TASK-221](../design-outputs/tasks/TASK-221-module-gating-refresh-for-every-affected-user.md) Module gating refresh within 60 s for every affected user | 015 | SR-015 AC 5 | 004 | S | 144 | new (split from 144) |
| 11 | [TASK-222](../design-outputs/tasks/TASK-222-debounced-inactivity-tracking.md) Session deadline only from server responses; the client timeout ends the session, the warning dialog included (D-33, D-34; was: activity re-arms at most once per second) | 025, 087, 089, 090 | SR-030 AC 1, AC 2, AC 4, AC 8; SR-026 AC 8 (P-20) | 005, 001 | S | 144, 221 | reworked (1.1); PRB-090 added by D-34 |
| 12 | [TASK-145](../design-outputs/tasks/TASK-145-route-based-code-splitting.md) Route-level splitting, chunk-failure boundary, budget check | 020 | SR-026 AC 7; SR-027 AC 3; SR-020 | — (relates RISK-007) | S | 144 | updated |
| 13 | [TASK-146](../design-outputs/tasks/TASK-146-frontend-unit-test-gaps-session-attachment-csrf.md) Unit tests: session provider, `AttachmentItem`, `csrf.ts` | 017 | NFR-006; SR-030 AC 1–5, 8; SR-015 AC 3–5; SR-031 AC 3 | — (evidence for 005, 004) | S | 143, 144, 221, 222 | updated |
| — | **Checkpoint C** | | | | | 8–13 | |
| P1 | [TASK-223](../design-outputs/tasks/TASK-223-module-boundary-test-with-an-allow-list.md) Module boundary allow-list | 030 | SR-016 AC 3 | — (relates RISK-001) | XS | 218 | new |
| P2 | [TASK-224](../design-outputs/tasks/TASK-224-drop-the-request-id-promise-from-the-logger.md) Logger docstring: no request-id promise | 032 | SR-043 | — (relates RISK-006) | XS | — (parallel) | new |
| 14 | [TASK-225](../design-outputs/tasks/TASK-225-arc42-and-design-records-for-cr-006.md) arc42 sections, ADR index, DEPLOY.md (Document Writer) | — | SR-013, 017, 026, 030 | — | M (docs) | all above | new |
| 15 | [TASK-226](../design-outputs/tasks/TASK-226-verify-cr-006-end-to-end.md) Verify end to end: suites, load test with approved pools, records, re-scoring, traceability (**Checkpoint D**) | all | SR-026 AC 1–8; SR-027 AC 5 | 007 (relates all seven) | S | all above | new |

PRB-022 and PRB-031 are `rejected` (D-1) and have no task; PRB-022's regression test is in TASK-219,
PRB-031's (`ConfirmDialog.test.tsx:120`, SR-027 AC 5) is re-run in TASK-226.

**Parallel work and shared files.** Sequential by shared file: `backend/app/attachments/service.py`
and `api/routers/attachments.py` (135 → 217 → 136; 218 uses 217's `open(max_bytes=)`);
`backend/app/core/config.py` (135 → 136); `frontend/src/auth/SessionActivityProvider.tsx` (144 → 222
→ 146); `frontend/src/app/App.tsx` (144 → 145); `frontend/src/api/queryKeys.ts` (144 → 221);
`backend/openapi/openapi.json` and `frontend/src/api/generated/openapi.ts` (141 and 144 regenerate;
the second to commit regenerates last). 219, 220, 141, 224 share no source file with 135–136 or with
each other; 143 shares none with 144 (`client.ts` only).

**Checkpoints.**

- **A** (after 1–3): backend and DICOM-module suites green; TS-007 and TS-019 cases pass; SOUP-036
  behaviour 14 confirmed by the run; OpenAPI export unchanged.
- **B** (after 4–7 and 4b): backend suite (coverage ≥ 85 %) green; TASK-227 tests 1 to 3 recorded failing on
  `9109267` and passing on the task head; scope inventory green with its negative control; OpenAPI export
  byte-identical; static no-blocking test green; load test
  on the task head recorded with the proposed pool values (human decision pending or taken); migrations
  0011 and 0012 up and down on test databases; TS-001 and TS-002 unchanged.
- **C** (after 8–13): frontend lint, type check, suite with coverage and build plus budget check
  green; OpenAPI and generated types drift-free; one `me` query; module refresh and session timers
  verified with fake timers.
- **D** = TASK-226.

**SR acceptance-criteria coverage** (every AC named in the CR scope):

| SR | AC → task |
|---|---|
| SR-013 | AC 1 (uploads > 1 MiB through the proxy) → 135; AC 5 → 217, 227 (regression after the session closes); AC 6 → 135 (upload), 217 (download) |
| SR-015 | AC 5 → 221; AC 3, AC 4 (unit level) → 146 |
| SR-017 | AC 6 → 218 |
| SR-024 | AC 5 → 141, 228 (lock); AC 6 → 141, 228 (commit-gated e-mail); AC 3 → 228 (one audit row); AC 1 to AC 4 (unchanged, regression) → 141 |
| SR-026 | AC 1, AC 2 → 136, 226; AC 3 → 218, 226; AC 5 → 136, 135, 217, 226; AC 6 → 219, 220; AC 7 → 145; AC 8 → 222 |
| SR-027 | AC 3 → 143, 145; AC 5 (fixed, PRB-031) → 226 regression |
| SR-030 | AC 8 → 144, 143; AC 4 → 144; AC 1, AC 2 → 222; AC 1 to AC 5 (unit level) → 146 |
| SR-012 | AC 5 → 227 |
| SR-023 | AC 10 → 227 |
| SR-008 | AC 4 (restored) → 227 |
| SR-014 AC 4 | 220 |
| SR-016 AC 3 | 223 |
| SR-031 | 143, 146 |
| SR-043 | 141 (failed-count log), 228 (drop and unconfirmed WARNINGs), 224 |
| NFR-006 AC 3, AC 4; NFR-008 | 146; 136 |

**ADD coverage** (class B; every SR in scope is implemented by at least one ADD; changed ADDs are
`in_review` with a "CR-006 (planned)" marker, confirmed by the implementing task): SR-013 (ADD-012
1.7, ADD-026 1.6), SR-015 (ADD-021 1.1; ADD-007, 009, 020 unchanged), SR-017 (ADD-015 1.1), SR-024
(ADD-008 1.2, ADD-017 1.4), SR-026 (ADD-005 1.3, ADD-009 1.1, ADD-012, ADD-015, ADD-016 1.3, ADD-018
1.3, ADD-019 1.1, ADD-026), SR-027 (ADD-018), SR-030 (ADD-006 1.4, ADD-019, ADD-023 1.2). Decisions:
ADR-0021 (bounded attachment IO, bound two-pass download) and ADR-0022 (blocking IO off the event
loop, matched pools), both "Proposed".

**SOUP** (none added, no version change):

| SOUP | Change |
|---|---|
| SOUP-036 SeaweedFS 4.51 | 1.4 `in_review`: relied-on behaviour 14 (conditional `GetObject`), link from ADD-012 |
| SOUP-019 boto3 1.43.117 | 1.4 `in_review`: streamed `put_object` body, `iter_chunks`, `IfMatch` |
| SOUP-003 Starlette 1.3.1 (and AnyIO) | relied-on text extended by TASK-135 (spooled `UploadFile`) and TASK-136 (default thread limiter); no version change |
| SOUP-008 SQLAlchemy 2.0.51, SOUP-013 redis-py 8.0.0 | relied-on text extended by TASK-136 (pool sizing, `max_connections`); no version change |
| SOUP-015 pydicom 3.0.2 | relied-on text extended by TASK-218 (header-only read on the module path); NumPy still absent (P-6) |
| SOUP-009 Alembic 1.18.4, SOUP-014 Celery 5.6.3, SOUP-017 python-multipart 0.0.32, SOUP-024 nginx, SOUP-025 React 18.3.1, SOUP-027 React Router 7.18.0, SOUP-028 TanStack Query 5.101.0 | relied on as recorded (migrations, `self.retry`, multipart parsing, `client_max_body_size`, `React.lazy`/`Suspense`, refetch options); no version or record change expected |

**arc42 sections for the Document Writer (TASK-225):** 04, 05, 06, 07, 08, 10, 11, 12, the ADR index
(`docs/design/adr/README.md`) and `infra/DEPLOY.md`. Not edited at the Plan stage.

**RISK rows to update with the TASK ids (human or Risk-stage edit; the RISK records are not changed
here):** RISK-003 DICOM-bounds row → TASK-218. RISK-004 module-refresh row: TASK-144 → TASK-221;
`groups_of` row → TASK-220. RISK-005 client-session row: add TASK-222 (and TASK-146 as verification).
RISK-007: bounded attachment IO row → TASK-135 and TASK-217; DICOM-bounds row → TASK-218;
data-access-cost row → TASK-219, TASK-220; the no-blocking-IO and retention rows already name TASK-136
and TASK-141. RISK-012 two-pass row: TASK-135 → TASK-217. RISK-008 and RISK-009 rows already name
TASK-141 (RISK-009: the erasure-site log-capture test is in TS-004, not TS-006).

### Findings for the human (Plan stage)

- **P-1. SeaweedFS conditional read (D-10):** supported in the published 4.51 source (412 on an `If-Match`
  mismatch); not yet run against the pinned digest. TASK-217 step 1 runs it first; a failure is the D-10
  fallback, your decision.
- **P-2. SR-026 AC 7 budget (D-8):** measured 172.55 kB gzip (559.07 kB minified), one chunk. Proposed
  value: initial JavaScript at most **165 kB gzip**. SR-026 is approved: writing the value is an SR change
  (Product Owner, re-approval).
- **P-3. Pool sizes (D-14):** candidate 40 threads, DB pool 20 + 20, timeout 10 s, Redis 40; final values
  proposed by TASK-136 with the before/after load test, for your approval before `infra/` changes.
- **P-4. Reverse proxy refuses uploads above 1 MiB today:** `infra/reverse-proxy/nginx.conf` has no
  `client_max_body_size`, so nginx's 1 MiB default answers 413 before the application (SR-013 AC 1 on the
  deployed stack). Fixed in TASK-135; recommendation: record it as a PRB resolved by this CR.
- **P-5. A-5 does not hold:** only the extend response carries `expires_at`; `GET /me` and login report no
  expiry. TASK-144 adds `sessionExpiresInSeconds` to `GET /me` and `expiresInSeconds` to extend (additive
  contract change, "ask first").
- **P-6. No NumPy:** the DICOM frame decode (`pixel_array`) cannot succeed in any environment (SOUP-015,
  PRB-048). TASK-218 implements and tests the bounds and the error path with the decode stubbed; a real
  150 MiB render needs NumPy (new SOUP, "ask first") and stays with PRB-048.
- **P-7. Erasure 503 (D-5, D-11):** an additive 503 response on the erasure route (regenerated OpenAPI and
  types), "ask first".
- **P-8. RISK rows to update** with the TASK ids: see "RISK rows to update" above.
- **P-9. Record gaps:** RISK-007 has no control row for cause 11 (failed lazy chunk; control in TASK-145);
  RISK-009's row names TS-006 for the erasure-site log test, which belongs in TS-004. Also observed, out of
  scope: `ErasureService.retrieve_anonymized` verifies the code with Argon2 against every dataset
  (`identity/erasure.py`, "scan all datasets"), so its cost grows with the data; no PRB records it.
  Recommendation: raise a PRB.

### Findings for the human (D-27 scope change)

- **P-10. Where the new criteria live.** Recommendation: SR-012 AC 5 (commit before a success response;
  a failed commit is a 5xx) and SR-023 AC 10 (SUCCESS audit entry committed before the response and before
  any content), both now `in_review`. Alternative: one platform-wide criterion in a new SR; rejected as
  more records for the same tests. Consent revoke and the download checksum rely on the existing SR-008
  AC 4 and SR-013 AC 5.
- **P-11. ADR-0023 (Proposed): `scope="function"` on every `get_db` use, through one alias, with a
  route-inventory test.** Explicit commits and per-route scopes are rejected (a mixed scope gives two
  sessions per request).
- **P-12. Audit reading of an aborted download.** The SUCCESS row is committed before the first byte; a
  pass-2 mismatch then adds a FAILURE row (today only the FAILURE row remains). Recommendation: accept, as
  it records what happened; it amends the ADR-0016 "Unchanged" note for failures after the response started.
- **P-13. RISK scope.** RISK-007, RISK-006 and RISK-001 get a control row (`in_review`); RISK-002 and
  RISK-012 are assessed and left unchanged (see the change analysis). Recommendation: accept.
- **P-14. Order.** TASK-227 after TASK-136 and before TASK-141, because TASK-141's erasure-rollback test
  (D-11) should be written against the final transaction boundary, and TASK-227 touches every router once
  before 141, 143 and 144 regenerate the contract. Parallel with TASK-219 and TASK-220 (no shared file).
- **P-15. Records deferred to TASK-227.** ADD-016, ADD-005, ADD-012 and SOUP-002 are updated by the task
  when it lands, not now: ADD-016 is also in TASK-219's area, which is being implemented concurrently.
  Every SR in scope is already covered by an ADD (SR-012 ADD-011, SR-023 ADD-013, SR-008 ADD-007).

### Plan risks

| Risk | Impact | Mitigation |
|---|---|---|
| SeaweedFS `If-Match` does not behave as the source reads on the pinned image with SSE-S3 | RISK-012 back to 4 × 2 → alarp; SR-013 AC 5 change | TASK-217 step 1 first; stop and return to the human (D-10 fallback) |
| Thread pool larger than the DB pool after PRB-009 (cause 3) | PRB-072 shape: queued requests, 500s | Start-up invariant (ADR-0022); load test before and after; human approves values |
| Upload guard or `UploadFile` change alters the OpenAPI document | Contract drift, regenerated types | Signature kept; export byte-identical test in TASK-135 and TASK-226 |
| 20 concurrent 150 MiB uploads fill the API host's temporary directory | Upload failures (RISK-007) | Recorded in ADR-0021; TASK-226 checks free space need in DEPLOY.md via TASK-225 |
| Two object-store reads per download slow a 150 MiB study | SR-026 AC 3 at risk once the viewer is deployed | Measured in TASK-226; viewer is not deployed (PRB-048) |
| Initial payload above 165 kB after splitting (shared MUI code) | SR-026 AC 7 value too tight | TASK-145 reports the measured value; human sets the final number |
| `useMe` replacement misses a call site | Repeated session checks, two sources | Static test in TASK-144; one commit for all sites |
| A `get_db` site left on the default scope after TASK-227 | Two sessions per request; part of the work commits after the response | Route-inventory test with a negative control (TASK-227 test 4) |
| A response generator touches the closed session | Aborted download raises or loses its FAILURE row (RISK-006, RISK-012) | Captured values; real-PostgreSQL abort test (TASK-227 test 3 (c)) |
| Erasure 503 changes the operator flow | A retry is needed when the broker is down | Clear problem text and `Retry-After`; TS-004 case |

## Version history

- 1.0 (2026-11-13) — Created at the Specify stage (GitHub sancharly/medhub#28). `in_review`.
- 1.1 (2026-11-13) — Decisions D-1 to D-9 recorded from the human's chat reply at the Specify gate; Open questions marked resolved; Scope entries for PRB-022 and PRB-031 marked rejected. Stays `in_review` until the human's MedTrace approval.
- 1.2 (2026-11-13) — Risk stage (§7.4, Software Architect role): change analysis completed; `affects_controls` confirmed, class B unchanged; eleven causes introduced by the change named with their controls; RISK-003, 004, 005, 007, 008, 009 and 012 updated and back in `in_review`; RISK-012 added to the links; findings R-1 to R-5 for the human.
- 1.3 (2026-11-13) — Risk gate: the human accepted R-1 to R-5 as recommended, recorded as D-10 to D-14 (conditional second read; SR-024 AC 6; four `mitigates` links; RISK acceptance in MedTrace; pool sizes approved at Plan).
- 1.4 (2026-11-13) — Plan stage (Software Architect role): "Plan" filled with 17 TASKs (TASK-135, 136, 141, 143–146 updated; TASK-217–226 new), checkpoints, AC, ADD and SOUP coverage and plan risks; Plan-stage open items D-8 (bundle measured, 165 kB gzip proposed), D-10 (SeaweedFS `If-Match` in the 4.51 source, run pending in TASK-217) and D-14 (candidate pool values, measured in TASK-136) recorded; ADR-0021 and ADR-0022 proposed; ADD-005, 006, 008, 009, 012, 015, 016, 017, 018, 019, 021, 023, 026 and SOUP-019, SOUP-036 back to `in_review`; links to the new TASKs and the two SOUP records added.
- 1.5 (2026-11-13) — Plan gate: the human approved the plan and P-1 to P-9 as recommended, recorded as D-15 to D-23. PRB-078 (proxy body limit) created and added to the scope with a `resolves` link (TASK-135); PRB-079 (retrieval scan) created, `relates_to` only, out of scope. RISK-003, 004, 005, 007, 009 and 012 updated with the TASK ids (D-22, D-23) and back in `in_review`. Stays `in_progress`.
- 1.6 (2026-11-13) — TASK-136 pool values approved by the human, recorded as D-24 to D-26. PRB-072 moved from `relates_to` to `resolves` (D-26). Stays `in_progress`.
- 1.7 (2026-11-13) — TASK-136 round 2: D-24 rationale corrected (the invariant bounds threads, not requests); PRB-080 and PRB-081 raised from QA round 1, not added to the scope pending the human. Stays `in_progress`.
- 1.8 (2026-11-13) — Human decision D-27 ("PRB-080 sí, 081 aparte"): PRB-080 added with a `resolves` link, PRB-081 linked `relates_to` and kept out of scope (availability only, beyond SR-026 AC 5). §7.4 change analysis for PRB-080 (class B unchanged; RISK-007, 006, 001 rows; RISK-002 and RISK-012 unchanged; causes 12 and 13); TASK-227 added to the plan (order 4b, Checkpoint B) with SR-012 AC 5 and SR-023 AC 10 (both `in_review`); ADR-0023 proposed; findings P-10 to P-15 for the human. Links to SR-008, SR-012, SR-023, RISK-001 and TASK-227 added. Stays `in_progress`.
- 1.9 (2026-11-13) — Human decision "Aprobar todo": D-28 (P-10 to P-15 accepted as recommended; ADR-0023 Accepted; RISK-002 and RISK-012 unchanged, confirmed) and D-29 (TASK-219 QA finding 1: indexes on `attachment.clinical_entry_id` and `consent_grant(doctor_id, active)` added to TASK-220 as migration 0012; the three unused 0011 indexes stay). Scope row of PRB-021, plan row of TASK-220 (size M, depends on TASK-219), "ask first" steps and Checkpoint B updated. SR-026 1.6 (AC 6 names the two lookups), PRB-021 1.1, RISK-007 1.15, TASK-220 1.1 and TASK-225 1.1 changed; ADR-0023 Accepted. Stays `in_progress`.
- 1.10 (2026-11-14) — Human decision D-30 ("Arreglarlos ahora", TASK-141 QA LOW 1 and LOW 3): PRB-083 (misleading erasure e-mail) and PRB-084 (duplicate retention audit row) created, `minor`, linked `resolves`; TASK-228 added (order 7b, Checkpoint B); §7.4 change analysis (class B unchanged, causes 14 to 16, residuals unchanged); cause 6 "harmless" corrected; RISK-008 1.5 and RISK-006 1.7 back in `in_review`; findings P-16 and P-17 for the human. Stays `in_progress`.
- 1.11 (2026-11-14) — Human decision D-31 ("Aprobar y construir"): P-16 and P-17 accepted as recommended, PRB-083 and PRB-084 confirmed `minor`; TASK-228 plan row updated to `approved` (QA round 1). Stays `in_progress`.
- 1.12 (2026-11-14) — Human decision D-32 ("Opción (a)", TASK-221 QA round 1 HIGH 1 and MEDIUM 2): `GET /me/modules` checks the session without extending it, and the poll is about 50 s. §7.4 change analysis (no new hazard, class B unchanged, causes 17 and 18, residuals unchanged). RISK-005 1.9 and RISK-004 1.6 are back in `in_review`. Findings P-18 (`handleExpired` gap, PRB proposed and not created) and P-19 (TASK-221 links) for the human. Stays `in_progress`.
- 1.13 (2026-11-14) — Human decisions D-33 (PRB-087 "Server responses only"; P-18 "Major, in CR-006"): PRB-087 and the new PRB-089 (`major`) added to the scope with `resolves` links, both fixed in TASK-222 (reworked to 1.1; the debounce is superseded and the activity listeners are removed; cause 10 superseded). §7.4 change analysis (no new hazard, class B unchanged, causes 19 and 20, residuals unchanged). P-18's "server session has already ended" corrected. RISK-005 1.10, RISK-001 1.6 and RISK-004 1.7 are back in `in_review`. Findings P-20 (SR-026 AC 8 moot) and P-21 (SR-030 "inactivity") for the human. Stays `in_progress`.
- 1.14 (2026-11-14) — Human decision D-34 ("Into CR-006, in 222", TASK-222 QA round 1 HIGH 1): PRB-090 (`major`, the warning dialog's own redirect) added to the scope with a `resolves` link and fixed in TASK-222 (the plan row names it). §7.4 note: the PRB-089 hazard by another route; no new hazard; class B unchanged; residuals unchanged. RISK-001 1.7 and RISK-005 1.11 name the dialog route. Stays `in_progress`.
