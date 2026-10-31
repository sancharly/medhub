---
id: "TASK-189"
type: task
title: "Route router-level role checks through AuthorizationService and forbid new ones"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-005"
    relation: implements
  - target: "SR-009"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "SR-008"
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
  - target: "TASK-188"
    relation: relates_to
  - target: "ADD-007"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
tags: ["security", "authz", "cr:CR-004", "control:design"]
---

# TASK-189 — Route router-level role checks through AuthorizationService and forbid new ones

- **Software item / unit:** SI-API `U-API-Routers` (ADD-005); SI-AUTHZ `U-AUTHZ-Policy`,
  `U-AUTHZ-AdminProjection` (ADD-007).
- **PRB:** PRB-027 (router part; found by the PRB-027 Investigation). **CR:** CR-004. **Design:** ADR-0006.
- **Depends on:** TASK-188.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`api/routers/accounts.py`, `modules.py`, `consents.py`, `clinical.py`,
  `authz/service.py`; 2 test files; TS-002, TS-009)
- **Needs:** a Docker daemon for the real-database audit test.

## Objective

Close SR-023 AC 7 and SR-005 AC 1 for the routers: `accounts.py:134` (unlock),
`modules.py:38` (module list), `consents.py:45,67,82` (consent grant, revoke, list),
`clinical.py:114` (patient roster). Make the rule permanent with a static check.

## Implementation detail

1. Extend `backend/tests/authz/test_decision_table.py` with the current router behaviour; green
   before the move.
2. `AuthorizationService` rules: `account:unlock` (already in `lifecycle_actions`),
   `module:list` (SYSADMIN), `consent:grant`, `consent:revoke`, `consent:list` (PATIENT, own),
   `patient_roster:list` (DOCTOR). Routers call `authorize(...)`.
3. The admin projection choice (`accounts.py:83,107`) moves behind one authz-package function
   (`requires_admin_projection(actor)`, `U-AUTHZ-AdminProjection`); routers stop comparing roles.
4. `backend/tests/authz/test_no_role_decisions_outside_authz.py`: an AST scan of `backend/app` and
   `backend/modules` that fails on a comparison involving `.user_type` or `UserType.<member>`
   outside `backend/app/authz/`, except an explicit allow-list with a reason per entry (the
   non-decision comparisons in the PRB-027 Investigation: `appointments/service.py:51,55`,
   `auth/session.py:23-24`, `api/routers/lifecycle.py:85`, `identity/account_service.py:113`).

## Tests (write first)

- `backend/tests/authz/test_decision_table.py` (extended; unchanged results).
- `backend/tests/authz/test_no_role_decisions_outside_authz.py` (static; negative control: add
  `if actor.user_type == UserType.ADMIN:` to a router and see it fail).
- `backend/tests/api/test_accounts_router.py`, `test_consents_router.py`, `test_clinical_router.py`,
  `test_admin_projection_integration.py`: status codes and projections unchanged.
- `backend/tests/audit/test_authz_decision_audit.py` (extend, real database): denied unlock,
  denied module list, denied consent grant by a DOCTOR, denied roster by a PATIENT → one
  `AUTHZ_DENIED` row each.

## Acceptance criteria

- [x] SR-005 AC 1, AC 3: no role comparison decides access outside `backend/app/authz/`
      (`backend/tests/authz/test_no_role_decisions_outside_authz.py`).
- [x] SR-023 AC 7: the router decisions are audited (`backend/tests/audit/test_authz_decision_audit.py`).
- [x] SR-009: the admin projection is unchanged (`backend/tests/api/test_admin_projection_integration.py`).

## Verification

```sh
cd backend && uv run pytest tests/authz tests/api tests/audit -v
cd backend && uv run pytest modules/dicom_viewer/tests -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

## Records

- **TS-002**: TC-002.8 (static check; router decisions in the table), `verifies` SR-005, SR-008, SR-009.
- **TS-009**: TC-009.10 extended (router decisions audited).
- **PRB-027**: `## Resolution` (TASK-188 and this task), `resolved`.

