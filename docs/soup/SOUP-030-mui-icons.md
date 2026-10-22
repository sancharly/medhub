---
id: SOUP-030
type: soup
title: MUI Icons (@mui/icons-material)
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: MUI
soup_version: 9.1.1
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-030 — MUI Icons (@mui/icons-material) 9.1.1

## Functional and performance requirements

Icon set used across navigation and actions.

## Required hardware and software environment

React 18; MUI Material (SOUP-029).

## Anomaly list review

**Review date:** 2026-10-22 (TASK-154, CR-001 AC-11). **Version reviewed:** `@mui/icons-material`
9.1.1, as resolved by `frontend/package-lock.json`; the lock's `integrity` hash matches the tarball
the npm registry publishes for that version.

**Anomaly source:** OSV (npm), GitHub Security Advisories for `mui/material-ui`, NVD, MUI changelog
and release notes.

**Method.** Published information only: advisory databases, the vendor's advisories and release
notes, and npm registry metadata. Nothing from the package's repository was fetched to be built or
run, and `npm audit` was not used. Each advisory found was checked against the exact version (its
affected and fixed ranges) and against how MedHub uses the package, cited by source file below.

**Sources checked**

- OSV, `POST https://api.osv.dev/v1/query` with
  `{"package":{"name":"@mui/icons-material","ecosystem":"npm"},"version":"9.1.1"}`
  (https://osv.dev/list?ecosystem=npm&q=%40mui%2Ficons-material). Also the OSV batch query (`POST
  https://api.osv.dev/v1/querybatch`) of all 96 non-dev packages in `frontend/package-lock.json`,
  for the transitive dependencies named below.
- GitHub Security Advisories, https://github.com/mui/material-ui/security/advisories
- NVD CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=material-ui
- MUI changelog, https://github.com/mui/material-ui/blob/master/CHANGELOG.md, and release notes
  for v9.5.0, https://github.com/mui/material-ui/releases/tag/v9.5.0
- npm registry metadata, https://registry.npmjs.org/@mui/icons-material (publish date 2026-06-11,
  not deprecated, integrity)

**Findings**

- OSV: no entry. GitHub: no published repository advisory. NVD: no CVE.
- Changelog 9.1.2 to 9.5.0: the only `@mui/icons-material` change is cosmetic, centring the
  WarningRounded icon in its `viewBox` (9.5.0).
- MedHub imports 11 icons by path (for example `@mui/icons-material/Menu` in
  `frontend/src/core/nav/AppNavigation.tsx`). They are static SVG components and take no data
  input.

**Judgement.** None found for 9.1.1 (2026-10-22). Not hazard-relevant: no RISK input and no PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 9.1.1 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11, AC-12): none
  found for 9.1.1. Record 1.0 → 1.1, approval record removed for re-approval.
