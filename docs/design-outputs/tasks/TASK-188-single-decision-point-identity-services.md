---
id: "TASK-188"
type: task
title: "Route identity and account-lifecycle access checks through AuthorizationService"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-032"
    relation: implements
  - target: "SR-034"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "SR-005"
    relation: implements
  - target: "RISK-001"
    relation: mitigates
  - target: "RISK-004"
    relation: mitigates
  - target: "RISK-006"
    relation: mitigates
  - target: "PRB-027"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-187"
    relation: relates_to
  - target: "ADD-007"
    relation: relates_to
  - target: "ADD-008"
    relation: relates_to
tags: ["security", "authz", "cr:CR-004", "control:design"]
---

# TASK-188 — Route identity and account-lifecycle access checks through AuthorizationService

- **Software item / unit:** SI-IDENTITY `U-ID-AccountCrud`, `U-ID-Activation`, `U-ID-Lifecycle`,
  `U-ID-Erasure` (ADD-008); SI-AUTHZ `U-AUTHZ-Policy` (ADD-007).
- **PRB:** PRB-027 (service part). **CR:** CR-004. **Design:** ADR-0006.
- **Depends on:** TASK-187 (decision table, edits `authz/service.py` first).
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`identity/account_service.py`, `identity/lifecycle.py`, `identity/activation.py`,
  `identity/erasure.py`, `authz/service.py`; tests; TS-003, TS-009)
- **Needs:** a Docker daemon for the real-database audit test.

## Objective

SR-032 AC 1, AC 4, AC 5 (role-constrained creation), SR-034 AC 1 (SYSADMIN-only lifecycle) and
SR-023 AC 7, decided once and audited. The PRB-027 Investigation lists the four service checks:
`account_service.py:119-126`, `lifecycle.py:32,71`, `activation.py:118`, `erasure.py:62`.

## Implementation detail

1. Extend `backend/tests/authz/test_decision_table.py` with the current behaviour of the four
   checks (creator role × target type for creation; actor role × self/other for deactivate,
   reactivate and delete; actor role for resend) and commit it green **before** the move.
2. `AuthorizationService._evaluate` gains the rules: `account:create` with the target type as a
   resource attribute (SYSADMIN any; ADMIN any but SYSADMIN; others none), `account:deactivate`
   and `account:reactivate` (SYSADMIN, not self), `account:delete` (SYSADMIN, or the account
   itself), `activation:resend` (ADMIN, SYSADMIN). The existing `lifecycle_actions` set
   (`authz/service.py:149-166`) is reconciled with these rules, not duplicated.
3. Each service calls `authorize(...)` instead of comparing `user_type`; refusals keep their
   current status codes and messages where the API contract fixes them.

## Tests (write first)

- `backend/tests/authz/test_decision_table.py` (extended; unchanged results after the move).
- `backend/tests/identity/test_account_service.py`, `test_lifecycle.py`, `test_activation.py`,
  `test_erasure.py`: updated to inject the real `AuthorizationService` with fakes beneath.
- `backend/tests/audit/test_authz_decision_audit.py` (extend, real database): a denied account
  creation (ADMIN → SYSADMIN), a denied deactivation (non-SYSADMIN), a denied self-deactivation,
  an allowed deletion of one's own account → one `AUTHZ_*` row each with the full fields.

## Acceptance criteria

- [ ] SR-032 AC 1, AC 4, AC 5 and SR-034 AC 1: decided by `AuthorizationService`; decision table
      unchanged (`backend/tests/authz/test_decision_table.py`, `backend/tests/identity/`).
- [ ] SR-023 AC 7: each decision audited (`backend/tests/audit/test_authz_decision_audit.py`).
- [ ] No `user_type` comparison deciding access remains in `backend/app/identity/`
      (`grep`, and TASK-189's static check once it lands).

## Verification

```sh
cd backend && uv run pytest tests/authz tests/identity tests/audit tests/api/test_accounts_router.py tests/api/test_lifecycle_router.py tests/api/test_activation_router.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
grep -n "user_type" backend/app/identity/*.py     # expect only account_service.py:113 (resource descriptor)
```

## Records

- **TS-003** → 1.2 (`in_review`): TC-003.6 (lifecycle and creation rules decided centrally,
  table unchanged), `verifies` SR-032, SR-034.
- **TS-009**: TC-009.10 extended (identity decisions audited).
- **PRB-027**: Resolution started (service part); it is `resolved` by TASK-189.

## Definition of Done

- [ ] Backend suite passes; coverage ≥ 85 %.
- [ ] TS-003 1.2 and TS-009 `in_review`.
- [ ] `traceability-check` shows no error for TASK-188, TS-003, TS-009, SR-032, SR-034.
