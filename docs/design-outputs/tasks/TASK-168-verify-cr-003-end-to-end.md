---
id: "TASK-168"
type: task
title: "Confirm RISK-010 and the anomaly reviews, and verify CR-003 end to end"
status: in_review
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-30"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: relates_to
  - target: "CR-003"
    relation: relates_to
  - target: "TASK-161"
    relation: relates_to
  - target: "TASK-162"
    relation: relates_to
  - target: "TASK-163"
    relation: relates_to
  - target: "TASK-164"
    relation: relates_to
  - target: "TASK-165"
    relation: relates_to
  - target: "TASK-166"
    relation: relates_to
  - target: "TASK-167"
    relation: relates_to
tags: ["risk", "soup", "regulatory", "cr:CR-003", "issue:sancharly/medhub#32"]
---

# TASK-168 — Confirm RISK-010 and the anomaly reviews, and verify CR-003 end to end

- **Software item / unit:** all (risk record, verification evidence, gap report). No code change
  is expected.
- **Depends on:** TASK-161..167, all merged on the branch (`relates_to`)
- **Branch:** `bug/soup-upgrades`
- **Size:** S
- **Needs:** a Docker host (Compose build and smoke run) and network access (CI on the branch
  head)
- **Checkpoint B:** this task is the end-to-end checkpoint over the whole CR.

## Objective

Confirm, with the evidence of TASK-161..167, that:

- the RISK-010 1.4 revision made at the Risk stage holds (AC-15);
- every anomaly review and escalation is complete (AC-14);
- the change works end to end (AC-16..AC-19).

The records then go to the human gate. This task implements no new control. It records the
evidence for the controls that TASK-161..165 re-implemented, so it links RISK-010 with
`relates_to`, not `mitigates`.

## Implementation detail

- **RISK-010** (1.4, `in_review` since the Risk stage):
  - Check that the path-1 statement "PRB-035 is resolved by TASK-162" is true: PRB-035 is
    `resolved`, and the build stage is on Node 24.
  - Check that the control-table entries name the records that exist (TASK-161..165, and the
    re-dated SOUP reviews).
  - If a review in TASK-161, 163 or 164 escalated a hazard-relevant, unfixed anomaly in a
    control-bearing item, re-score with a rationale under the same version and bump `updated`.
    Otherwise confirm 3 × 2 → `alarp` and change nothing.
  - Do not set `approved`.
- **AC-11 check:** no record that is not `obsolete` keeps a `relates_to` link to SOUP-033 (command
  below).
- **AC-14 check:**
  - SOUP-003, 011, 019 and 021 each carry an `anomaly_review` on or after 2026-10-29, at their
    AC-13 versions, with the sources cited by name and URL. SOUP-021's review covers every Debian
    source package.
  - CR-003's "Escalations" list has an entry or "none" for each of the four. Complete it if not.
- **AC-13 check:** each `soup_version` against the build:
  - SOUP-021 against the Compose tag;
  - SOUP-011 against `uv.lock`;
  - SOUP-003 and SOUP-019 keep 1.3.1 and 1.43.117, with the transitive versions in the body
    matching `uv.lock`.

  This is TS-013 TC-013.9.
- **TS-013** (at 1.4 from TASK-162): in "Preconditions and environment", record that TC-013.9 and
  the CR-003 end-to-end run used branch `bug/soup-upgrades` at commit `<sha>`, dated
  `<date>`. The test cases do not change.
- **End-to-end run** (AC-16..AC-18), on the branch head:
  - the pin check and `uv lock --check`;
  - the Compose build, start and smoke test (17/17), with `INFO server` showing 7.4.12;
  - the backend suite (coverage ≥ 85 %) and the frontend suite, locally;
  - every CI job green.
- **AC-19 check:** PRB-045, 035, 047 and 044 are `resolved`, each with a `## Resolution` and an
  incoming `resolves` link from CR-003. Every design record that CR-003 created or changed is
  `in_review`, apart from SOUP-033 and ADD-004 (`obsolete`). The TASKs follow QA.
- **Gap report:** run `medical-records:traceability-check` over `docs/` and commit the report as
  `docs/reports/gap-report-<YYYY-MM-DD>.md`.
- **CR-003:** tick nothing and leave its status alone. Its status change is the orchestrator's.

