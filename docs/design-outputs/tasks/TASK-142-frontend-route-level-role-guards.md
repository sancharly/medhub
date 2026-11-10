---
id: "TASK-142"
type: task
title: "Frontend route-level role guards"
status: approved
version: "1.7"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-07"
links:
  - target: "RISK-001"
    relation: mitigates
  - target: "SR-005"
    relation: implements
  - target: "SR-009"
    relation: implements
  - target: "PRB-014"
    relation: relates_to
  - target: "PRB-067"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-018"
    relation: relates_to
  - target: "TASK-082"
    relation: relates_to
  - target: "TASK-101"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium", "control:protective", "cr:CR-004"]
---

# TASK-142 — Frontend route-level role guards

- **Software item / unit:** SI-FE-SHELL `U-FE-RouteGuard` (new, ADD-018); `frontend/src/app/App.tsx`,
  `frontend/src/core/nav/`.
- **Resolves (through CR-004):** PRB-014. Source: `docs/reports/CODE-REVIEW-2026-07.md` finding L.
- **Depends on:** none. Independent of every backend task; can run in parallel.
- **Branch:** `fix/review-2026-07-security` (CR-004).
- **Size:** M (`App.tsx`, `navConfig.ts`/`types.ts`, new `RequireRole.tsx`, 2 test files; TS-002)
- **Scope decision:** CR-004 Q-4 (2026-10-31): no new AC on SR-005. This is defence in depth
  under SR-005 and SR-009; the server-side tests stay the evidence of the control.

## Objective

A role never mounts a view it cannot use. Today `App.tsx:36-57` mounts every route behind
`RequireAuth` only, and role filtering exists only in navigation (`navConfig.ts`).

## Implementation detail

- One role table: extend `navConfig.ts` (or a sibling `routeRoles.ts` that `navConfig` derives
  from) so every role-scoped path, including `/patients/:patientId/clinical-entries` (not in the
  nav today), has its role list. Use the uppercase `UserType` constants (`CLAUDE.md`).
- `RequireRole` (sibling of `RequireAuth`): reads `me.userType`; if it is not in the route's
  role list, renders `<Navigate to="/profile" replace />` and does not mount the child. While
  `me` is loading, render nothing (no query of the child fires).
- Wrap every role-scoped route in `App.tsx` with it.

## Tests (write first)

- `frontend/src/app/RequireRole.test.tsx` (Vitest + Testing Library): allowed role renders the
  child; denied role redirects and the child's query hook is never called; `me` undefined or
  loading renders nothing; unknown role string is denied.
- `frontend/src/core/nav/routeRoles.test.ts`: every role-scoped `<Route>` in `App.tsx` is wrapped
  and its path is in the role table; a nav entry whose route is unguarded fails.
- Existing `useNavItems.test.ts` and `AppNavigation.test.tsx` pass.

## Acceptance criteria

- [x] SR-005, SR-009 (defence in depth): PATIENT or DOCTOR at `/admin/accounts` is redirected to
      `/profile` without mounting the page or firing admin queries (`frontend/src/app/RequireRole.test.tsx`).
- [x] ADMIN and SYSADMIN flows unchanged (existing frontend suite).
- [x] Guard and navigation share one table; an unguarded role-scoped route fails a test
      (`frontend/src/core/nav/routeRoles.test.ts`).

## Verification

```sh
cd frontend && npx tsc --noEmit && npm run lint && npm test
```

Negative control: remove the wrapper from `/admin/accounts`; both new test files fail.

## Records

- **TS-002** → 1.2 (`in_review`; TASK-187 bumps it first if it lands first, then this task adds
  under that version): TC-002.9 (client route guard, defence in depth), `verifies` SR-005, SR-009.
- **ADD-018** 1.1: confirm the `U-FE-RouteGuard` unit text.
- **PRB-014**: `## Resolution`, `resolved`.

## Implementation notes (Software Developer, 2026-11-02)

- `frontend/src/core/nav/routeRoles.ts` (new): the one role table, keyed by path, all four
  `UserType` values spelled uppercase; covers `/password`, `/profile`, `/patients`,
  `/patients/:patientId/clinical-entries` (DOCTOR, PATIENT), `/appointments` (all four roles, round 2), `/consent`,
  `/admin/accounts`, `/admin/groups`. `navConfig.ts` now derives each entry's roles from it.
