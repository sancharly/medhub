---
id: "TASK-137"
type: task
title: "Capture client IP in authorization and consent audit records"
status: draft
version: "1.3"
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

- [ ] SR-023 AC 6: request-caused rows record the originating client address
      (`backend/tests/audit/test_audit_client_address.py`).
- [ ] SR-023 AC 6: background and scheduled rows record no address and are written
      (`backend/tests/audit/test_audit_writer.py`, `backend/tests/workers/test_email_tasks.py`).
- [ ] SR-042 AC 2: a forged `X-Forwarded-For` from an untrusted peer does not reach the audit row
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

- [ ] Lint, type-check and the backend suite pass; coverage ≥ 85 %.
- [ ] TS-009 1.3 `in_review` with TC-009.9; PRB-010 `resolved`.
- [ ] `traceability-check` shows no error for TASK-137, TS-009, SR-023, SR-042, PRB-010.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-006 (risk register bootstrap, TASK-147).
  Traceability only: the requirement content is unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.3 (2026-10-31) — CR-004 Plan stage (Software Architect role): rescoped against the current
  tree. The address rule moves to TASK-185 (SR-042, ADR-0019); this task consumes it. Links
  `implements` SR-042, `relates_to` PRB-010, CR-004, TASK-185, ADD-013 added. Tests named by path,
  TS-009 TC-009.9 planned. Still `draft`.
