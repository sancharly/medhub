# ADR-0016: Failure audit events are committed on their own transaction

## Status

Accepted (2026-10-30, CR-002 D-8: the human approved the PRB-052 amendment). Proposed earlier the
same day by the Software Architect role. It refines
[ADR-0011](0011-security-compliance-approach.md) (append-only audit log) and replaces the
`durable=True` flag that CR-002 TASK-173 introduced.

## Context

`get_db` (`backend/app/db/repositories/session.py`) gives each request one session. It commits
when the endpoint returns and rolls back on any exception. `AuditService.record` adds its row to
that same session. An event that records a failure is almost always followed by an error
response, so the row is rolled back with the request
([PRB-052](../../problem-reports/PRB-052-failure-audit-events-rolled-back-on-error-response.md)).
The affected events are `AUTHZ_DENIED`, `LOGIN_FAILURE`, `ACTIVATION_FAILED`, the
`DICOM_STUDY_READ` FAILURE and, found while planning this ADR, `ACCOUNT_LOCKOUT`. That last one has
outcome SUCCESS but is recorded inside the failing login that then returns 401.

TASK-173 worked around the problem for one event with `AuditService.record(..., durable=True)`,
which commits the whole request session. On a write path that would also commit unfinished
business writes.

## Options

1. **Keep `durable=True` and pass it at every failure call site.** Rejected: it commits the
   caller's whole unit of work, so the next write-path caller commits half-done business writes.
   Every new call site must also remember the flag.
2. **Have `get_db` re-insert the audit rows after the rollback.** Rejected: it couples the
   session dependency to the audit model, relies on inspecting flushed objects, and does not
   cover Celery workers, which open their own sessions.
3. **A SAVEPOINT around the audit insert.** Rejected: rolling back the outer transaction
   discards a released savepoint too.
4. **Commit every audit event on its own transaction.** Rejected: a SUCCESS event for a business
   write that is later rolled back would claim something that did not happen. That is false
   evidence, which is worse than a missing row. It also doubles connection use on every request.
5. **Queue audit events to a worker (Celery or Redis).** Rejected: an event is lost when the
   broker is down, it adds SOUP surface, and the audit write is no longer synchronous with the
   decision (SR-023, "never swallows").
6. **Chosen: commit failure events on their own short-lived session, inside `AuditService`.**

## Decision

- `AuditService.record` decides, from the event alone, whether the row is **independent**:
  `outcome` is `FAILURE`, or `action` is in one module-level set of refusal events recorded
  inside a failing request. Today that set is `{ACCOUNT_LOCKOUT}`. Callers do not choose. There is
  no flag.
- An independent row is written by `AuditRepository` on a new `Session` bound to the request
  session's engine (`session.get_bind()`). It is committed and closed before `record` returns. A
  failed write raises, so the event is never silently dropped (TS-009 §5.5.3).
- Every other event stays in the request's transaction, as it does now, and commits or rolls back
  with the business operation it describes.
- The `durable` parameter and `AuditRepository.commit()` are removed.

## Consequences

- **Gained:** failure evidence (SR-023 AC 1 and AC 2, RISK-006) survives the error response on
  every path, request or worker, with one mechanism in one place. A write path can no longer be
  partly committed by an audit call.
- **Given up:** an independent row is not atomic with its request. If a request records a failure
  and later succeeds, the row stays. That is correct, because the failure did happen.
- **Cost:** each independent event briefly takes a second pooled connection. A login burst is
  bounded by the Redis lockout. The default pool (5 + 10 overflow) is enough for the MVP load
  (SR-026). Pool exhaustion makes the request fail with an error and does not drop the row
  silently.
- **Constraint:** the independent session cannot see the request's uncommitted rows. `audit_log`
  has no foreign key (`actor_id` is not an FK), so the insert does not depend on them.
- **Tests:** an independent row commits outside any test-held transaction. Real-database tests
  must clean `audit_log` themselves. Unit tests that mock `AuditRepository` assert which method
  was called.
- **Unchanged:** an `AUTHZ_ALLOWED` row of a request that then fails (for example with 404 or
  502) is still rolled back. The access did not complete, and the FAILURE event, where one
  exists, records it.
