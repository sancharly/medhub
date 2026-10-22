---
id: SOUP-032
type: soup
title: Emotion styled (@emotion/styled)
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Emotion contributors
soup_version: 11.14.1
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-032 — Emotion styled (@emotion/styled) 11.14.1

## Functional and performance requirements

Styled-component API used by MUI.

## Required hardware and software environment

React 18; @emotion/react (SOUP-031).

## Anomaly list review

**Review date:** 2026-10-22 (TASK-154, CR-001 AC-11). **Version reviewed:** `@emotion/styled`
11.14.1 with `@emotion/is-prop-valid` 1.4.0, as resolved by `frontend/package-lock.json`; the lock's
`integrity` hash matches the tarball the npm registry publishes for that version.

**Anomaly source:** OSV (npm), GitHub Security Advisories for `emotion-js/emotion`, NVD, Emotion
releases.

**Method.** Published information only: advisory databases, the vendor's advisories and release
notes, and npm registry metadata. Nothing from the package's repository was fetched to be built or
run, and `npm audit` was not used. Each advisory found was checked against the exact version (its
affected and fixed ranges) and against how MedHub uses the package, cited by source file below.

**Sources checked**

- OSV, `POST https://api.osv.dev/v1/query` with
  `{"package":{"name":"@emotion/styled","ecosystem":"npm"},"version":"11.14.1"}`
  (https://osv.dev/list?ecosystem=npm&q=%40emotion%2Fstyled). Also the OSV batch query (`POST
  https://api.osv.dev/v1/querybatch`) of all 96 non-dev packages in `frontend/package-lock.json`,
  for the transitive dependencies named below.
- GitHub Security Advisories, https://github.com/emotion-js/emotion/security/advisories
- NVD CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=emotion%20styled
- Emotion releases, https://github.com/emotion-js/emotion/releases (`@emotion/styled@11.14.1`,
  2025-06-26)
- npm registry metadata, https://registry.npmjs.org/@emotion/styled (publish date 2025-06-26, not
  deprecated, integrity)

**Findings**

- OSV: no entry for `@emotion/styled` 11.14.1 or for `@emotion/is-prop-valid` 1.4.0.
- GitHub: no published repository advisory. NVD: no CVE.
- Releases: 11.14.1 is the latest `@emotion/styled`, and no later fix exists.
- MedHub does not import `@emotion/styled` directly. MUI's `styled()` uses it, through
  `@mui/styled-engine`, on MedHub's static theme.

**Judgement.** None found for 11.14.1 (2026-10-22). Not hazard-relevant: no RISK input and no PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 11.14.1 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11, AC-12): none
  found for 11.14.1. Record 1.0 → 1.1, approval record removed for re-approval.
