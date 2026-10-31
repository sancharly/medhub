---
id: "TASK-188"
type: task
title: "Route identity and account-lifecycle access checks through AuthorizationService"
status: approved
version: "1.1"
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

- [x] SR-032 AC 1, AC 4, AC 5 and SR-034 AC 1: decided by `AuthorizationService`; decision table
      unchanged (`backend/tests/authz/test_decision_table.py`, `backend/tests/identity/`).
- [x] SR-023 AC 7: each decision audited (`backend/tests/audit/test_authz_decision_audit.py`).
- [x] No `user_type` comparison deciding access remains in `backend/app/identity/`
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

- [x] Backend suite passes; coverage ≥ 85 %.
- [x] TS-003 1.2 and TS-009 `in_review`.
- [x] `traceability-check` shows no error for TASK-188, TS-003, TS-009, SR-032, SR-034.

## Implementation notes

Order followed (RISK-004 control): the identity tables in `backend/tests/authz/test_decision_table.py`
(55 new cases, 93 in the file) were written and run green against the unchanged role comparisons
(93 passed), then the rules moved into `AuthorizationService`, then the same rows were run again
(93 passed). Only the `_*_service` builders in that file changed (they inject the real
`AuthorizationService`); no row changed.

Table cases: creation 16 (creator role x target type) + 1 unknown role; deactivate 8 + reactivate 8
(role x other/self); refusal-before-lookup 6; lifecycle unknown role 2; delete 8 + 1 unknown role;
resend 4 + 1 unknown role. Every refusal row asserts the 403 status and the exact `detail`.

- `app/authz/service.py`: `Resource.target_user_type`; `AuthorizationService.decide()` (evaluate and
  audit, never raises) with `authorize()` now `decide()` + raise (same behaviour); `_eval_identity`
  for `account:create` (SYSADMIN any, ADMIN any but SYSADMIN, others none; denial basis `TARGET` or
  `ROLE`), `account:deactivate` (SYSADMIN, not itself; basis `SELF` or `ROLE`), `account:reactivate`
  (SYSADMIN), `account:delete` (SYSADMIN or the account itself), `activation:resend` (ADMIN,
  SYSADMIN). The four account actions are removed from the SYSADMIN `lifecycle_actions` set so each
  rule is stated once. The basis tells the service which legacy message to keep.
- `app/identity/account_service.py`, `lifecycle.py`, `activation.py`, `erasure.py`: ask
  `decide(...)` and raise `AuthorizationError` with the existing message; `_check_create_permission`
  removed. `LifecycleService`, `ActivationService` (before `group_repo`) and `ErasureService` take a
  required `authz_svc`. Refusal still precedes the account lookup.
- Wiring only (constructors changed): `api/routers/accounts.py` (resend), `lifecycle.py`,
  `activation.py`, `anonymized_data.py` build an `AuthorizationService`. No router check was changed
  (those are TASK-189).
- Tests: `tests/identity/test_lifecycle.py`, `test_activation.py`, `test_erasure.py` inject the real
  `AuthorizationService` (`test_account_service.py` already did); four real-database tests added to
  `tests/audit/test_authz_decision_audit.py`.
- No schema change: OpenAPI and generated types untouched.

Behaviour changes (intended, SR-023 AC 7): each identity decision above now writes one `AUTHZ_ALLOWED`
or `AUTHZ_DENIED` row (none before); an allowed creation, deactivation, reactivation, deletion or
resend adds one row to the request. Responses, status codes and messages are unchanged.
A denied account creation has an empty audit target (no account exists yet). Same PRB-060 limit as
TASK-187: an allowed row is lost if the request then fails.

`grep -n user_type backend/app/identity/*.py` now shows only descriptors and data: `account_service.py:32`
(dataclass field), `:64` (resource descriptor `target_user_type`), `:78` (new account), `:126`
(resource descriptor), `erasure.py:88` (payload), `activation.py:97` (comment). None decides access.
The verification note's "only account_service.py:113" predates the added descriptor line.

Left for TASK-189 (not touched): `app/api/routers/accounts.py` unlock (`user_type != SYSADMIN`) and the
admin projection checks (projection, not a refusal), `routers/modules.py:38`, `routers/consents.py:45,67,82`,
`routers/clinical.py:114`; the static check. PRB-027 stays `open` (CR-004 maps it to TASK-188 and 189).

## Verification results

- `uv run pytest tests/authz tests/identity tests/audit tests/api/test_accounts_router.py tests/api/test_lifecycle_router.py tests/api/test_activation_router.py`: all pass (identity tables 93 in the file; audit file 11).
- Full `uv run pytest --cov=app --cov-fail-under=85`: 752 passed, 4 skipped, 92.58 % coverage.
- `ruff check .`, `black --check .`, `mypy app`: clean.
- Negative control: `account:reactivate` weakened to allow ADMIN fails three table rows
  (`test_reactivate_by_role_and_relation[ADMIN-other]`, `[ADMIN-self]`,
  `test_lifecycle_refusal_precedes_the_lookup[ADMIN-reactivate]`); restored afterwards.

