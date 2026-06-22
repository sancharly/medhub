# TASK-034 — Worker session-kill propagation

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-WORKER / U-WK-SessionRevoke
- **Implements:** SR-034.2 (invalidate active sessions within 30 s of deactivation/deletion);
  SR-030.5 (server-side session invalidation)
- **Depends on:** TASK-033 (lifecycle deactivate), TASK-031 (Celery base)
- **Branch:** `feature/worker-session-revoke`
- **Status:** Completed

## Objective

Provide the asynchronous `propagate_session_kill(account_id)` Celery task that guarantees every
active session of a deactivated or deleted account is invalidated within the SR-034.2 30-second
bound, complementing the synchronous `invalidate_all` performed inline by the lifecycle/erasure
operations. It is the propagation safety net for distributed session-store delay (ADR-0012,
SR-034 control measure) and reuses the worker base from TASK-031.

## Interfaces to honor

Provided task interface (from [12-interfaces.md](../../design/12-interfaces.md), SI-WORKER),
signature verbatim:

```python
def propagate_session_kill(account_id: UUID) -> None: ...
```

Enqueued by `AccountService.deactivate` (TASK-033) and `erase`/delete (TASK-035). Consumes
`SessionService.invalidate_all` (TASK-021) and `AuditService` (TASK-014).

Must **not**: be the *only* revocation path — the caller already invalidates synchronously; this
task ensures completion within 30 s and is idempotent (re-running on an already-empty account set
is a no-op); talk to PostgreSQL for session state (Redis only, via SessionService, §12.3.3).

## Implementation detail

- Files to create:
  - `backend/app/workers/session_tasks.py` — `propagate_session_kill` Celery task.
- The task calls `SessionService.invalidate_all(account_id)` (TASK-021) — enumerate the per-account
  session index and delete every session record (immediate, enumerable revocation, ADR-0012,
  SR-030.5). Idempotent: a second run finds no sessions and exits cleanly.
- Timing: enqueued at deactivation/deletion time; with the inline synchronous `invalidate_all`
  already done by the caller (TASK-033/035), the worker is the propagation guarantee. Configure the
  task with no long delay (immediate dispatch) so the 30 s bound (SR-034.2) holds even under broker
  backlog; bounded retries on transient Redis errors.
- Audit: record `SESSION_KILL_PROPAGATED` (account_id, ts) on completion (§8.4) — security-relevant
  side effect; no session token values logged.
- Config keys: none beyond TASK-003/031 (broker, Redis).
- Error cases: transient Redis failure → retry within the 30 s window; persistent failure logged and
  alertable (operational concern, ADR-0010) — but the synchronous inline kill already revoked, so
  access is not left open.

## Tests (write first — TDD, CLAUDE.md §4)

Run eager (`task_always_eager`) with fakeredis.

- Unit (`backend/tests/workers/test_session_revoke.py`):
  - `propagate_session_kill` invalidates all of an account's sessions; subsequent `resolve` returns
    `None` for each (SR-034.2, SR-030.5).
  - Idempotent: a second invocation on an account with no sessions is a clean no-op.
  - Completion audited as `SESSION_KILL_PROPAGATED` with account_id + ts, no token values (§8.4).
  - Transient Redis error retries; persistent failure surfaces without crashing the worker.
- Integration (`backend/tests/identity/test_deactivate_30s_kill.py`, with TASK-021/033): deactivate
  → both the inline `invalidate_all` and the enqueued task run → all sessions invalid within the
  30 s bound (SR-034.2).

## Acceptance criteria

Distilled from SR-034.2 / SR-030.5:

- [ ] `propagate_session_kill` invalidates every active session of the account (SR-030.5).
- [ ] Combined with the inline synchronous kill, sessions are gone within 30 s of deactivation/deletion
      (SR-034.2).
- [ ] The task is idempotent and resilient to transient Redis errors.
- [ ] Propagation is audited; no session token values are logged (§8.4).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (N/A — no HTTP endpoint)
- [ ] Audit events emitted for security-relevant actions (SESSION_KILL_PROPAGATED — SR-023)
- [ ] Traceability matrix row updated (SR-034.2, SR-030.5 → TASK-034 → tests)
- [ ] Security review completed (auth/session/authz task — SR-031.6)
