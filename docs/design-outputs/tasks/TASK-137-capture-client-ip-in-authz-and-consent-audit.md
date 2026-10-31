---
id: "TASK-137"
type: task
title: "Capture client IP in authorization and consent audit records"
status: approved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-10-31"
links:
  - target: "RISK-006"
    relation: mitigates
  - target: "SR-023"
    relation: implements
  - target: "SR-042"
    relation: implements
  - target: "PRB-010"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-185"
    relation: relates_to
  - target: "ADD-013"
    relation: relates_to
  - target: "TASK-027"
    relation: relates_to
  - target: "TASK-014"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium", "control:protective", "cr:CR-004"]
---

# TASK-137 — Capture client IP in authorization and consent audit records

- **Software item / unit:** SI-AUDIT `U-AUD-Writer` (ADD-013); consumers in SI-API (`auth`,
  `accounts` routers).
- **Resolves (through CR-004):** PRB-010. Source: `docs/reports/CODE-REVIEW-2026-07.md` finding D.
- **Depends on:** TASK-185 (the originating client address and its `ContextVar`).
- **Branch:** `fix/review-2026-07-security` (CR-004). One commit per QA-approved task.
- **Size:** S (3 source files, 1 new test file, TS-009)
- **Needs:** a Docker daemon for the testcontainers PostgreSQL test.
- **Design:** [ADR-0019](../../design/adr/0019-originating-client-address-trusted-proxy-rule.md)

## Objective

SR-023 AC 6: every audit entry for an event caused by an HTTP request records the originating
client address of that request (SR-042); an event with no request records none and is still
written. Today the authorization, consent and most service rows have `ip=None`, and the login,
logout, password and unlock rows carry the proxy's address (PRB-010 Investigation).

## Implementation detail

1. `AuditService.record` (`backend/app/audit/service.py:31-70`): when `ip` is `None`, use the
   value of the client-address `ContextVar` from TASK-185. An explicit `ip` keeps precedence.
   Outside a request the variable is unset and the row is written with no address.
