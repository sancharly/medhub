---
id: "TASK-159"
type: task
title: "Re-assess RISK-010 and verify CR-001 end to end"
status: draft
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

- [ ] CR-001 **AC-14**: RISK-010 revised as above; residual confirmed at 1 or re-scored with
      rationale; `acceptability` derived; preconditions no longer stated as unmet; SOUP-018 link
      removed.
- [ ] CR-001 **AC-15**: TS-013 has test cases with expected results for SR-028 AC-5 (TC-013.5..8)
      and AC-6 (TC-013.9), and still `verifies` SR-028.
- [ ] CR-001 **AC-16**: every job in `.github/workflows/ci.yml`, `image-pins` included, is green on
      the branch head; backend and frontend suites pass locally; the pinned stack passes the smoke
      test after the TASK-157/158 image changes (AC-5 re-run).
- [ ] CR-001 **AC-18**: `traceability-check` over the whole project reports 0 errors and no
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

- [ ] RISK-010 and TS-013 `in_review`; gap report committed with 0 errors
- [ ] Every CR-001 acceptance criterion has its evidence named in the task that satisfies it
