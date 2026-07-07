---
id: "TASK-021"
type: task
title: "SessionService (Redis opaque tokens)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-030"
    relation: implements
  - target: "TASK-012"
    relation: relates_to
  - target: "TASK-003"
    relation: relates_to
tags: ["audit-verified", "phase:2-auth-session-authorization-identity"]
---

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-AUTH / U-AUTH-Session
- **Implements:** SR-030 (session management); ADR-0012 (server-side opaque tokens in Redis)
- **Depends on:** TASK-012 (repositories; Redis client wiring established in TASK-003)
- **Branch:** `feature/session-service`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Implement server-side, **opaque** session tokens backed by Redis (ADR-0012): create on login,
resolve per request with sliding inactivity refresh, enforce role-dependent inactivity timeouts,
an absolute 8-hour lifetime cap, and a 3-concurrent-session-per-user cap that evicts the oldest;
and expose immediate, enumerable invalidation (single session and all-of-account) so logout
(TASK-023), deactivation/deletion (TASK-033/035) and the worker kill-propagation (TASK-034) can
revoke access on demand. Stateless JWTs were rejected precisely because they cannot satisfy
immediate revocation, the cap, or 30-second deactivation (ADR-0012).

## Interfaces to honor

Provided interface (from [12-interfaces.md](../../design/12-interfaces.md), SI-AUTH
`SessionService`), signatures verbatim:

```python
class SessionService:
    def create_session(self, account: Account) -> Session: ...
    def resolve(self, session_id: str) -> Session | None: ...
    def invalidate(self, session_id: str) -> None: ...
    def invalidate_all(self, account_id: UUID) -> None: ...
```

`Session` is an in-process record `{session_id, account_id, role, created_at, last_seen_at, ip,
absolute_expires_at}` (ADR-0012). `resolve` returns `None` for missing/expired/absolute-expired
sessions (it does not raise). Consumers: SI-API (`U-API-Deps`, TASK-025), SI-IDENTITY lifecycle,
SI-WORKER.

Must **not**: store anything decodable in the token (opaque random id only); be the only writer
of the cookie (cookie issuance is TASK-022); talk to PostgreSQL for session state — **only
SI-AUTH/SI-WORKER talk to Redis** (12-interfaces.md §12.3.3).

## Implementation detail

- Files to create:
  - `backend/app/auth/session.py` — `SessionService`, `Session` dataclass, Redis key helpers.
- Library: `redis` (async client from the shared pool wired in TASK-003).
- Token: `session_id = secrets.token_urlsafe(32)` (≥256-bit opaque id, CSPRNG). Stored value is a
  serialized `Session` record; **no** user data is encoded in the id itself (ADR-0012).
- Redis data model:
  - `session:{session_id}` → JSON record, with Redis **TTL = inactivity timeout** for the role
    (native expiry, ADR-0012).
  - `account_sessions:{account_id}` → sorted set of `session_id` scored by `created_at`, for the
    concurrency cap and `invalidate_all` enumeration.
- Timeouts / lifetimes (SR-030, authoritative):
  - Inactivity TTL by role: **15 min** for clinical roles (DOCTOR, PATIENT) (AC-1); **30 min** for
    admin roles (ADMIN/administrative personnel, SYSADMIN) (AC-2).
  - **Absolute lifetime 8 h** stored as `absolute_expires_at` and re-checked on every `resolve`,
    independent of the sliding TTL (AC-3). `resolve` returns `None` and deletes the record once the
    absolute cap passes.
  - Sliding refresh: each successful `resolve` updates `last_seen_at` and **re-arms the inactivity
    TTL**, but the new TTL is **capped** so it never extends past `absolute_expires_at`
    (`ttl = min(inactivity_ttl, absolute_expires_at - now)`) (AC-3/AC-4).
- Concurrency cap (AC-7): on `create_session`, add to the per-account sorted set; if size > **3**,
  pop and `invalidate()` the **oldest** (lowest `created_at`) and return a flag/marker the login
  flow surfaces as the SR-030 AC-7 notification.
- `invalidate(session_id)`: delete `session:{id}` and remove from the account set — immediate,
  non-reusable (AC-5).
- `invalidate_all(account_id)`: read the account sorted set, delete every `session:{id}` and the
  set itself — the enumerable revocation primitive used by logout-all, deactivation (TASK-033/034)
  and erasure (TASK-035), satisfying the SR-034 ≤30 s requirement when invoked synchronously.
- The 2-minute pre-timeout warning (AC-4) is client-driven from the known role timeout returned at
  login; the server side is the `/auth/session/extend` touch, which is a plain `resolve` (it re-arms
  the TTL). No server push needed.
- Config keys (TASK-003): `SESSION_INACTIVITY_CLINICAL_SECONDS=900`,
  `SESSION_INACTIVITY_ADMIN_SECONDS=1800`, `SESSION_ABSOLUTE_LIFETIME_SECONDS=28800`,
  `SESSION_MAX_CONCURRENT=3`.
- Error cases: none surfaced as HTTP here; `resolve` returning `None` becomes
  `https://medhub.example/errors/unauthenticated` (401) at the dependency layer (TASK-025).

## Tests (write first — TDD, CLAUDE.md §4)

Use `fakeredis` (or a dockerized Redis in integration) and a frozen clock.

- Unit (`backend/tests/auth/test_session_service.py`):
  - `create_session` for a clinical role sets a 900 s TTL; admin role sets 1800 s (AC-1/AC-2).
  - `resolve` within the window refreshes `last_seen_at` and re-arms TTL (sliding) (AC-1).
  - Absolute cap: `resolve` at +8 h returns `None` and the record is gone, even with continuous
    activity; sliding TTL never pushes past `absolute_expires_at` (AC-3).
  - Inactivity expiry: no `resolve` for > role TTL → record gone, `resolve` returns `None` (AC-1/AC-2).
  - `invalidate` makes a subsequent `resolve` return `None`; the id is not reusable (AC-5).
  - Concurrency cap: 4th `create_session` evicts the oldest; oldest no longer resolves; exactly 3
    remain; eviction marker returned (AC-7).
  - `invalidate_all` removes every session for the account; none resolve afterward (basis for
    SR-034 30 s kill).
- Integration (`backend/tests/auth/test_session_redis.py`): against a real Redis, verify native
  TTL expiry and the sorted-set cap behavior (crosses the SI-AUTH↔Redis boundary, §12.3.3).

## Acceptance criteria

Distilled from SR-030:

- [x] Clinical-role inactivity timeout 15 min (AC-1); admin-role 30 min (AC-2).
- [x] Absolute lifetime 8 h enforced on every resolve regardless of activity (AC-3).
- [x] Sliding refresh on activity, capped by the absolute lifetime (AC-3/AC-4).
- [x] `invalidate` immediately and permanently revokes a session (AC-5).
- [x] ≤3 concurrent sessions; a 4th evicts the oldest and signals a notification (AC-7).
- [x] Tokens are opaque, server-side, contain no user data (ADR-0012).
- [x] `invalidate_all` enumerates and revokes all of an account's sessions (basis for SR-034 AC-2).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit (and required integration) tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (N/A — no endpoint here)
- [x] Audit events emitted for security-relevant actions (login/logout audit is in TASK-023; N/A here)
- [x] Traceability matrix row updated (SR-030, ADR-0012 → TASK-021 → tests)
- [x] Security review completed (auth/session/authz task — SR-031.6)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
