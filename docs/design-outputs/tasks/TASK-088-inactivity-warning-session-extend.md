---
id: "TASK-088"
type: task
title: "Inactivity warning + session extend"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-030"
    relation: implements
  - target: "TASK-080"
    relation: relates_to
tags: ["audit-verified", "phase:6-frontend-foundation"]
---

- **Phase:** 6 — Frontend foundation
- **Software item / unit:** SI-FE-AUTH / U-FEA-IdleWarning
- **Implements:** SR-030 (AC-4 a visible countdown 2 minutes before an inactivity timeout, with the option to extend the session); ADR-0012
- **Depends on:** TASK-080 (typed `ApiClient` + cookie/CSRF + Query) — must be merged first
- **Branch:** `feature/fe-idle-warning`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Implement the **client-driven 2-minute pre-expiry inactivity warning**: while authenticated, the SPA tracks user activity and, **2 minutes before** the role-dependent inactivity timeout would fire, shows a visible countdown with an "extend session" option that calls `POST /auth/session/extend` to reset the inactivity timer (SR-030 AC-4). The server remains authoritative over session lifetime (timeouts, the 8-hour absolute cap, and revocation all live server-side, ADR-0012); this unit only warns the user and offers the extend action so unattended sessions are not silently lost mid-task. Traces to SR-030.4.

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2):

```ts
// generated from OpenAPI (TASK-080)
await apiClient.extendSession();   // POST /auth/session/extend -> { expiresAt }  (touches the session TTL)
```

- Uses the role-dependent inactivity window (15 min clinical: doctor/patient; 30 min admin: administrative personnel/system administrator — SR-030 AC-1/2) to schedule the warning at `timeout − 2min`; the role comes from the cached `['me']` (TASK-080).
- "Extend" calls `POST /auth/session/extend` (api-design.md "Authentication & session", SR-030.4), which slides the inactivity TTL server-side (ADR-0012) and returns the new `expiresAt`; the client reschedules from that.
- The extend call is state-changing → it carries the CSRF token automatically via the API client (TASK-080 / SR-031.3).
- Must **not**: enforce the timeout or the 8-hour absolute cap client-side as authoritative — the server expires/invalidates sessions; if extend returns `401` (absolute cap reached, SR-030.3), the client routes to login (TASK-085) rather than pretending the session is alive; keep the session alive automatically without the user's action (the warning requires an explicit extend, SR-030.4); track activity by polling the server (it uses local input events).

## Implementation detail

- Files to create:
  - `frontend/src/auth/useIdleTimer.ts` — tracks user activity (debounced `mousemove`/`keydown`/`click`/`touchstart`/`scroll`); computes the next inactivity deadline from the role timeout; fires a `warn` callback at `deadline − 2min` and a `expired` callback at the deadline.
  - `frontend/src/auth/IdleWarningDialog.tsx` — an MUI `Dialog` showing a visible **2-minute countdown** and two actions: "Stay signed in" (calls `extendSession`, reschedules from the returned `expiresAt`) and "Log out now" (calls `apiClient.logout`, routes to login). On reaching zero with no action, routes to login (the server will have/also expire the session) (SR-030 AC-4).
  - `frontend/src/auth/SessionActivityProvider.tsx` — mounts the idle timer + warning dialog for the authenticated route tree; reads the role from `['me']` to pick 15 vs 30 minutes (SR-030 AC-1/2).
  - `frontend/src/auth/roleTimeouts.ts` — the role → inactivity-window map (single source: clinical 15 min, admin 30 min, warning lead 2 min).
  - `frontend/src/auth/index.ts` — export additions; mount `SessionActivityProvider` inside the authenticated tree (after `RequireAuth`, TASK-085).
- Libraries (exact stack): React 18 (timers via `useEffect`/`useRef`), MUI `Dialog`, TanStack Query (extend/logout mutations), TASK-080 client, TypeScript.
- The countdown is a visible mm:ss timer (SR-030 AC-4 "visible countdown"). Any tracked activity event before the warning resets the local deadline; once the warning is showing, only an explicit "Stay signed in" extends (matching the SR's "option to extend").
- If `extendSession` returns `401 /errors/unauthenticated` (8-hour absolute lifetime reached, SR-030.3, or server-side revocation per SR-034), the dialog routes to `/login` — the client never overrides a server expiry (ADR-0012, SR-031.5).
- This unit handles no PHI; it only schedules a warning and calls the extend/logout endpoints.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + React Testing Library + MSW, fake timers), `frontend/src/auth/IdleWarningDialog.test.tsx`:
  - for a clinical role (15-min window), after 13 minutes of inactivity the warning appears with a visible 2-minute countdown; for an admin role it appears after 28 minutes (SR-030 AC-1/2/4).
  - clicking "Stay signed in" calls `POST /auth/session/extend`, the dialog closes, and the timer reschedules from the returned `expiresAt` (SR-030 AC-4).
  - user activity (e.g. a keydown) before the warning resets the deadline so the warning does not appear (SR-030 AC-4 behavior).
  - reaching zero with no action routes to login; `extendSession` returning `401` (absolute cap) also routes to login (SR-030 AC-3, SR-031.5).
  - the extend request carries the CSRF token (delegated to TASK-080) (SR-031.3).
- Unit test, `frontend/src/auth/useIdleTimer.test.ts`: schedules `warn` at `timeout − 2min` and `expired` at `timeout` for each role window (SR-030 AC-1/2/4).
- Each test names the SR AC it verifies.

## Acceptance criteria

- [x] A visible countdown appears 2 minutes before the role-dependent inactivity timeout (15 min clinical / 30 min admin) (SR-030 AC-1/2/4).
- [x] "Stay signed in" calls `POST /auth/session/extend`, resetting the inactivity timer from the server-returned expiry (SR-030 AC-4, ADR-0012).
- [x] User activity before the warning resets the local deadline (SR-030 AC-4).
- [x] The client never overrides a server expiry: reaching zero or an extend `401` (absolute cap / revocation) routes to login (SR-030 AC-3, SR-031.5).
- [x] The extend call is CSRF-protected via the API client (SR-031.3).

## Definition of Done

- [x] Lint + type-check pass (`eslint`/`tsc`)
- [x] Unit/component tests pass; coverage target met
- [x] Traceability matrix row updated (SR-030 → TASK-088 → tests)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
