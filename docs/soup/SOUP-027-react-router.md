---
id: SOUP-027
type: soup
title: React Router (react-router-dom)
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Remix Software / Shopify
soup_version: 7.18.0
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-027 — React Router (react-router-dom) 7.18.0

## Functional and performance requirements

Client-side routing, authentication redirect and route composition.

## Required hardware and software environment

React 18 (SOUP-025).

## Anomaly list review

**Review date:** 2026-10-22 (TASK-154, CR-001 AC-11). **Version reviewed:** `react-router-dom`
7.18.0 and its runtime dependency `react-router` 7.18.0, as resolved by
`frontend/package-lock.json`; the lock's `integrity` hash matches the tarball the npm registry
publishes for that version.

**Anomaly source:** OSV (npm), GitHub Security Advisories for `remix-run/react-router`, NVD, React
Router v7 changelog.

**Method.** Published information only: advisory databases, the vendor's advisories and release
notes, and npm registry metadata. Nothing from the package's repository was fetched to be built or
run, and `npm audit` was not used. Each advisory found was checked against the exact version (its
affected and fixed ranges) and against how MedHub uses the package, cited by source file below.

**Sources checked**

- OSV, `POST https://api.osv.dev/v1/query` with
  `{"package":{"name":"react-router-dom","ecosystem":"npm"},"version":"7.18.0"}`
  and the same for `react-router` 7.18.0 (https://osv.dev/list?ecosystem=npm&q=react-router).
  Every `react-router` advisory OSV lists, for any version, was read for its affected range. Also
  the OSV batch query (`POST https://api.osv.dev/v1/querybatch`) of all 96 non-dev packages in
  `frontend/package-lock.json`, for the transitive dependencies named below.
- GitHub Security Advisories, https://github.com/remix-run/react-router/security/advisories
  (22 advisories, 2025-04-01 to 2026-07-22)
- NVD CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=react-router
- React Router v7 changelog, https://github.com/remix-run/react-router/blob/v7/CHANGELOG.md
  (7.18.0 to 7.18.4), and the release tags `react-router@7.18.0` to `react-router@7.18.2`
- npm registry metadata, https://registry.npmjs.org/react-router-dom and
  https://registry.npmjs.org/react-router (publish date 2026-06-16, not deprecated, integrity)

**How MedHub uses it.** Declarative mode only: `<BrowserRouter>`, `<Routes>`, `<Route>` and
`<Navigate>` in `frontend/src/app/App.tsx`, and `useNavigate`, `useLocation`, `useParams` and
`<Outlet>` in `frontend/src/auth/` and `frontend/src/core/`. There is no data router
(`createBrowserRouter`/`RouterProvider`), no framework mode, no SSR or prerendering, no React
Server Components, and no `@react-router/*` package in the lock file. Every navigation target is
a constant or `/patients/${patient.id}/clinical-entries`, with the id taken from the API. The
`next` query parameter that `RequireAuth.tsx` sets is read by no component, so no untrusted
value reaches `navigate()`.

**Findings**

- **GHSA-qwww-vcr4-c8h2** (no CVE; CWE-352). An action can run before the 400 response in the
  unstable RSC mode, a follow-up to CVE-2026-22030. Affects `react-router` 7.12.0 up to 7.18.2,
  so it **applies to 7.18.0**; fixed in 7.18.2 ("Harden RSC CSRF codepaths", #15353). The
  repository advisory rates it moderate; the GitHub-reviewed entry rates it high (CVSS 4.0
  VI:H). The advisory says it affects an application only when the unstable RSC APIs are used.
  MedHub use: not affected. No RSC API is used and none is in the bundle; the code path runs
  server-side, in an action-request handler, and MedHub has none. MedHub's CSRF control (SR-031)
  is enforced by the backend.
- Advisories whose fix is 7.18.0 itself, so 7.18.0 is not affected: GHSA-337j-9hxr-rhxg
  (CVE-2026-53666, SSR hydration constructor injection), GHSA-chx6-hx7r-mcp5 (CVE-2026-55685,
  route-matching DoS), GHSA-h8fp-f39c-q6mh (CVE-2026-53667, RSCErrorHandler XSS) and
  GHSA-wrjc-x8rr-h8h6 (CVE-2026-53669, open redirect via a backslash in `<Link>`/`useNavigate`,
  a bypass of CVE-2025-68470).
- The other 16 advisories are fixed before 7.18.0 or affect only server adapters
  (`@react-router/node`, `@react-router/express`) that MedHub does not install. That includes
  the client-side open-redirect and XSS class relevant to RISK-005: GHSA-9jcx-v3wj-wh4m
  (CVE-2025-68470), GHSA-2j2x-hqr9-3h42 (CVE-2026-40181), GHSA-jjmj-jmhj-qwj2 (CVE-2026-53668) and
  GHSA-2w69-qvjg-hvjx (CVE-2026-22029). NVD lists five `react-router` CVEs, all among these.
- Later patches in the 7.18 line: 7.18.1 (CommonJS `main` field of `react-router-dom`; MedHub
  bundles ESM), 7.18.2 (the GHSA-qwww fix), 7.18.3 (2026-08-27: route-matching performance, action
  origin validation, and "additional URL validation on client side navigations/redirects",
  #15446, with no advisory published as of this review) and 7.18.4 (2026-09-15: RSC redirect
  escaping, view transitions). Only #15446 touches MedHub's declarative APIs. It makes
  `navigate()` reject external destinations. MedHub passes only internal constant paths, so
  MedHub is not affected.
- Transitive `cookie` 1.1.1 and `set-cookie-parser` 2.7.2 (used by React Router's server APIs):
  no OSV entry.

**Judgement.** One anomaly applies to the version, GHSA-qwww-vcr4-c8h2. It does not apply to
MedHub's use: declarative client routing, no RSC, no server actions. It is not hazard-relevant
for RISK-005 (session riding through CSRF) or RISK-001. No RISK input and no PRB (2026-10-22).
For monitoring: if an advisory is published for the client-navigation hardening in 7.18.3
(#15446), re-judge it against MedHub's navigation targets.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 7.18.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11, AC-12):
  GHSA-qwww-vcr4-c8h2 applies to 7.18.0 (fixed in 7.18.2) but only to the unstable RSC APIs, which
  MedHub does not use (declarative routing); not hazard-relevant, no escalation. Record 1.0 → 1.1,
  approval record removed for re-approval.
