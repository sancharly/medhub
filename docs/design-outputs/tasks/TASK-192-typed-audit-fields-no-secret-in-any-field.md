---
id: "TASK-192"
type: task
title: "Typed audit fields so no secret can be stored in any field"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-023"
    relation: implements
  - target: "RISK-006"
    relation: mitigates
  - target: "RISK-005"
    relation: mitigates
  - target: "PRB-005"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-137"
    relation: relates_to
  - target: "ADD-013"
    relation: relates_to
tags: ["security", "audit", "cr:CR-004", "control:design"]
---

# TASK-192 — Typed audit fields so no secret can be stored in any field

- **Software item / unit:** SI-AUDIT `U-AUD-Writer` (ADD-013); SI-API auth router.
- **PRB:** PRB-005 (scrub part, and the logout token it found). **CR:** CR-004.
- **Depends on:** TASK-137 (both edit `backend/app/audit/service.py`). Independent of
  TASK-187..189 otherwise; may run in parallel with them.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`audit/service.py`, `audit/actions.py`, `api/routers/auth.py`; 2 test files; TS-009)

## Objective

SR-023 AC 9 and AC 5: a value issued or received as a credential or secret is never stored in
plaintext in an audit entry, whatever field the caller passes it under. The PRB-005
Investigation: the scrub matches only `key=value` text (`audit/service.py:12-24`), and the logout
event stores the session token as `target_id` (`api/routers/auth.py:101-108`).

## Implementation detail

1. Logout: record `target_type="account"`, `target_id=str(session.account_id)`. The session token
   never reaches `record`.
2. `AuditAction` gains `LOGOUT` and `PASSWORD_CHANGED` (now string literals at `auth.py:103,165`).
3. `AuditService.record` validates before building the row, and raises `AuditFieldError`
   (message names the field, never the value) on anything else:
   - `action`: a member of `AuditAction`;
   - `target_type`: a member of a closed set (`account`, `appointment`, `clinical_entry`,
     `patient_roster`, `group`, `group_membership`, `group_module`, `anonymized_dataset`,
     `attachment`, `module`, `session`, … taken from the current callers);
   - `target_id`: `None`, a UUID, `UUID:UUID`, or `UUID:<module key>` with the module key matching
     `^[a-z][a-z0-9_]{0,63}$`.
   The existing scrub stays as a second line on `action` and `target_type`.
4. Confirm every existing caller passes (the suite will show it); fix any that passes free text.

## Tests (write first)

- `backend/tests/audit/test_audit_no_secrets.py`: for each kind in SR-023 AC 9 (a
  policy-compliant password, a session token from `secrets.token_urlsafe(32)`, an activation
  token, an anonymized-data retrieval code from the erasure service's generator, a
  base64 32-byte key, an object-store access key) and each field (`action`, `target_type`,
  `target_id`, and `target_id` as `UUID:<secret>`): `record` raises and nothing is added to the
  repository. A real-database case shows no row is written.
- `backend/tests/api/test_auth_router.py`: logout writes `LOGOUT` with the account id, and the
  stored row does not contain the session cookie value.
- `backend/tests/audit/test_audit_writer.py`: valid shapes from every current caller pass.

## Acceptance criteria

- [x] SR-023 AC 9: no listed secret kind can be stored under any field (`backend/tests/audit/test_audit_no_secrets.py`).
- [x] SR-023 AC 5: the logout row carries no session token (`backend/tests/api/test_auth_router.py`).
- [x] Every current audit caller still records (full backend suite).

## Verification

```sh
cd backend && uv run pytest tests/audit tests/api/test_auth_router.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
cd backend && uv run pytest modules/dicom_viewer/tests -v
```

Negative control: drop the `target_id` check; the secret-in-`target_id` cases fail.

## Records

- **TS-009**: TC-009.12 (no secret under any field; logout row), `verifies` SR-023.
- **ADD-013** 1.2: confirm the typed-fields text.
- **PRB-005**: Resolution started (scrub part); `resolved` by TASK-191, the last PRB-005 task.

## Definition of Done

- [x] Backend suite and DICOM module tests pass; coverage ≥ 85 %.
- [x] TS-009 `in_review`.
- [x] `traceability-check` shows no error for TASK-192, TS-009, SR-023.

