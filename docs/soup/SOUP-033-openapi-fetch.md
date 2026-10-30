---
id: SOUP-033
type: soup
title: openapi-fetch
status: obsolete
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-29"
manufacturer: Drew Powers
soup_version: 0.17.0
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-033 — openapi-fetch 0.17.0

> No longer part of MedHub: removed from `frontend/package.json` and `frontend/package-lock.json` (PRB-044, CR-003). It is no longer a dependency, so it is not SOUP; it was never imported.

## Functional and performance requirements

None. MedHub relies on no function of this item. It was declared in `frontend/package.json`
`dependencies` (`^0.17.0`, locked at 0.17.0) until CR-003 (TASK-165) removed it; no frontend
source or test file imported it, so it was never part of the production bundle. MedHub's typed HTTP client, including RFC 7807
error handling, is the hand-written `ApiClient` over the browser `fetch`
(`frontend/src/api/client.ts`). Its types come from `src/api/generated/types.ts`, which the
dev tool `openapi-typescript` generates.

## Required hardware and software environment

Browser `fetch`; the generated `openapi.ts` types.

## Anomaly list review

**Review date:** 2026-10-22 (TASK-154, CR-001 AC-11). **Version reviewed:** `openapi-fetch` 0.17.0
with `openapi-typescript-helpers` 0.1.0, as resolved by `frontend/package-lock.json`; the lock's
`integrity` hash matches the tarball the npm registry publishes for that version.

**Anomaly source:** OSV (npm), GitHub Security Advisories for `openapi-ts/openapi-typescript`, NVD,
the `openapi-fetch` changelog and issue tracker.

**Method.** Published information only: advisory databases, the vendor's advisories and release
notes, and npm registry metadata. Nothing from the package's repository was fetched to be built or
run, and `npm audit` was not used. Each advisory found was checked against the exact version (its
affected and fixed ranges) and against how MedHub uses the package, cited by source file below.

**Sources checked**

- OSV, `POST https://api.osv.dev/v1/query` with
  `{"package":{"name":"openapi-fetch","ecosystem":"npm"},"version":"0.17.0"}`
  and the same for `openapi-typescript-helpers` 0.1.0
  (https://osv.dev/list?ecosystem=npm&q=openapi-fetch).
  Also the OSV batch query (`POST https://api.osv.dev/v1/querybatch`) of all 96 non-dev packages in
  `frontend/package-lock.json`, for the transitive dependencies named below.
- GitHub Security Advisories, https://github.com/openapi-ts/openapi-typescript/security/advisories
- NVD CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=openapi-fetch
- Changelog,
  https://github.com/openapi-ts/openapi-typescript/blob/main/packages/openapi-fetch/CHANGELOG.md,
  and the open issues labelled `openapi-fetch` + `bug`,
https://github.com/openapi-ts/openapi-typescript/issues?q=is%3Aissue+is%3Aopen+label%3Aopenapi-fetch+label%3Abug
  (30 open)
- npm registry metadata, https://registry.npmjs.org/openapi-fetch (publish date 2026-02-11, not
  deprecated, integrity; 0.17.0 is the latest)

**Findings**

- OSV: no entry for either package, at this or any version. GitHub: no published repository
  advisory. NVD: no CVE.
- Open bug reports against 0.17.0 include #2717 (a request body type `{ x?: null }` rejected at
  compile time, a regression from 0.16.0), #2530 (an empty error body gives an `undefined`
  `error`) and #2557 (middleware `onError`).
- MedHub use: none. `openapi-fetch` is declared in `frontend/package.json` `dependencies` but no
  file in `frontend/src` or `frontend/tests` imports it or `openapi-typescript-helpers`, so Vite
  leaves it out of the production bundle. MedHub's HTTP client is the hand-written `ApiClient`
  over the browser `fetch` (`frontend/src/api/client.ts`). It takes request and response types
  from `src/api/generated/types.ts`, which the dev tool `openapi-typescript` generates. None of
  the open bugs can therefore affect MedHub.

**Judgement.** None found for 0.17.0 (2026-10-22). Not hazard-relevant: no RISK input. The
review found that MedHub does not use this item, so the functional requirement in this record
was corrected (see Change log). Removing the unused dependency is outside CR-001 (A-4). It is
raised as [PRB-044](../problem-reports/PRB-044-openapi-fetch-declared-but-unused.md) (minor,
2026-10-22), together with the correction of ADD-004's SI-FE-APICLIENT row.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 0.17.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11, AC-12): none
  found for 0.17.0. Record 1.0 → 1.1, approval record removed for re-approval. Fact correction:
  "Functional and performance requirements" described a typed HTTP client this item does not provide
  to MedHub. The package is declared but not imported, so the section now says MedHub relies on no
  function of it (ADD-004's row for this item has the same error and is corrected at its next
  revision). Removal and the ADD-004 correction are tracked in PRB-044 (minor).
- 2026-10-29 — removed from `frontend/package.json` and `package-lock.json`; never imported (PRB-044, CR-003). Together with its only dependency `openapi-typescript-helpers` 0.1.0. Record 1.1 → 1.2, `obsolete`, approval record removed. Impact analysis (§7.4): the package was not in the production bundle, and the `dist/` output is byte-identical before and after (TASK-165). No risk control depended on it.
