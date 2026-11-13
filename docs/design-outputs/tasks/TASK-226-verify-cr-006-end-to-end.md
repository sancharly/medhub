---
id: "TASK-226"
type: task
title: "Verify CR-006 end to end"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
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

- [ ] All suites, checks and the budget check green; generated files unchanged.
- [ ] SR-026 AC 5: 0 × 5xx and AC 1 / AC 2 p95 ≤ 3 s at 20 clients with the approved pools.
- [ ] Records complete; `traceability-check` 0 errors in CR-006 scope.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect).
