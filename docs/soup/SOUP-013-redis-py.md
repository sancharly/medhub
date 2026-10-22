---
id: SOUP-013
type: soup
title: redis-py
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Redis Ltd.
soup_version: 8.0.0
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-013 — redis-py 8.0.0

## Functional and performance requirements

Client for the opaque session store with TTLs (SR-030) and for the Celery broker connection.

## Required hardware and software environment

Python 3.12; Redis server 7 (SOUP-021).

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for redis-py (`redis`) 8.0.0, the version `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/redis/redis-py/security/advisories; NVD; https://github.com/redis/redis-py/releases

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `redis` 8.0.0.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `redis@8.0.0`.
- redis-py repository advisories — https://github.com/redis/redis-py/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `redis-py`.
- Release notes — https://github.com/redis/redis-py/releases/tag/v8.0.1 (2026-06-23), the later patch in the 8.0 line, and v8.1.0 (2026-07-30).

### Findings

**None found** on 2026-10-22. No advisory in OSV, the GitHub Advisory Database, the repository or
NVD. 8.0.1 fixes Unix-socket maintenance notifications, async cluster and `MultiDBClient`
connection handling, hiredis readiness checks, RESP3 `FT.SEARCH` parsing, blocking
`PubSub.listen()` and async `Pipeline.reset()` cancellation. 8.1.0 fixes Sentinel failover pool
capacity, RESP3 with hiredis, double URL decoding in `unquote()`, and search helpers.

### MedHub use and judgement

MedHub uses the synchronous client, `Redis.from_url("redis://redis:6379/0")`, over TCP with the
default protocol, for the opaque session store with TTLs (SR-030, the RISK-005 design control), the
lockout counters (`app/auth/lockout.py`) and, through Celery, the broker. It does not use hiredis
(not installed), asyncio, cluster, Sentinel, search or `PubSub.listen()`. Its Redis URL carries no
credentials or percent-encoding, so the `unquote()` fix does not apply. Not hazard-relevant; no
RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 8.0.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): none found for 8.0.0; 8.0.1/8.1.0 bug fixes reviewed, none on MedHub's paths; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