## Implementation notes (1.1, 2026-10-31)

Files: `backend/app/audit/service.py` (`AuditFieldError`, `_validate`, closed `_TARGETS` table),
`backend/app/audit/actions.py` (`LOGOUT`, `PASSWORD_CHANGED`), `backend/app/api/routers/auth.py`
(logout records `target_type="account"`, `target_id=<account id>`; both actions now `AuditAction`
members). Tests: new `backend/tests/audit/test_audit_no_secrets.py`; additions to
`backend/tests/api/test_auth_router.py` and `backend/tests/audit/test_audit_writer.py`; two existing
tests adjusted (`test_audit_writer.py` free-text actions, `test_failure_audit_persistence.py` target
type `"x"` to `"account"`). TS-009 TC-009.12 added (`in_review`).

Design points:

- `target_id` is checked against the shape of its `target_type` (a table), not against a union of
  shapes, so a bare lowercase string is accepted only where a module key is expected (`module`) and
  `<uuid>:<key>` only for `group_module`. Shapes beyond the task text, all taken from current callers:
  bare module key for `module` (module discovery, `module:access` decision); `user_type:<UserType>`
  for `account` (`account:create` decision, TASK-188); the empty string (a decision with no resource
  id, asserted by TASK-189 tests); `consent`/`consent_grant`, `module_registry` (always no id),
  `patient_roster`, `anonymized_dataset`. `session` is not in the set: nothing records it any more.
- `ip` is not validated: it is derived by the client-address rule (ADR-0019), not passed by a
  caller, and a non-IP peer (test client) is legal there.
- The `_scrub` pass stays as a second line; `action` and `target_type` are now closed sets, so it can
  no longer alter them. The module-key shape cannot tell a lowercase identifier-shaped secret from a
  key; recorded as a limitation in TS-009 Notes.
- Checkpoint B: `test_flow_rows_hold_no_session_token_and_logout_records_the_address` scans every
  column of every audit row written by login x2, change password and logout for both session
  tokens, both CSRF tokens, both passwords and the session signing key.
- Behaviour change: a bad audit value is now refused (`AuditFieldError`, a 500 on a request) instead
  of written. Rows are unchanged for every existing caller.
- Negative controls run: logout reverted to `target_id=session.session_id` (3 tests fail with the
  check on; 2 with the check also removed); `target_id` check removed (88 of 89 tests in
  `test_audit_no_secrets.py` fail).
- Verification: tests/audit + test_auth_router 168 passed; full suite 948 passed, 4 skipped, coverage
  93.73 %; ruff, black, mypy clean; DICOM module tests 21 passed. No schema or migration change.
- PRB-005 stays `open` (scrub part done; TASK-190 and TASK-191 remain). ADD-013 needs wording changes
  (see report).

## QA review round 1 (QA engineer, 2026-10-31): CHANGES REQUESTED

`in_review → draft`. TS-009 stays `in_review`. PRB-005 correctly stays `open`: the CR-004 Scope
table maps it to TASK-190, 191 and 192, and the TASK-191 Definition of Done is where it becomes `resolved`.

### Findings

1. **[HIGH] The real module key is refused, so the DICOM module breaks.** `backend/app/audit/service.py:25`
   (`_MODULE_KEY = [a-z][a-z0-9_]{0,63}`) has no `-`. The only module key that exists is
   `dicom-viewer` (`backend/modules/dicom_viewer/dicom_viewer/manifest.py:12`, entry point in
   `modules/dicom_viewer/pyproject.toml:8`). QA probes:
   - `ModuleRegistryService.sync_installed([dicom manifest])` raises `AuditFieldError`, and HEAD
     syncs the same manifest without error. `app/main.py:53-58` re-raises, so the API **does not start**
     once the module is installed.
   - `_validate("AUTHZ_DENIED", "module", "dicom-viewer")` and the `AUTHZ_ALLOWED` case are refused.
     Every `module:access` decision (`app/api/deps.py:158-167`) then returns a 500 instead of a 403 or
     the module response, and the `AUTHZ_DENIED` row is lost. This breaks SR-023 AC 7 and the RISK-006
     control. The request is still refused (no access is granted), but the evidence of the decision is lost.
   - `MODULE_ENABLE`/`MODULE_DISABLE` with `<group uuid>:dicom-viewer` (`app/groups/service.py:173-180`)
     is refused after `set_enablement`. The request rolls back with a 500, so a SYSADMIN cannot enable the module.

   Discovery does not constrain `module_key` (`app/modules/discovery.py:23` checks only that it is a
   non-empty string), so the two rules disagree.
   → Define one module-key pattern that includes `-` (e.g. `^[a-z][a-z0-9_-]{0,63}$`). Use it in
   `_is_valid_manifest`, so a manifest whose key does not match is rejected with a warning, and import the
   same constant in `audit/service.py`. Update the TS-009 Notes pattern to match.
