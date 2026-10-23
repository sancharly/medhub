---
id: SOUP-028
type: soup
title: TanStack Query (@tanstack/react-query)
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: Tanner Linsley / TanStack
soup_version: 5.101.0
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: 514664394ef5fa3b589e36872ccd4f5e26b22868f7a902a704dca6d258ff7c42
approval_note: self-approved
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-028 — TanStack Query (@tanstack/react-query) 5.101.0

## Functional and performance requirements

Server-state caching and invalidation; consent and module changes depend on correct invalidation (SR-008, SR-015).

## Required hardware and software environment

React 18 (SOUP-025).

## Anomaly list review

**Review date:** 2026-10-22 (TASK-154, CR-001 AC-11). **Version reviewed:** `@tanstack/react-query`
5.101.0 and its runtime dependency `@tanstack/query-core` 5.101.0, as resolved by
`frontend/package-lock.json`; the lock's `integrity` hash matches the tarball the npm registry
publishes for that version.

**Anomaly source:** OSV (npm), GitHub Security Advisories for `TanStack/query`, NVD, the
`query-core` and `react-query` changelogs.

**Method.** Published information only: advisory databases, the vendor's advisories and release
notes, and npm registry metadata. Nothing from the package's repository was fetched to be built or
run, and `npm audit` was not used. Each advisory found was checked against the exact version (its
affected and fixed ranges) and against how MedHub uses the package, cited by source file below.

**Sources checked**

- OSV, `POST https://api.osv.dev/v1/query` with
  `{"package":{"name":"@tanstack/react-query","ecosystem":"npm"},"version":"5.101.0"}`
  and the same for `@tanstack/query-core` 5.101.0
  (https://osv.dev/list?ecosystem=npm&q=%40tanstack%2Freact-query).
  Also OSV entries GHSA-g7cv-rxg3-hmpx / CVE-2026-45321, and the OSV batch query (`POST
  https://api.osv.dev/v1/querybatch`) of all 96 non-dev packages in `frontend/package-lock.json`,
  for the transitive dependencies named below.
- GitHub Security Advisories, https://github.com/TanStack/query/security/advisories, and the
  advisory GHSA-g7cv-rxg3-hmpx,
  https://github.com/TanStack/router/security/advisories/GHSA-g7cv-rxg3-hmpx
- NVD CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=tanstack
- Changelogs, https://github.com/TanStack/query/blob/main/packages/query-core/CHANGELOG.md and
  https://github.com/TanStack/query/blob/main/packages/react-query/CHANGELOG.md (5.101.1 to
  5.104.5, the latest, 2026-10-19)
- npm registry metadata, https://registry.npmjs.org/@tanstack/react-query and
  https://registry.npmjs.org/@tanstack/query-core (publish date 2026-06-02, not deprecated,
  integrity)

**How MedHub uses it.** One `QueryClient` (`frontend/src/api/queryClient.ts`), `useQuery`/
`useMutation`, prefix invalidation after mutations (`["me", "consents"]`, `["appointments"]`,
`["groups"]`, `["accounts"]`, `["clinicalEntries", patientId]`, `["attachments", entryId]`),
`setQueryData(["me"], …)`, and `queryClient.clear()` on sign-out and session end
(`SignOutButton.tsx`, `SessionActivityProvider.tsx`). It does not use `select`, `useQueries`,
Suspense queries, `resetQueries`, `useMutationState` or `useIsMutating`.

**Findings**

- OSV: no entry for either package at 5.101.0, and none for `@tanstack/react-query` at any
  version.
- GitHub (`TanStack/query`): one advisory, GHSA-997g-27x8-43rf (CVE-2024-24558, XSS). It affects
  `@tanstack/react-query-next-experimental` only, which MedHub does not install.
- NVD `tanstack`: CVE-2024-24558 (above). CVE-2026-45321 / GHSA-g7cv-rxg3-hmpx: malicious versions
  of 42 `@tanstack/*` packages were published on 2026-05-11, all router and start packages.
  `@tanstack/react-query` and `@tanstack/query-core` are not in the affected list. 5.101.0 was
  published on 2026-06-02, the lock's integrity matches the registry, and OSV, which carries
  malicious-package entries, has none for it. Not affected. The other `tanstack` CVEs (TanStack
  DB, devtools-vite, Router, orval) concern packages that MedHub does not install.
- Changelog fixes after 5.101.0, checked against MedHub's use:
  - #11502 (5.103.0): a partial query-key filter with a trailing `undefined` matched shorter
    keys. In 5.101.0 this can only widen an invalidation, never narrow one. MedHub's filters
    carry defined ids. Stale consent or module data cannot result.
  - #11234: a fix for a skipped observer notification. The skip was introduced by #11214, and
    both are in 5.102.0. 5.101.0 has neither, so it is not affected.
  - #11470 (5.104.4): the mutation cache is now cleared before subscribers are notified on
    `queryClient.clear()`. This is visible only through `useMutationState`/`useIsMutating`,
    which MedHub does not use. The query cache that `clear()` empties at sign-out behaves as
    before.
  - #11161 (5.102.0: a stale `select` error leaking into a new result) and #11211 (`resetQueries`)
    concern APIs MedHub does not use. The rest are typing, performance and memory-retention
    fixes.

**Judgement.** None found that applies to 5.101.0 in MedHub's use (2026-10-22). Not
hazard-relevant: the invalidation behaviour that consent and module changes rely on (SR-008,
SR-015; RISK-001 and RISK-002 stale-cache causes) has no published defect at this version. No
RISK input and no PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 5.101.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11, AC-12): none
  found for 5.101.0; not among the malicious `@tanstack/*` versions of CVE-2026-45321. Record 1.0 →
  1.1, approval record removed for re-approval.
