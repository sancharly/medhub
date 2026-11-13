# ADR-0022: Blocking IO runs off the event loop, and the thread pool is sized against the connection pools

## Status

Accepted (2026-11-13, Carlos Santiago Liceras, CR-006 plan gate). Proposed the same day at the
CR-006 Plan stage by the Software Architect role. The numeric pool sizes are approved separately
with the load-test evidence before the deployed configuration changes (CR-006 D-14).

## Context

The backend stack is synchronous (SQLAlchemy 2 with psycopg2, redis-py, boto3; ADR-0002). FastAPI
runs a plain `def` dependency or handler in AnyIO's worker-thread pool and an `async def` one on the
event loop. Several `async def` dependencies and handlers make blocking calls (PRB-009):
`get_session` and `get_current_user` on every authenticated request (`api/deps.py:43,70`),
`require_module_enabled` (`:138`), `upload_attachment`, and the `logout` and `extend_session`
routes. One slow call therefore stalls every concurrent request. PRB-072 (writes collapse the API
at 20 clients, not at 8) has the same shape.

Moving the work to threads (cause 3 of the CR-006 change analysis) creates a second failure mode:
AnyIO's default limiter allows 40 threads, SQLAlchemy's default `QueuePool` allows 5 + 10
connections with a 30 s `pool_timeout`, and redis-py's pool is unbounded. Forty threads competing
for fifteen connections queue for up to 30 s and then fail with a 500, which is again PRB-072.
SR-026 AC 5 (D-3): 20 concurrent mixed clients on one API worker, no 5xx, AC 1 and AC 2 budgets.

## Options

1. **Plain `def` for every dependency and handler that blocks**, with the thread limiter and the
   database pool configured together from settings.
2. **Async drivers** (asyncpg with async SQLAlchemy, `redis.asyncio`, aioboto3): no threads.
3. **More processes** (Gunicorn workers) and keep the code as is.

## Decision

Option 1.

- Every dependency and handler that calls a blocking client is a plain `def`. A handler that must
  stay `async` (the upload, because it awaits `UploadFile`) calls the blocking service through
  `starlette.concurrency.run_in_threadpool`. A static test fails if an `async def` in `app/api`
  calls a known blocking client or service method (TASK-136).
- Three settings, read at start-up: `API_THREADPOOL_SIZE` (applied in the lifespan to AnyIO's
  default limiter, `total_tokens`), `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` (the engine in
  `db/repositories/session.py`), plus `DB_POOL_TIMEOUT`. The invariant
  `API_THREADPOOL_SIZE ≤ DB_POOL_SIZE + DB_MAX_OVERFLOW` is checked at start-up; a violation refuses
  to start. The Redis client gets `max_connections` equal to the thread-pool size.
- Values: measured by the SR-026 AC 5 load test (TASK-136) and proposed to the human; until then
  the code defaults equal today's effective behaviour except for the invariant. Candidate for the
  measurement: 40 threads, pool 20 + 20, timeout 10 s; PostgreSQL's `max_connections` (100) leaves
  room for the worker and migrations.

Option 2 was rejected: it replaces the persistence and session layers (ADD-016, ADD-006) and the
SOUP set for a single-host deployment sized at 20 clients, against ADR-0002. Option 3 was rejected:
it multiplies memory (each worker holds its own pools and imports) and leaves the stall inside each
worker; SR-026 AC 5 is stated per worker.

## Consequences

### Positive

- A slow call blocks one thread, not the loop; unrelated requests keep their budgets.
- Thread and connection limits are visible settings with a start-up check, so the PRB-072 shape
  cannot be configured silently.

### Negative

- A thread per in-flight request: memory grows with the limiter size (about 8 MiB of stack
  reserved per thread, mostly untouched).
- A pool-size change is a deployed-configuration change and needs the human's approval (D-14).

### Neutral

- The authorization and session decisions do not change; only where they run. TS-001 and TS-002
  run unchanged as the guard (RISK-001, RISK-005).

## References

- Requirements: SR-026 AC 1, AC 2, AC 5; NFR-008
- Problem reports: PRB-009; PRB-072 (relates)
- Risks: RISK-007; RISK-001 and RISK-005 (decision unchanged)
- SOUP: SOUP-002 (FastAPI), SOUP-003 (Starlette and AnyIO), SOUP-008 (SQLAlchemy), SOUP-013 (redis-py), SOUP-004 and SOUP-005 (Uvicorn, Gunicorn)
- Related: ADR-0002, ADR-0010; ADD-005, ADD-016, ADD-026; CR-006 D-3, D-14