2. **[MEDIUM] The caller-shape list is not taken from the callers.** `backend/tests/audit/test_audit_writer.py:339-340`
   uses the invented key `dicom_viewer`, which is why finding 1 passed. The DICOM module tests mock the
   audit service and are not in CI `testpaths`.
   → Take the module key from the real manifest (`dicom_viewer.manifest.manifest.module_key`). Add a test
   that `sync_installed` with the real manifest records `MODULE_DISCOVERED`. Add an app-level test that a
   denied `require_module_enabled("dicom-viewer")` returns 403 and writes one `AUTHZ_DENIED` row.
   Re-run negative control: the old pattern must make these tests fail.
3. **[MEDIUM] The implementation differs from the approved ADD-013 typed-fields text.** ADD-013 (lines 42-45)
   says "`target_id` one or two UUIDs or a UUID plus a **registered** module key". The code checks the
   shape only, and it accepts shapes ADD-013 does not list. The human decides which side changes; QA
   does not edit ADD-013. Wording changes to carry to the human (or implement the registry check instead
   of the first one):
   - "registered module key" becomes "a module key of the manifest key pattern", unless a registry check is added;
   - add the bare module key for `target_type="module"` (module discovery, `module:access`);
   - add `user_type:<UserType>` for `account` (the `account:create` decision, TASK-188);
   - add the empty `target_id` (a decision with no resource id) and `module_registry` with no id;
   - add "`target_id` requires a `target_type`";
   - add "refusal raises `AuditFieldError`; on a request this is a 500 and no row is written".
4. **[LOW] A refused `LOGIN_FAILURE` would skip the lockout counter.** `app/auth/login.py:98-120` calls
   `record(LOGIN_FAILURE)` before `lockout_svc.record_failure`. If `record` raised there, the brute-force
   counter would not increment (RISK-004, RISK-007). This cannot happen today: every argument on that path
   is a constant or an account UUID, and `ip` is not validated. So it is not blocking.
   → Either increment the lockout counter before the audit call, or state in ADD-013 that the refusal is a
   programming-error guard. Optionally, for FAILURE and independent events, write the row with `target_id`
   NULL and an error log rather than losing it.