## Definition of Done

- [x] Backend suite and DICOM module tests pass; coverage ≥ 85 %.
- [x] TS-002, TS-009 `in_review`; PRB-027 `resolved`.
- [x] `traceability-check` shows no error for TASK-189, TS-002, TS-009, SR-005, SR-023, PRB-027.

## Implementation notes

Order followed (RISK-004 control): the router rows in `backend/tests/authz/test_decision_table.py`
(30: 6 routes x 4 roles, plus 6 no-role cases) were written and run green against the unchanged
router checks (123 passed), then moved, then run again unchanged. The file is now 132 cases (the
extra 9 are TASK-188 QA findings: SYSADMIN target rows for deactivate and delete, 8; ADMIN creating
without a requested type, 1). Every refusal row asserts status 403 and the exact `detail`.

- `app/authz/service.py`: `_ROLE_ONLY_ACTIONS` (`account:unlock`, `module:list`, `consent:grant`,
  `consent:revoke`, `consent:list`: patient only; `patient_roster:list`: doctor only);
  `account:unlock` leaves `lifecycle_actions` so the rule is stated once. TASK-188 finding 1:
  an ADMIN creating with no requested type is denied (`basis="TARGET_UNSET"`).
- `app/authz/admin_projection.py`: `requires_admin_projection(actor)`.
- Routers `accounts.py`, `modules.py`, `consents.py`, `clinical.py` call `decide()` and keep their
  message; no role comparison is left in them. `accounts.py` unlock now builds one
  `AuthorizationService` and reuses its `AuditService` for the lockout.
- TASK-188 finding 4: the audit target of an account creation is `user_type:<TYPE>`.
- Dead `AuthorizationServiceProtocol` removed from `app/api/deps.py`.
- `tests/api/test_client_address_middleware.py`: the exemption is the exact path
  `core/client_address.py`; `getattr(x, "client")` is a caught form; a same-named file elsewhere
  is flagged.
- Static check `tests/authz/test_no_role_decisions_outside_authz.py` (17 tests): AST scan of
  `app/` and `modules/`; function-level exceptions with a reason, stale exceptions fail.
- Existing router tests (`test_clinical_router.py`, `test_consents_router.py`,
  `test_lockout_integration.py`, `tests/modules/test_discovery.py`) stub `AuditService.record`
  (and the module list test stubs the session): a denied decision now writes a row on its own
  session, as in TASK-187. No assertion changed.
- No schema change: OpenAPI export identical to the committed file; generated types untouched.

Behaviour changes (intended, SR-023 AC 7): unlock, module list, consent grant/revoke/list and the
roster now write an `AUTHZ_ALLOWED`/`AUTHZ_DENIED` row (none before); an allowed `GET /modules` or
roster call adds one row. Responses, status codes and messages unchanged. Audit target: the account
(unlock), the actor (consent, as the owner), empty for module list and roster.

Records needing a human (not edited): ADD-005/ADD-007 should list the new actions and
`requires_admin_projection`; RISK-006 should note the added audit volume and PRB-060 (as for TASK-187).

## Verification results

- (round 1 figures, superseded by round 2 below) `uv run pytest tests/authz tests/api tests/audit tests/identity`: 448 passed.
- `uv run pytest modules/dicom_viewer/tests`: 21 passed.
- Full `uv run pytest --cov=app --cov-fail-under=85`: 817 passed, 4 skipped, 92.90 % coverage.
- `ruff check .`, `black --check .`, `mypy app`: clean.
- Negative controls: `_ROLE_ONLY_ACTIONS` evaluation changed to always allow: 24 router and table
  rows fail. A temporary `app/api/routers/_tmp_offender.py` with `if actor.user_type == UserType.ADMIN:`
  fails `test_no_role_comparison_decides_access_outside_authz` (file removed afterwards).