- `frontend/src/app/RequireRole.tsx` (new): reads `["me"]` (same query as `RequireAuth`; `useMe`
  of TASK-144 is not in the tree). No `me` (loading or failed) renders nothing; unlisted role
  renders `<Navigate to="/profile" replace />`. `RequireAuth` still sends unauthenticated users to login.
- `App.tsx`: a `guarded(path, element)` helper wraps every route; `/*` and public routes unchanged.
- Tests: `RequireRole.test.tsx`, `App.test.tsx` (full `<App/>` with MSW `/me`, pages stubbed to record mounts),
  `routeRoles.test.ts` (static check on the `App.tsx` source; exempt set is `/login`, `/activation/:token`, `*`, `/*`).
- Negative controls run: guard removed from `/admin/accounts` fails `App.test.tsx` (5 tests) and
  `routeRoles.test.ts` (1); `RequireRole.test.tsx` tests the component alone and stays green, so
  "both new test files fail" holds for the two integration-level files. An unguarded `/new-thing`
  route fails `routeRoles.test.ts`.
- ADD-018 `U-FE-RouteGuard` text still holds; it names `navConfig.ts` as the table, which is now
  `routeRoles.ts` (navConfig derives from it). Not edited (human-approved); for the reviewer.

## QA review — round 1 (2026-11-06): CHANGES REQUESTED

The guard works as built. A denied role is redirected and the page never mounts. Nothing mounts
while `me` loads or after it fails. Lint, typecheck and build are clean, and the generated types are
unchanged. QA mutations were caught: making `RequireRole` always allow fails 19 tests, rendering
the child while `me` loads fails 6, and wrapping `/admin/accounts` so the page still renders
fails 4. The verdict is CHANGES REQUESTED for four reasons. The table blocks admin appointment
scheduling, which the requirements allow (finding 1). The verification command fails (finding 2).
A route can escape the static check (finding 3). Nothing independent pins the role matrix
(finding 4).

1. **HIGH — `/appointments` denies ADMIN and SYSADMIN, which removes a required function.**
   `frontend/src/core/nav/routeRoles.ts:14` lists `["PATIENT", "DOCTOR"]`. SR-010 AC 4 lets
   administrative personnel create appointments, and SR-011 AC 3 lets them view appointments. The
   server allows both: `appointment:create` and `appointment:list` are allowed for ADMIN and
   SYSADMIN in `backend/app/authz/service.py`, `_eval_admin` and `_eval_sysadmin`.
   `backend/tests/authz/test_decision_table.py:90-91` gives them `list_all`, and lines 138-143 make
   every appointment visible to them. `AppointmentsPage.tsx:45` shows `CreateAppointmentForm` to
   every non-patient, so this page was the admins' only UI path. Before this task it worked as a
   deep link (it had no nav entry). The guard now redirects it to `/profile`, which breaks this
   task's AC 2 ("ADMIN and SYSADMIN flows unchanged"). `App.test.tsx` derives its expectation
   from the table, so it encodes the regression. → Fix: set `"/appointments"` to all four roles.
   Because `navConfig` derives from the table, admins also get an Appointments nav entry; that
   closes the nav gap for SR-010 AC 4 and SR-011 AC 3. If the nav must stay unchanged, the
   orchestrator or the human must decide that first, and SR-010/SR-011 then need another UI
   path. Add an ADMIN/SYSADMIN-at-`/appointments` case to the suite that protects AC 2.
