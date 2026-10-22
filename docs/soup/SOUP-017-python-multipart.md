---
id: SOUP-017
type: soup
title: python-multipart
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Andrew Dunham / Kludex
soup_version: 0.0.32
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-017 — python-multipart 0.0.32

## Functional and performance requirements

Multipart form parsing for attachment uploads (SR-013).

## Required hardware and software environment

Python 3.12; FastAPI/Starlette form handling.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for python-multipart 0.0.32, the version `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/Kludex/python-multipart/security/advisories; NVD; https://github.com/Kludex/python-multipart/releases/tag/0.0.32

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `python-multipart` 0.0.32.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `python-multipart@0.0.32`.
- Repository advisories — https://github.com/Kludex/python-multipart/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `python-multipart`.
- Release notes — https://github.com/Kludex/python-multipart/releases/tag/0.0.32 (2026-06-04). 0.0.32 is the latest release.

### Findings

**None found** for 0.0.32 on 2026-10-22. All seven repository advisories published since 2026-01
are fixed in earlier releases: GHSA-wp53-j4wj-2cfg / CVE-2026-24486 (0.0.22),
GHSA-mj87-hwqh-73pj / CVE-2026-40347 (0.0.26), GHSA-pp6c-gr5w-3c5g / CVE-2026-42561 (0.0.27),
GHSA-vffw-93wf-4j4q / CVE-2026-53537, GHSA-6jv3-5f52-599m / CVE-2026-53538 and
GHSA-5rvq-cxj2-64vf / CVE-2026-53539 (0.0.30), and GHSA-v9pg-7xvm-68hf / CVE-2026-53540 (0.0.31).
NVD lists the same CVEs. 0.0.32 changes only the partial-boundary scan (performance).

### MedHub use and judgement

MedHub parses attachment uploads (`UploadFile` in `app/api/routers/attachments.py`, SR-013)
through Starlette's form parser on top of python-multipart. No published anomaly applies to 0.0.32.
PRB-008 (the upload buffers the whole body) is MedHub's own defect and is unrelated. Not
hazard-relevant; no RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 0.0.32 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): none found for 0.0.32 (all published advisories fixed in ≤ 0.0.31); nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
