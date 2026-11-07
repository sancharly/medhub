---
id: SOUP-013
type: soup
title: redis-py
status: in_review
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-11-06"
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

Relied-on behaviour (the Redis commands MedHub issues through this client, each of which the client
must send as documented and return the server's reply for unchanged):

- `INCR` and `EXPIRE key seconds NX` queued in one transaction pipeline (`Redis.pipeline(transaction=True)`,
  sent as `MULTI` … `EXEC`) by the retrieval rate limiter (`app/api/routers/anonymized_data.py`).
  `EXPIRE … NX` needs Redis 7.0 or later (SOUP-021).
- Optimistic locking for the concurrent-session cap (SR-030 AC 7, PRB-023, TASK-199):
  `Pipeline.watch(key)` followed by an immediate-mode read, then `Pipeline.multi()`, queued commands
  and `Pipeline.execute()`, which must raise `redis.WatchError` when the watched key changed between
  `WATCH` and `EXEC` and must discard the queued commands. `ZRANGE … WITHSCORES` and one `EXISTS`
  per member are read in immediate mode after `WATCH` and before `MULTI` (TASK-205, PRB-065); they
  are not queued in the transaction. The commands in the transaction are `ZREM` (expired members),
  `DEL`, `ZREM` (evicted), `SET … EX`, `ZADD` and `EXPIRE`. The atomic primitive is
  `WATCH`/`MULTI`/`EXEC`, not a Lua script and not a database row lock.
- `Redis.set(name, value, ex=seconds, xx=True)` for the sliding refresh of a session (TASK-205,
  PRB-064): sent as `SET key value EX seconds XX`, and returning a falsy value (`None`) when the key
  does not exist, in which case the client must not have created it.
- `GET`, `DEL`, `ZRANGE`, `ZREM` for session resolve, invalidate and revoke-all.

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
- 2026-11-02 — 8.0.0 (unchanged). Version 1.2: relied-on requirements extended with `INCR`, `MULTI`/`EXEC`, `EXPIRE … NX` (retrieval rate limiter, carried from the TASK-186 QA review) and `WATCH`/`MULTI`/`EXEC` with `WatchError` (atomic session cap, TASK-199, PRB-023). No version change, no new anomaly review. Approval record cleared for re-approval.
- 2026-11-06 — 8.0.0 (unchanged). Version 1.3: relied-on requirements extended with `set(..., ex=..., xx=True)` returning `None` when the key is absent (conditional session refresh, TASK-205, PRB-064) and `EXISTS` read before `MULTI` (live-member count, PRB-065); corrected that `ZRANGE … WITHSCORES` is an immediate-mode read after `WATCH`, not one of the commands in the transaction (TASK-199 QA finding 4); `SETEX` no longer used. No version change, no new anomaly review. Record stays `in_review`.