## Acceptance criteria

- [x] CR-003 **AC-11**: no non-obsolete record links SOUP-033.
- [x] CR-003 **AC-14**: the four reviews are complete, and the escalation list has an entry, or
      "none", per item.
- [x] CR-003 **AC-15**: the change analysis is in CR-003. RISK-010 1.4 has no SOUP-033 link, does
      not cite PRB-035 as open, and its residual is confirmed (or re-scored with a rationale).
- [x] CR-003 **AC-16**: the pin check exits 0 and `uv lock --check` succeeds on the branch head.
- [x] CR-003 **AC-17**: the stack builds and starts, the smoke test passes 17/17, and Redis
      reports 7.4.12.
- [ ] CR-003 **AC-18**: every CI job passes on the branch head. The backend suite (coverage ≥ 85 %)
      and the frontend suite pass locally.
- [x] CR-003 **AC-19**: the four PRBs are `resolved`. `traceability-check` reports 0 errors and no
      `soup_anomaly_review_stale` warning for any non-obsolete SOUP record.

## Verification

```sh
python3 infra/check_image_pins.py && (cd backend && uv lock --check)
docker compose -f infra/docker-compose.yml build && docker compose -f infra/docker-compose.yml up -d
bash infra/smoke-test.sh                                                    # 17 passed
docker compose -f infra/docker-compose.yml exec redis redis-cli INFO server | grep redis_version   # 7.4.12
(cd backend && uv run pytest --cov=app --cov-fail-under=85) && (cd frontend && npm test -- --run)
grep -rlE 'target: "?SOUP-033"?$' docs | xargs grep -L '^status: obsolete'   # no output (AC-11)
gh run list --branch bug/soup-upgrades --limit 1                           # all jobs green (AC-18)
```

Then `medical-records:traceability-check` over `docs/`. Tear the stack down with
`docker compose down`, keeping the volumes.

## Definition of Done

- [ ] All of the above is recorded under "Implementation notes and evidence".
- [ ] The gap report is committed.
- [x] No record created or changed by CR-003 is left in `draft`, apart from TASKs still under QA.

## Implementation notes and evidence (developer, 2026-10-30)

Run on branch `bug/soup-upgrades`, commit `d57ec72` (TASK-161..167 all committed), on the reference
workstation (macOS, arm64, Docker context `desktop-linux`). The only changes made by this task are
record edits (listed at the end). No source file changed.

**The branch has not been pushed, so CI on the branch head was not run.** AC-18 is therefore open
(see "Open items"). Nothing below claims a CI result.

### Results

