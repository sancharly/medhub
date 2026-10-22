---
id: SOUP-031
type: soup
title: Emotion (@emotion/react)
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Emotion contributors
soup_version: 11.14.0
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-031 — Emotion (@emotion/react) 11.14.0

## Functional and performance requirements

CSS-in-JS engine behind MUI theming.

## Required hardware and software environment

React 18.

## Anomaly list review

**Review date:** 2026-10-22 (TASK-154, CR-001 AC-11). **Version reviewed:** `@emotion/react` 11.14.0
with `@emotion/cache` 11.14.0, `@emotion/serialize` 1.3.3, `@emotion/sheet` 1.4.0, `@emotion/utils`
1.4.2 and `stylis` 4.2.0, as resolved by `frontend/package-lock.json`; the lock's `integrity` hash
matches the tarball the npm registry publishes for that version.

**Anomaly source:** OSV (npm), GitHub Security Advisories for `emotion-js/emotion`, NVD, Emotion
releases.

**Method.** Published information only: advisory databases, the vendor's advisories and release
notes, and npm registry metadata. Nothing from the package's repository was fetched to be built or
run, and `npm audit` was not used. Each advisory found was checked against the exact version (its
affected and fixed ranges) and against how MedHub uses the package, cited by source file below.

**Sources checked**

- OSV, `POST https://api.osv.dev/v1/query` with
  `{"package":{"name":"@emotion/react","ecosystem":"npm"},"version":"11.14.0"}`
  and the same for `@emotion/cache` 11.14.0 and `@emotion/serialize` 1.3.3
  (https://osv.dev/list?ecosystem=npm&q=%40emotion%2Freact). Also the OSV batch query (`POST
  https://api.osv.dev/v1/querybatch`) of all 96 non-dev packages in `frontend/package-lock.json`,
  for the transitive dependencies named below.
- GitHub Security Advisories, https://github.com/emotion-js/emotion/security/advisories
- NVD CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=emotion%20styled
- Emotion releases, https://github.com/emotion-js/emotion/releases
- npm registry metadata, https://registry.npmjs.org/@emotion/react (publish date 2024-12-09, not
  deprecated, integrity)

**Findings**

- OSV: no entry for `@emotion/react` at any version, nor for 11.14.0. Transitive Emotion packages
  (`cache`, `serialize`, `sheet`, `utils`, `hash`, `memoize`, `weak-memoize`,
  `use-insertion-effect-with-fallbacks`, `babel-plugin` 11.13.5) and `stylis` 4.2.0: no entry.
- GitHub: no published repository advisory. NVD: no CVE.
- Releases: 11.14.0 (2024-12-09) is still the latest `@emotion/react`. The later releases
  (`@emotion/styled` 11.14.1, `@emotion/is-prop-valid` 1.4.0, `@emotion/jest`) do not change this
  package.
- MedHub does not import Emotion directly (no `@emotion` import in `frontend/src`). It reaches
  Emotion only through MUI's `@mui/styled-engine`, with styles from MedHub's static theme and
  `sx` props, not from user input.

**Judgement.** None found for 11.14.0 (2026-10-22). Not hazard-relevant: no RISK input and no PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 11.14.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11, AC-12): none
  found for 11.14.0. Record 1.0 → 1.1, approval record removed for re-approval.
