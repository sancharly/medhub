---
id: SOUP-026
type: soup
title: React DOM
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Meta Platforms
soup_version: 18.3.1
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-026 — React DOM 18.3.1

## Functional and performance requirements

DOM rendering with escaping by default (XSS mitigation, SR-031).

## Required hardware and software environment

Modern evergreen browsers; React (SOUP-025).

## Anomaly list review

**Review date:** 2026-10-22 (TASK-154, CR-001 AC-11). **Version reviewed:** `react-dom` 18.3.1, as
resolved by `frontend/package-lock.json`; the lock's `integrity` hash matches the tarball the npm
registry publishes for that version.

**Anomaly source:** OSV (npm), GitHub Security Advisories for `facebook/react`, NVD, React changelog
and release posts.

**Method.** Published information only: advisory databases, the vendor's advisories and release
notes, and npm registry metadata. Nothing from the package's repository was fetched to be built or
run, and `npm audit` was not used. Each advisory found was checked against the exact version (its
affected and fixed ranges) and against how MedHub uses the package, cited by source file below.

**Sources checked**

- OSV, `POST https://api.osv.dev/v1/query` with
  `{"package":{"name":"react-dom","ecosystem":"npm"},"version":"18.3.1"}`
  (https://osv.dev/list?ecosystem=npm&q=react-dom). Also the OSV batch query (`POST
  https://api.osv.dev/v1/querybatch`) of all 96 non-dev packages in `frontend/package-lock.json`,
  for the transitive dependencies named below.
- GitHub Security Advisories, https://github.com/facebook/react/security/advisories
- NVD CVE API 2.0, https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=react-dom
- React changelog, https://github.com/facebook/react/blob/main/CHANGELOG.md, and the React 16.9
  release post,
  https://legacy.reactjs.org/blog/2019/08/08/react-v16.9.0.html#deprecating-javascript-urls
- npm registry metadata, https://registry.npmjs.org/react-dom (publish date 2024-04-26, not
  deprecated, integrity)

**Findings**

- OSV: no entry for 18.3.1. The one historical `react-dom` advisory, GHSA-mvjj-gqq2-p4hw
  (CVE-2018-6341, XSS in server-side rendering of attribute names), affects 16.0.0 to 16.4.1 only.
- GitHub: the ten 2025-2026 React advisories affect the `react-server-dom-*` 19.x packages only
  (see SOUP-025). None affects `react-dom` 18.3.1, and none of those packages is in the lock file.
- NVD: no CVE for `react-dom` 18.x.
- Changelog: 18.3.1 is the last 18.x release.
- Documented behaviour, not an advisory, relevant to the XSS mitigation this record names
  (SR-031, RISK-005): React escapes text and attribute values by default. A `javascript:` URL in
  an `href` is not blocked, however. Since 16.9 React logs a warning and still renders it; the
  16.9 post defers blocking to a later major release, which is not 18.x. MedHub: `frontend/src`
  contains no `dangerouslySetInnerHTML`. The only dynamic `href` is in
  `frontend/src/core/clinical/AttachmentItem.tsx`, built by `ApiClient.getAttachmentUrl` from the
  fixed prefix `/api/v1/attachments/` and an attachment id returned by the API. No user-supplied
  URL reaches an `href`, so MedHub is not affected.

**Judgement.** None found for 18.3.1 (2026-10-22). The escaping-by-default behaviour MedHub relies
on holds for its use. Not hazard-relevant: no RISK input and no PRB. The `javascript:` URL
behaviour stays a constraint on future code: an `href` taken from user or API-supplied text needs
its scheme validated.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 18.3.1 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11, AC-12): none
  found for 18.3.1; the documented `javascript:` URL behaviour does not affect MedHub's use. Record
  1.0 → 1.1, approval record removed for re-approval.
