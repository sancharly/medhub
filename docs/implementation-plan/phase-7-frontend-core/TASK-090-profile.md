# TASK-090 — Profile view

- **Phase:** 7 — Frontend core views
- **Software item / unit:** SI-FE-CORE / U-FEC-Profile
- **Implements:** SR-003 (AC-2/3 own-profile self-service, data-minimization), SR-007 (AC-1 patient views own personal data); ADR-0003
- **Depends on:** TASK-080 (typed `ApiClient` from OpenAPI), TASK-081 (app shell + routing + `ShellServices`), TASK-082 (navigation) — must be merged first
- **Branch:** `feature/fe-profile`
- **Status:** Not started

## Objective

Build the authenticated user's **own profile** view: a single route that renders the personal information of the currently logged-in user (any role) from `GET /me`. It is every user type's first authenticated screen and realizes the GDPR self-access aspect of SR-003/SR-007. The view shows only the user's own data — it never queries another user's profile — so confidentiality (SR-003 AC-3) is preserved structurally by always calling `GET /me`, never `GET /accounts/{id}` for self.

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2) and `ShellServices`:

```ts
// generated from OpenAPI (TASK-080): GET /me -> CurrentUser DTO (camelCase)
const me = await apiClient.getMe();            // { id, email, firstName, surname, userType, ... }
// ShellServices (TASK-081): error toast + layout slot
shell.errorToast(message); shell.layoutSlot(...)
```

- Reads **only** `GET /me` (api-design.md "Authentication & session"). It must **not** call `GET /accounts/{id}` to display the current user, and must **not** render any clinical field (profile is non-clinical personal data only).
- Auth is cookie + CSRF, handled centrally by `ApiClient` (SR-031.3); this view sets no headers itself.
- Server-side authorization is authoritative; the view only renders what `GET /me` returns and never assumes a field is safe to show that the API withheld (SR-031.5).

## Implementation detail

- Files to create:
  - `frontend/src/core/profile/ProfilePage.tsx` — route component; `useQuery` (TanStack Query) keyed `['me']` calling `apiClient.getMe()`.
  - `frontend/src/core/profile/ProfileFields.tsx` — presentational MUI layout (name, surname, email, user type, DOB where present); responsive (SR-020 via shell layout).
  - `frontend/src/core/profile/index.ts` — route export.
  - Register the route in the shell router (TASK-081) under `/profile`.
- Libraries (exact stack): React 18, TanStack Query (`useQuery`), MUI components, React Router route.
- Data fetching: single `GET /me`; loading → MUI skeleton, error → `ShellServices` error toast with the RFC 7807 `detail` (SR-027.3). `401` is handled by the shell's auth boundary (redirect to login), not here.
- No mutations in this task (password change is SI-FE-AUTH / TASK out of scope here).
- Error cases surfaced: network/5xx → actionable error surface; `401` → shell redirects.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + React Testing Library + MSW), `frontend/src/core/profile/ProfilePage.test.tsx`:
  - MSW mocks `GET /me` → renders the user's name, surname, email, user type (SR-003 AC-2, SR-007 AC-1).
  - asserts the component issues a request to `/me` and **never** to `/accounts/{id}` (SR-003 AC-3 — own data only).
  - asserts **no clinical fields** are rendered (profile is non-clinical).
  - MSW returns `500 application/problem+json` → error surface shows the `detail`, no crash (SR-027.3).
- Each test names the SR AC it verifies in its title.

## Acceptance criteria

- [ ] An authenticated user of any type sees a profile page with their own personal information from `GET /me` (SR-003 AC-2, SR-007 AC-1).
- [ ] The view requests only `/me`; it does not fetch another user's profile (SR-003 AC-3).
- [ ] No clinical data is shown on the profile view (data-minimization, SR-009 boundary respected).
- [ ] Errors render a clear, actionable message via `ShellServices` (SR-027.3).
- [ ] Layout is responsive with no horizontal scroll of primary content (SR-020, inherited from shell).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-003, SR-007 → TASK-090 → tests)
