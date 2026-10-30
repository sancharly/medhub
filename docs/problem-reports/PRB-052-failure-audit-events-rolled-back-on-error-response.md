---
id: "PRB-052"
type: problem-report
title: "FAILURE audit events written before an error response are rolled back"
status: open
version: "1.0"
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
`critical`. All released versions with the audit trail are affected. Whether notification is
needed depends on whether any installation relies on the audit trail for failure evidence; to be
decided by the human with the resolving CR.

## Proposed resolution

Write security-relevant audit events on their own short-lived session (or connection) inside
`AuditService`, so they commit regardless of the request's outcome. Replace TASK-173's `durable`
flag with it. Add tests against a real database that assert the rows persist after an error
response, for each affected path. Revisit RISK-006 for the new cause. Needs a task and a CR.

## Source

Software developer and QA, CR-002 TASK-173 (2026-10-30); outside CR-002's scope unless the human
decides otherwise.