| CR-003 AC | Command or check | Result |
|---|---|---|
| AC-16 | `python3 infra/check_image_pins.py` | exit 0 |
| AC-16 | `python3 -m unittest discover -s infra/tests` | 11 tests OK |
| AC-16 | `cd backend && uv lock --check` | "Resolved 86 packages", exit 0 |
| AC-17 | `docker compose -f infra/docker-compose.yml up -d --build` (build cache warm) | Succeeded. The images it produced have the IDs of the running containers (`infra-backend` `450032b393c4`, `infra-celery-worker` `40b33926a5c9`, `infra-frontend` `a047f4eb63aa`), so nothing was stale. Redis, Postgres, MinIO and the proxy run their pinned `tag@digest` references. `infra-createbuckets-1` exited 0 |
| AC-17 | `bash infra/smoke-test.sh` | 17 passed, 0 failed |
| AC-17 | `redis-cli INFO server` in `infra-redis-1` | `redis_version:7.4.12`. `INFO persistence`: `aof_enabled:1`, `loading:0`, `aof_last_write_status:ok` |
| AC-2 | `cat /etc/os-release`, `/etc/debian_version` in `infra-redis-1` | `Debian GNU/Linux 12 (bookworm)`, `VERSION_ID="12"`, `VERSION_CODENAME=bookworm`, 12.15 |
| AC-1, AC-3, AC-4 | `grep` of `infra/docker-compose.yml:84`, `.github/workflows/ci.yml:64`, `frontend/Dockerfile:1`, `ci.yml:114-190` | Both Redis references are identical (`redis:7.4.12-bookworm@sha256:b6b6e3dc…82f5`). Build stage `node:24.22.2-trixie-slim@sha256:54f84b4c…b6d446`. `node-version: "24"` in `frontend-quality`, `frontend-tests` and `openapi-lint` (`setup-node`). No "Node.js 20" |
| AC-8 | `importlib.metadata.version()` in the running `backend` and `celery-worker` containers | Both report anyio 4.14.2, urllib3 2.8.0, cryptography 50.0.2 (Starlette 1.3.1, boto3 1.43.117 unchanged) |
| AC-10 | `grep` of the manifest and lock; `git grep -E 'openapi-fetch' -- . ':!docs'`; the backend container's distributions | No `openapi-fetch` or `openapi-typescript-helpers` in `package.json`, `package-lock.json`, `frontend/src`, or the built bundle. `openapi-typescript` 7.13.0 stays (dev tool). The backend image has no `openapi*` distribution |
| AC-18 (local) | `cd backend && DOCKER_CONTEXT=desktop-linux uv run --frozen pytest --cov=app --cov-fail-under=85` | 499 passed, 0 skipped (the real-DB tests ran), coverage 91.71 %, threshold 85 % met |
| AC-18 (local) | `uv run --frozen ruff check .`; `black --check .`; `mypy app` | "All checks passed"; 220 files unchanged; "no issues found in 124 source files" |
| AC-18 (local) | `git archive HEAD frontend` into a scratch directory, then in `node:24.22.2-trixie-slim@sha256:54f84b4c…` (v24.22.2, npm 11.19.1): `npm ci`, `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build` | `npm ci` added 466 packages. Lint 0 warnings (`--max-warnings 0`). Typecheck exit 0. Vitest: 27 files, 155 tests passed. Build succeeded: 16 files in `dist/` |
| AC-5 (local part) | SHA-256 of the 16 `dist/` files of the clean Node 24 build against the files served by the running `infra-frontend-1` (excluding nginx's `50x.html`) | Identical. So the 17/17 smoke run covers the Node 24 bundle, and the host `node_modules` that a local build copies (PRB-050) did not change the output |
| AC-13 / TC-013.9 | A script compared every non-obsolete `soup_version` with `backend/uv.lock`, `frontend/package-lock.json`, and the `tag` of the image references in Compose and the Dockerfiles | 27 of 27 package records match (17 Python, 10 npm). The images match: SOUP-021 7.4.12, SOUP-020 16.15, SOUP-022 and SOUP-023 `RELEASE.…`, SOUP-024 1.31.8, SOUP-001 3.12.15. SOUP-003 and SOUP-019 keep 1.3.1 and 1.43.117; their bodies name the locked transitives (anyio 4.14.2, idna 3.18; urllib3 2.8.0, botocore 1.43.117, s3transfer 0.19.3, jmespath 1.1.0), which equal `uv.lock`. SOUP-011's body names cffi 2.0.0 and pycparser 3.0, which equal `uv.lock` |
| AC-19 | Statuses (below), `traceability-check` | 0 errors, no `soup_anomaly_review_stale`. See the gap report |

`docker compose down` from the Verification block was **not** run: the stack is left running, on the
orchestrator's instruction.

### AC-11 and decision D-6

`grep -rlE 'target: "?SOUP-033"?$' docs` returns one file, TASK-165. `| xargs grep -L '^status: obsolete'`
returns the same file, because TASK-165 is not `obsolete`. So the command in the Verification
block, read literally, is **not** empty. That is what D-6 intends: TASK-165 is the task that
removed the package, and it keeps its `relates_to` link to SOUP-033 by decision D-6. Under CR-001,
neither CR-001 nor TASK-158 linked SOUP-018, so this is a new choice, not a precedent. I
read AC-11 as **"no non-obsolete record other than TASK-165 links SOUP-033"**. Under that reading
AC-11 holds: CR-003, ADD-023 and RISK-010 have no link to SOUP-033 (checked in the files), SOUP-033
is `obsolete` 1.2 with a change-log entry citing PRB-044 and CR-003, and the gap report shows one W6
(TASK-165 → SOUP-033). **For the human to confirm at CR close**, as the QA review of TASK-165 also
says.

### AC-14, AC-13: the four SOUP reviews

| Record | Version / `soup_version` | `anomaly_review` | Record status | Named sources with URL | Result |
|---|---|---|---|---|---|
| SOUP-003 | 1.2 / 1.3.1 (anyio 4.14.2, idna 3.18) | 2026-10-29 | `in_review` | yes | none found; the 3 anyio advisories are fixed at 4.14.2 |
| SOUP-011 | 1.2 / 50.0.2 | 2026-10-29 | `in_review` | yes | none found; GHSA-g6cj-pr64-35w5 fixed at 50.0.0 |
| SOUP-019 | 1.3 / 1.43.117 (urllib3 2.8.0) | 2026-10-29 | `in_review` | yes | none found; the 3 urllib3 advisories are fixed at 2.8.0 |
| SOUP-021 | 1.3 / 7.4.12 | 2026-10-29 | `in_review` | yes | Redis findings carry forward (CVE-2026-92925, GHSA-2r7g-8hpc-rpq9, not reachable); 97 Debian base-OS entries with no bookworm fix, none reachable through the Redis protocol; end-of-support finding cleared (Debian LTS to 2028-06-30) |

None of the four says "Not yet performed". Each has a dated "Anomaly list review" section with
named sources. SOUP-021 covers the 64 source packages of the image. SOUP-033 is `obsolete`.
The CR-003 "Escalations" list has an entry for every item, each "none" (complete, so I only added a
confirmation line). No RISK was raised. PRB-049 and PRB-050 are tooling defects found during
TASK-161 and the QA of TASK-162. They are open and outside this CR.

### AC-15: RISK-010 and the change analysis

- The change analysis (Risk stage, 2026-10-29) is in CR-003 and covers the six changes and the RISK
  records linked to SOUP-003, 011, 019, 021 and 033. It states that no hazard is added and that
  class B is unchanged.
- **RISK-010 1.4 holds, and I changed nothing in it.** Checks:
  - no `relates_to` SOUP-033 link remains (frontmatter checked);
  - the path-1 statement "PRB-035 is resolved by TASK-162, Node 24 LTS, end of life 2028-04-30" is
    true: PRB-035 is `resolved` 1.2 with a `## Resolution`; `frontend/Dockerfile` and `ci.yml` are on
    Node 24 (above); the dates match the Node.js schedule that TASK-162's QA re-read;
  - PRB-034 "still open" is true (`open`); PRB-042 and PRB-043 are `open`; PRB-044, 045 and 047
    are `resolved`; PRB-035 is not cited as open anywhere in the record;
  - every ID the record cites exists (82 IDs; the only one without a record is CR-002, named in
    prose, reserved and not yet created). The control table names TASK-154..158, TASK-161..164,
    SR-028, SR-001, SR-022, SR-025, TS-001, TS-008, TS-011, TS-013 (TC-013.5..9 exist) and
    TR-001, all present;
  - no CR-003 review escalated a hazard-relevant, unfixed anomaly (the escalation list), so there is
    no input to re-score. 3 × 2 → `alarp` is the value `risk_matrix` row 3, column 2 gives, and the
    parser's check of every RISK's `acceptability` against the matrix passes.
- **Observation for the human:** RISK-010 is already `approved` (1.4, `approval_note:
  self-approved`, `approved_on: 2026-10-29`, committed in 3443d03). The task text and AC-19 expect
  it `in_review`. The approval record was written before this confirmation, and the file is
  unchanged since. I did not change the status or the approval record, and I cannot compute
  `approved_digest`. If the human wants the confirmation to precede the approval, RISK-010 must go
  back to review (a version bump); that is the human's decision.

### AC-19: record statuses

- PRB-045, PRB-035, PRB-047 and PRB-044: `resolved` 1.2, each with a `## Resolution`, and CR-003
  carries `resolves` links to all four (frontmatter checked; the parser's E9 passes).
- `in_review`: ADD-023 (1.1), RISK-011 (1.2), SOUP-003 (1.2), SOUP-011 (1.2), SOUP-019 (1.3),
  SOUP-021 (1.3), TS-001..TS-013 (13 records), and this TASK. `obsolete`: SOUP-033 (1.2) and ADD-004
  (1.1). `approved` by QA: TASK-161..167. `open`: CR-003 (unchanged).
- **Exception:** RISK-010 is `approved` (see above), not `in_review` as AC-19 literally requires.
- `traceability-check` over the whole project (fallback parser, 350 records): 0 errors, 50
  warnings, 0 class-gated findings, no `soup_anomaly_review_stale`. The report is
  [`docs/reports/gap-report-2026-10-30.md`](../../reports/gap-report-2026-10-30.md). The warnings are
  40 × W5 (CR-003 records held at `in_review`, plus the old TASK-132 → TASK-101), 1 × W6 (TASK-165,
  D-6), 3 × W1, 4 × W2, 1 × W7 (SR-017/018/019/026, pre-existing) and 1 × W3 (RISK-012, CR-002).

### Items deferred to TASK-168 by the QA reviews of TASK-161..167

| From | Item | Disposition |
|---|---|---|
| TASK-161 | CI: `backend-tests` with the new service container, and `image-pins` | **Open** (pending push) |
| TASK-161 | [LOW] PRB-045 says the workstation has no container runtime | Closed: PRB-045 now says it is superseded by TASK-161 (Alpine 3.21.9 read from the old image). `updated` 2026-10-30 |
| TASK-161 | [LOW] PRB-049 cites line 5 for the import | Closed: now "line 6". `updated` 2026-10-30 |
| TASK-162 | CI part of AC-5 (the `build` job), AC-18, frontend jobs on Node 24 | **Open** (pending push). The local half is done: 27 files, 155 tests, build and lint on Node 24, bundle identical to the running container |
| TASK-162 | TS-001..013 name Node 24 next to a commit whose recorded run used Node 20; no TR records a Node 24 run | Partly closed: TS-013's environment now states the branch and commit of this run (`d57ec72`, 2026-10-30), and this record holds the Node 24 evidence. The TR for the release is not written (no release yet), and it should copy the evidence from here |
| TASK-162 | [LOW] PRB-035 "byte-identical" claim | Already closed: PRB-035:111-113 states the 16-file SHA-256 comparison |
| TASK-162 | `npm ci` reports 16 npm audit findings (4 moderate, 9 high, 3 critical) | Closed (dispositioned). `npm audit --omit=dev` on a `git archive HEAD` copy of `frontend/`, in the pinned `node:24.22.2-trixie-slim` image (2026-10-30), reports one production advisory, GHSA-qwww-vcr4-c8h2 in `react-router` 7.18.0 (shown twice, through `react-router-dom`; 2 high entries, exit 1). SOUP-027 (`:76-81`, `:104-105`) already judges it: it affects the unstable RSC mode, which MedHub does not use. Every other finding is dev-only, and development tooling is not SOUP. The lock is unchanged by CR-003 |
| TASK-162, TASK-163 | PRB-050 (`frontend/` has no `.dockerignore`) | **Open**, its own CR. Local check above shows no effect on today's output |
| TASK-163 | CI collects `tests/db/test_crypto_known_answer.py` (AC-9, `backend-tests`) | **Open** (pending push). Locally the 3 KAT tests run and pass inside the 499 |
| TASK-163 | Running Compose `backend` predates the lock change; AC-17 rebuilds | Closed: stack rebuilt from HEAD, the backend and worker report cryptography 50.0.2 |
| TASK-163 | [LOW] "Verified by" cell repeats TS-008 | Already closed (RISK-011:64 reads `TS-008 (incl. TC-008.5)`) |
| TASK-163 | [LOW] KAT fixture not committed before the lock change | Not closable (history). Recorded by QA, mitigated by QA's independent regeneration under 49.0.0 |
| TASK-164 | [MEDIUM] SOUP-003 and CR-003 omit the `CancelScope` fix | Already closed (`CancelScope` is in SOUP-003 and in the CR-003 §7.4 row) |
| TASK-164 | [LOW] SOUP-019 2.8.0 paragraph lists a subset | Already closed (SOUP-019:82-87 names the omitted fixes) |
| TASK-164 | PRB-047 date "2026-07-07" and present tense | Already closed (PRB-047:53) |
| TASK-164 | CI "production dependency set" step on the branch head | **Open** (pending push). Locally the AC-8 versions are confirmed in the running containers |
| TASK-165 | D-6: the AC-11 check applies the D-6 reading | Closed, **for the human to confirm** (above) |
| TASK-165 | [LOW] SOUP-033 banner and requirements tense | Already closed (SOUP-033:22 and :26-27) |
| TASK-165 | CI frontend jobs and `openapi-lint` | **Open** (pending push) |
| TASK-166 | None deferred | — |
| TASK-167 | CI frontend jobs and `openapi-lint` (AC-18) | **Open** (pending push) |
| TASK-167 | CR-003 `status: open` although tasks are committed; the human should set `in_progress` | **Open**, the orchestrator's (not changed here) |
| TASK-167 | `docs/templates/task.md:76, :90` still say "generated client" | **Open**, outside AC-12; to be raised separately |
| TASK-167 | [LOW] PRB-044 `updated`, suite line | Already closed (`updated` 2026-10-30; the suite line says the results come from the pinned image) |

### Open items

- [ ] **CI on the branch head (CR-003 AC-18): pending push; to be verified by the orchestrator with
      `gh run` on the pushed head.** The six jobs (`backend-tests`, `image-pins`, `frontend-quality`,
      `frontend-tests`, `openapi-lint`, `build`) must be green, with Node v24 in the frontend job
      logs, and the `build` job's `npm ci` and `npm run build` in the Node 24 stage (AC-5). Not run,
      not recorded as passed. This is also the CI evidence for the AC-9 test (TASK-163), the AC-8
      dependency step (TASK-164), and the Redis service container (TASK-161).
- [ ] The human confirms the D-6 reading of AC-11.
- [ ] The human decides what to do with RISK-010 1.4 being already `approved` (above).
- [ ] The human approves the `in_review` records and sets CR-003 `in_progress`, then closes it.
- [ ] PRB-049, PRB-050 and the `docs/templates/task.md` wording stay open outside this CR.

### Deviations and assumptions

- I edited records beyond TASK-168 and the gap report, to close QA findings that were assigned to
  "the next edit": PRB-045 (one paragraph) and PRB-049 (one line number), each `updated`
  2026-10-30 with the version kept. Also TS-013 (environment line, as the task requires, and the
  missing 1.4 history entry for TASK-162's change, kept at version 1.4), and CR-003 (one line in
  "Escalations", version 1.1 → 1.2 with a history line; status and the AC boxes untouched).
- The compose rebuild used the warm layer cache. The images came out identical to the running ones,
  which is the evidence that the running stack was built from HEAD. A `--no-cache` rebuild was not
  done.
- No test account was created, so none needed deleting. The session round trip through the proxy was
  not repeated: Redis, its image and its data volume are unchanged since QA's round trip on TASK-161.
- The traceability parser is a throwaway script (no MedTrace tooling in the repository), the same
  procedure as the earlier gap reports. It does not compute `modified_after_approval`.
- None of the acceptance-criteria boxes above is ticked: ticking is QA's approval.

## QA review — local part (2026-10-30)

**Verdict (local part): PASS. Approval pending CI on the pushed head (AC-18).** The status stays
`in_review`. There is no CRITICAL, HIGH or MEDIUM finding.

- QA re-checked each local claim and ticked the boxes that are met locally: AC-11 (under D-6),
  AC-14, AC-15, AC-16, AC-17 and AC-19, plus the third Definition of Done item.
- Three boxes stay open: AC-18, and the first two Definition of Done items. They need the CI run
  and the commit.
- The local half of AC-18 passed: the backend and frontend suites, below.

### Judgements for the human

- **RISK-010 `approved` 1.4, against AC-19's "`in_review`".** QA's recommendation is to accept the
  deviation and record it at CR close. The record does not need to go back to review.
  - The human approves RISKs, and the approval is the Risk-stage gate's acceptance of the 1.4
    residual. RISK-010's own 1.4 history says that "acceptance is the human's, through approval
    of this version".
  - The same history entry anticipates this task: "TASK-168 confirms the PRB-035 statement once
    TASK-162 has landed". The approval was given knowing that the confirmation would follow.
  - The file is unchanged since 3443d03. QA confirmed each statement this task had to check:
    PRB-035 is `resolved`, Node 24 is in the Dockerfile and in CI, there is no SOUP-033 link, and
    3 × 2 → `alarp` is unchanged. Nothing calls for a re-score.
  - Sending it back to review would bump the version without changing content.
  - Precondition: the human checks in MedTrace that RISK-010 shows no `modified_after_approval`.
    Only the tool can compute `approved_digest`. If it does show the finding, the record returns
    to review.
  - CR-003 should then record this reading of AC-19: "every changed record is `in_review` or
    approved by the human at its own gate", in the same way as the CR-001 AC-18 reading.
- **The D-6 reading of AC-11 is sound.**
  - D-6 is part of the plan the human approved. It names TASK-165's link explicitly ("so does
    TASK-165's link").
  - A link from the task that removed an item to the retired item is useful configuration
    traceability (§8), and it is the gap report's single W6.
  - The literal Verification command does not encode D-6. AC-11's wording should be amended, or
    the reading recorded, at CR close.
  - One correction to this record's account of D-6 is listed under Findings.

### Findings

- **[LOW] The D-6 precedent is misstated.** In "AC-11 and decision D-6", the sentence "it keeps
  its `relates_to` link to SOUP-033, like CR-001 for SOUP-018" is wrong. No record links SOUP-018:
  neither CR-001 nor TASK-158 links it (`grep -rlE 'target: "?SOUP-018"?$' docs` finds nothing).
  D-6's precedent is about the CR's own link. Keeping TASK-165's link is a new choice, recorded in
  D-6. Fix: "TASK-165 keeps its `relates_to` link to SOUP-033 by decision D-6. Under CR-001,
  neither CR-001 nor TASK-158 linked SOUP-018."
- **[LOW] The "Sources cited (URLs)" counts cannot be reproduced.** In the AC-14/AC-13 table, the
  counts are 12 / 8 / 15 / 12. A unique-URL count of each "Anomaly list review" section gives
  14 / 11 / 16 / 10 (SOUP-003, 011, 019, 021). The reviews themselves are complete: QA reviewed
  them in TASK-161, 163 and 164, and none of the four files has changed since. Fix: state how the
  counts were made, or replace the column with "named sources with URL: yes".
- **[LOW] TASK-168 is still at `version: "1.0"`.** TASK-161..167 were bumped to 1.1 when they were
  handed to QA. Fix: set 1.1 with this handoff.

### Deferred QA items

QA checked each disposition in the developer's table against the files. Each row marked "Already
closed" or "Closed" holds:

- PRB-045 `:60-63` and PRB-049 `:19` (line 6, which is correct);
- PRB-035 `:111-113`;
- RISK-011 `:64`;
- the `CancelScope` text in SOUP-003 (`:73`, `:75`, `:92`) and in the CR-003 §7.4 row `:251`;
- SOUP-019 `:82-87`;
- PRB-047 `:38-39` and `:53`;
- SOUP-033 `:22` and `:26-27`;
- PRB-044 `:9` and `:148`;
- the rebuild of the backend container.

One row should be refined:

- **npm audit findings (from TASK-162).** `npm audit --package-lock-only --omit=dev` on HEAD's
  lock reports one advisory in the production set: GHSA-qwww-vcr4-c8h2 in `react-router`
  7.18.0, counted twice through `react-router-dom`. SOUP-027 already judges it, at `:76-81` and
  `:104-105`: it affects the unstable RSC mode, which MedHub does not use. The other findings are
  dev-only, and development tooling is not SOUP. Suggested disposition: "production subset
  dispositioned in SOUP-027; the rest are dev-only". The row should not stay "Open".

### Remaining for the CI step (AC-18)

On the pushed head, `gh run` must show all six jobs green: `backend-tests`, `image-pins`,
`frontend-quality`, `frontend-tests`, `openapi-lint` and `build`.

- Node v24 appears in the frontend job logs.
- In the `build` job, `npm ci` and `npm run build` run in the Node 24 stage (AC-5).
- `backend-tests` collects `tests/db/test_crypto_known_answer.py` (AC-9) and uses the
  `redis:7.4.12-bookworm@sha256:b6b6e3dc…` service.
- The "production dependency set" step passes (AC-8).

After that, QA ticks AC-18 and the first Definition of Done item, then sets `approved`. The
second Definition of Done item (gap report committed) is met by the commit of this task.

### Verification run (QA, 2026-10-30)

Inputs and reuse:

- `backend/`, `infra/` and `.github/` are unchanged since 4df23d2, which QA tested in TASK-164.
- `frontend/` is unchanged since 89f84c9. `git rev-parse 89f84c9:frontend HEAD:frontend` gives the
  same tree, `b1217f64…`.
- The frontend lint, typecheck, test and build results are therefore reused from QA's TASK-165
  runs: round 1 on an identical tree (`diff -r` confirmed), and round 2's build of 89f84c9. Every
  other check below was re-run on HEAD d57ec72.

| Check | Result |
|---|---|
| `python3 infra/check_image_pins.py`; `python3 -m unittest discover -s infra/tests` | exit 0; OK |
| `cd backend && uv lock --check` | "Resolved 86 packages", exit 0 |
| `DOCKER_CONTEXT=desktop-linux uv run --frozen pytest --cov=app --cov-fail-under=85` (re-run) | 499 passed, 0 skipped (real-DB tests ran), coverage 91.71 % |
| `ruff check .`; `black --check .`; `mypy app` | All checks passed; 220 files unchanged; no issues in 124 source files |
| Frontend, in `node:24.22.2-trixie-slim@sha256:54f84b4c…` from a clean copy (reused, see above) | `npm ci` 466 packages; lint 0 warnings; typecheck 0; Vitest 27 files, 155 tests; build 16 files |
| `docker compose -f infra/docker-compose.yml build` (warm cache), then image IDs against the running containers | `infra-backend` `450032b393c4`, `infra-celery-worker` `40b33926a5c9` and `infra-frontend` `a047f4eb63aa` equal the running containers. The redis, postgres, minio and reverse-proxy containers run exactly the Compose `tag@digest` references |
| SHA-256 of the files served by `infra-frontend-1` (excluding `50x.html`) against QA's clean Node 24 build of the same tree | 16 of 16 identical |
| `bash infra/smoke-test.sh` | 17 passed, 0 failed |
| `redis-cli INFO server`; `/etc/os-release` in `infra-redis-1` | `redis_version:7.4.12`; Debian 12 (bookworm) 12.15 |
| `importlib.metadata` in `backend` and `celery-worker` | anyio 4.14.2, urllib3 2.8.0, cryptography 50.0.2, starlette 1.3.1, boto3 1.43.117, idna 3.18, botocore 1.43.117, s3transfer 0.19.3, jmespath 1.1.0, cffi 2.0.0, pycparser 3.0. No `openapi*` distribution |
| `openapi-fetch` | Absent from HEAD's manifest and lock, and `git grep` outside `docs/` finds nothing (TASK-165 QA; the tree is unchanged) |
| TC-013.9: QA's own script compares every non-obsolete `soup_version` with `uv.lock`, the `package-lock.json` top-level entries and the image tags in Compose, the Dockerfiles and `ci.yml` | 27 of 27 packages match, and the 6 image-based records match their tags (SOUP-001, 020, 021, 022, 023, 024). The transitive versions named in SOUP-003, 011 and 019 equal the running containers |
| AC-14: SOUP-003, 011, 019, 021 | `in_review`; `anomaly_review` 2026-10-29; `soup_version` 1.3.1, 50.0.2, 1.43.117, 7.4.12; no "Not yet performed". `git diff 4df23d2 HEAD -- docs/soup docs/risks` touches only SOUP-033. The CR-003 escalation list has a "none" entry for each item |
| AC-19 statuses: every record changed on the branch since f807bfb, plus the working tree | `resolved`: PRB-035, 044, 045, 047, each with `## Resolution` and an incoming `resolves` from CR-003. `in_review`: ADD-023, RISK-011, SOUP-003/011/019/021, TS-001..013, TASK-168. `obsolete`: ADD-004, SOUP-033. `approved`: TASK-161..167 (QA) and RISK-010 (see above). `open`: CR-003, PRB-049, PRB-050. No `draft` |
| `traceability-check`, whole project: the fallback parser plus a QA cross-check script for W1-W4, W7 and the risk rules | 350 records, 0 errors. W5 40, W6 1 (TASK-165 → SOUP-033), W1 3, W2 4, W3 1, W7 1, W4 0. No `soup_*` findings, and no `risk_unscored` or `risk_not_acceptable` |
| `docs/reports/gap-report-2026-10-30.md` | Accurate. The counts equal QA's (50 warnings), the 40 W5 rows add up to the per-target triage, and the inventory sums to 350 |
| TS-013, CR-003, PRB-045, PRB-049 diffs | Environment and history lines only (TS-013 stays at 1.4, `in_review`). CR-003 is at 1.2 with one confirmation line, and its status and boxes are untouched. The PRB edits are as the dispositions say |
