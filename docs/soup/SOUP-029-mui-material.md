---
id: SOUP-029
type: soup
title: MUI Material (@mui/material)
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

# SOUP-029 — MUI Material (@mui/material) 9.1.1

## Functional and performance requirements

Accessible, responsive components and the CSS-variables theming of ADD-001 (SR-020, SR-027, SR-037..039).

## Required hardware and software environment

React 18; Emotion (SOUP-031, SOUP-032).

## Anomaly list review

**Review date:** 2026-10-22 (TASK-154, CR-001 AC-11). **Version reviewed:** `@mui/material` 9.1.1
with `@mui/system`, `@mui/utils`, `@mui/styled-engine`, `@mui/private-theming` and `@mui/types`
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
  `{"package":{"name":"@mui/material","ecosystem":"npm"},"version":"9.1.1"}`
  and the same for `@mui/system` and `@mui/utils` 9.1.1
  (https://osv.dev/list?ecosystem=npm&q=%40mui%2Fmaterial).
  Also the OSV batch query (`POST https://api.osv.dev/v1/querybatch`) of all 96 non-dev packages in
  `frontend/package-lock.json`, for the transitive dependencies named below.
- GitHub Security Advisories, https://github.com/mui/material-ui/security/advisories
- NVD CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=material-ui
- MUI changelog, https://github.com/mui/material-ui/blob/master/CHANGELOG.md (9.1.1 to 9.4.0), and
  release notes for v9.5.0, https://github.com/mui/material-ui/releases/tag/v9.5.0 (2026-10-09,
  the latest), with the pull requests behind the two entries discussed below
- npm registry metadata, https://registry.npmjs.org/@mui/material (publish date 2026-06-11, not
  deprecated, integrity)

**Findings**

- OSV: no entry for `@mui/material`, `@mui/system` or `@mui/utils` 9.1.1, and none for
  `@mui/material` at any version. Transitive `react-transition-group` 4.4.5, `@popperjs/core`
  2.11.8 and `clsx` 2.1.1: no entry.
- GitHub: no published repository advisory. NVD: no CVE.
- Changelog, 9.1.2 to 9.5.0. Two entries were examined against MedHub's use:
  - `@mui/system` 9.3.0, "Prevent prototype pollution in cssVarsParser" (#48822, no advisory).
    A theme object holding `__proto__`/`constructor` keys could write onto `Object.prototype`.
    The pull request notes this is reachable only when the theme comes from untrusted input.
    MedHub's theme is a static object in `frontend/src/core/theme/theme.ts` (`cssVariables`,
    `colorSchemes`). Its only runtime input is the fixed light/dark mode passed to
    `useColorScheme().setMode` in `ModeToggle.tsx`. Not affected. The sibling fix in
    `fastDeepAssign` (#48580) shipped in 9.1.0, so 9.1.1 already contains it.
  - `@mui/material` 9.3.1, "Prevent exit transitions from getting stuck" (#48881). A Modal can
    stay in `exiting`, with the backdrop and scroll lock left in place, when React reconnects
    effects or when the Modal's portal `container` changes during exit. MedHub uses `Dialog`
    (`IdleWarningDialog`, `ConfirmDialog`, `DeleteConfirmDialog`), `Snackbar` and `Drawer`, and
    sets no `container`. React 18 reconnects effects only under `StrictMode` in development
    builds. The production build meets neither trigger: not affected in production, and at most
    a development-only usability glitch.
  - The other entries are accessibility, typing, styling and localisation fixes. None is a
    security fix, and none changes a behaviour that a MedHub risk control relies on.

**Judgement.** None found that applies to MedHub's use of 9.1.1 (2026-10-22). Not
hazard-relevant: no RISK input and no PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 9.1.1 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11, AC-12): none
  found that applies to MedHub's use; the cssVarsParser hardening (9.3.0) and the stuck
  exit-transition fix (9.3.1) do not apply to MedHub's static theme or production build. Record 1.0
  → 1.1, approval record removed for re-approval.
