---
id: "TASK-159"
type: task
title: "Re-assess RISK-010 and verify CR-001 end to end"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: relates_to
  - target: "TASK-154"
    relation: relates_to
  - target: "TASK-155"
    relation: relates_to
  - target: "TASK-156"
    relation: relates_to
  - target: "TASK-157"
    relation: relates_to
  - target: "TASK-158"
    relation: relates_to
  - target: "TASK-160"
    relation: relates_to
  - target: "RISK-012"
    relation: relates_to
tags: ["risk", "soup", "regulatory", "cr:CR-001", "issue:sancharly/medhub#26"]
---

# TASK-159 — Re-assess RISK-010 and verify CR-001 end to end

- **Software item / unit:** all (risk record and verification evidence; no code change expected)
- **Depends on:** TASK-154, TASK-155, TASK-156, TASK-157, TASK-158 (all merged on the branch), as
  `relates_to` links
- **Branch:** `bug/soup-pinning`

## Objective

When the controls RISK-010 assumes exist and are verified, revise RISK-010 (IEC 62304 §7.4.3,
CR-001 scope item 7), complete TS-013 with the SR-028 AC-6 case, and run the full verification of
CR-001 so the records can go to the human gate. The task implements no new control: it records the
evidence for the controls TASK-154..158 implemented, hence `relates_to` RISK-010, not `mitigates`.

## Implementation detail

- **RISK-010** (approved: `version` 1.3, `updated` bumped, approval record removed, `in_review`):
  - Control table:
    - "Every image and dependency pinned to an immutable version" | Design | CR-001: TASK-155
      (images), the committed lock files, TASK-157 / TASK-158 (manifest corrections) | TS-013
      TC-013.5, TC-013.7, TC-013.8.
    - New row "CI rejects any image reference without a digest" | Protective | TASK-156 | TS-013
      TC-013.5, TC-013.6.
    - "Anomaly and advisory review per version, at least yearly and before release" | Protective |
      TASK-154 | the dated reviews in SOUP-001..035 (SOUP-018 obsolete); TS-013 TC-013.9.
  - Residual risk: the text no longer states the PRB-001 / TASK-154 preconditions as unmet. Confirm
    probability 1 using the CR-001 Risk-stage rationale (§7.4 analysis). Re-score against
    `risk_matrix` only if TASK-154 escalated an anomaly that leaves a control-bearing SOUP item with
    a known unfixed defect. Write the rationale either way. `acceptability` is derived from the
    scores (3 × 1 → `acceptable`), never typed by choice. "Decided by" stays pending; the human's
    approval of the record is the acceptance.
  - Risks introduced by controls: keep "pinning delays security patches". Add what TASK-154 found
    for MinIO (D-4), referencing its PRB if one was raised.
  - Remove the `relates_to` link to SOUP-018 (obsolete since TASK-158). Keep the other 34.
- **TS-013** (at 1.2): add `TC-013.9` | SR-028 | review: each non-obsolete `soup` record against
  `backend/uv.lock`, `frontend/package-lock.json` and the pinned image tags, plus
  `traceability-check` | every `soup_version` equals the version the build resolves, and every
  non-obsolete record has a sourced `anomaly_review` within `soup_anomaly_max_age_days` | no
  mismatch, no `soup_anomaly_review_stale` warning. Check that TC-013.5..9 together cover SR-028
  AC-5 and AC-6 (CR-001 AC-15), and update "Preconditions and environment" to the commit tested.
- **CR-001**: confirm the AC-12 escalation list written by TASK-154 is present. Tick nothing in the
  CR: its status change is the orchestrator's.
- **Gap report**: run `medical-records:traceability-check` over `docs/` and commit the report as
  `docs/reports/gap-report-<YYYY-MM-DD>.md`.

## Acceptance criteria

- [x] CR-001 **AC-14**: RISK-010 revised as above; residual confirmed at 1 or re-scored with
      rationale; `acceptability` derived; preconditions no longer stated as unmet; SOUP-018 link
      removed.
