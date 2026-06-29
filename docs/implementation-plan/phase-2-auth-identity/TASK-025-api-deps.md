# TASK-025 — API auth/session dependency (deny-by-default)

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-API / U-API-Deps
- **Implements:** SR-005 (deny-by-default authorization on every request); SR-031.5 (server-side
  access enforcement)
- **Depends on:** TASK-021 (SessionService)
- **Branch:** `feature/api-auth-deps`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Provide the FastAPI dependency-injection providers that turn a request cookie into a resolved
session and current user, and the single guard every protected endpoint declares to invoke the
`AuthorizationService`. This is the choke point that makes deny-by-default structural: an endpoint
without the guard cannot reach protected data, and the guard always runs server-side (SR-005,
SR-031.5, §8.2). The `AuthorizationService` itself is TASK-027; this task wires the request-time
plumbing and the dependency surface it plugs into.

## Interfaces to honor

Provides FastAPI dependencies (SI-API `U-API-Deps`):

```python
async def get_session(request: Request) -> Session: ...        # resolves cookie -> SessionService.resolve; 401 if None
async def get_current_user(session: Session = Depends(get_session)) -> Account: ...
def require(action: str, resource_loader: Callable[..., Resource]) -> Callable: ...  # returns a dependency that calls AuthorizationService.authorize(actor, action, resource)
```

Consumes `SessionService.resolve` (TASK-021) and — once available — `AuthorizationService.authorize`
(TASK-027), which **raises on deny** (12-interfaces.md). The dependency translates that raise into
an HTTP 403. Until TASK-027 merges, `require` integrates against the `AuthorizationService`
interface (Protocol), so this task can land with a test double.

Must **not**: implement any access logic itself (it only resolves identity and delegates to
`AuthorizationService` — SR-005, no per-feature checks, ADR-0006); trust any client-supplied role
or id for the decision (SR-031.5); allow an endpoint to opt out silently — unguarded endpoints are
caught in review per the §12.3 dependency rules.

## Implementation detail

- Files to create:
  - `backend/app/api/deps.py` — `get_session`, `get_current_user`, `require(...)` factory,
    `Resource`/`Actor` adapters.
- `get_session`: read `medhub_session` cookie → `SessionService.resolve`. `None` → raise the
  app's `UnauthenticatedError` (→ 401, TASK-026). On success, also enforce CSRF for state-changing
  methods by composing `require_csrf` (TASK-022).
- `get_current_user`: load the `Account` for `session.account_id` via the account repository
  (TASK-012); a deactivated/deleted account whose session somehow survived resolves to a denied
  state (defense in depth — but TASK-033/034 guarantee sessions are killed ≤30 s).
- `require(action, resource_loader)`: returns a dependency that builds the `Actor` (from the
  current user: id, role) and the `Resource` (via the per-route loader, e.g. load the patient or
  clinical entry), then calls `AuthorizationService.authorize(actor, action, resource)`. The
  service raises `AuthorizationError` on deny → mapped to 403 (TASK-026); the dependency returns
  the loaded resource on allow so the handler reuses it (no double fetch).
- Deny-by-default is **structural**: the default app router config has no implicit auth bypass;
  health/openapi are the only unauthenticated routes and are explicitly listed.
- Error cases: `UnauthenticatedError` → `https://medhub.example/errors/unauthenticated` (401,
  generic); `AuthorizationError` → `https://medhub.example/errors/forbidden` (403, no protected
  data) (api-design.md).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_deps.py`):
  - No/invalid session cookie → `get_session` raises 401 (SR-005, deny-by-default).
  - Valid session → `get_current_user` returns the right `Account`.
  - `require(...)` calls `AuthorizationService.authorize` with the correct actor/action/resource and
    re-raises deny as 403; allow returns the loaded resource (SR-005 AC-1/AC-2/AC-4).
  - A protected route declared without `require(...)` is detectable by a route-introspection test
    that asserts every non-public route depends on the guard (structural deny-by-default).
- Integration (`backend/tests/api/test_protected_route.py`): a sample protected endpoint returns
  401 without a session, 403 when authorization denies, 200 when it allows — all server-side
  (SR-031.5).

## Acceptance criteria

Distilled from SR-005 / SR-031.5:

- [x] Every protected request resolves a session before reaching a handler; missing → 401 (AC-1).
- [x] Access denied by default; only the `AuthorizationService`-approved path proceeds (AC-2).
- [x] The decision is delegated to the central `AuthorizationService`, never re-implemented (ADR-0006).
- [x] Denied requests return 403 and disclose no protected data (AC-4).
- [x] Enforcement is server-side; no client-supplied role/id is trusted (SR-031.5).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit (and required integration) tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (dependency surface; security scheme reflected once routers land)
- [x] Audit events emitted for security-relevant actions (denials audited by AuthorizationService, TASK-027)
- [x] Traceability matrix row updated (SR-005, SR-031.5 → TASK-025 → tests)
- [x] Security review completed (auth/session/authz task — SR-031.6)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