5. **[LOW] `_scrub` no longer does anything.** `app/audit/service.py:122-126`: every value that reaches
   `_scrub` has already passed the closed-shape check and cannot contain `=`, so the scrub changes nothing.
   The `record` docstring line "Credential-like patterns in the action string are scrubbed" overstates it.
   → Keep the scrub as the documented second line, but reword the docstring ("defensive; cannot alter a
   validated value"). `test_password_scrubbed_by_second_line` takes an unused fixture `audit_repo_mock`.

### Answers to the review questions

- **Fail-closed under SR-023 AC 9.** AC 9 says a secret "is not stored in plaintext". Refusing and redacting
  both meet it, and this task's own Implementation detail 3 chose refusal. Fail-closed is acceptable as a
  guard against programming errors, but only when every caller shape is valid; finding 1 shows one is
  not. On the control paths: `AUTHZ_DENIED` is still a refusal (a 500, not a 403) but loses its row.
  `LOGIN_FAILURE` and `ACCOUNT_LOCKOUT` use constant shapes and cannot be refused (but see finding 4).
  The DICOM `DICOM_STUDY_READ` rows (`router.py:44-61`) use the attachment UUID, which is valid.
- **Caller shapes, QA grep of all 44 `record(` calls and 27 `Resource(` constructions in `app/` and
  `modules/`.** Every `target_type` is in `_TARGETS`. Each `target_id` is one of: a canonical `str(uuid)`
  (the workers pass `str(id)` from `.delay(str(...))` or from a DB row); `<uuid>:<uuid>`; `user_type:<value>`;
  `""`; `None`; or a module key. The module key is the only shape that fails, and it fails for the only
  real module (finding 1). The developer's 20-shape list misses no target type, but it uses the wrong
  key value.
- **Secrets shaped like a module key.** Acceptable without a PRB. No module-key position is fed by
  request input. `module` and `module:access` take the manifest key. `group_module` records only after
  `get_by_key` confirms that the key is registered (`groups/service.py:165-167`), and the
  `modules:enable` decision carries no id. Every generated secret is `token_urlsafe(32)` (mixed case and
  `-`; the chance of an all-lowercase 43-character value is about 6e-11), and policy passwords require an
  upper-case letter. A registry check would close the residual only together with finding 3.
- **`ip`.** Every caller passes `None`, `client_address(request)` (`auth.py:60,109,171`,
  `accounts.py:160`), or the login `ip` that comes from it. `record` falls back to
  `current_client_address()`. Both read the value `ClientAddressMiddleware` sets: the ASGI TCP peer, or an
  `X-Forwarded-For` entry that has been through `ipaddress.ip_address`, so malformed entries are skipped
  and the result is canonical. No caller passes request text.
- **Logout and the flow scan.** The logout row is `account`/`<account id>`, and the cookie is the raw
  `session_id`, so the scan compares like with like. QA negative controls on scratch copies, with the
  session token and then the CSRF token injected into the `LOGIN_SUCCESS` `ip`: in both copies the flow
  test fails at the scan line (`assert not any(value in cell ...)`), so the scan is real.
- **Rewritten scrub tests.** No protection is lost. The `key=value` action is now refused rather than
  redacted (`test_action_with_embedded_credential_is_refused`, which asserts nothing is added), and
  `_scrub` is still tested on its own.

### Verification run (QA, 2026-10-31, working tree on `1d86b5b`)

- `uv run pytest tests/audit tests/api/test_auth_router.py`: 168 passed.
- `uv run pytest modules/dicom_viewer/tests`: 21 passed. These tests mock the audit service, so they
  do not exercise finding 1.
- `uv run pytest --cov=app --cov-fail-under=85`: 948 passed, 4 skipped, 93.73 %.
- `ruff check .`, `black --check .` and `mypy app`: clean. OpenAPI export is identical to `openapi/openapi.json`.
- `cd frontend && npm test -- --run`: 155 passed. `cd infra && python3 -m unittest discover -s tests`: 37 OK.
- Suite-wide token scan (QA pytest plugin, run on the whole `tests/` suite). It recorded every session
  and CSRF token issued and every `AuditLog` row inserted into any real database: 25 tokens, 45 rows,
  0 hits. With the session token injected into `LOGIN_SUCCESS.ip`, 2 hits and 4 failures.
- Traceability (TASK-192, TS-009, PRB-005, SR-023; 406 scanned): 0 errors, 7 warnings (in_review or
  obsolete link targets, none of them caused by this task).

## Checkpoint B result (QA engineer, 2026-10-31): NOT CLOSED, TASK-192 CHANGES REQUESTED

Checkpoint B is defined as after tasks 4 to 7 (CR-004 Plan, Checkpoints). Every criterion was re-run on
the working tree:

| Checkpoint B criterion | Result |
|---|---|
| Backend suite green (coverage ≥ 85 %) | 948 passed, 4 skipped, 93.73 % |
| DICOM-module suite green | 21 passed. Green, but the module cannot start or be accessed with this change (finding 1), which the mocked suite does not show |
| Frontend suite green | 155 passed |
| Static role-check test green | passed (within `tests/` run) |
| Decision table green | passed (within `tests/` run) |
| No audit row in the suite's database contains a session token | **Pass.** Suite-wide scan: 45 real-DB rows, 25 session/CSRF tokens, 0 hits. The negative control is detected. The flow test scans every column |

Every criterion passes as written, but task 7 is not approved, and finding 1 is a regression in the
TASK-187 scope (`module:access` decisions). Checkpoint B closes at the TASK-192 round-2 approval. That
round must re-run the token scan and the module-access test from finding 2.

## Round 2 notes (1.2, 2026-10-31)

Answers to QA round 1:

1. **Module key (HIGH).** One pattern, `MODULE_KEY = [a-z][a-z0-9_-]{0,63}`, in the new
   `backend/app/core/module_key.py`; `audit/service.py` imports it and module discovery
   (`_is_valid_manifest`) now rejects a manifest whose key does not match. Checked against the real
   `dicom-viewer` and the test manifests (`test-module`, `good-module`); `""` is still rejected.
2. **Real-caller tests.** `backend/modules/dicom_viewer/tests/test_audit_module_key.py` takes the key
   from the real manifest (the backend tests cannot import `dicom_viewer`, so `test_audit_writer.py`
   uses the literal `dicom-viewer`): discovery accepts it; `sync_installed` with a real `AuditService`
   records MODULE_DISCOVERED and MODULE_REGISTRY_SYNC; MODULE_ENABLE records one row; a denied
   `require_module_enabled("dicom-viewer")` returns 403 with exactly one AUTHZ_DENIED row (real
   database). `tests/modules/test_discovery.py::TestModuleKeyShape` covers accepted and refused keys.
3. **ADD-013** is human-approved and was not edited. Wording changes needed (for the human):
   - "`target_id` one or two UUIDs or a UUID plus a registered module key" becomes: "`target_id` is
     checked against the shape of its `target_type`: `None`; one UUID (account, appointment,
     attachment, clinical entry, consent, consent grant, group, patient roster, anonymized dataset);
     `<uuid>:<uuid>` (group membership); `<uuid>:<module key>` (group module); a bare module key
     (module); `user_type:<UserType>` (account, for an `account:create` decision); the empty string
     for a decision with no resource id; no id for the module registry."
   - "registered module key" becomes "module key of the shape `^[a-z][a-z0-9_-]{0,63}$`, checked by
     shape only, not against the registry".
   - Add: "`action` is a member of `AuditAction`; `ip` is derived by the client-address rule and not
     validated by the writer"; "the module-key pattern is defined once and shared with module discovery".
   - Add: "a refused value raises `AuditFieldError` before any row is built; the failed-login counter is
     incremented before the audit write, so a refusal cannot skip it".
4. **Lockout order (LOW).** `LoginService.login` now calls `lockout_svc.record_failure` before the
   LOGIN_FAILURE audit write in both failure branches; tests in `tests/auth/test_login_service.py`.
5. **`_scrub` (LOW).** Docstring reworded as defence in depth; unused fixture removed from
   `test_password_scrubbed_by_second_line`.

Negative controls: pattern reverted to no hyphen, 4 tests in `test_audit_module_key.py`, 7 in
`test_discovery.py` and 2 in `test_audit_writer.py` fail; audit-before-counter order restored, the 2
lockout-order tests fail. Both restored afterwards.

Verification: `tests/audit tests/api/test_auth_router.py tests/modules tests/auth` 269 passed;
`modules/dicom_viewer/tests` 25 passed; full suite 961 passed, 4 skipped, coverage 93.74 %; ruff,
black, mypy clean.

## QA review round 2 (QA engineer, 2026-10-31): APPROVED

`in_review → approved`; TS-009 `in_review → approved`. PRB-005 stays `open` (TASK-190, TASK-191).

Round 1 findings:

1. HIGH module key: **closed.** One pattern, `backend/app/core/module_key.py:9` (`[a-z][a-z0-9_-]{0,63}`), is used by
   `audit/service.py` and by `discovery._is_valid_manifest`. Every module key in the repo matches it,
   test fixtures included (`dicom-viewer`, `test-module`, `good-module`, `mod-a`, `mod-b`, `m1`, `live-module`,
   `probe`, `dicom`, `dicom_viewer`, `enmod`, `test_mod`, `xray`; frontend `analytics`, `dicom-viewer`). Only the
   deliberate `""` is rejected. QA negative control (scratch copy, pattern without `-`): 9 tests fail in `tests/`
   (2 `test_audit_writer.py`, 7 `test_discovery.py`) and 4 fail in `test_audit_module_key.py`.
2. MEDIUM real-manifest tests: **closed.** The 403 test is genuine: real `get_db` on a Postgres container, real
   `ModuleAccessGuard`, `AuthorizationService` and `AuditService`, no mocked audit; it asserts exactly one
   `AUTHZ_DENIED` row. Under the mutated pattern it fails (500).
3. MEDIUM ADD-013 wording: **carried, not blocking.** The code checks shape only, and ADD-013 says "registered".
   The wording list is in `## Round 2 notes` item 3; TASK-201 (ADD-013 unit notes, line 55) must carry it to
   the human. Until then ADD-013 overstates the check.
4. LOW lockout order: **closed.** `record_failure` now runs before the `LOGIN_FAILURE` write in both branches.
   QA negative control (HEAD `login.py`): both new tests fail.
5. LOW `_scrub`: **closed.**

Round 2 findings (LOW, not blocking):

- **R2-1 [LOW] CI does not run the DICOM module tests.** `.github/workflows/ci.yml:105` runs `pytest` with
  `testpaths = ["tests"]` (`backend/pyproject.toml:58`), so `modules/dicom_viewer/tests` (including the
  real-manifest and real-DB 403 tests) never runs in CI. This is pre-existing. The pattern regression itself is
  still caught in CI by the 9 literal-key tests. → Add a CI step `uv run pytest modules/dicom_viewer/tests`
  (a separate call, because of the conftest path). Carry it to TASK-202.
- **R2-2 [LOW] A rejected manifest only logs a WARNING.** `app/modules/discovery.py:27-29`: a module with a bad
  key is skipped with a warning, and startup goes on (the TASK-070 isolation rule). The module becomes
  unreachable, so the failure is closed, not open. If the module was registered before, `remove_absent` then
  deletes its registry row: with group enablements this fails on the FK (startup stops, with an unclear error),
  and without them the module disappears silently. → Log at ERROR and name the entry point. Whether a rejected
  installed entry point should stop startup is a design decision for TASK-201/ADD-013.

Verification run (QA, working tree on `1d86b5b`):

- `tests/audit tests/api/test_auth_router.py tests/auth tests/modules`: 269 passed.
- `modules/dicom_viewer/tests`: 25 passed.
- Full suite with coverage and the QA token-scan plugin: 961 passed, 4 skipped, 93.74 %; 25 tokens, 45 real-DB
  audit rows, 0 hits (DICOM suite: 2 rows, 0 hits).
- ruff, black, mypy: clean. OpenAPI export unchanged.
- Frontend: 155 passed. Infra: 37 OK.
- Traceability (TASK-192, TS-009, PRB-005, SR-023, TASK-189): 0 errors.

## Checkpoint B final result (QA engineer, 2026-10-31): PASSED

Tasks 4 to 7 (TASK-187, 188, 189, 192) are all `approved`. Every criterion was re-run on the working tree:

| Checkpoint B criterion | Result |
|---|---|
| Backend suite green (coverage ≥ 85 %) | 961 passed, 4 skipped, 93.74 % |
| DICOM-module suite green | 25 passed, including the real `dicom-viewer` key and the real-DB 403 gate test (not in CI, R2-1) |
| Frontend suite green | 155 passed |
| Static role-check test green | `tests/authz/test_no_role_decisions_outside_authz.py`: 35 passed |
| Decision table green | `tests/authz/test_decision_table.py`: 135 passed |
| No audit row in the suite's database contains a session token | Pass: the suite-wide scan found 0 hits in 45 rows against 25 session and CSRF tokens, and the injected-token negative control was detected (round 1). The flow test scans every column |

The earlier "NOT CLOSED" result above is superseded.

## Version history

- 1.1 (2026-10-31) — Implemented; handed to QA (`in_review`).
- 1.1 (2026-10-31) — QA review round 1: CHANGES REQUESTED (`in_review → draft`), findings 1 to 5; Checkpoint B re-run, not closed.
- 1.2 (2026-10-31) — Round 2: QA findings 1 to 5 addressed; handed to QA (`in_review`).
- 1.2 (2026-10-31) — QA review round 2: APPROVED (`in_review → approved`); TS-009 approved; Checkpoint B passed.
