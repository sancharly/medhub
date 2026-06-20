# TASK-085 — Login UI + session handling

- **Phase:** 6 — Frontend foundation
- **Software item / unit:** SI-FE-AUTH / U-FEA-LoginForm
- **Implements:** SR-002 (AC-1 authenticate with email/password and obtain a session; AC-2 generic failure with no field disclosure; AC-3 unauthenticated requests routed to the login flow); ADR-0003, ADR-0012
- **Depends on:** TASK-080 (typed `ApiClient` + cookie/CSRF + Query), TASK-082 (role-based navigation, post-login destination) — must be merged first
- **Branch:** `feature/fe-login-ui`
- **Status:** Not started

## Objective

Build the **login screen and the SPA-side session boundary**: an email/password form that calls `POST /auth/login` via the typed client, and an auth boundary that redirects unauthenticated users to the login flow and routes authenticated users into the app (SR-002 AC-1/AC-3). On failure the UI shows the backend's **single generic** message (no indication of whether the email exists or the password was wrong, SR-002 AC-2). Session credentials are handled entirely by the hardened cookie set by the backend (ADR-0012) — the SPA stores no token. Traces to SR-002.

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2) and the shell error surface (TASK-084):

```ts
// generated from OpenAPI (TASK-080)
await apiClient.login({ email, password });   // POST /auth/login -> LoginResponse { user, mustChangePassword, evictedSession }
const me = await apiClient.getMe();           // GET  /me  (establishes the cached session identity)
```

- Submits to `POST /auth/login` (api-design.md "Authentication & session"); on success the backend sets the `Secure; HttpOnly; SameSite=Strict` session cookie and the CSRF cookie (ADR-0012, TASK-022) — the form reads/stores neither.
- On `mustChangePassword === true`, routes to the change-password flow (TASK-087) before any other screen (SR-025.6) rather than into the app.
- Surfaces the `evictedSession` notice (oldest session evicted on a 4th login, SR-030.7) to the user.
- Must **not**: display which field was wrong or whether the account exists / is locked — all failures render the single generic `401 /errors/unauthenticated` message (SR-002 AC-2, SR-029.6); store the session token in JS-accessible storage (ADR-0012); treat the client as the access gate — protected routes are still enforced server-side (SR-031.5).

## Implementation detail

- Files to create:
  - `frontend/src/auth/LoginPage.tsx` — the route component: MUI `TextField` (email, password) + submit; uses a TanStack Query mutation calling `apiClient.login`. On success, invalidates/sets the `['me']` query and navigates to the role landing route (via TASK-082); on `mustChangePassword`, navigates to `/password` (TASK-087).
  - `frontend/src/auth/RequireAuth.tsx` — the auth boundary: wraps protected routes; if `GET /me` resolves the user is authenticated; on the typed `401 /errors/unauthenticated` (from TASK-080) it redirects to `/login`, preserving the intended destination (SR-002 AC-3).
  - `frontend/src/auth/useLogin.ts` — the login mutation hook (encapsulates success routing + generic-error mapping via TASK-084).
  - `frontend/src/auth/index.ts` — exports `LoginPage`, `RequireAuth`.
  - Register `/login` (public) and wrap the protected route tree with `RequireAuth` in the shell router.
- Libraries (exact stack): React 18, React Router (redirect/`Navigate`), TanStack Query (mutation), MUI form components, TypeScript.
- Generic failure: any `401` from `login` renders the single mapped message via the shell error surface (TASK-084) — the form never branches its message on the failure cause (SR-002 AC-2).
- Client-side field presence checks (non-empty email/password) are convenience only; the server is authoritative (SR-031.5). The email field uses `type="email"` for input hints, not as a security control.
- `RequireAuth` is the SPA realization of SR-002 AC-3 ("unauthenticated requests are routed to the login flow"); it never grants access — it only redirects, the backend still authorizes every call (SR-031.5).

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + React Testing Library + MSW), `frontend/src/auth/LoginPage.test.tsx`:
  - submitting valid credentials → MSW `200` sets the session; the app navigates to the role landing route (SR-002 AC-1).
  - MSW returns `401 /errors/unauthenticated` for a wrong password **and** for an unknown email → the form shows the **identical** generic message both times; no field is flagged (SR-002 AC-2).
  - a locked account also surfaces the same generic `401` (indistinguishable, SR-029.6).
  - `mustChangePassword: true` routes to `/password` (TASK-087) and not into the app (SR-025.6).
  - `evictedSession: true` shows the eviction notice (SR-030.7).
  - the form never writes a token to `localStorage`/`sessionStorage`/`document.cookie` (ADR-0012).
- Boundary test, `frontend/src/auth/RequireAuth.test.tsx`: an unauthenticated visit to a protected route (`GET /me` → `401`) redirects to `/login` preserving the destination (SR-002 AC-3).
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] A user authenticates with email + password and is granted a session via the backend cookie (SR-002 AC-1, ADR-0012).
- [ ] Unknown email, wrong password, and locked account render the **same** generic failure; no field/enumeration disclosure (SR-002 AC-2, SR-029.6).
- [ ] Unauthenticated access to a protected route redirects to the login flow, preserving the destination (SR-002 AC-3).
- [ ] `mustChangePassword` routes to the change-password flow before app access (SR-025.6); `evictedSession` is surfaced (SR-030.7).
- [ ] No session token is stored in JS-accessible storage; the SPA is never the sole access gate (ADR-0012, SR-031.5).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-002 → TASK-085 → tests)