- [x] CR-001 **AC-15**: TS-013 has test cases with expected results for SR-028 AC-5 (TC-013.5..8)
      and AC-6 (TC-013.9), and still `verifies` SR-028.
- [ ] CR-001 **AC-16**: every job in `.github/workflows/ci.yml`, `image-pins` included, is green on
      the branch head; backend and frontend suites pass locally; the pinned stack passes the smoke
      test after the TASK-157/158 image changes (AC-5 re-run).
- [x] CR-001 **AC-18**: `traceability-check` over the whole project reports 0 errors and no
      `soup_anomaly_review_stale` warning for a non-obsolete SOUP record. Every record created or
      changed by CR-001 is `in_review`, or `obsolete` for SOUP-018. TASK records follow QA's own
      transitions.

## Verification

```sh
cd backend && uv lock --check && uv run ruff check . && uv run black --check . && uv run mypy app && uv run pytest --cov=app --cov-fail-under=85
cd frontend && npm run lint && npm run typecheck && npm test -- --run
python3 -m unittest discover -s infra/tests && python3 infra/check_image_pins.py
docker compose -f infra/docker-compose.yml build && docker compose -f infra/docker-compose.yml up -d && bash infra/smoke-test.sh; docker compose -f infra/docker-compose.yml down
gh run list --branch bug/soup-pinning --limit 1    # all jobs green on the head commit
```

Then run `traceability-check` and list the changed records' statuses:
`git diff --name-only origin/main -- docs/ | xargs grep -H '^status:'`.

## Definition of Done

- [x] RISK-010 and TS-013 `in_review`; gap report committed with 0 errors
- [x] Every CR-001 acceptance criterion has its evidence named in the task that satisfies it

## Implementation notes

Records only; no source, manifest or infrastructure file changed.

- **RISK-010 1.2 → 1.3** (`approved` → `in_review`, approval record and `approval_note` removed,
  version-history section added).
  - Control table: the pinning row names TASK-155, the lock files and TASK-157/158, verified by the
    AC-3 pin check and TS-013 TC-013.5..8. A new protective row covers the CI pin check (TASK-156,
    TC-013.5/6). The review row names TASK-154 and PLAN-002, verified by the dated reviews in
    SOUP-001..017 and SOUP-019..035 and by TC-013.9.
  - `cause` and Sequence of events: no longer name the floating tags. They state the two paths
    that remain: an unreviewed change of a pinned version, and an anomaly with no fix path (MinIO).
  - `relates_to` SOUP-018 removed (34 SOUP links remain), and `relates_to` RISK-012 added (shared
    MinIO path).
- **Residual re-scored: 3 × 1 → 3 × 2, `acceptability: alarp`.** The task's re-score condition
  was triggered: TASK-154 escalated a control-bearing SOUP item with known, unfixed defects (MinIO
  carries SSE, SR-022; PRB-042, PRB-043).
  - One residual per record, and the worst path governs. Path 1 (every item except MinIO) is
    probability 1, using the CR-001 Risk-stage rationale. Path 2 (SOUP-022/023) stays at the initial
    probability 2, because the review cannot lead to a fix (D-4). That is the input stated in
    RISK-012, applied by the human's decision of 2026-10-22.
  - Severity stays 3. The severity-4 substitution harm is RISK-012's.
  - `acceptability` derived from `docs/medtrace.yml` `risk_matrix[3-1][2-1]` = `alarp`, computed,
    not typed.
  - The "ALARP justification" section states that the residual is not justified for a release:
    reduction is practicable under CR-002, and there is no release before CR-002. "Decided by"
    stays pending.
