---
id: SOUP-025
type: soup
title: React
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: Meta Platforms
soup_version: 18.3.1
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: 72e6c94161f779d425e9b3ab3ae0f1b0c1bdd0f34613bf9dd27d12d0a9531989
approval_note: self-approved
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-025 — React 18.3.1

## Functional and performance requirements

Component model and rendering for every frontend item.

## Required hardware and software environment

Modern evergreen browsers (SR-019).

## Anomaly list review

**Review date:** 2026-10-22 (TASK-154, CR-001 AC-11). **Version reviewed:** `react` 18.3.1, as
resolved by `frontend/package-lock.json`; the lock's `integrity` hash matches the tarball the npm
registry publishes for that version.

**Anomaly source:** OSV (npm), GitHub Security Advisories for `facebook/react`, NVD, React
changelog.

**Method.** Published information only: advisory databases, the vendor's advisories and release
notes, and npm registry metadata. Nothing from the package's repository was fetched to be built or
run, and `npm audit` was not used. Each advisory found was checked against the exact version (its
affected and fixed ranges) and against how MedHub uses the package, cited by source file below.

**Sources checked**

- OSV, `POST https://api.osv.dev/v1/query` with
  `{"package":{"name":"react","ecosystem":"npm"},"version":"18.3.1"}`
  (https://osv.dev/list?ecosystem=npm&q=react). OSV aggregates the GitHub Advisory Database and
  the OpenSSF Malicious Packages feed. Also the OSV batch query (`POST
  https://api.osv.dev/v1/querybatch`) of all 96 non-dev packages in `frontend/package-lock.json`,
  for the transitive dependencies named below.
- GitHub Security Advisories, https://github.com/facebook/react/security/advisories
- NVD CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=react-dom
- React changelog, https://github.com/facebook/react/blob/main/CHANGELOG.md
- npm registry metadata, https://registry.npmjs.org/react (publish date 2024-04-26, not deprecated,
  integrity)

**Findings**

- OSV: no entry for 18.3.1. The two historical `react` advisories, GHSA-g53w-52xc-2j85
  (CVE-2013-7035) and GHSA-hg79-j56m-fxgv, affect 0.x releases only. Transitive `scheduler` 0.23.2
  and `loose-envify` 1.4.0: no entry.
- GitHub: ten repository advisories published 2025-12-03 to 2026-10-14, among them
  GHSA-fv66-9v8q-g76r (CVE-2025-55182) and GHSA-xqc2-xf4c-x3h3 (remote code execution in React
  Server Components), plus denial-of-service and source-exposure advisories. All of them affect
  only `react-server-dom-webpack`, `react-server-dom-parcel` and `react-server-dom-turbopack` 19.x.
  None affects `react` 18.3.1. MedHub has no `react-server-dom-*` package in the lock file. The
  frontend is a client-rendered SPA (`createRoot` in `frontend/src/main.tsx`), built by Vite and
  served as static files by nginx.
- NVD: no CVE for React 18.x.
- Changelog: 18.3.1 (2024-04-26) is the last 18.x release. Every fix since then has gone to the
  19.0, 19.1, 19.2 and 19.3 lines.

**Judgement.** None found for 18.3.1 (2026-10-22). Not hazard-relevant: no RISK input and no PRB.
For monitoring: the 18.x line gets no further releases. A later advisory that does affect 18.x
may have no backported fix, which would mean a major upgrade under its own CR.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 18.3.1 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11, AC-12): none
  found for 18.3.1; the React Server Components advisories of 2025-2026 affect `react-server-dom-*`
  19.x only, which MedHub does not use. Record 1.0 → 1.1, approval record removed for re-approval.
