---
id: "TASK-226"
type: task
title: "Verify CR-006 end to end"
status: approved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-16"
links:
  - target: "SR-026"
    relation: implements
  - target: "SR-027"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "RISK-003"
    relation: relates_to
  - target: "RISK-004"
    relation: relates_to
  - target: "RISK-005"
    relation: relates_to
  - target: "RISK-008"
    relation: relates_to
  - target: "RISK-009"
    relation: relates_to
  - target: "RISK-012"
    relation: relates_to
  - target: "TASK-135"
    relation: relates_to
  - target: "TASK-136"
    relation: relates_to
  - target: "TASK-141"
    relation: relates_to
  - target: "TASK-143"
    relation: relates_to
  - target: "TASK-144"
    relation: relates_to
  - target: "TASK-145"
    relation: relates_to
  - target: "TASK-146"
    relation: relates_to
  - target: "TASK-217"
    relation: relates_to
  - target: "TASK-218"
    relation: relates_to
  - target: "TASK-219"
    relation: relates_to
  - target: "TASK-220"
    relation: relates_to
  - target: "TASK-221"
    relation: relates_to
  - target: "TASK-222"
    relation: relates_to
  - target: "TASK-223"
    relation: relates_to
  - target: "TASK-224"
    relation: relates_to
  - target: "TASK-225"
    relation: relates_to
tags: ["verification", "traceability", "cr:CR-006"]
---

# TASK-226 — Verify CR-006 end to end

- **Software items:** all touched by CR-006.
- **CR:** CR-006 ("Verification approach", "Whole change"). **Depends on:** TASK-135 … TASK-225, all
  QA-approved and committed. **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S (records: TS-018 TC-018.3 result, CR-006, the RISK records' "planned" evidence, PRB resolutions,
  this task).
- **Needs:** a Docker daemon and a started stack; the human's go-ahead to push for hosted CI.

## Objective

Evidence on the branch head that the whole change holds, that the SR-026 AC 5 budget holds under the approved
pool values, that the records are complete and traceable, and that the §7.4.3 verification of every affected
control is recorded.

## Steps

1. **Regression:** `cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85`;
   `uv run pytest modules/dicom_viewer/tests`; `uv run ruff check . && uv run mypy app`;
   `cd frontend && npm run lint && npm run typecheck && npm test -- --run --coverage && npm run build` plus the
   budget check (TASK-145); `python3 -m unittest discover -s infra/tests -v`; OpenAPI export and
   `generate:types` byte-identical to the committed files. `ConfirmDialog.test.tsx` (SR-027 AC 5, PRB-031
   regression) is part of the frontend run.
2. **Load test (SR-026 AC 1, AC 2, AC 5; TS-018 TC-018.3):** `backend/scripts/load_test.py`, 20 clients, 5 min,
   on a stack started from the branch head with the pool values **the human approved** (D-14; if not yet
   approved, stop and ask). Record: 5xx count (must be 0), p95 per operation (≤ 3 s for AC 1 and AC 2), a
   150 MiB attachment download time (two reads, ADR-0021; SR-026 AC 3 context) and the before values from
   TASK-136 step 1. If PRB-072's failure is gone, report it for D-1.
3. **Started-stack checks:** a 100 MiB upload through nginx succeeds; a 151 MiB upload is refused with the
   problem response; download of a replaced object gives 502 (TASK-217 real-store test re-run); migration 0011
   applied on the test database only.
4. **Hosted CI (needs the human's go-ahead to push):** every job green on the pushed head, recorded as in
   TASK-216.
5. **Records:** TS-004, 005, 007, 010, 011, 012, 001, 017 (changed) and TS-018, TS-019 (new) `in_review` and
   consistent; each PRB in scope has its `## Resolution` (PRB-022 and PRB-031 their rejection evidence);
   RISK-003, 004, 005, 007, 008, 009, 012: replace "none yet (planned …)" by the evidence, re-score from it
   (CR-006 "Residual scores per record"), RISK-012's condition (second read bound) shown met. SR-026 AC 7 holds
   the approved budget value.
6. **Traceability:** `medical-records:traceability-check` over `docs/`: 0 errors for CR-006's records (CR-006,
   the seven SRs, TASK-135, 136, 141, 143–146, 217–226, TS above, ADDs changed at the Plan stage, ADR-0021/0022,
   SOUP-019, SOUP-036 and those changed by the tasks, the seven RISKs, the 17 PRBs).