## QA review (2026-10-31, round 1): CHANGES REQUESTED

What holds:
- **Characterisation.** I ran the new `test_decision_table.py` in a detached worktree of HEAD
  `03c879e`: 131 passed and 1 failed. The failure is
  `test_admin_creation_without_a_requested_type_is_denied`, a new test for the deliberate fix of
  TASK-188 finding 1, not an edited row. Every other pre-existing row is identical. The diff only
  adds rows: the `other_sysadmin` relation (4 deactivate, 4 delete) and the 30 router rows, and all
  of them pass on the old code. TASK-188 finding 4 changes the audit target, which is not part of
  the table.
- **Messages.** All six router 403 messages are unchanged; each row asserts its `detail` on the old
  code and on the new.
- **Audit targets.** Unlock records the account id, consent records the actor, module list and
  roster record nothing. These are sensible.
- **Stubbed router tests.** In the four files, the only change is an autouse stub of `record` (and,
  in `test_discovery.py`, a stub DB). No assertion was removed or loosened. Real-DB audit tests
  exist for unlock, module list, consent grant, consent list and roster. Revoke has none (finding 6).
- **The three listed exceptions** are data or input rules, not access decisions:
  `AppointmentService.create` (`appointments/service.py:50,54`), `get_profile` (a descriptor) and
  `delete_account` (`lifecycle.py:91`, the typed confirmation).

Findings:

1. **[HIGH] An access decision remains outside `app/authz/`, and the static check cannot see it** —
   `backend/app/auth/lockout.py:102-103`: `if actor_role != "SYSADMIN": raise AuthorizationError("Only
   SYSADMIN can unlock accounts.")`. The router passes it `actor.user_type.value`
   (`backend/app/api/routers/accounts.py:161`).
   - This is a second, unaudited copy of the `account:unlock` rule, which is exactly what PRB-027
     describes. It is missing from the PRB-027 Investigation.
   - The comparison is a string on a parameter, with no `.user_type` and no `UserType` member, so
     `test_no_role_decisions_outside_authz.py` passes over it.
   - AC 1 ("no role comparison decides access outside `backend/app/authz/`") is therefore unmet, and
     the PRB-027 Resolution's "every row of the Investigation table is closed / the rule is
     permanent" is not true.
   → Remove the `actor_role` parameter and its check from `LockoutService.admin_unlock`. The router
   already decides `account:unlock`. Update the caller at `accounts.py:161`, and drop or move
   `tests/auth/test_lockout.py::test_admin_unlock_requires_sysadmin` (the table's unlock rows
   already cover that refusal). Add the location to the PRB-027 Investigation and Resolution. Make
   the static check catch this form (finding 2).
2. **[MEDIUM] The static check misses the usual ways of writing a role decision** —
   `backend/tests/authz/test_no_role_decisions_outside_authz.py:46-56` (`_is_role_operand`). I ran
   `role_comparisons()` on synthetic files. It missed all 8 forms:
   - a local alias (`t = actor.user_type; if t == 'ADMIN'`);
   - a string parameter (`actor_role != 'SYSADMIN'`, the live case above);
   - a dict lookup (`PERMS[actor.user_type]`) and `PERMS.get(actor.user_type)`;
   - an alias tested with `in` against a set;
   - a `.value` alias;
   - `session.role == 'SYSADMIN'`;
   - `actor.user_type.name.startswith(...)`.

   This check is the permanent RISK-001 control (TC-002.8).
   → Extend `_is_role_operand` and the finder:
   - (a) treat a `Constant` whose value is one of `"PATIENT"`, `"DOCTOR"`, `"ADMIN"`, `"SYSADMIN"`
     as a role operand;
   - (b) treat a `.role` attribute as a role operand;
   - (c) per function, taint the names assigned from an expression that holds a role operand, and
     the parameters annotated `UserType` or named `role`, `actor_role` or `user_type`; count a
     tainted `Name` as a role operand;
   - (d) flag a `Subscript` or a `.get(...)` call whose key is a role operand;
   - (e) flag a method call on a role operand (`.startswith`, and so on).

   Add each form to `OFFENDING`. With (c), `auth/session.py::SessionService._inactivity_ttl` becomes
   visible and needs a listed exception (SR-030 timeout, not access), as plan step 4 intended. That
   also removes the "known limit" sentence.