## QA review (2026-10-31): APPROVED

**Characterisation holds.** I ran the new `test_decision_table.py` in a detached worktree of HEAD
`df7c6bc`, which still has `_check_create_permission` and the role comparisons. To fit the old
constructors I edited only three builders: I dropped `_real_authz()` from `_lifecycle_service`,
`_activation_service` and `_erasure_service`. Result: 93 passed. The script check confirmed that
nothing else in the file differs, so no row expectation was edited. The TASK-187 rows are unchanged
from the committed file.

**Behaviour.** The `basis` mechanism reproduces all seven pre-change messages, and each one is
asserted per row. Precedence is unchanged: a role refusal comes before the self check, and before
the account lookup.

**Auditing.**
- `decide()` always audits, and `authorize()` is `decide()` plus the raise.
- No caller uses both, so there are no double rows. The real-DB tests count exactly one `AUTHZ_*` row.
- The public `activate` and anonymized-retrieval flows build an `AuthorizationService` but never call
  it, so they write no spurious row and need no actor.

**Router edits** in `accounts.py`, `activation.py`, `anonymized_data.py` and `lifecycle.py` are
wiring only. The identity test edits are constructor changes only.

**PRB-027** staying `open` is correct. CR-004:222 maps it to TASK-188 and TASK-189, both tasks link
it, and TASK-189's Definition of Done resolves it.

**Remaining `user_type` uses.** `grep user_type app/identity/*.py` shows only descriptors and data.

Findings (all LOW, not blocking; candidates for TASK-189, which extends this table):

1. **[LOW] `account:create` is fail-open when the target type is missing**
   (`backend/app/authz/service.py:190-193`). An ADMIN with `target_user_type=None` is allowed. Today's
   only caller always sets it.
   → Deny unless `target_user_type` is set and is not SYSADMIN, and add a table row for it.
2. **[LOW] SR-034 AC 1 names "other system administrators", but the table never uses one.**
   `_target_for` (`backend/tests/authz/test_decision_table.py:346`) always makes a PATIENT target.
   → Add SYSADMIN→SYSADMIN rows to the deactivate and delete tables.
3. **[LOW] There is no real-DB audit evidence for resend, reactivate or an allowed creation.** The
   plan's four cases are met, and `decide()` is shared and unit-tested. However, a QA plugin that
   skipped auditing for `account:*` was caught only by the four planned cases. `activation:resend`
   has no audit test at all.
   → Add one denied-resend real-DB row.
4. **[LOW] A denied creation is audited with an empty target.** No account exists yet. The
   `appointment:list` precedent is the same. The attempted type is the only target information.
   → Optional: set `resource_id` to the requested type (for example `"user_type:SYSADMIN"`).

Observations (not findings):
- `authorize()` now allows `account:create` for ADMIN and `account:delete` for the owner, which
  `_eval_admin`/`_eval_patient` used to deny. No caller uses those actions through `authorize()`,
  in the backend or in `modules/`.
- The plan says reactivate is "SYSADMIN, not self". The code keeps the pre-change rule (no self
  check), which is right for a characterisation. A deactivated account cannot log in anyway.

Verification run by QA:
- Targeted suites: `tests/authz tests/identity tests/audit tests/appointments tests/modules` plus
  the accounts, lifecycle, activation and appointments router tests: 307 passed.
  `modules/dicom_viewer/tests`: 21 passed.
- Full suite: 752 passed, 4 skipped, 92.58 %. `ruff`, `black --check` and `mypy app` are clean.
  The OpenAPI export is identical to the committed file.
- Negative controls (pytest plugins, no source edits):

  | Weakened check | Tests that fail |
  |---|---|
  | ADMIN→SYSADMIN creation allowed | table row, `test_admin_cannot_create_sysadmin`, real-DB denied-creation test |
  | SYSADMIN self-deactivation allowed | table row, `test_deactivate_self_raises`, real-DB test |
  | `account:*` decided without audit | 2 unit tests, 4 real-DB tests |

- Traceability (TASK-188, TS-003, TS-009, PRB-027, SR-032, SR-034): 0 errors. The 2 warnings were
  TP-001 → TS-003/TS-009 `in_review`, and they clear with this approval.

## Version history

- 1.1 (2026-10-31) — Implemented; handed to QA (`in_review`). Implementation notes and verification results added. Checkboxes left for QA.
- 1.1 (2026-10-31) — QA review: APPROVED (`in_review → approved`); TS-003 and TS-009 approved; LOW findings 1–4 recorded for TASK-189.