## Acceptance criteria

- [x] All suites, checks and the budget check green; generated files unchanged.
- [x] SR-026 AC 5: 0 × 5xx and AC 1 / AC 2 p95 ≤ 3 s at 20 clients with the approved pools.
- [x] Records complete; `traceability-check` 0 errors in CR-006 scope.

## Implementation record (Software Developer, 2026-11-15)

Branch `fix/review-2026-07-reliability`, head `0130394`, nothing committed. Project `medhub-verify`: a copy of
`infra/docker-compose.yml` in the scratchpad with only four substitutions (the repository paths made absolute,
the network subnet 10.77.77.0/24 to 10.78.78.0/24 and the proxy address to match, host ports 80/443 to
127.0.0.1:18080/18443), its own volumes, generated throw-away secrets and test accounts (not in the repository).
`infra/docker-compose.yml` was not edited. The user's `infra` project (8 containers) was running before, during
and after; it was not touched. Teardown: `docker compose -p medhub-verify down -v`, the seven `medhub-verify-*`
images and the temporary port-forwarder container removed; `docker compose ls` shows only `infra`.

### Step 1 — regression (all green)

| Check | Result |
|---|---|
| `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85` | 1743 passed, 10 skipped, coverage 95.15 % |
| `uv run pytest modules/dicom_viewer/tests` | 31 passed |
| `uv run ruff check .`, `uv run mypy app` | clean; 137 files, no issues |
| `npm run lint`, `npm run typecheck` | clean |
| `npm test -- --run --coverage` | 41 files, 412 tests passed (`ConfirmDialog.test.tsx`: 7 passed, includes "destructive variant autofocuses Cancel, not Confirm") |
| `npm run build` (runs the budget check) | initial JavaScript 160.06 kB gzip on the host's Node 18.17.1 (the frontend regression ran on 18.17.1, not the pinned 24.22.2); **160.44 kB** in the production image build on Node 24.22.2 (`v226/build.log:633`), budget 165 kB: within. A separate `npm run check:budget` after the build fails only because `--clean` has already removed the manifest it reads; the build's own run is the check |
| `python3 -m unittest discover -s infra/tests -v` | 178 tests OK |
| OpenAPI export vs `backend/openapi/openapi.json`; `generate:types` | byte-identical; `git diff` of both generated files empty |

### Step 2 — load test (TS-018 TC-018.3), PASS

`backend/scripts/load_test.py run`, 20 clients, 300 s, through nginx (`https://127.0.0.1:18443`), one Gunicorn
worker, deployed pools 20 / 20 / 20 / 10, empty database, migrations 0001 to 0012. Server log: the capture was empty (`lt-server.log`, 0 bytes: `docker logs --since` returned nothing), so 0 `WORKER TIMEOUT` and 0 `QueuePool limit` are not evidence; the verdict rests on 0 × 5xx and 0 transport errors on the client side. Proxy log: one 5xx in the whole session, the expected 502 of the replaced-object
check below (not in the run).

| Operation | Count | 5xx | p95 now (s) | p95 before, `8028685` (s) |
|---|---|---|---|---|
| GET /me | 8351 | 0 | 0.281 | 2.167 (121 requests, 38 failed, 83 answered) |
| list appointments | 5549 | 0 | 0.332 | 2.196 (39 transport errors) |
| list clinical entries | 5679 | 0 | 0.370 | 2.200 (41 transport errors) |
| create clinical entry | 4016 | 0 | 0.371 | 2.317 (28 transport errors) |
| upload 1 MiB | 2171 | 0 | 1.009 | none answered (54 transport errors) |
| download | 1778 | 0 | 1.051 | none issued |
| `/healthz` probe | 2057 | 0 | 0.116 | 2.000 |
| **Total** | **29 601** | **0** | | 456 requests, 210 transport errors, 10 worker kills |

