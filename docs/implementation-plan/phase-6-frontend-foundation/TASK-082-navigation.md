# TASK-082 — Role-based navigation

- **Phase:** 6 — Frontend foundation
- **Software item / unit:** SI-FE-SHELL / U-FE-Nav
- **Implements:** SR-027 (AC-1 consistent navigation structure and terminology across screens and modules)
- **Depends on:** TASK-081 (AppLayout + MUI theme + breakpoints) — must be merged first
- **Branch:** `feature/fe-navigation`
- **Status:** Not started

## Objective

Build the **role-based navigation** that fills the layout's navigation slot (TASK-081): a single, consistent navigation structure and terminology shared across every screen and (later) every module, whose visible entries depend on the current user's role (patient, doctor, administrative personnel, system administrator). Consistent navigation/terminology is a core usability control (SR-027 AC-1). The nav only **hides** entries the user's role would not use — it is never the access-control gate (server-side authz is authoritative, SR-031.5); module entries are gated separately against `GET /me/modules` in TASK-101. Traces to SR-027.

## Interfaces to honor

Provides the navigation half of `ShellServices` from [12-interfaces.md](../../design/12-interfaces.md) §12.2 (provider SI-FE-SHELL; consumers SI-FE-CORE, modules) and the `NavItem` shape used by the module registry:

```ts
interface NavItem {            // reused verbatim by FrontendModule (TASK-100)
  label: string;
  path: string;
  icon?: React.ReactNode;
}
// the nav renders the core items permitted for the current user's role
function AppNavigation(props: { userType: UserType }): React.ReactNode;
```

- Renders into the navigation slot exposed by `AppLayout` (TASK-081); collapses/expands at the phone/tablet/desktop breakpoints from `breakpoints.ts` (SR-020 inherited).
- Role drives **visibility only**; navigating to a route the server forbids still yields a server `403 /errors/forbidden` rendered by the error surface (TASK-084). The nav is **not** an authorization mechanism (SR-031.5, ADR-0003 negative consequence).
- Uses the same `NavItem` shape that `FrontendModule.navItem` uses (api-design.md / §12.2), so module nav entries (TASK-101) compose consistently with core entries (SR-027 AC-1 consistency).
- Must **not**: call the API for authorization decisions; decide module enablement here (that is `GET /me/modules`, TASK-101); diverge in terminology between roles or screens (SR-027 AC-1).

## Implementation detail

- Files to create:
  - `frontend/src/core/nav/navConfig.ts` — the canonical core navigation entries (Profile, Patients, Clinical entries, Appointments, Consent, Admin · accounts, Admin · groups & modules) with consistent labels/terminology, each tagged with the roles permitted to see it.
  - `frontend/src/core/nav/AppNavigation.tsx` — renders the role-filtered entries into the layout nav slot using MUI navigation components (`List`/`ListItemButton`/`Drawer`), responsive (persistent on desktop, drawer on phone, per TASK-081 breakpoints).
  - `frontend/src/core/nav/useNavItems.ts` — selects the visible entries for the current `userType` (and a hook point where TASK-101 appends enabled module entries).
  - `frontend/src/core/nav/types.ts` — `NavItem`, `UserType` (matching the OpenAPI DTO from TASK-080).
  - `frontend/src/core/nav/index.ts` — exports `AppNavigation`, `NavItem`.
- Libraries (exact stack): React 18, React Router (`NavLink` for active state), MUI navigation primitives, TypeScript.
- Current user/role comes from the cached `GET /me` (`['me']` query, TASK-080); the nav reads it from cache and does not fetch authorization state itself.
- Consistency: one `navConfig` is the single source so labels/terminology are identical across screens and form factors (SR-027 AC-1); module entries appended by TASK-101 reuse the same `NavItem` rendering for visual consistency.
- This unit owns no feature routes; it links to routes defined by Phase 7 views.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + React Testing Library), `frontend/src/core/nav/AppNavigation.test.tsx`:
  - a **patient** sees patient-appropriate entries (Profile, Appointments, Consent) and **not** admin entries; a **system administrator** sees the admin entries — visibility filtered by role (SR-027 AC-1 consistency, role-scoped presentation).
  - labels/terminology come from the single `navConfig` and are identical across roles where an entry is shown (SR-027 AC-1).
  - at a phone-width viewport the nav renders as a drawer; at desktop, persistent (responsive, inherited SR-020).
  - clicking an entry routes via React Router and marks the active item.
- Unit test, `frontend/src/core/nav/useNavItems.test.ts`: returns exactly the entries permitted for each `userType`; exposes the append point for module entries (consumed by TASK-101).
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] Navigation structure and terminology are consistent across screens (single `navConfig`) and ready for modules to compose consistently (SR-027 AC-1).
- [ ] Visible entries are filtered by the current user's role; the nav hides, but never authorizes (SR-031.5).
- [ ] The nav renders responsively into the layout slot (drawer on phone, persistent on desktop) (SR-020 inherited).
- [ ] Module nav entries can be appended later via the same `NavItem` shape without changing the nav (SR-016.2 / TASK-101 hook).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-027 → TASK-082 → tests)
