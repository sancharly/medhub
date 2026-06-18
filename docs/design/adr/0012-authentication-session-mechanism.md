# ADR-0012: Server-side opaque session tokens in hardened cookies

## Status

Accepted

## Context

SR-030 imposes precise, **server-controlled** session behavior: role-dependent inactivity timeouts (15 min clinical / 30 min admin), an 8-hour absolute lifetime, a 2-minute pre-timeout warning with extend, **immediate invalidation on logout**, a **3-concurrent-session cap** that invalidates the oldest, and cookies with `Secure`/`HttpOnly`/`SameSite=Strict`. SR-034 requires that deactivating/deleting an account **invalidate active sessions within 30 seconds**. SR-029 requires lockout. All of these require the server to be able to **enumerate and revoke** sessions on demand.

## Decision

Use **server-side, opaque session tokens** backed by a **session store in Redis** (ADR-0002), delivered to the browser in a hardened cookie. Do **not** use self-contained stateless JWTs as the session credential.

- On login (after Argon2id verification, SR-002), the server creates a session record `{session_id, user_id, role, created_at, last_seen_at, ip}` in Redis with a TTL = inactivity timeout, plus a tracked absolute expiry.
- The cookie carries only the opaque `session_id`, with `Secure`, `HttpOnly`, `SameSite=Strict` (SR-030 AC-6).
- Each request refreshes `last_seen_at`/TTL (sliding inactivity) but is hard-capped by the 8-hour absolute lifetime (SR-030 AC-1–3).
- Logout, account deactivation/deletion (SR-034), and password change delete the relevant server-side session record(s) → **immediate, enumerable revocation** (SR-030 AC-5, SR-034 AC-2).
- A per-user index of active sessions enforces the 3-session cap, evicting the oldest on a 4th login (SR-030 AC-7).
- The 2-minute inactivity warning is driven by the client from the known timeout, with an "extend" call that touches the session (SR-030 AC-4).

## Consequences

### Positive

- Server-side records make sessions **enumerable and instantly revocable**, which is exactly what SR-030 (logout, cap) and SR-034 (30-second invalidation) require — stateless JWTs cannot be revoked before expiry without a denylist that re-introduces server state anyway.
- Opaque tokens leak nothing about the user and are immune to client-side tampering.
- Redis TTLs implement inactivity expiry natively and cheaply; the concurrent-session index is a simple Redis structure.
- Cookie hardening (`Secure`/`HttpOnly`/`SameSite=Strict`) defends against XSS token theft and CSRF (SR-030 AC-6, SR-031 AC-3).

### Negative

- Requires Redis as a session store (already in the stack for Celery, ADR-0002) — one more stateful component to secure/back up.
- A session lookup per request adds latency; negligible with Redis and well within SR-026 budgets.

### Neutral

- Redis persistence/HA is an operational concern (ADR-0010); session loss forces re-login, which is acceptable.

## Alternatives Considered

**Stateless JWT access tokens.** Rejected as the session credential: cannot satisfy immediate logout (SR-030 AC-5), the concurrent-session cap (SR-030 AC-7), or 30-second deactivation revocation (SR-034 AC-2) without a server-side denylist — which negates JWT's only advantage while adding complexity.

**External IdP session management (Keycloak/Auth0).** Deferred per ADR-0011: viable later, but adds an external dependency and integration/regulatory surface; the precise SR-030/029 behaviors are simple and auditable to implement in-process at MVP scale.

**Database-backed sessions (PostgreSQL).** Workable but Redis gives native TTL/expiry and lower-latency per-request lookups; PostgreSQL stays focused on durable domain data (ADR-0004).

## References

- Requirements: SR-002, SR-029, SR-030, SR-031, SR-034; NFR-007
- Related: ADR-0002, ADR-0006, ADR-0010, ADR-0011