Transport errors now: 0. Slowest single request 5.04 s (an upload; upload time is excluded from AC 2). The
"before" run bypassed the proxy (PRB-078 refused bodies above 1 MiB then). Throughput is not comparable between
the two (different data size, proxy in the path); the failure pattern is. 150 MiB attachment download: 2.83 s (two
reads, SHA-256 equal); 100 MiB: 2.49 s. **PRB-072's failure is gone** (D-1, D-26): 8 clients pass, 16 and 20 failed
on `8028685`; 20 pass now.

### Step 3 — started-stack checks

| Check | Result |
|---|---|
| 100 MiB upload through nginx | 201 in 7.46 s; download 200, SHA-256 equal |
| 150 MiB upload (the limit) | 201 in 8.46 s; download 200 in 2.83 s, SHA-256 equal |
| 151 MiB upload | 400 `application/problem+json` (`validation-error`, "The attachment exceeds the maximum size.") after 3.76 s |
| Replaced object (same length, other bytes, written into the store) downloaded through nginx | 502 `application/problem+json` `attachment-integrity-failure`, 292 body bytes, FAILURE audit row (`ATTACHMENT_ACCESS`) |
| TASK-217 real-store test re-run against the stack's SeaweedFS 4.51 (`OBJECT_STORE_INTEGRATION=1`, through a temporary forwarder container) | `test_object_store_conditional_read.py`: 4 passed; with `test_attachment_download.py`: 61 passed |
| Migrations on the empty database (wall time including the Python and Alembic start, about 1.6 s of it) | 0001 to 0010: 1.93 s; **0011: 1.74 s; 0012: 1.64 s**, head 0012, no error. The tables were empty, so these do not measure the index build on a populated database (that is TS-018 TC-018.5 and TC-018.8, 10 000 rows) |
| TS-001 TC-001.14 (script level) | sign in, `GET /me` 200, `POST /auth/logout` 204, then `GET /me` and `GET /me/modules` with the old cookie: 401 `application/problem+json`. PASS (server half) |
| Real DICOM render | **Not possible**: `dicom_viewer` not installed and no `medhub.modules` entry point on the stack (PRB-048), NumPy not installed (PRB-046); pydicom 3.0.2 only. TS-019 TC-019.5 and TS-018 TC-018.11 record this |

### Step 4 — hosted CI

