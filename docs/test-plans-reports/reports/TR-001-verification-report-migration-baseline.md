---
id: TR-001
type: test-report
title: Verification report for the agentic-os migration baseline
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: SR-001
    relation: verifies
  - target: SR-002
    relation: verifies
  - target: SR-005
    relation: verifies
  - target: SR-006
    relation: verifies
  - target: SR-007
    relation: verifies
  - target: SR-008
    relation: verifies
  - target: SR-009
    relation: verifies
  - target: SR-011
    relation: verifies
  - target: SR-012
    relation: verifies
  - target: SR-013
    relation: verifies
  - target: SR-014
    relation: verifies
  - target: SR-015
    relation: verifies
  - target: SR-016
    relation: verifies
  - target: SR-020
    relation: verifies
  - target: SR-022
    relation: verifies
  - target: SR-024
    relation: verifies
  - target: SR-025
    relation: verifies
  - target: SR-027
    relation: verifies
  - target: SR-028
    relation: verifies
  - target: SR-029
    relation: verifies
  - target: SR-030
    relation: verifies
  - target: SR-032
    relation: verifies
  - target: SR-033
    relation: verifies
  - target: SR-034
    relation: verifies
  - target: SR-035
    relation: verifies
  - target: SR-036
    relation: verifies
  - target: SR-037
    relation: verifies
  - target: SR-038
    relation: verifies
  - target: SR-039
    relation: verifies
  - target: TP-001
    relation: relates_to
tags:
  - class:B
  - baseline
---

# TR-001 — Verification report (agentic-os migration baseline)

## Summary

| | |
|---|---|
| Version tested | branch `doc/agentic-os-migration`, commit `40401a1` |
| Date | 2026-09-17 |
| Executed by | `software-developer` role (automated suites run locally by the agent) |
| Plan | [TP-001](../plans/TP-001-verification-plan-migration-baseline.md) |
| Overall result | **Pass with blocked cases** — no failures; 40 real-database cases could not execute |

## Environment

- Backend: Python 3.12, dependencies as locked in `backend/uv.lock`; `pytest` 9.1.1,
  `pytest-cov` 7.1.0, `fakeredis` 2.36.2, `testcontainers` 4.14.2.
- Frontend: Node 20, dependencies as locked in `frontend/package-lock.json`; `vitest` 1.6.1,
  Testing Library (react 16.3.2), `jsdom` 24.1.3, `msw` 2.3.0.
- Static tools: `ruff` 0.15.18, `black` 26.5.1, `mypy` 2.1.0, `eslint` 8.57.1, `tsc` 5.9.3.
- **No Docker daemon was available on the execution host**, so every testcontainers case errored at
  setup (`docker.errors.DockerException`).
- SOUP versions: the `soup` records in [`../../soup/`](../../soup/) (same versions as the
  run; the list moved from ADD-004 on 2026-10-21).

## Results

| Suite | Command | Result | Evidence |
|---|---|---|---|
| Backend unit + integration | `uv run pytest -q` (in `backend/`) | **455 passed, 40 errors, 50 warnings in 228.15s** | console output of the run; the 40 errors are all `docker.errors.DockerException` at fixture setup in `tests/db/test_models.py`, `tests/db/test_repositories.py`, `tests/db/test_constraints.py` and `tests/db/test_migration.py` |
| Frontend unit | `npx vitest run` (in `frontend/`) | **27 files, 155 tests, all passed, 8.08s** | console output of the run |
| Backend lint | `uv run ruff check` | pass — "All checks passed!" | console output |
| Backend format | `uv run black --check .` | pass — 218 files unchanged | console output |
| Backend types | `uv run mypy app` | pass — no issues in 124 source files | console output |
| Frontend lint | `npm run lint` | pass (max-warnings 0) | console output |
| Frontend types | `npm run typecheck` | pass | console output |

No test case failed. Coverage figures were not collected in this run and are therefore not claimed.

## Blocked cases

The 40 errored cases are an **environment limitation, not a product defect**: they require a
PostgreSQL 16 container. They are dispositioned as *blocked*, not passed, and the software
requirements that depend on them are reported as unverified below. Running them on a host with
Docker is an entry criterion for the first release test plan.

## Anomalies

| Description | PRB | Criticality | Disposition |
|---|---|---|---|
| None found by this run | — | — | — |

This run surfaced no new anomaly. The 30 problem reports open against the project
([`../../problem-reports/`](../../problem-reports/)) come from the earlier audit and code review;
none of them is `critical`, and none was created by this verification.

## Requirements verified

29 of 39 software requirements are verified by this report: SR-001, SR-002, SR-005, SR-006, SR-007, SR-008, SR-009, SR-011, SR-012, SR-013, SR-014, SR-015, SR-016, SR-020, SR-022, SR-024, SR-025, SR-027, SR-028, SR-029, SR-030, SR-032, SR-033, SR-034, SR-035, SR-036, SR-037, SR-038, SR-039.

## Requirements NOT verified

| SR | Reason |
|---|---|
| SR-003 | database constraint and model cases blocked (no Docker daemon) |
| SR-004 | user-type-not-null case is a real-DB case, blocked |
| SR-010 | appointment constraint case is a real-DB case, blocked |
| SR-017 | DICOM viewer not implemented (frontend module phase outstanding) |
| SR-018 | DICOM viewer controls not implemented |
| SR-019 | cross-browser matrix not executable in jsdom; needs TASK-111 |
| SR-021 | FHIR model case is a real-DB case, blocked |
| SR-023 | audit persistence case is a real-DB case, blocked |
| SR-026 | no performance validation run yet; TASK-112 open |
| SR-031 | repository parameterization case is a real-DB case, blocked |

These are the verification gaps a release must close: the real-database suite needs a Docker host,
the DICOM viewer (SR-017, SR-018) is not implemented, the browser matrix (SR-019) and performance
validation (SR-026) need the system-test tasks TASK-111 and TASK-112.

## Known residual anomalies (§5.8.2–5.8.3)

Not applicable: this report is a verification baseline, not a release. A release report must
evaluate every problem report still open at that point and state why any remaining anomaly does not
contribute to unacceptable risk, against the criteria in
[PLAN-005](../../plans/PLAN-005-risk-management-plan.md).

## Conclusion

The implemented software passes every executable verification case at unit and service level, with
clean static verification. It is **not** release-verified: 10 of 39 software requirements remain
unverified for the reasons above, and system-level testing has not been performed. The record set
itself passes `traceability-check` with zero errors (see
[`../../reports/`](../../reports/)).