2. **HIGH — the frontend suite fails.** `frontend/src/app/App.test.tsx:133` ("mounts nothing when
   me fails with 403") hit the 5 s timeout in all 5 full `npm test -- --run` runs QA made (208/209).
   It passes when run alone, and it passes with `--testTimeout=30000`, where it took 16.7 s.
   The cause predates this task. When `/me` returns an error that is not an auth error, the
   client re-requests `/me` in a tight loop. A QA probe counted 176 requests in 0.9 s, and 709 in
   3.3 s with the HEAD `App.tsx` (no guard). With no cached data, each refetch resets the query
   to `pending`, so `RequireAuth` (`frontend/src/auth/RequireAuth.tsx:25`) returns `null` and
   unmounts the subtree. When the error arrives the subtree remounts, and the new observers
   refetch on mount. In production this floods the API during a backend 5xx outage. → Fix: raise
   a PRB for the `/me` refetch loop (it is outside this task), and fix it under CR-004 or schedule
   it. One way is to keep `RequireAuth` from unmounting on a refetch, e.g. gate on
   `status === "pending" && !error` or set `retryOnMount: false` on the `["me"]` observers. Then
   assert in this test that `/me` is requested a bounded number of times. Until then the
   verification command is not green, and this task cannot be approved.
3. **MEDIUM — routes can escape the static test.** `frontend/src/core/nav/routeRoles.test.ts:16`
   uses `/<Route\s+path="([^"]+)"/` on `App.tsx` only. QA probes on a scratch copy added an
   unguarded `<Route element={<ConsentPage />} path="/secret" />` (element first), then
   `<Route path={"/secret"} element={<AccountsPage />} />` (expression path). Both left
   `routeRoles.test.ts` and `App.test.tsx` at 48/48 passed, so AC 3 ("an unguarded role-scoped
   route fails a test") does not hold in general. Routes in another file, `useRoutes` and
   `createBrowserRouter` object configs are not scanned either. None exists today: only `App.tsx`
   declares routes, all of them in flat `<Routes>`. → Fix: parse with the TypeScript compiler API
   (`typescript` is already a devDependency). Visit every JSX element named `Route` in
   `src/**/*.tsx`, whatever the attribute order. Fail on a non-literal `path`. Require
   `element={guarded("<same path>", …)}` unless the path is exempt. Fail if `useRoutes`,
   `createBrowserRouter` or `createRoutesFromElements` appears anywhere. Then reword the claim in
   TS-002 TC-002.9 and the PRB-014 Resolution to match.
4. **MEDIUM — no test pins the role matrix itself.** `App.test.tsx:69-82` computes "allowed" from
   `routeRoles`, so it is tautological against the table. QA mutation: adding ADMIN and SYSADMIN
   to `/patients/:patientId/clinical-entries` left the whole suite green (208/208). Nav entries
   are only pinned indirectly, by the pre-existing nav tests. → Fix: hard-code the expected matrix
   in `App.test.tsx` (route × role → allowed) from SR-005, SR-009, SR-010/011, SR-032/034 and the
   decision table. Assert `routeRoles` equals it, and drive the 32 cases from that matrix.
5. **LOW — PATIENT nav fallback.** `frontend/src/app/App.tsx:38` falls back to `"PATIENT"`.
   `AuthenticatedApp` only renders after `RequireAuth` stops loading, so during normal loading
   nothing shows. When `/me` fails with an error that is not an auth error, the shell renders the
   Profile, Appointments and Consent links for any account. The nav fires no API calls, and a
   click lands on a guard that renders nothing, so this is a UX issue, not a disclosure. This
   predates the task. → Fix: render `AppNavigation` only when `me` is defined, e.g.
   `navigation={me ? <AppNavigation userType={me.userType} /> : null}`, and drop the fallback.
6. **LOW — ADD-018 names `navConfig.ts` as the role table.** The table is now `routeRoles.ts`.
   → Fix: have the architect update ADD-018's `U-FE-RouteGuard` text, which needs human
   re-approval, or record in CR-004 that `navConfig.ts` derives from `routeRoles.ts`.

UI vs API, by page:

| Route | UI roles | API the page uses → roles the server allows | Result |
|---|---|---|---|
| `/password` | all | `POST /auth/password`: any authenticated user | match |
| `/profile` | all | `GET /me`: any authenticated user | match |
| `/patients` | DOCTOR | `GET /patients`: `patient_roster:list`, DOCTOR only | match |
| `/patients/:id/clinical-entries` | DOCTOR, PATIENT | `clinical:read`: PATIENT own only (`ClinicalDataService.list_entries` passes the path `patient_id`), DOCTOR with consent; ADMIN/SYSADMIN denied; write DOCTOR only (form hidden for PATIENT) | match |
| `/appointments` | PATIENT, DOCTOR | `appointment:list`/`create`: all four roles (SR-010 AC 4, SR-011 AC 3); confirm/decline: PATIENT own | **UI denies roles the requirements allow (finding 1)** |
| `/consent` | PATIENT | `consent:grant`/`revoke`/`list`: PATIENT only | match |
| `/admin/accounts` | ADMIN, SYSADMIN | `account:list` ADMIN+SYSADMIN (ADMIN projection); create ADMIN (not a SYSADMIN target) + SYSADMIN; resend ADMIN+SYSADMIN; deactivate/reactivate/delete SYSADMIN only (page gates them on `isSysadmin`) | match |
| `/admin/groups` | SYSADMIN | `groups:*`, `modules:enable`, `module:list`: SYSADMIN only | match |

No server gap found: no page's API allows a role that the requirements say must be denied.

Traceability (QA parser, 416 records; scope TASK-142, TS-002, PRB-014, SR-005, SR-009, CR-004,
RISK-001): 0 errors, 0 warnings.

## Round 2 (Software Developer, 2026-11-06)

Human decisions 2026-11-06: PRB-067 (the `/me` refetch loop) is folded into CR-004 (D-12) and fixed
here; admins get the Appointments page and its nav entry.

1. **Finding 1.** `routeRoles.ts`: `/appointments` is `PATIENT, DOCTOR, ADMIN, SYSADMIN`. Admin and
   sysadmin cases come from the hard-coded matrix in `App.test.tsx`; `navConfig` derives the admin nav entry.
2. **Finding 2, PRB-067.** Fix in `frontend/src/api/queryClient.ts`:
   `queryClient.setQueryDefaults(["me"], { retryOnMount: false })`. Chosen over only changing
   `RequireAuth` because the loop comes from every observer of the key refetching an errored,
   data-less query on mount; one default covers all current and future observers, while keeping the
   tree mounted would still let each observer issue its own request. `RequireAuth` keeps
   `retry: false`, so a failing `/me` is requested once. Test: `App.test.tsx` "requests /me a bounded
   number of times when it fails with 500" (waits for the error, then 1 s, asserts at most 3 requests).
   The 403 test now finishes well inside the default timeout.
3. **Finding 3.** `routeRoles.test.ts` scans every `<Route>` in `frontend/src/**/*.tsx` (production
   files) with the TypeScript compiler API: literal `path`, entry in the table, `element={guarded("<same path>", ...)}`
   in any attribute order; exempt paths (`/login`, `/activation/:token`, `*`, `/*`) may only carry their
   listed root element. It fails on `useRoutes`, `createBrowserRouter`, `createMemoryRouter`,
   `createHashRouter` and `createRoutesFromElements`. Fixtures cover QA's element-first and expression-path probes.
4. **Finding 4.** `App.test.tsx` hard-codes the expected route x role matrix (from SR-005, SR-009,
   SR-010/011, the server decision table and QA's UI-vs-API table), asserts `routeRoles` equals it and drives the 32 cases from it.
5. **Finding 5.** `App.tsx`: `navigation={me ? <AppNavigation userType={me.userType} /> : null}`; the PATIENT fallback is gone.
6. **Finding 6.** ADD-018 not edited. Wording for the architect (TASK-201): "The role table is
   `routeRoles.ts`; `navConfig.ts` derives its role lists from it."
- Negative controls (all caught): ADMIN added to clinical entries (2 failures); admin dropped from
  appointments (3); element-first unguarded route (1); expression-path route (1); `retryOnMount`
  default removed (1, the bounded-request test); `RequireRole` always allowing (17).

## QA review — round 2 (2026-11-06): CHANGES REQUESTED

All six round-1 findings are fixed.
- `npm test -- --run` passed 303/303 in three runs; lint, typecheck and build are clean.
- The generated types are unchanged by this task. The `openapi.ts`/`openapi.json` diff in the tree
  is TASK-205's session-cap 503.
- QA re-ran its three missed round-1 mutations on a scratch copy. The element-first route fails 1
  test, the expression path fails 1 and ADMIN/SYSADMIN on clinical entries fails 3. A template-literal
  path also fails 1, and so does a `<Route>` in another file. Removing the `["me"]` default fails 2.
- The PRB-067 loop is gone: a failing `/me` is requested once.

The verdict is CHANGES REQUESTED because of finding R2-1: the loop fix leaves a failed `/me` as a
blank screen that never recovers.

R2-1. **HIGH — a failed `/me` leaves the user on a blank screen with no message and no automatic
   recovery (SR-027 AC 3).**
   - `RequireAuth.tsx:14` sets `retry: false`, so one transient 5xx is final. `RequireAuth.tsx:28`
     then renders the tree. `RequireRole.tsx:23` returns `null`, and the nav is `null` (finding 5).
   - QA probe (`/me` answers 500, then 200 from 0.5 s on): only the `MedHub` app bar shows.
     - After 3 s with the backend healthy: still 1 request and no page.
     - A window `focus` event does nothing (`refetchOnWindowFocus: false` in `queryClient.ts`).
     - Only a browser `online` event (`refetchOnReconnect`) or a full reload recovers the session.
       The backend coming back fires neither.
   - With `retryOnMount: false`, navigating inside the app does not retry either.
   - Before this task, the pages mounted and showed their own error alerts. The storm also
     re-checked `/me` constantly, so the session recovered by itself.
   - In this medical records app, a short backend blip (a deploy, a 502 from the proxy) leaves
     clinicians on an empty page with nothing to act on. SR-027 AC 3 requires "a clear, actionable
     message". The PRB-067 Resolution ("retried by an explicit reload or sign-in") assumes the user
     knows to reload, and nothing tells them.
   - → Fix, keeping `retryOnMount: false`, which is the right loop fix:
     - (a) In `RequireAuth`, when `error` is set and is not an `AuthError`, render an error state
       instead of `<Outlet />`: an `Alert` with role `alert` ("Could not load your account. Check
       your connection and try again.") and a "Try again" button that calls `refetch()`.
     - (b) Remove `retry: false` from `RequireAuth`. The client-wide policy already skips retries
       for 4xx, so a 401 still redirects at once, and a 5xx gets up to 3 retries with backoff.
       That is a bounded number of requests inside one fetch, not the loop.
     - (c) Test: `/me` answers 500 then 200. Assert the alert shows, click "Try again", and assert
       the page mounts. Keep the request-bound test, with the bound adjusted to the retry count.
     - (d) Update the PRB-067 Resolution and TS-002 TC-002.9 to match.
R2-2. **LOW — the `["me"]` default also applies to `["me", "consents"]`.** `queryClient.ts:26`:
   `setQueryDefaults` matches by key prefix. QA check: `getQueryDefaults(["me","consents"])`
   returns `{retryOnMount:false}`. A failed consent list (`ConsentPage.tsx:12`) is therefore not
   reloaded when the page is opened again within `gcTime` (5 min). → Fix: either give the consent
   list a key that does not start with `"me"`, or move `retryOnMount: false` into a shared
   `meQuery` options object used by the `["me"]` observers. Otherwise record the wider scope in
   the PRB-067 Resolution.
R2-3. **LOW — an aliased or namespaced `Route` escapes the static test.**
   `routeRoles.test.ts:55` compares the tag text with `"Route"`. A QA probe file with
   `import { Route as R }` and `<R path="/alias" …/>`, or `import * as RR` and
   `<RR.Route path="/ns" …/>`, raised no violation. Only a deliberate rename can hit this. → Fix:
   in the same scan, fail on any import from `react-router-dom` that renames `Route` or
   namespace-imports the module, or resolve tag names through the file's import bindings.
R2-4. **LOW — formatting-only edits outside the task.** The diffs of
   `frontend/src/core/nav/AppNavigation.tsx`, `AppNavigation.test.tsx`, `useNavItems.test.ts` and
   the two re-wrapped statements in `api/queryClient.ts` change only line wrapping (a formatter
   run). This breaks "Surgical Changes" (CLAUDE.md). → Fix: revert those formatting-only hunks.
   Keep only the `setQueryDefaults` addition in `queryClient.ts`.
R2-5. **LOW — open record items.**
   - The human decision that admins get the Appointments page and nav entry (2026-11-06) is
     recorded only in this task. CR-004 D-12 covers PRB-067 alone. → Fix: add it to CR-004 as
     part of D-12 or as its own decision.
   - The CR-004 change-analysis row "CSRF exact match; session cap; route guard" does not mention
     the PRB-067 availability fix. → Fix: add it to that row.
   - The finding-6 ADD-018 wording sits only in this task; TASK-201 does not mention it. → Fix:
     add the ADD-018 note to TASK-201 so the architect picks it up.

Observation: the "at most 3 requests in 1 s" bound clearly separates the loop (about 200
requests/s) from the fixed behaviour, which makes exactly 1 request. A tighter `toBe(1)`, or the
retry count once R2-1 (b) lands, would also catch a slow re-request.

The CR-004 1.11 D-12 edit is limited to the D-12 pieces: the `resolves` link, the Scope row, the
D-12 line and its version-history line. The 1.10 edits are TASK-205's.

PRB-067 meets the problem-report contract (mandatory fields, `criticality: major`, `links: []`,
Observed/Impact/Investigation/Safety evaluation/Resolution, version history). Its Resolution needs
the R2-1 update.

Traceability (417 records; scope TASK-142, TS-002, PRB-014, PRB-067, SR-005, SR-009, CR-004,
RISK-001): 0 errors, 0 warnings. CR-004 `resolves` both PRB-014 and PRB-067, so check E9 will hold
when they move to `resolved`.

## Round 3 (Software Developer, 2026-11-07)

- **R2-1.** `RequireAuth.tsx`: `retry: false` removed (client-wide policy: no retry on 4xx, so a 401
  still redirects at once; a 5xx is retried 3 times with backoff). A non-auth `error` renders an
  `Alert` (role `alert`) with a "Try again" button calling `refetch()`. `retryOnMount: false` kept.
  Tests in `App.test.tsx` (retry backoff set to 0 there so they stay fast): `/me` 500 is requested
  exactly 4 times and the alert shows; 500 then 200 recovers through "Try again" and the page mounts;
  a 401 is requested once and goes to login. PRB-067 Resolution and TS-002 TC-002.9 updated.
- **R2-2.** `queryClient.ts`: explicit `setQueryDefaults(["me","consents"], { retryOnMount: true })`
  (the prefix match would otherwise apply the `["me"]` default). New `api/queryClient.test.tsx`.
- **R2-3.** `routeRoles.test.ts` fails on a `react-router-dom` import that renames `Route` or imports
  the namespace; fixtures for QA's two probes.
- **R2-4.** Formatting-only hunks reverted in `AppNavigation.tsx`, `AppNavigation.test.tsx`,
  `useNavItems.test.ts` and the two re-wrapped statements in `queryClient.ts`.
- **R2-5.** CR-004 1.12 adds D-13 (admins get Appointments and its nav entry) and the PRB-067 fix in
  the route-guard change-analysis row; TASK-201 1.2 carries the ADD-018 wording.
- Negative controls (all caught): alert removed (2 failures); `retry: false` back (1, the bound
  test); consents override removed (1); renamed-import check removed (2).

## QA review — round 3 (2026-11-07): CHANGES REQUESTED

All five round-2 findings are closed.
- R2-1: QA re-ran the probe on a scratch copy with retry delay 0. `/me` answered 500, so 4
  requests went out, and the alert with "Try again" showed. The backend then recovered. A focus
  event and in-app navigation still did not refetch, but the alert is on screen, which meets
  SR-027 AC 3. "Try again" recovered, and the page mounted.
- R2-2: the override order holds. `getQueryDefaults` merges every matching default with
  `Object.assign`, in the order the defaults were first registered (a Map). So the later
  `["me","consents"]` default wins over the `["me"]` prefix. QA also checked that calling
  `setQueryDefaults(["me"])` again does not move it: `["me","consents"]` still gets
  `retryOnMount: true`. `queryClient.test.tsx` pins this.
- R2-3: QA's renamed and namespace probes now fail the static test, with 2 failures.
- R2-4: the formatting hunks are gone.
- R2-5: CR-004 1.12 has D-13 and the change-analysis row; TASK-201 has the ADD-018 wording.

`npm test -- --run` passed 311/311 in 3 runs. Lint and typecheck exit 0, and the build succeeds.
Generated types are unchanged by this task (the `openapi.ts` diff is TASK-205's).

The verdict is CHANGES REQUESTED because this round's alert brings a new regression:

R3-1. **HIGH — a failed background refetch of `/me` replaces the whole working app with the
   alert, even though the account is already loaded.**
   - `frontend/src/auth/RequireAuth.tsx:31` tests `if (error)`. TanStack Query v5 keeps `data` and
     sets `error` when a refetch of a loaded query fails. So the check also fires for a signed-in
     user whose account is still loaded.
   - `/me` is refetched in the background on every navigation. Each new `["me"]` observer
     (`RequireRole`, `ProfilePage`, `AppointmentsPage`, `AccountsPage`) mounts on stale data
     (`staleTime` 0). It is also refetched on `online`.
   - If such a refetch fails after its retries (a deploy, a proxy 502, a network flap; about 7 s
     with backoff), the `<Outlet />` is unmounted. Whatever page the user is on disappears, along
     with any unsaved form input such as a clinical entry being written.
   - QA probe: `/profile` loaded, `/me` switched to 500, `refetchQueries(["me"])`. The page was
     replaced by "Could not load your account…".
   - At HEAD, and in round 2, a failed refetch with data kept the app mounted. So this is a
     regression added in round 3, and no test covers it.
   - The trigger is narrow, a failure lasting through the retries while the user is working, but
     the cost is lost clinical input and an interrupted session that was valid.
   - → Fix: show the alert only when no account is loaded. Take `data` from `useQuery` and use
     `if (error && !data)`. Add a test: `/me` succeeds and the page mounts; `/me` switches to 500;
     a refetch of `["me"]` runs; the page is still shown.
   - QA checked this fix on the scratch copy: the probe passes and the rest of the suite stays
     green (310/310 there).

Observation (not a finding): with the client-wide retries, the screen stays blank for up to about
7 s (backoff 1 s, 2 s, 4 s) before the alert. That is acceptable.

Traceability (417 records; scope TASK-142, TS-002, PRB-014, PRB-067, SR-005, SR-009, CR-004,
RISK-001): 0 errors, 0 warnings.

## Round 4 (Software Developer, 2026-11-07)

R3-1 fixed per human decision 2026-11-07, QA's verified fix: `RequireAuth.tsx` renders the alert only
when `error && !data`, so a failed background refetch of a loaded `/me` keeps the app mounted. Test:
`App.test.tsx` "keeps the page mounted when a refetch of a loaded /me fails with 500"; putting back
`if (error)` makes it fail.

## QA check — R3-1 (2026-11-07, CR-004 D-15): APPROVED

The diff is exactly the specified fix: `RequireAuth.tsx` destructures `data` and the condition is now
`if (error && !data)`. The new test "keeps the page mounted when a refetch of a loaded /me fails with 500"
covers it. QA re-ran probe B on a scratch copy: `/profile` loaded, `/me` switched to 500 and
`["me"]` was refetched. The query ended in `error`, the page stayed mounted and no alert showed.
`npm test -- --run` passed 312/312 and `npm run typecheck` exited 0.

Traceability (TASK-142, TS-002, PRB-014, PRB-067, CR-004): 0 errors, 0 warnings.

Status: TASK-142 and TS-002 are `approved`; PRB-014 and PRB-067 are `resolved` (CR-004 D-8).

## Definition of Done

- [x] `tsc`, lint and the frontend suite pass.
- [x] TS-002 `in_review` with TC-002.9; PRB-014 `resolved`.
- [x] `traceability-check` shows no error for TASK-142, TS-002, SR-005, SR-009, PRB-014.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-001 (risk register bootstrap, TASK-147).
  Traceability only: the requirement content is unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.3 (2026-10-31) — CR-004 Plan stage (Software Architect role): Q-4 recorded; clinical-entries
  route added to scope (absent from the nav table). Links `implements` SR-009, `relates_to` PRB-014,
  CR-004, ADD-018 added. Tests named by path, TS-002 TC-002.9 planned. Still `draft`.
- 1.4 (2026-11-02) — Implemented (Software Developer role). Added implementation notes; TS-002 1.4 carries TC-002.9. `in_review`.
- 1.4 (2026-11-06) — QA review round 1: CHANGES REQUESTED (findings 1-6). `in_review → draft`.
- 1.5 (2026-11-06) — Round 2 after QA round 1 (findings 1-6) and human decisions on PRB-067 (D-12) and admin appointments. `relates_to` PRB-067 added. `draft → in_review`.
- 1.5 (2026-11-06) — QA review round 2: CHANGES REQUESTED (R2-1 HIGH, R2-2..R2-5 LOW). `in_review → draft`.
- 1.6 (2026-11-07) — Round 3 after QA round 2 (R2-1 to R2-5). `draft → in_review`.
- 1.6 (2026-11-07) — QA review round 3: CHANGES REQUESTED (R3-1 HIGH). `in_review → draft`.
- 1.7 (2026-11-07) — R3-1 fixed (QA round 3, human decision 2026-11-07). `draft → in_review`.
- 1.7 (2026-11-07) — QA R3-1 check (CR-004 D-15): fix verified; approved (`in_review → approved`).