**PASS** (recorded by QA, 2026-11-16, after the human's push). Branch head
`331e2724a66366eeff2ec6eda92cb6e0d6e9c161`, PR #40:

| Run | Event | Head | Result |
|---|---|---|---|
| 43896524793 | push | `331e272` | success, 8 of 8 jobs |
| 43897144750 | pull_request | `331e272` | success, 8 of 8 jobs |
| 43824313319 | push | `ef3510f` | success |
| 43824318806 | pull_request | `ef3510f` | success |
| 43823245736 / 43823253427 | push / pull_request | `09bcc69` | failure: Backend Quality, Frontend Tests (OpenAPI Lint skipped) |

The eight jobs on `331e272`, both runs: Backend Quality, Backend Tests, Docker Build, Frontend Quality,
Frontend Tests, Image Pin Check, Object Store Integration, OpenAPI Lint (`gh pr checks 40`: all pass).

The first push, at `09bcc69`, failed two jobs: Backend Quality (Black reformat of
`backend/tests/workers/test_retention_lock.py`) and Frontend Tests (the upload FormData test in
`frontend/src/api/client.test.ts`, which read the multipart body in an MSW handler and fails under CI's Node 24).
Commit `ef3510f` fixed both and touches only those two test files (`git show --stat ef3510f`: 2 files, 30+/20-);
no product code changed, so the step 1 to 3 evidence still applies. `331e272` changes CR-006 only (D-35).

### Step 5 — records

Updated (all `in_review`, approval record removed where the record was approved, version bumped, history line
added): TS-001 1.11, TS-007 1.12, TS-018 1.9, TS-019 1.1; RISK-003 1.5, RISK-004 1.8, RISK-005 1.12,
RISK-007 1.19, RISK-008 1.8, RISK-009 1.7, RISK-012 1.5; PRB-021 (`resolved`, 1.2), PRB-031 (rejection
evidence), PRB-008, 009, 072, 078, 089 (verification lines); CR-006 1.17 (1.18 adds D-35); this task 1.2 (round-2 versions). TS-004, 005, 010, 011, 012,
017 are unchanged: their cases are automated and passed in the regression above, and they carry no system-level
case for this task. SR content untouched; SR-026 AC 7 holds the approved 165 kB (production image build 160.44 kB; host run 160.06 kB).

RISK re-scores (all from the evidence above; no score changed):

| RISK | Residual | Acceptability |
|---|---|---|
| 003 | 4 × 2 | alarp (viewer still not deployed, reference-image controls unverified) |
| 004 | 3 × 2 | alarp |
| 005 | 3 × 1 | acceptable |
| 007 | 3 × 2 | alarp (set by ADR-0010, PRB-057, PRB-081; not 3 × 1) |
| 008 | 2 × 2 | acceptable |
| 009 | 2 × 2 | acceptable |
| 012 | 4 × 1 | acceptable (condition met: the second read is bound to the first, shown on the real store) |

### Step 6 — traceability

`trace.py` (the fallback parser of the traceability-check procedure) over `docs/` for the 104 records that name CR-006 plus TS-003, TS-010, TS-012 and SOUP-036, expanded to their linked records (307): **0 errors**, 378 warnings (W5 approved-on-in_review, W6 and missing digests: the usual baseline, the records of this task stay `in_review`). Evidence: scratchpad `v226/trace.out`.

### Open points for QA and the human

- **Resolved (2026-11-16): SR-026 AC 3 (first DICOM image within 10 s) is deferred.** CR-006 verifies the DICOM bounds only (TASK-218); the real render and its 10 s budget stay with PRB-048 and PRB-046 (D-20), which now say so, and AC 3 cannot be verified until they are resolved. The human confirmed the deferral as decision D-35 in CR-006 1.18 (commit `331e272`).
- PRB-093 (standalone `check:budget` fails after a build, `minor`, outside CR-006) was raised.
- Step-3 evidence is kept in `v226/`: `ev-replaced-object.txt`, `ev-real-store.txt`, `ev-migrations.txt`, `ev-dicom-probe.txt`, `ev-teardown.txt` (transcribed from the session output; the stack is gone).
- PRB-021 is `resolved`, not `closed`, like the other CR-006 problem reports; `closed` follows the CR.
- Step 4 (hosted CI): resolved 2026-11-16, green on `331e272` (see Step 4).
- The load run is the final one for the approved pools; PRB-081 (more than threads + connections concurrent
  requests give 500) was not exercised, as decided in D-27.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect).
- 1.1 (2026-11-15) — Build stage (Software Developer): steps 1 to 3, 5 and 6 run and recorded; step 4 (hosted CI) pending a push. `draft → in_review`.
- 1.1 (2026-11-15) — QA review round 1: CHANGES REQUESTED, `in_review` to `draft` (findings in "QA review round 1").
- 1.2 (2026-11-15) — Round 2 (Software Developer): QA round 1 findings M-1, M-2, L-1 to L-4 fixed in the records (CR-006 1.17, PRB-046 and PRB-048 notes, RISK-012 1.5, RISK-007 1.19, PRB-008 1.5, PRB-072 1.4, TS-018 1.9, PRB-093 raised, evidence files). `draft → in_review`.
- 1.2 (2026-11-15) — QA review round 2: APPROVED, `in_review` to `approved`; the three acceptance criteria ticked. Step 4 (hosted CI) stays open, pending the human's go-ahead to push (see "QA review round 2").
- 1.3 (2026-11-16) — QA, hosted part: step 4 recorded and checked, runs 43896524793 (push) and 43897144750 (pull_request) on head `331e272`, 8 of 8 jobs green; the `09bcc69` failures were fixed by the test-only commit `ef3510f`. SR-026 AC 3 open point marked resolved by D-35 (CR-006 1.18). Carried LOW R2-3 fixed (Step 5 versions, duplicate AC 3 item). Re-approved: status stays `approved`.

## QA review round 1 (qa-engineer, 2026-11-15) — CHANGES REQUESTED

0 HIGH, 2 MEDIUM, 4 LOW. The measured results hold: every number in the Implementation record, TS-001,
TS-007, TS-018, TS-019, the seven RISK records and the PRB lines matches the evidence (`lt.txt`/`lt.json`,
`uploads.json`, `tc1_14.log`, `regress.log` and `r-*.log`, `pytest-main.log`, `trace.out` in the scratchpad
`v226/`; the replaced-object 502 with 292 body bytes and its three audit rows, the 4 and 61 real-store passes, the
0010/0011/0012 timings 1.934/1.739/1.637 s, the `numpy False / dicom_viewer False / entry points []` probe and
the teardown are in the developer's session output, not in a file, see L-4). The "before" column matches TASK-136
step 1. No score changed and each matches the `risk_matrix`. No SR file changed. The changes are in the records
this task delivers, and the TS records under review carry two of them, so they are fixed before approval.

- **[MEDIUM] M-1 SR-026 AC 3 is claimed by CR-006 but verified nowhere, and the deferral is not recorded where
  the Done gate looks.** `docs/change-requests/CR-006-…-review.md:1124` reads "AC 3 → 218, 226". TASK-218 verifies
  only the bounds with the decode stubbed (TS-019 TC-019.4 says so). TASK-226 does not list AC 3 among its
  acceptance criteria, and TC-018.11 and TC-019.5 record it as not executable. D-20 (`:492-493`) keeps the real
  render with PRB-048, but D-20 is about the render, not the SR-026 AC 3 10 s budget. PRB-048 and PRB-046 have
  `links: []` and do not mention SR-026 AC 3. The TASK needs to say this explicitly. → (a) CR-006 SR coverage
  row: "AC 3 → not verified in CR-006 (bounds only, 218); deferred to PRB-048 and PRB-046 (D-20)", plus a
  version line. (b) A dated line in PRB-048 and PRB-046 stating that SR-026 AC 3 (first image within 10 s) stays
  unverified until each is resolved (TC-018.11, TC-019.5). (c) This task's "Open points" gives it as a deferral
  for the human to confirm at the Done gate. If the human does not accept D-20 as covering AC 3, a new human
  decision is needed before CR-006 can close.
- **[MEDIUM] M-2 RISK-012's condition argument cites the wrong run.** `docs/risks/RISK-012-…-unpatchable.md:194`
  says the binding of the second read is "proved on the real store: a replaced object is refused with a 412,
  `ObjectChangedError`, and the response is 502 with no content". The started-stack 502 (TC-007.16,
  `replace.py`) replaces the object *before* the download, so pass 1's checksum fails and pass 2 is never issued.
  That is the path of `test_download_mismatch_in_first_pass_gives_502_without_second_read`
  (`backend/tests/attachments/test_attachment_download.py:146-157`, `len(store.calls) == 1`). It does not test the
  `If-Match` binding. The condition *is* met, but by two other pieces of evidence:
  `test_download_reads_object_twice_second_conditional` (`:117-125`, pass 2 carries the pass-1 ETag) and
  `test_object_store_conditional_read.py::test_replaced_object_is_refused_with_object_changed` on SeaweedFS 4.51
  (the store refuses a stale `If-Match`). → Reword `:194`, and the real-store sentence of the row at `:131`, to
  cite those two tests for the binding. Name the stack 502 as the pass-1 checksum path with its FAILURE row. Do
  the same where the stack 502 is offered as conditional-read evidence: RISK-007 `:79` and PRB-008 `:60` (the
  facts are correct; only the attribution is wrong).
- **[LOW] L-1 The AC 7 value is not from the production build.** `r-build.log` ran on host Node v18.17.1
  (`r-budget.log` prints it), and measured 160.06 kB. The production image build of the same head
  (`v226/build.log:633`, `node:24.22.2-trixie-slim`, the CI and Dockerfile pin) measured **160.44 kB**. SR-026
  AC 7 says "on the production build". → Record 160.44 kB (image build) as the AC 7 evidence and 160.06 kB as the
  host run in TASK-226 `:133`/`:185`, TS-018 TC-018.10/TC-018.12 and "Verification results", RISK-007 `:76`, and
  state that the frontend regression ran on Node 18.17.1, not the pinned 24.22.2.
- **[LOW] L-2 "121 answered" is wrong.** TASK-226 `:146`: in TASK-136 step 1, 121 is the request count and 38
  of them were transport errors (83 answered). → "2.167 (121 requests, 38 transport errors)".
- **[LOW] L-3 Standalone `npm run check:budget` cannot succeed after `npm run build`.**
  `frontend/scripts/check-bundle-budget.mjs:111-119` with `package.json:8-9`: the build's `--clean` removes
  `dist/.vite`, so the script dies with an uncaught ENOENT stack trace. It fails closed (exit 1). CI does not call
  it, and the Dockerfile (`:9`) uses `npm run build`, so there is no false green and no safety impact. It is still
  a defect in a documented script, outside this task. → Raise a `minor` PRB (out of CR-006 scope). The fix can be
  a clear "run `npx vite build` first, or use `npm run build`" message when the manifest is missing, or a
  `check:budget` that builds first.
- **[LOW] L-4 Part of the step 3 evidence is not retained, and the server-log check read an empty capture.** No
  `v226/` file holds the replaced-object output, the real-store re-run (4 and 61 passed), the migration timings,
  the module and NumPy probe or the teardown listing. They exist only in the session transcript, where QA found
  and checked them. `lt-server.log` is 0 bytes, so "0 `WORKER TIMEOUT`, 0 `QueuePool limit`" is a count over an
  empty capture: `docker logs` returned nothing, with no error. → Save those outputs as files beside the others.
  In TC-018.3 and PRB-072, say the backend log captured no line in the run window.

Not findings:
- PRB-021 `resolved` is right. Under the overlay `closed` means confirmed through a shipped release, and
  CR-006 carries the `resolves` link (E9 holds).
- PRB-031 `rejected` with evidence is correct (`ConfirmDialog.tsx:46,51`, test `:120`, commit `24240f8`
  2026-06-30).
- RISK-007 stays at 3 × 2 for the reason CR-006 `:704` gives (ADR-0010, PRB-057). Naming PRB-081 as well is
  consistent with D-27.
- The approved-record rule is followed: TS-001/007/018/019 and RISK-004/005/009/012 had their approval record
  cleared, their version bumped and a history line added.
- Step 4 (hosted CI) is pending a push. That is the human's decision, and the round-2 approval can follow the
  TASK-216 precedent (local part, then hosted).

### Verification run (QA, 2026-11-15)

- `cd backend && uv run pytest -q`: 1743 passed, 10 skipped (the real-store cases), exit 0.
- `cd frontend && npm test -- --run` (host Node 18.17.1): 41 files, 412 tests passed.
- Trace, the developer's scope (`v226/scope.txt` plus TS-003, TS-010, TS-012, SOUP-036): 307 records,
  0 errors, 378 warnings (reproduced). Over CR-006's 79 `links` plus TS-001, 003, 004, 005, 007, 010, 011, 012,
  017, 018, 019: 353 records, **0 errors**, 406 warnings (199 W5, 5 W6, 202 approval without digest, the
  baseline kinds).
- `docker compose ls`: only `infra` (running 8). No `medhub-verify` container, image, volume or network remains.
  `optimistic_goldwasser` (port 51106, up 26 h) predates this run and is not part of it.

## QA review round 2 (qa-engineer, 2026-11-15) — APPROVED

All round-1 findings are fixed. 0 HIGH, 0 MEDIUM, 3 LOW carried (wording only, not blocking).

- **M-1 fixed.** CR-006 1.17, `:1124`: "AC 3 → not verified in CR-006 (bounds only, TASK-218); deferred to PRB-048
  and PRB-046 (D-20)", with a history line. PRB-046 1.1 and PRB-048 1.1 have a dated note naming SR-026 AC 3,
  TC-018.11 and TC-019.5. Open points list the deferral first, for the human to confirm.
- **M-2 fixed.** RISK-012 1.5 (`:131`, `:194`) bases the condition on
  `test_download_reads_object_twice_second_conditional` and the real-store
  `test_replaced_object_is_refused_with_object_changed`. The stack 502 is named as the first-pass checksum path
  and kept out of the argument. RISK-007 1.19 and PRB-008 1.5 carry the same attribution. Scores are unchanged
  (4 × 1 acceptable; 3 × 2 alarp).
- **L-1 fixed** in this task, the TS-018 "Verification results" and RISK-007 `:76`: 160.44 kB (production image
  build, Node 24.22.2, `v226/build.log:633`), with the host run on Node 18.17.1 noted separately.
- **L-2 fixed:** "121 requests, 38 failed, 83 answered".
- **L-3 fixed:** PRB-093 is well formed. It has the frontmatter in schema order, `open`, `minor`, `links: []`,
  and the sections Observed, Impact, Investigation, Safety evaluation, Resolution and Version history, as in
  PRB-092. The ID is the next free one. Its facts match `package.json:8-9` and `r-budget.log`.
- **L-4 fixed.** `v226/ev-replaced-object.txt`, `ev-real-store.txt`, `ev-migrations.txt`, `ev-dicom-probe.txt` and
  `ev-teardown.txt` exist, are marked as transcribed, and match the session output QA read in round 1. TC-018.3,
  PRB-072 1.4 and this task say that the backend log capture was empty.

Carried LOWs (fix when the record is next touched; none changes a result or a score):
- **R2-1** TS-018 TC-018.12 still cites "160.06 kB gzip of 165" for AC 7. → Cite 160.44 kB (production image build).
- **R2-2** RISK-007's no-blocking-IO row still says "0 worker kills, 0 `QueuePool limit` lines" with no
  qualifier. → Add "(backend log capture empty; the verdict rests on 0 × 5xx and 0 transport errors)", as in
  PRB-072.
- **R2-3** In this task, Step 5 still lists the round-1 versions (TS-018 1.8, RISK-007 1.18, RISK-012 1.4,
  CR-006 1.16), and "Open points" states the AC 3 item twice. PRB-046 and PRB-048 were bumped to 1.1 with no
  version-history line: neither had a history section before, and 40 of the 93 PRBs have none.
  → Bring them into line at the next edit.
- QA moved the developer's 1.2 history line from the end of the file, inside the round-1 verification list, into
  "Version history". No content change.

Open item: **Step 4 (hosted CI) is not run.** It needs the human's go-ahead to push. When the push is made, the
hosted run is recorded here and checked by QA, as in TASK-216.

### Verification run (QA, round 2)

- Trace over CR-006's 79 `links` plus TS-001, 003, 004, 005, 007, 010, 011, 012, 017, 018, 019, PRB-046, PRB-048 and
  PRB-093: 356 records, **0 errors**, 406 warnings (the baseline kinds). Over the developer's scope plus PRB-093,
  PRB-046 and PRB-048: 310 records, 0 errors, 378 warnings (matches the reported 310).
- No change under `backend/`, `frontend/`, `infra/` or `docs/design-inputs/`, so the round-1 runs still apply
  (backend 1743 passed, 10 skipped; frontend 412 passed).
- `docker compose ls`: only `infra` (running 8).

## QA review, hosted part (qa-engineer, 2026-11-16) — APPROVED

Step 4 checked with `gh run list --branch fix/review-2026-07-reliability` and `gh pr checks 40`: runs 43896524793
(push) and 43897144750 (pull_request) on `331e2724a66366eeff2ec6eda92cb6e0d6e9c161` concluded `success`, each with
the 8 jobs passing. The earlier head `ef3510f` is green too (43824313319, 43824318806). The `09bcc69` runs failed
Backend Quality and Frontend Tests (`gh run view 43823245736`); `ef3510f` changes only
`backend/tests/workers/test_retention_lock.py` and `frontend/src/api/client.test.ts`, so no product code changed
after the local evidence. The open item of round 2 is closed. R2-3 fixed in this pass; R2-1 and R2-2 stay carried
(TS-018, RISK-007).
