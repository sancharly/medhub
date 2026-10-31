---
id: "TASK-192"
type: task
title: "Typed audit fields so no secret can be stored in any field"
status: draft
version: "1.0"
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

- [ ] SR-023 AC 9: no listed secret kind can be stored under any field (`backend/tests/audit/test_audit_no_secrets.py`).
- [ ] SR-023 AC 5: the logout row carries no session token (`backend/tests/api/test_auth_router.py`).
- [ ] Every current audit caller still records (full backend suite).

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

- [ ] Backend suite and DICOM module tests pass; coverage ≥ 85 %.
- [ ] TS-009 `in_review`.
- [ ] `traceability-check` shows no error for TASK-192, TS-009, SR-023.
