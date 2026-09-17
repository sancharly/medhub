---
id: "TP-001"
type: test-plan
title: "Verification plan for the agentic-os migration baseline"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "TS-001"
    relation: relates_to
  - target: "TS-002"
    relation: relates_to
  - target: "TS-003"
    relation: relates_to
  - target: "TS-004"
    relation: relates_to
  - target: "TS-005"
    relation: relates_to
  - target: "TS-006"
    relation: relates_to
  - target: "TS-007"
    relation: relates_to
  - target: "TS-008"
    relation: relates_to
  - target: "TS-009"
    relation: relates_to
  - target: "TS-010"
    relation: relates_to
  - target: "TS-011"
    relation: relates_to
  - target: "TS-012"
    relation: relates_to
  - target: "TS-013"
    relation: relates_to
tags: ["class:B", "baseline"]
---

# TP-001 — Verification plan (agentic-os migration baseline)

## Version under test

Branch `doc/agentic-os-migration`, commit `40401a1`. Not a product release: this plan establishes
the verification baseline that the record set needs, so that a later release can be planned against
a known starting point.

## Scope

All 39 software requirements, through [TS-001..TS-013](../../design-outputs/tests-specifications/).
Software items: every item in [05-building-blocks.md](../../design/05-building-blocks.md).

## Levels executed (class B)

| Level | Clause | Executed here | How |
|---|---|---|---|
| Unit verification | §5.5 | yes | `pytest` (backend), `vitest` (frontend), plus `ruff`, `black`, `mypy`, `eslint`, `tsc` as static verification |
| Integration | §5.6 | partly | service-and-router tests run; the testcontainers real-database suite could not run in this environment |
| System | §5.7 | no | needs the Compose stack and the browser matrix (TASK-110, TASK-111, TASK-112) |
| Regression | §5.6.6, §5.7.3 | yes | the full suites are re-run on every change, in CI and locally |

## Environment

Backend: Python 3.12, dependencies per `backend/uv.lock`. Frontend: Node 20, dependencies per
`frontend/package-lock.json`. Exact SOUP versions in
[ADD-004](../../design-outputs/architecture/ADD-004-soup-list.md). Real-database cases require a
PostgreSQL 16 container via testcontainers and therefore a running Docker daemon.

## Entry criteria

- The record set passes `traceability-check` with zero errors.
- Static verification (lint, format, type check) is clean on both sides.

## Exit criteria

- Every test case of every TS in scope either passes or is dispositioned in the test report.
- Every SR is either verified by the report or listed in it as unverified with the reason.
- No `critical` problem report created before the run is still open.

## Regression strategy

Changed items are re-verified by their own TS plus the full automated suites. A change to a risk
control additionally re-runs the cases named in the corresponding RISK record.

## Roles and schedule

Execution and reporting: `software-developer` and `qa-engineer` roles. Approval of the report and
the release decision: the human owner. Cadence: at every pull request for the automated suites, and
once per release for the full plan.