3. **[LOW] An exception covers a whole function, so it also excuses new comparisons there** —
   `test_no_role_decisions_outside_authz.py:27-40`. Adding `if actor.user_type == UserType.DOCTOR:
   raise ...` inside `AppointmentService.create` would pass.
   → Key each exception by (path, function, `ast.unparse(compare)`) or by an exact count, so that a
   new comparison in an excepted function fails.
4. **[LOW] TASK-188 finding 1 is fixed for ADMIN only** — `backend/app/authz/service.py:205-207`. A
   SYSADMIN with `target_user_type=None` is still allowed. Today this cannot happen (`AccountCreate.user_type`
   is required), but deny by default argues for one rule: no stated type, no creation.
   → Move the `target_user_type is None → deny (TARGET_UNSET)` check above the role branches, and
   add a SYSADMIN row to `test_admin_creation_without_a_requested_type_is_denied`.
5. **[LOW] The PRB-027 Resolution states "`auth/session.py` ... is outside the rule"** as an
   accepted gap. After finding 2 it becomes a listed exception. Update the sentence.
6. **[LOW] There is no real-DB audit test for consent revoke.** It goes through the same
   `_patient_only` helper as grant and list, so this is optional: add one denied-revoke row.

Verification run by QA:
- (round 1 figures, superseded by round 2 below) `uv run pytest tests/authz tests/api tests/audit tests/identity`: 448 passed.
  `modules/dicom_viewer/tests`: 21 passed.
- Full suite: 817 passed, 4 skipped, 92.90 %. `ruff`, `black --check` and `mypy app` are clean.
  The OpenAPI export is identical to the committed file. `infra` unittest: 37 OK. Frontend `npm test`:
  155 passed (27 files).
- Negative controls: a plugin that lets a DOCTOR revoke consent fails the table row
  `test_router_check_by_role[DELETE /api/v1/consents/{id}-DOCTOR]`. No existing consents router test
  caught it. The static-check probe gave 8 of 8 forms missed (finding 2).
- Traceability (TASK-189, TS-002, TS-003, TS-009, PRB-026, PRB-027, SR-005, SR-023): 0 errors and
  9 warnings, all pre-existing or `in_review`-related.

## Checkpoint B result (QA engineer, 2026-10-31, updated at TASK-189 round 2): PENDING TASK-192

The CR-004 Plan places Checkpoint B after tasks 4–7. Task 7 is TASK-192, which is still `draft`.

| Checkpoint B criterion | Result |
|---|---|
| Backend suite green (coverage ≥ 85 %) | 838 passed, 4 skipped, 92.89 % |
| DICOM-module suite green | 21 passed |
| Frontend suite green | 155 passed |
| Static role-check test green | 35 passed. QA probe: 8/8 round-1 forms caught. Of 10 further forms, 7 caught, and 3 documented or LOW limits (round 2, findings R2-1 and R2-2) |
| Decision table green | 135 passed; 133 of them also pass on `03c879e` (the other two are the deliberate `TARGET_UNSET` rows for ADMIN and SYSADMIN) |
| No audit row in the suite's database contains a session token | **not checked: TASK-192 deliverable** (the logout token, PRB-005) |

Every criterion that does not depend on TASK-192 passes. Re-run the session-token criterion and close Checkpoint B when TASK-192 is approved.

## Round 2 (software developer, 2026-10-31)

QA round 1 findings 1 to 6, all addressed:

1. [HIGH] `app/auth/lockout.py`: `LockoutService.admin_unlock` lost its `actor_role` parameter and
   check; `accounts.py` no longer passes the role. `tests/auth/test_lockout.py::test_admin_unlock_requires_sysadmin`
   removed (the refusal is the router's `account:unlock`; the table row and
   `test_denied_unlock_writes_one_row` assert the same message the user sees,
   "Only SYSADMIN can unlock accounts."). PRB-027 Investigation and Resolution name `lockout.py`.
2. [MEDIUM] `_is_role_operand` replaced by role-expression detection in
   `tests/authz/test_no_role_decisions_outside_authz.py`: role atoms (`.user_type`, `.role`,
   `UserType.<x>`, role-name strings, `getattr(x, "user_type")`), parameters annotated `UserType` or
   named `role`/`actor_role`/`user_type`, names assigned from a role expression (per function and at
   module level, to a fixed point, through `.value`/`.name`, subscripts, method calls, conditional
   expressions and collections), and use sites that include subscripts and `.get()` keyed on a role
   and method calls on a role. QA's probe: 8 of 8 forms caught (0 of 8 before). All probe forms and
   other aliases are in `OFFENDING` (24 forms), and 7 permitted forms (data, descriptors) are pinned.
   `SessionService._inactivity_ttl` is now flagged and listed ("SR-030 inactivity timeout, not an
   access decision"), as is the auto-group filter in `GroupRepository` (query data).
3. [LOW] Exceptions are keyed by (path, function, exact expression), six entries;
   `test_a_new_comparison_inside_an_excepted_function_is_not_excused` covers the new-use case.
4. [LOW] `account:create` with no requested type is denied for every role, above the role branches
   (`TARGET_UNSET`); `test_creation_without_a_requested_type_is_denied` has a row per role
   (SYSADMIN included). `test_authorization_service.py::test_sysadmin_can_create_account` now states a type.
5. [LOW] PRB-027 Resolution rewritten (v1.4): the static check, its six listed exceptions
   including `auth/session.py`, and the lockout change. Status stays `resolved`.
6. [LOW] `test_denied_consent_revoke_by_doctor_writes_one_row` added (real DB).

Round 2 verification:

- `uv run pytest tests/authz tests/api tests/audit tests/identity tests/auth`: 535 passed.
- `uv run pytest modules/dicom_viewer/tests`: 21 passed.
- Full `uv run pytest --cov=app --cov-fail-under=85`: 838 passed, 4 skipped, 92.89 % coverage.
- `ruff check .`, `black --check .`, `mypy app`: clean. OpenAPI export identical to the committed file.
- `test_decision_table.py`: 135 cases. Static check file: 35 tests.
- Negative controls: (a) `admin_unlock` given back a role check: the static check fails (parameter
  `actor_role` compared with `"SYSADMIN"`) and 4 lockout tests fail; (b) a temporary
  `app/api/routers/_tmp_alias.py` with `t = actor.user_type; if t == "ADMIN"` fails the static
  check naming `t == 'ADMIN'`; (c) `if role == UserType.SYSADMIN` added inside
  `SessionService._inactivity_ttl` fails it (not excused by the listed exception). All three
  reverted/removed.

## QA review (2026-10-31, round 2): APPROVED

Round-1 findings, all closed:
1. **Lockout role check (HIGH): closed.** `LockoutService.admin_unlock` (`backend/app/auth/lockout.py:94`) no
   longer takes or checks a role. Its only caller anywhere in `backend/` (scripts, CLI and modules
   included) is `accounts.py:161`, and that call comes after the `account:unlock` decision. A
   non-SYSADMIN still gets 403 "Only SYSADMIN can unlock accounts.": the table rows assert it, and so
   does `test_denied_unlock_writes_one_row` (real DB). Removing the unit test leaves no gap. The PRB-027
   Investigation and Resolution now name `lockout.py`.
2. **Static check too weak (MEDIUM): closed.** My round-1 probe, re-run against `role_uses`, now
   catches 8 of 8 forms. A copy of `app/` with the lockout check put back is flagged.
3. **Function-wide exceptions (LOW): closed.** Exceptions are now keyed by exact expression. A new
   comparison inside `AppointmentService.create`, tried on a copy of `app/`, is flagged as
   `actor.user_type == UserType.DOCTOR`.
4. **Missing type allowed for SYSADMIN (LOW): closed.** `TARGET_UNSET` is now checked before any role
   branch (`backend/app/authz/service.py:202-204`), with one row per role. On `03c879e` only the ADMIN
   and SYSADMIN rows fail, which is expected: they are the deliberate fix. The other 133 rows pass
   unchanged.
5. **PRB-027 wording on `auth/session.py` (LOW): closed.** `_inactivity_ttl` is a listed exception.
6. **No real-DB test for revoke (LOW): closed.** A real-DB denied-revoke test asserts the message
   and one row.

Exceptions checked: `GroupRepository.list_auto_groups_for_type`
(`backend/app/db/repositories/group_repo.py:60-62`) is a SQL filter that picks the automatic groups
of an account type, for `groups/auto_membership.py:21`. It is a data rule: module access is still
decided by `module:access` on the resulting memberships. The other five exceptions are unchanged
data or input rules.

Round-2 findings (LOW, not blocking):
- **R2-1 [LOW] Two plausible forms are missed and not documented** — `backend/tests/authz/test_no_role_decisions_outside_authz.py:116-121,207-214`.
  - The first is `getattr(policy, "allow_" + actor.user_type.value)()`: `getattr` with a role in its
    second argument is not a use.
  - The second is `self.r = a.user_type` followed by `self.r == other`: an attribute alias not named
    `role` or `user_type` is not tracked, because `_assigned_names` binds plain names only.

  Neither form exists in the tree.
  → Flag a `getattr` call whose second argument holds a role, and taint `self.<attr>` targets that
  are assigned from a role expression. Otherwise, list both forms next to the stated limit in the
  docstring and in the PRB-027 Resolution.
- **R2-2 [LOW] A role returned from a helper and used as a key is the stated limit** (for example
  `H[r(actor)]` with `H = {UserType.ADMIN: ...}`). Comparing such a value against a role still
  fails the check. I accept the limit as stated.
- The stated byte-identical-duplicate gap is acceptable. A duplicate of a data rule inside the same
  function is still a data rule.

Verification run by QA (round 2):
- Characterisation: in a detached worktree of `03c879e`, 133 of 135 rows pass. The two that fail are
  the deliberate `TARGET_UNSET` rows for ADMIN and SYSADMIN.
- `uv run pytest tests/authz tests/api tests/audit tests/identity tests/auth tests/modules`: 558
  passed. DICOM module tests: 21 passed. Full suite: 838 passed, 4 skipped, 92.89 %.
- `ruff`, `black --check` and `mypy app` are clean. The OpenAPI export is identical. `infra`
  unittest is OK. Frontend: 155 passed.
- Static-check probes (scratchpad): 8 of 8 round-1 forms caught. Of 10 further forms, 7 were caught
  and 3 missed (R2-1, R2-2). Mutated copies of `app/` (lockout check put back, a new comparison in an
  excepted function) were both flagged.
- Traceability (TASK-189, TS-002, TS-003, TS-009, PRB-027, SR-005, SR-023): 0 errors. The warnings
  are pre-existing or caused by the `in_review` status, which this approval clears.

## Version history

- 1.1 (2026-10-31) — Implemented; handed to QA (`in_review`). Checkboxes left for QA.
- 1.2 (2026-10-31) — QA round 1: CHANGES REQUESTED (`in_review → draft`); round 2 by the developer, findings 1 to 6 addressed; handed back to QA (`in_review`).
- 1.2 (2026-10-31) — QA review round 2: APPROVED (`in_review → approved`); TS-002, TS-003, TS-009 approved; Checkpoint B updated (pending TASK-192).
