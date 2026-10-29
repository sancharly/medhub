---
id: "TASK-168"
type: task
title: "Confirm RISK-010 and the anomaly reviews, and verify CR-003 end to end"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-29"
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

- [ ] CR-003 **AC-11**: no non-obsolete record links SOUP-033.
- [ ] CR-003 **AC-14**: the four reviews are complete, and the escalation list has an entry, or
      "none", per item.
- [ ] CR-003 **AC-15**: the change analysis is in CR-003. RISK-010 1.4 has no SOUP-033 link, does
      not cite PRB-035 as open, and its residual is confirmed (or re-scored with a rationale).
- [ ] CR-003 **AC-16**: the pin check exits 0 and `uv lock --check` succeeds on the branch head.
- [ ] CR-003 **AC-17**: the stack builds and starts, the smoke test passes 17/17, and Redis
      reports 7.4.12.
- [ ] CR-003 **AC-18**: every CI job passes on the branch head. The backend suite (coverage ≥ 85 %)
      and the frontend suite pass locally.
- [ ] CR-003 **AC-19**: the four PRBs are `resolved`. `traceability-check` reports 0 errors and no
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
- [ ] No record created or changed by CR-003 is left in `draft`, apart from TASKs still under QA.