2. Replace every `request.client.host` read with the TASK-185 accessor:
   `backend/app/api/routers/auth.py:58,107,169`, `backend/app/api/routers/accounts.py:146`. After
   this task no code under `backend/app` reads `request.client.host` (TASK-185's test enforces it).
3. No signature change in `AuthorizationService`, `ConsentService` or the other services: their
   `ip=None` arguments now mean "take it from the request".

## Tests (write first)

- `backend/tests/audit/test_audit_client_address.py` (real database, `create_app()`, real
  `get_db`, PostgreSQL testcontainer; pattern of `backend/tests/audit/test_failure_audit_persistence.py`):
  - a PATIENT reads another patient's data through a trusted peer with
    `X-Forwarded-For: 203.0.113.7` → 403 → the `AUTHZ_DENIED` row has `ip == "203.0.113.7"`;
  - the same through an untrusted peer with a forged header → the row has the peer's address;
  - a consent grant through the trusted peer → the `CONSENT_GRANT` row has the client address;
  - a login failure → the `LOGIN_FAILURE` row has the client address, not the peer's.
- `backend/tests/audit/test_audit_writer.py`: unit cases: explicit `ip` wins; unset variable →
  `None`; worker-context record (no request) → `None`, no error.
- `backend/tests/workers/test_email_tasks.py`: existing worker tests still pass (rows with no address).

## Acceptance criteria

- [x] SR-023 AC 6: request-caused rows record the originating client address
      (`backend/tests/audit/test_audit_client_address.py`).
- [x] SR-023 AC 6: background and scheduled rows record no address and are written
      (`backend/tests/audit/test_audit_writer.py`, `backend/tests/workers/test_email_tasks.py`).
- [x] SR-042 AC 2: a forged `X-Forwarded-For` from an untrusted peer does not reach the audit row
      (`backend/tests/audit/test_audit_client_address.py`).

## Verification

```sh
cd backend && uv run pytest tests/audit tests/authz tests/api/test_auth_router.py tests/workers -v
cd backend && uv run pytest --cov=app --cov-fail-under=85
cd backend && uv run ruff check . && uv run mypy app
grep -rn "client.host" backend/app        # expect matches only in app/core/client_address.py
```

Negative control: make `record` ignore the `ContextVar`; the address tests fail. Record the
result in the handoff.

## Records

- **TS-009** → 1.3 (first CR-004 task to change it; approval record cleared, `in_review`): add
  TC-009.9 (address on request-caused rows, none on background rows), `verifies` SR-023 and
  SR-042. Later CR-004 tasks add TC-009.10..12 under the same version.
- **PRB-010**: `## Resolution` with the commit, the tests and the negative-control result; status
  `resolved`, not `closed`.

## Definition of Done

- [x] Lint, type-check and the backend suite pass; coverage ≥ 85 %.
- [x] TS-009 1.3 `in_review` with TC-009.9; PRB-010 `resolved`.
- [x] `traceability-check` shows no error for TASK-137, TS-009, SR-023, SR-042, PRB-010.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-006 (risk register bootstrap, TASK-147).
  Traceability only: the requirement content is unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.3 (2026-10-31) — CR-004 Plan stage (Software Architect role): rescoped against the current
  tree. The address rule moves to TASK-185 (SR-042, ADR-0019); this task consumes it. Links
  `implements` SR-042, `relates_to` PRB-010, CR-004, TASK-185, ADD-013 added. Tests named by path,
  TS-009 TC-009.9 planned. Still `draft`.
- 1.4 (2026-10-31) — Implemented (Software Developer role); `in_review`. `AuditService.record` falls
  back to `current_client_address()`; `auth.py` and `accounts.py` use `client_address(request)`;
  `KNOWN_READS` lost `auth.py` and `accounts.py`. TS-009 1.3 (TC-009.9), PRB-010 `resolved`.
- 1.4 (2026-10-31) — QA review: APPROVED (`in_review → approved`); review recorded.

## Implementation notes

- Files: `backend/app/audit/service.py`, `backend/app/api/routers/auth.py`,
  `backend/app/api/routers/accounts.py`, `backend/tests/audit/test_audit_client_address.py` (new),
  `backend/tests/audit/test_audit_writer.py`, `backend/tests/api/test_client_address_middleware.py`.
- `backend/app/api/routers/anonymized_data.py:66` still reads `request.client.host`; it is the
  unauthenticated rate-limit key, not an audit row, and stays in `KNOWN_READS` for TASK-186. The
  `grep` in Verification therefore also matches that file until TASK-186.
- No schema, OpenAPI or migration change.
- Negative control: `record` with `ip=ip` only: 4 tests fail (3 in `test_audit_client_address.py`,
  1 in `test_audit_writer.py`); the login-failure test still passes because the login flow passes
  the address explicitly. Restored: all pass.

## QA review (QA engineer, 2026-10-31)

**Verdict: APPROVED.** TASK-137 → `approved`; TS-009 1.3 → `approved` (reviewed). PRB-010 stays
`resolved` (closure follows CR-004). SR-023, SR-042 and RISK-006 are not edited.

Behaviour (checked against the code and by running it):

- `AuditService.record` (`backend/app/audit/service.py:65`): an explicit `ip` wins; `ip=None` takes
  `current_client_address()`; outside a request the `ContextVar` default is `None` and the row is
  still written. `AuditService.record` is the only `AuditLog` constructor in `backend/app` (the
  only other insert path, `AuditRepository.add_independent`, is called only from `record`), so no
  audit write path bypasses the address. The workers (`retention_tasks.py`, `session_tasks.py`) go
  through `record` and run with no request context.
- Real application, real `get_db`, PostgreSQL testcontainer: trusted peer + `X-Forwarded-For` →
  the client address on `AUTHZ_DENIED`, `CONSENT_GRANTED` and `LOGIN_FAILURE`; untrusted peer with a
  forged header → the peer's address (SR-042 AC 2).
- Negative controls (pytest plugin, no source edit): `record` ignoring the variable → 4 failures
  (authz, forged header, consent, unit fallback), matching the developer's result; routers
  reverted to the raw TCP peer → the login-failure test fails.

Developer deviations:

1. `anonymized_data.py:66` still reads `request.client.host`: accepted. It keys the no-session
   rate limit and writes no audit row; it stays in `KNOWN_READS` for TASK-186, and the static check
   in `test_client_address_middleware.py` blocks any new read.
2. `CONSENT_GRANTED` vs `CONSENT_GRANT`: accepted. `ConsentService.grant` emits `CONSENT_GRANTED`
   (`backend/app/authz/consent.py:60`); `AuditAction.CONSENT_GRANT` (`backend/app/audit/actions.py:8`)
   is not emitted anywhere under `backend/app` (pre-existing, used only in `test_audit_writer.py`).
3. CSRF in the consent test: not a defect. CSRF is enforced twice by design: the `require_csrf`
   dependency and the app-wide `CsrfEnforcementMiddleware` (`backend/app/main.py:83`, TASK-128).
   Overriding the dependency cannot bypass the middleware, which answers 403 before routing. No PRB.
4. PRB-010 `resolved`: valid. TASK-185 (rule) and TASK-137 (every request-caused row) together
   restore SR-023 AC 6 for audit; CR-004 carries `resolves` → PRB-010; the Resolution names the
   tests and the negative control.

Risk control: RISK-006's protective control (SR-023 AC 6, SR-042; TASK-185, TASK-137) is
implemented and tested (TC-016.1..3, TC-009.9). OpenAPI unaffected (fresh export identical to
`backend/openapi/openapi.json`).

Findings (all LOW, not blocking):

1. **TS-009 left `approved` during the change** — `docs/design-outputs/tests-specifications/TS-009-audit-logging.md:5`.
   Version 1.3 changed content but the status stayed `approved` (the Records section asked for
   `in_review`). This review now covers 1.3, so the status is correct as of now. Fix for next
   time: move a TS to `in_review` when its content changes.
2. **RISK-006 verification column stale** — `docs/risks/RISK-006-*.md:73,76,84-85` still say
   "none yet", "TC-009.9 (planned)" and "TASK-137, still `draft`". Fix: update them in the CR-004
   risk re-review. RISK-006 is human-approved, so QA does not edit it.
3. **Logout, password-change and admin-unlock rows have no behavioural address test** —
   `backend/app/api/routers/auth.py:108,170`, `backend/app/api/routers/accounts.py:147`. Reverting
   them to the raw peer fails no behavioural test; only the static `KNOWN_READS` check guards them.
   Fix (optional): add one real-DB case (e.g. logout through the trusted peer) in a later TC-009 case.
4. **TC-009.9 cites `tests/workers/test_email_tasks.py` as no-address evidence** — those tests patch
   `AuditService.record`, so they do not show `ip=None`. The real evidence is
   `test_audit_writer.py::test_no_request_context_records_no_address`. Fix: drop the citation or
   reword it as "worker tests still pass" when TS-009 next changes.

Pre-existing (not blocking): `backend/app/api/deps.py:51-53` says the CSRF dependency "can be
overridden in tests"; with the app-wide middleware an override alone cannot let a state-changing
request through.

Verification run (from `backend/`):

- `uv run pytest tests/audit tests/authz tests/api/test_auth_router.py tests/workers tests/api/test_client_address_middleware.py` → 102 passed.
- `uv run pytest tests/audit/test_audit_client_address.py -v` → 4 passed (Docker).
- `uv run pytest --cov=app --cov-fail-under=85` → 625 passed, 4 skipped (object-store SSE, needs
  `OBJECT_STORE_INTEGRATION=1`); coverage 91.66 %.
- `uv run ruff check .` → clean; `uv run black --check .` → 238 unchanged; `uv run mypy app` → no issues.
- `grep -rn "client.host" app` → only `app/api/routers/anonymized_data.py:66` (deviation 1).
- Fresh `python -m app.export_openapi` → identical to `openapi/openapi.json`.
- Traceability (scope TASK-137, TS-009, PRB-010, SR-023, SR-042 and their neighbours; 405 records
  scanned, 42 checked): 0 errors; 6 warnings, none on these records (W5 TASK-185 → ADD-026,
  ADD-005 → SOUP-004/005 `in_review`; W6 ADD-004 → ADD-002, CR-002 → SOUP-022/023 `obsolete`).
