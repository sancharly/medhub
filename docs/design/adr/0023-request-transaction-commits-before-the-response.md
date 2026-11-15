# ADR-0023: The request transaction commits before the response is sent

## Status

Accepted (2026-11-13, Carlos Santiago Liceras, CR-006 D-28). Proposed the same day by the
Software Architect role (CR-006 D-27, PRB-080). It refines [ADR-0016](0016-failure-audit-events-on-own-transaction.md) for streamed
responses (see "Consequences") and builds on [ADR-0021](0021-bounded-attachment-io-and-bound-two-pass-download.md)
(two-pass download) and [ADR-0022](0022-blocking-io-off-the-event-loop-with-matched-pools.md).

## Context

`get_db` (`backend/app/db/repositories/session.py:34-45`) is a FastAPI dependency with `yield`: it
commits after the handler and rolls back on any exception. It is reached by 31 `Depends(get_db)`
sites in 15 files (routers, `api/deps.py`, `audit/deps.py`). FastAPI 0.138 (SOUP-002) runs the
teardown of a dependency with the default scope `"request"` after `await response(...)`
(`fastapi/routing.py:131-137`), so the commit runs after the body has been sent (PRB-080):

1. A 201 can reach the client before the row is committed; an immediate read answers 404 (QA probe).
2. A commit that fails after the 201 loses a write the user saw acknowledged (clinical entry,
   attachment record, consent revoke); the response cannot be changed any more.
3. A download's SUCCESS `ATTACHMENT_ACCESS` and `AUTHZ_ALLOWED` rows are committed only after the
   transfer; content is disclosed before its audit row exists, and a failing commit is invisible.
4. A streamed download keeps its session, and its pooled connection, for the whole transfer (PRB-081
   names this as one contribution to its bound).

FastAPI 0.138 offers `Depends(..., scope="function")` (`fastapi/params.py:749`): the teardown runs on
the function exit stack, which closes when the endpoint has returned and its response has been
serialised, before the response is sent. Two facts constrain its use
(`fastapi/dependencies/models.py:63-71`, `dependencies/utils.py:318-329`):

- The dependency cache key includes the computed scope. `Depends(get_db)` and
  `Depends(get_db, scope="function")` in one request are **two sessions**, two transactions, one
  of them still committing after the response.
- A generator dependency with scope `"request"` that depends on a `"function"` one is refused at
  start-up (`DependencyScopeError`). No generator dependency depends on `get_db` today.

## Options

1. **`scope="function"` on every use of `get_db`, through one shared alias.** One change at the
   transaction boundary; every route, read or write, commits (or rolls back) before its response.
2. **Explicit `session.commit()` in each handler or service before it returns.** Rejected: read
   routes write audit rows too (`AUTHZ_ALLOWED`, `ATTACHMENT_ACCESS`), so every route needs it; a
   missed site silently keeps today's order, and `get_db` still commits after the response.
3. **Per-route scope (write routes and the download only).** Rejected: a request whose dependencies
   mix the two scopes gets two sessions (cache key), splitting one unit of work across two
   transactions; read routes would keep committing audit rows late.
4. **A custom `APIRoute` or middleware that commits before sending.** Rejected: re-implements, in
   project code, what the framework now provides.
5. **Unit of work owned by the services (no commit in `get_db`).** Rejected: a refactor of every
   service for the same effect as option 1.

## Decision

Option 1.

- `get_db` keeps its body (commit on return, rollback on exception, close). Every dependency on it
  is declared with `scope="function"` through one alias in `app/db/repositories/session.py`
  (for example `DbSession = Annotated[Session, Depends(get_db, scope="function")]`), and the 31
  sites use it. A test walks the dependants of every route of the assembled application (core and
  modules) and fails if any `get_db` dependant has another scope, or if a route resolves more than
  one `get_db` cache key.
- **Commit failure.** The commit raises inside the function exit stack, before `await response(...)`,
  so the exception reaches the error handlers and the client gets a 5xx problem response, never the
  prepared success status.
- **Streamed download (ADR-0021).** The SUCCESS `ATTACHMENT_ACCESS` row and the `AUTHZ_ALLOWED` row
  join the request transaction as today and are now **committed before the first byte is sent**.
  If that commit fails, no content is served. The response generator runs after the session is
  closed: it must not use the request session or an ORM instance of it (they are expired by the
  commit and detached by the close). `open_stream` captures the plain values the generator needs
  (attachment id, size, checksum, actor id) before it returns. A mismatch in pass 2 still records a
  FAILURE row on its own transaction (ADR-0016), bound to the engine rather than to the closed
  request session.
- **Upload.** The multipart body is parsed before the handler, so the scope does not change the
  upload path. The 201 is sent only after the attachment row is committed. A commit failure after
  the object was written to the object store leaves an unreferenced encrypted object (as a rollback
  does today); no record points to it.
- **Side effects outside the database** (Redis sessions, object-store writes, Celery enqueues) keep
  their current order relative to the commit. What changes is that a commit failure is now reported.

## Consequences

### Positive

- A success status means the change is committed: an immediate read sees it, and a failed commit is
  a 5xx the client can act on (SR-012 AC 5).
- No content is served before the audit row of that access is committed (SR-023 AC 10).
- A download no longer holds a database connection during the transfer, which removes the streaming
  part of PRB-081 (PRB-081 itself stays open: its bound still applies to non-streamed bursts).

### Negative

- **Audit reading of an aborted download changes.** Today a pass-2 mismatch rolls the SUCCESS row
  back and leaves only the FAILURE row. With this decision the SUCCESS row is already committed and
  the FAILURE row follows: the pair means "serving started, then was aborted". This is accurate, as
  all but the last chunk had been sent. It amends ADR-0016's "Unchanged" note (an `AUTHZ_ALLOWED`
  row of a request that then fails is rolled back) for failures **after** the response has started;
  failures before it are unchanged.
- The generator constraint (no session, no ORM instance) is a rule a future streamed route must
  follow; the download test fails on a violation (`DetachedInstanceError`).
- 31 sites change in one commit; overrides in tests (`app.dependency_overrides[get_db]`) keep
  working because the override is keyed on the callable.

### Neutral

- Serialisation of the response model still runs before the commit, inside the same transaction.
- FastAPI's `scope` parameter becomes relied-on behaviour of SOUP-002.

## References

- Requirements: SR-012 AC 5, SR-023 AC 10 (new, `in_review`); SR-008 AC 4 and SR-013 AC 5 (restored, unchanged)
- Problem reports: PRB-080 (resolved by this decision); PRB-081 (relates, out of CR-006 scope)
- Risks: RISK-007, RISK-006, RISK-001; RISK-012 and RISK-002 considered, unchanged
- SOUP: SOUP-002 (FastAPI 0.138), SOUP-003 (Starlette), SOUP-008 (SQLAlchemy)
- Related: ADR-0016, ADR-0021, ADR-0022; ADD-016, ADD-005, ADD-012, ADD-013; TASK-227; CR-006 D-27

## Amendment notes

- 2026-11-14 (TASK-225, Document Writer): the Context, the Decision and the Consequences ("31 sites change in one commit") count "31 `Depends(get_db)` sites in 15 files". Counted again at the parent of commit `03b1400` (`git grep "Depends(get_db" -- backend/app`): 30 sites in 14 files, all of which use `DbSession` after TASK-227. The decision is unchanged. Needs the human's acknowledgement, as for the amendment notes of ADR-0020.
