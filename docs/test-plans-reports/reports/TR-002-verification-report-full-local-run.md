---
id: TR-002
type: test-report
title: Verification report for the full local run with the real-database suite
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 6893e8b236941cf1f5dbd2719bcff6ce948a1abbf1245d7764e28c0a9e5ca463
approval_note: self-approved
links:
  - target: SR-001
    relation: verifies
  - target: SR-002
    relation: verifies
  - target: SR-003
    relation: verifies
  - target: SR-004
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
  - target: SR-010
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
  - target: SR-021
    relation: verifies
  - target: SR-022
    relation: verifies
  - target: SR-023
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
  - target: SR-031
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
  - target: TR-001
    relation: relates_to
tags:
  - class:B
  - baseline
---

# TR-002 — Verification report (full local run with the real-database suite)

## Summary

| | |
|---|---|
| Version tested | branch `doc/agentic-os-migration`, commit `9b2a3bd` |
| Date | 2026-10-21 |
| Executed by | `software-developer` role (automated suites run locally by the agent) |
| Plan | [TP-001](../plans/TP-001-verification-plan-migration-baseline.md) |
| Previous report | [TR-001](TR-001-verification-report-migration-baseline.md) — same plan, 40 real-database cases blocked |
| Overall result | **Pass** — no failures, no blocked cases |

This run closes TR-001's blocked cases: a Docker daemon was available, so every testcontainers
case ran against PostgreSQL 16. No product code changed between the two runs; the commits in between
touch only `docs/`, `CLAUDE.md` and `graphify-out/`.

## Environment

- Backend: Python 3.12.3, dependencies as locked in `backend/uv.lock`; `pytest` 9.1.1,
  `testcontainers` 4.14.2 with the `postgres:16` image, Docker Engine 24.0.5.
- Frontend: Node 20, dependencies as locked in `frontend/package-lock.json`; `vitest` 1.6.1,
  Testing Library (react 16.3.2), `jsdom` 24.1.3, `msw` 2.3.0.
- Static tools: `ruff` 0.15.18, `black` 26.5.1, `mypy` 2.1.0, `eslint` 8.57.1, `tsc` 5.9.3.
- SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Results

| Suite | Command | Result |
|---|---|---|
| Backend unit + integration (incl. real database) | `uv run pytest -q` (in `backend/`) | **495 passed**, 0 failed, 0 errors, 50 warnings, 31.93s |
| Frontend unit | `npx vitest run` (in `frontend/`) | **27 files, 155 tests, all passed**, 9.28s |
| Backend lint | `uv run ruff check` | pass — "All checks passed!" |
| Backend format | `uv run black --check .` | pass — 218 files unchanged |
| Backend types | `uv run mypy app` | pass — no issues in 124 source files |
| Frontend lint | `npm run lint` | pass (max-warnings 0) |
| Frontend types | `npm run typecheck` | pass |
| Design records | `traceability-check` | 0 errors ([gap report](../../reports/gap-report-2026-10-21.md)) |

Evidence is the console output of the commands above, run on 2026-10-21. The 50 warnings are
deprecation notices (`starlette` per-request cookies in tests, redis-py `setex` in
`app/auth/session.py`); none is a test failure. Coverage was not collected and is not claimed.

The 40 cases that were blocked in TR-001 — `tests/db/test_models.py`, `test_repositories.py`,
`test_constraints.py` and `test_migration.py` — all passed. They complete TC-003.1, TC-008.1,
TC-008.3, TC-008.4 and TC-009.3.

## Anomalies

| Description | PRB | Criticality | Disposition |
|---|---|---|---|
| None found by this run | — | — | — |

The redis-py `setex` deprecation is not an anomaly today: the call works in the locked version
(SOUP-013). It is recorded here so the next redis-py upgrade checks it.

## Requirements verified

35 of 39 software requirements are verified by this report — every SR whose test-specification
cases all ran and passed: SR-001, SR-002, SR-003, SR-004, SR-005, SR-006, SR-007, SR-008, SR-009, SR-010, SR-011, SR-012, SR-013, SR-014, SR-015, SR-016, SR-020, SR-021, SR-022, SR-023, SR-024, SR-025, SR-027, SR-028, SR-029, SR-030, SR-031, SR-032, SR-033, SR-034, SR-035, SR-036, SR-037, SR-038, SR-039.

## Requirements NOT verified

| SR | Reason |
|---|---|
| SR-017 | DICOM viewer not implemented (TASK-102) |
| SR-018 | DICOM viewer controls not implemented (TASK-103) |
| SR-019 | cross-browser matrix not executable in jsdom; needs the Playwright system tests (TASK-111) |
| SR-026 | no performance validation run yet (TASK-112) |

## Known residual anomalies (§5.8.2–5.8.3)

Not applicable: this is a verification baseline, not a release. The release report must evaluate
every problem report open at that point against
[PLAN-005](../../plans/PLAN-005-risk-management-plan.md).

## Conclusion

Every executable verification case passes at unit and integration level, including the
real-database suite, with clean static verification. 35 of 39 SRs are verified. The remaining four
need work that does not exist yet: the DICOM viewer (SR-017, SR-018), the browser-matrix system
tests (SR-019) and the performance validation (SR-026).