- **TS-013 1.2 → 1.3** (it was approved after TASK-158, so it is bumped instead of extending the
  1.2 entry; `approved` → `in_review`, approval record removed).
  - TC-013.9 added for SR-028 AC-6, with a coverage note for AC-5/AC-6.
  - TC-013.7 moved from the review level to the integration level with TC-013.8 (the carried LOW
    from TASK-158's QA), and the `level:integration` tag added.
  - Environment names the commit tested.
- **CR-001** stays at 1.4: a dated TASK-159 outcome note under "RISK-010 residual" and a line in the
  1.4 history entry. No scope or AC change. AC-12's escalation list (TASK-154) is present.
- **Gap report** `docs/reports/gap-report-2026-10-22.md` written (to be committed with this task).
- No new defect found, so no PRB was raised.

## Evidence

Run on the reference workstation, 2026-10-22, on `7ef8f93` plus this task's record changes.

| Check (CR-001 AC) | Command | Result |
|---|---|---|
| Lock current (AC-16, TC-013.7) | `cd backend && uv lock --check` | exit 0, "Resolved 86 packages" |
| Backend lint (AC-16) | `uv run ruff check .` | exit 0, "All checks passed!" |
| Backend format (AC-16) | `uv run black --check .` | exit 0, 219 files unchanged |
| Backend types (AC-16) | `uv run mypy app` | exit 0, no issues in 124 source files |
| Backend suite (AC-16) | `uv run pytest --cov=app --cov-fail-under=85 -q` | 496 passed, 0 failed, 0 skipped; coverage 91.71 % (≥ 85 %) |
| Frontend lint (AC-16) | `cd frontend && npm run lint` | exit 0 |
| Frontend types (AC-16) | `npm run typecheck` | exit 0 |
| Frontend suite (AC-16) | `npm test -- --run` | 27 files, 155 tests passed |
| Pin-check unit tests (AC-16, TC-013.6) | `python3 -m unittest discover -s infra/tests` | 11 tests, OK, exit 0 |
| Pin check (AC-3, AC-16, TC-013.5) | `python3 infra/check_image_pins.py` | exit 0, no output |
| OpenAPI contract (AC-16, job `openapi-lint`) | `uv run python -m app.export_openapi --output <scratch>/openapi.json` (CI env values); `npx --no-install openapi-typescript <scratch>/openapi.json -o <scratch>/openapi.ts` | Export and generated types byte-identical to the committed `backend/openapi/openapi.json` and `frontend/src/api/generated/openapi.ts`. The `@redocly/cli lint` step was **not** run locally: it is not installed and would need a download. CI runs it |
| Production dependency set (AC-8, AC-9, TC-013.8) | `docker run --rm --entrypoint python infra-backend -c "…import boto3; sys.exit(find_spec('fakeredis') is not None)"` | exit 0 (Compose-built image from the same `backend/Dockerfile`) |
| Pinned stack (AC-5) | `docker compose -f infra/docker-compose.yml build` then `up -d` | both exit 0; running images nginx `1.31.8-alpine@sha256:e2d9…`, postgres `16.15@sha256:9e2c…`, redis `7.4.11-alpine@sha256:8920…`, minio `RELEASE.2025-09-07T16-13-09Z@sha256:14ce…`; backend `healthy` |
| Smoke test (AC-5) | `bash infra/smoke-test.sh` | **17 passed, 0 failed**, exit 0 |
| Teardown | `docker compose -f infra/docker-compose.yml down` (no `-v`) | exit 0; volumes `infra_postgres_data`, `infra_redis_data`, `infra_minio_data` kept |
| TC-013.9 (AC-15, SR-028 AC-6) | Review aid that compares each non-obsolete `soup_version` with `backend/uv.lock`, the top-level `frontend/package-lock.json` entries and the pinned image tags, and checks `anomaly_review` age and cited sources | 34/34 PASS: every version matches the build, every review is dated 2026-10-22 (0 d ≤ 365 d) and cites 4–15 source URLs; SOUP-018 obsolete, skipped |
| `traceability-check` (AC-18, TC-013.1) | whole project, fallback parser (see the gap report) | 339 records, **0 errors**, 96 warnings, none `soup_anomaly_review_stale` |
| CI on the branch head (AC-16) | `gh run list --branch bug/soup-pinning` | **Pending.** The last run, 39767474884, is green on `e836c58`. `3a5eed0`, `7ef8f93` and this task's commit are not pushed yet. The orchestrator confirms after the push |

### Statuses of the records CR-001 changed (AC-18)

`git diff --name-only origin/main...HEAD -- docs/` plus this task's changes, 68 records, gap
reports excluded:

- `in_review` (37): RISK-010, RISK-012, TS-013, and SOUP-001..017 and SOUP-019..035.
- `obsolete` (1): SOUP-018.
- `approved` by the human (4): SR-028, ADD-024, RISK-007, TS-007.
- `approved` by QA (6): TASK-154..158 and TASK-160.
- `in_review`: TASK-159 (this task).
- Change-request and problem-report status sets:
  - CR-001 is `in_progress`.
  - PRB-001, PRB-002, PRB-033 and PRB-037 are `resolved` (AC-17).
  - PRB-034..036 and PRB-038..048 are `open`: raised by CR-001 tasks, and not resolved by CR-001
    by decision.

## QA review (2026-10-22)

**Verdict: APPROVED** (`in_review → approved`). There is no CRITICAL, HIGH or MEDIUM finding.

**Records that stay `in_review` for the human:** RISK-010, TS-013 and RISK-012, and SOUP-001..017
and SOUP-019..035.

**Acceptance criteria:**
- AC-14, AC-15 and AC-18 are confirmed by QA. The architect ticked them in the record; QA's
  confirmation is this review.
- AC-16 stays open for one item only: the CI run on the pushed head. Everything that can run
  locally passes (see below). The orchestrator ticks AC-16 once `gh run list` shows every job
  green on the final head.

### Findings

- **[LOW] RISK-010 names the wrong owner of the SSE control.**
  `docs/risks/RISK-010-unreviewed-soup-change.md`, Residual risk, path 2, calls SR-022 server-side
  encryption "RISK-001's at-rest control". In the register, that control belongs to RISK-011:
  `RISK-011…md:70`, "Server-side encryption enforced on the object store … SR-022". RISK-001
  carries no SR-022 control. The frontmatter `harm` ("re-enables the harms of RISK-001, RISK-005
  or RISK-008") also leaves out RISK-011 and RISK-007, which are the harms path 2 actually
  re-enables.
  → Change "RISK-001's at-rest control" to "RISK-011's at-rest control". Add RISK-011 (and
  RISK-007) to `harm` and to the "## Harm" body. Scores are unaffected. The record is still
  `in_review`, so the fix can go in before the commit, under the same 1.3.

Observations (no action needed):
- **AC-18 wording.** AC-18 literally reads "every record created or changed by this CR is
  `in_review`, or `obsolete` for SOUP-018". That cannot hold literally:
  - PRB and CR records use their own status sets;
  - the human has already approved SR-028, ADD-024, TS-007 and RISK-007 (`e836c58`);
  - QA approves TASK records.

  QA reads AC-18 as "nothing changed by CR-001 is in `draft`; every changed record is at or past
  its review gate". That holds for all 68 records (tally below). The human should record this
  reading when closing CR-001.
- **No double counting.** RISK-010 keeps severity 3 for "control silently weakened" and assigns
  the severity-4 substitution harm to RISK-012 explicitly. Path 2's P = 2 equals RISK-012's P2, and
  the worst-path rule is stated. Both "ALARP justification" sections honestly say the residual is
  not justified for a release until CR-002. PRB-043 (critical) blocks the release gate anyway.
- `risk_control_unverified` is clear only because TR-001 (pre-CR-001) verifies SR-028 and SR-013.
  The CR-001 controls still need the release test report. The gap report says so, and so does
  CR-001's "Verification approach".
- `@redocly/cli lint` (job `openapi-lint`) runs only in CI. The exported schema and the generated
  types match the committed files (architect's evidence).

### Verification run (QA, 2026-10-22, on `7ef8f93` plus this task's record changes)

| Check (CR-001 AC) | Result |
|---|---|
| RISK-010 against `risk-management` (AC-14) | Initial and residual 3 × 2. `risk_matrix[3][2]` = `alarp`, which matches `acceptability`. Control table names the implementers and evidence for pinning (TASK-155, locks, TASK-157/158; TC-013.5..8), the CI pin check (TASK-156; TC-013.5/6) and the review (TASK-154; TC-013.9). The PRB-001/TASK-154 preconditions are stated as met. Floating-tag text survives only as history ("Before CR-001 …"). `SOUP-018` link removed (`git diff`); 34 SOUP links plus RISK-012 remain. "Decided by: pending" |
| TS-013 TC-013.9 (AC-15) | Well-formed: verifies SR-028 AC-6, with steps, expected result and pass criteria. The coverage note maps TC-013.5..8 to AC-5 and TC-013.9 to AC-6. TS-013 still `verifies` SR-028. Run: `tc0139.py` gives 34/34 PASS, `failures=0`. QA's own check: each image tag in Compose and the Dockerfiles equals the SOUP-001 and SOUP-020..024 `soup_version`; package versions equal the locks (28/28, round 1) |
| AC-1 / AC-2 recheck | 11 image references in Compose, the Dockerfiles and `ci.yml`, all `<repo>:<release tag>@sha256:<64 hex>`, with one distinct reference per image |
| `cd backend && uv lock --check`; ruff; black --check; mypy app | 86 packages, exit 0; all checks passed; 219 files unchanged; no issues in 124 source files |
| `uv run pytest --cov=app --cov-fail-under=85 -q` | **496 passed**, coverage 91.71 % |
| `cd frontend && npm test -- --run`; `npm run lint`; `npm run typecheck` | 27 files, **155 passed**; lint exit 0; typecheck exit 0 |
| `python3 infra/check_image_pins.py`; `python3 -m unittest discover -s infra/tests` | exit 0, no output; OK (11 tests) |
| Smoke test (AC-5, part of AC-16) | Not re-run. `git diff --stat 3a5eed0 -- . ':!docs'` is empty, so the code is unchanged since QA's own 17/17 run at TASK-160. The architect's `t159-smoke.log` (14:44) shows `17 passed, 0 failed`, exit 0 |
| `trace2.py docs 2026-10-22` (project-wide, 339 records) | **0 errors**, 96 warnings. The output matches the committed `docs/reports/gap-report-2026-10-22.md` exactly from "## Errors" on. The inventory counts (339; 48 PRB, 35 SOUP, 12 RISK) are correct |
| `trace.py` (project-wide cross-check, 337 records) | **0 errors.** `soup_anomaly_review_stale` only for the obsolete SOUP-018 (a parser artefact) |
| Statuses of the 68 CR-001-changed records (AC-18) | **`in_review` (38):** TASK-159, TS-013, RISK-010, RISK-012, SOUP-001..017, SOUP-019..035. **`approved` (10):** SR-028, ADD-024, TS-007 and RISK-007 by the human; TASK-154..158 and TASK-160 by QA. **`resolved` (4):** PRB-001, 002, 033, 037. **`open` by decision (14):** PRB-034..036, PRB-038..048. **`obsolete` (1):** SOUP-018. **`in_progress` (1):** CR-001. None in `draft` |
| `trace2.py` after this approval | 0 errors, **98** warnings. The 2 added are W5: TASK-159 `approved` → RISK-010 and RISK-012 (`in_review`). They are expected. The committed gap report (96) is the snapshot from before approval. Regenerate it before the commit (`python trace2.py docs 2026-10-22 --md docs/reports/gap-report-2026-10-22.md`, then re-apply the triage text, W5 87 → 89) so that it matches the committed tree. Otherwise, add one line noting the two W5s |
| CI on the branch head (AC-16) | **Pending the push.** The last green run (39767474884) is on `e836c58` |
