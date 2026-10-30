---
id: "PRB-052"
type: problem-report
title: "FAILURE audit events written before an error response are rolled back"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
criticality: major
links: []
tags: ["audit", "security", "backend"]
---

# PRB-052 — FAILURE audit events written before an error response are rolled back

## Observed

Found by the software developer while implementing CR-002 TASK-173 and confirmed by QA on
2026-10-30. A PATIENT requesting another patient's attachment gets `403`, but the database holds no
audit row for that actor: the `AUTHZ_DENIED` event is never stored. QA reproduced this with a
throwaway test (not kept) using the real `get_db`, a PostgreSQL testcontainer and a real
`AuthorizationService`.

## Impact

Audit events that record a failure and are followed by an error response are lost across the
application. This covers authorization denials and, by reading the code, failed logins, failed
activations and failed DICOM study reads. SR-023 AC 1 (failed authentication is recorded) and AC 2
are not met for failures, so evidence of brute-force attempts and access denials is missing from
the audit trail.

## Investigation

`get_db` (`backend/app/db/repositories/session.py:22-32`) commits only when the request succeeds
and calls `session.rollback()` on any exception. FastAPI passes the endpoint's `ProblemError` into
the dependency's generator, so every row the request added before raising is rolled back,
including audit rows. Affected paths:

- `AUTHZ_DENIED`: `backend/app/authz/service.py:74-82` records the row, then the caller raises
  (reproduced).
- `LOGIN_FAILURE`: rows written at `backend/app/auth/login.py:80-115`, then the router raises
  `UnauthenticatedError` at `backend/app/api/routers/auth.py:63-64` (code reading, not run).
- `ACTIVATION_FAILED`: `backend/app/identity/activation.py:69-77` (code reading, not run).
- `DICOM_STUDY_READ` FAILURE: `backend/modules/dicom_viewer/dicom_viewer/router.py:34-43` (code
  reading, not run).
- `ACCOUNT_LOCKOUT`: `backend/app/auth/lockout.py:80-88`, recorded with outcome SUCCESS inside a
  failing login that ends in a 401. Not in the original list, found while designing the fix: an
  outcome-based rule alone would miss it.

The defect went undetected because the existing tests mock the audit repository: they assert that
a row was added to the session, never that it was committed. TASK-173 worked around it for the
`ATTACHMENT_ACCESS` FAILURE event only, with `AuditService.record(..., durable=True)`, which
commits the whole request session (`backend/app/audit/service.py:61-62`,
`backend/app/db/repositories/audit_repo.py:23-25`). That is safe on a read path but would commit
unfinished business writes on a write path.

## Safety evaluation

No direct patient harm: clinical data is not changed or wrongly shown, the access itself is still
denied, and the Redis login lockout still works. It is a security and compliance control (SR-023)
that silently fails, and it is a cause not considered in RISK-006 (severity 2). Hence `major`, not
`critical`. No released version exists, so no released version is affected and no notification is needed
(the human's answer to the notification question in CR-002, Q-8).

## Resolution

Fixed by the commit with the subject "FIX, TEST: Commit failure audit events on their own
transaction (TASK-183)", under CR-002 and ADR-0016.

- `AuditRepository.add_independent` (`backend/app/db/repositories/audit_repo.py`) writes the row on
  its own short-lived `Session` bound to `session.get_bind()` and commits it. `AuditRepository.commit()`
  and `AuditService.record(..., durable=)` are removed.
- `AuditService.record` (`backend/app/audit/service.py`) sends an event through `add_independent`
  when its outcome is FAILURE or its action is in `_INDEPENDENT_ACTIONS` (`ACCOUNT_LOCKOUT`); other
  events stay in the request transaction. No call site changed apart from dropping `durable=True`
  in `backend/app/attachments/service.py`. An independent row is not atomic with the request.
- Both 502 responses (attachment fetch, DICOM study) now declare `application/problem+json` with
  `ProblemDetail`; `backend/openapi/openapi.json` and `frontend/src/api/generated/openapi.ts` were
  regenerated.

Verification, reproducible with a Docker daemon:

```sh
cd backend
uv run pytest tests/audit tests/attachments/test_attachment_integrity_persistence.py -v  # 25 passed
uv run pytest modules/dicom_viewer/tests -v                                              # 21 passed
```

The real-database tests (TS-009 TC-009.4..8, TS-007 TC-007.6) send each request through
`create_app()` with the real `get_db`, receive the error status and find the row on a separate
session, for `AUTHZ_DENIED` (403), `LOGIN_FAILURE` (unknown email, wrong password, inactive account,
locked account), `ACCOUNT_LOCKOUT`, `ACTIVATION_FAILED`, `DICOM_STUDY_READ` and
`ATTACHMENT_ACCESS`. An atomicity test shows a business row and a SUCCESS event of a failing request
are rolled back while the FAILURE row persists.

Mutation check: with `AuditService.record` routing every event through `add` (the old behaviour),
9 of the 9 persistence tests fail (7 in `tests/audit/test_failure_audit_persistence.py`, the TC-007.6
test, and the DICOM test); restored, they pass.

## Source

Software developer and QA, CR-002 TASK-173 (2026-10-30). Brought into CR-002's scope by the human
(D-7, 2026-10-30; amendment approved in D-8) and resolved by TASK-183.
