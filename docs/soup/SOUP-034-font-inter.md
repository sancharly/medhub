---
id: SOUP-034
type: soup
title: Fontsource Inter (@fontsource-variable/inter)
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: Fontsource
soup_version: 5.2.8
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: 8a55a951f95e43212c3e005d018d524bd0169c351c443ac1a757b3cfc54bb57a
approval_note: self-approved
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-034 — Fontsource Inter (@fontsource-variable/inter) 5.2.8

## Functional and performance requirements

Self-hosted body typeface, so no third-party font CDN receives user traffic.

## Required hardware and software environment

Browser with variable-font support.

## Anomaly list review

**Review date:** 2026-10-22 (TASK-154, CR-001 AC-11). **Version reviewed:**
`@fontsource-variable/inter` 5.2.8, as resolved by `frontend/package-lock.json`; the lock's
`integrity` hash matches the tarball the npm registry publishes for that version.

**Anomaly source:** OSV (npm), GitHub Security Advisories for `fontsource/fontsource`,
`fontsource/font-files` and `rsms/inter`, NVD, npm registry metadata.

**Method.** Published information only: advisory databases, the vendor's advisories and release
notes, and npm registry metadata. Nothing from the package's repository was fetched to be built or
run, and `npm audit` was not used. Each advisory found was checked against the exact version (its
affected and fixed ranges) and against how MedHub uses the package, cited by source file below.

**Sources checked**

- OSV, `POST https://api.osv.dev/v1/query` with
  `{"package":{"name":"@fontsource-variable/inter","ecosystem":"npm"},"version":"5.2.8"}`
  (https://osv.dev/list?ecosystem=npm&q=%40fontsource-variable%2Finter). Also the OSV batch query
  (`POST https://api.osv.dev/v1/querybatch`) of all 96 non-dev packages in
  `frontend/package-lock.json`, for the transitive dependencies named below.
- GitHub Security Advisories for the packaging project,
  https://github.com/fontsource/fontsource/security/advisories
  and https://github.com/fontsource/font-files/security/advisories (the package's source repository)
- Upstream typeface: GitHub Security Advisories for `rsms/inter`,
  https://github.com/rsms/inter/security/advisories (none), and its releases,
  https://github.com/rsms/inter/releases (latest v4.1, 2024-11-16)
- NVD CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=fontsource
- npm registry metadata, https://registry.npmjs.org/@fontsource-variable/inter (publish date
  2025-09-17, not deprecated, integrity, licence OFL-1.1, no dependencies, no install scripts).
  The next version, 5.3.0 (2026-07-19), is a whole-catalogue rebuild ("update packages") with no
  Inter-specific change.

**Findings**

- No anomaly list is published for this package: OSV has no entry and the GitHub repositories
  have no advisory. NVD has no CVE for Fontsource or for Inter.
- The package holds only static font files (`woff2`) and CSS `@font-face` rules, imported in
  `frontend/src/main.tsx` and emitted by Vite as hashed assets served by nginx from the same
  origin. It runs no code. A malformed font would be parsed by the browser's font engine, which
  is covered by the browser environment (SR-019), not by this item.

**Judgement.** None found for 5.2.8 (2026-10-22). Not hazard-relevant: no RISK input and no PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 5.2.8 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11, AC-12): none
  found for 5.2.8; no anomaly list is published for the package. Record 1.0 → 1.1, approval record
  removed for re-approval.
