---
id: SOUP-004
type: soup
title: Uvicorn
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: Encode
soup_version: 0.49.0
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: 386ed17d5fb46fad6d0967464fd9d352f51f23c87788531e9472e386b8348902
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-004 — Uvicorn 0.49.0

## Functional and performance requirements

ASGI server process for the API (development and the worker class under Gunicorn).

## Required hardware and software environment

Python 3.12; Linux container.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for Uvicorn 0.49.0 with the `standard` extras `backend/uv.lock` resolves: h11 0.16.0, httptools 0.8.0, uvloop 0.22.1, websockets 16.0, watchfiles 1.2.0, python-dotenv 1.2.2, PyYAML 6.0.3, click 8.4.1. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/Kludex/uvicorn/security/advisories; NVD; https://github.com/Kludex/uvicorn/releases

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `uvicorn` 0.49.0 and each extra at the version above.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `uvicorn@0.49.0`, `h11@0.16.0`, `httptools@0.8.0`, `uvloop@0.22.1`, `websockets@16.0`.
- Uvicorn repository advisories — https://github.com/Kludex/uvicorn/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `uvicorn`.
- Release notes — https://github.com/Kludex/uvicorn/releases: 0.49.0 has no later 0.49.x patch; 0.50.0 to 0.54.0 (2026-07-04 to 2026-09-25) were read for fixes that apply to 0.49.0.

### Findings

**None found** on 2026-10-22. No OSV or GitHub advisory for Uvicorn 0.49.0 or any of its extras,
and no repository advisory. NVD's `uvicorn` matches are other products or rejected
(CVE-2025-15603, withdrawn by its CNA). Releases 0.50.0–0.54.0 add features (zttp parser, HTTP/2,
WebSocket handshake and flow-control fixes for the `websockets-sansio` implementation) and carry no
security fix for the HTTP/1.1 `httptools` path MedHub uses.

### MedHub use and judgement

The backend runs `gunicorn -k uvicorn.workers.UvicornWorker` (`backend/entrypoint.sh`), so Uvicorn's
`httptools` protocol parses every request behind nginx. MedHub serves no WebSockets. Not
hazard-relevant; no RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 0.49.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): none found for 0.49.0 or its `standard` extras; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
