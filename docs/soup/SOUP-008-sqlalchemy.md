---
id: SOUP-008
type: soup
title: SQLAlchemy
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-11-13"
manufacturer: SQLAlchemy authors
soup_version: 2.0.51
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-008 — SQLAlchemy 2.0.51

## Functional and performance requirements

ORM and repositories with parameterized queries only (SQL-injection mitigation, SR-031.1), transactions and constraint enforcement.

**Relied-on behaviour: connection pool sizing (SR-026 AC 5, ADR-0022, TASK-136).** The one engine
(`app/db/repositories/session.py`) is created with `pool_size=DB_POOL_SIZE`,
`max_overflow=DB_MAX_OVERFLOW` and `pool_timeout=DB_POOL_TIMEOUT` (deployed 20 / 20 / 10 s, code
defaults 5 / 10 / 30 s, CR-006 D-24/D-25). MedHub relies on `QueuePool` keeping at most
`pool_size + max_overflow` connections open, making a caller wait up to `pool_timeout` seconds for
one, and then raising `sqlalchemy.exc.TimeoutError` ("QueuePool limit of size … overflow … reached")
rather than opening more. The start-up check keeps the API thread limit (SOUP-003) at or below
that total, which does not make a checkout wait-free: a connection belongs to the request (its `get_db`
session, held between dependency steps, through a whole streaming download and until `get_db` exits after
the response is sent), not to the thread, so one worker serves about threads + connections concurrent
requests; beyond that, requests wait `pool_timeout` and answer 500 (PRB-081). A FAILURE audit row on its
own transaction (ADR-0016) is why the deployed total is twice the thread limit. Verified by `test_engine_pool_follows_the_settings`
(`tests/core/test_pool_settings.py`) and the SR-026 AC 5 load test (TS-018).

## Required hardware and software environment

Python 3.12; PostgreSQL 16 through psycopg2 (SOUP-010).

Transitive dependencies covered by this record: greenlet 3.5.2.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for SQLAlchemy 2.0.51 with greenlet 3.5.2, the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/sqlalchemy/sqlalchemy/security/advisories; NVD; https://docs.sqlalchemy.org/en/20/changelog/changelog_20.html

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `sqlalchemy` 2.0.51, `greenlet` 3.5.2.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `sqlalchemy@2.0.51`, `greenlet@3.5.2`.
- Repository advisories — https://github.com/sqlalchemy/sqlalchemy/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `sqlalchemy`.
- Changelog — https://docs.sqlalchemy.org/en/20/changelog/changelog_20.html, for 2.0.52 (2026-08-11), 2.0.53 (2026-09-14), 2.0.54 (2026-09-15) and 2.0.55 (2026-10-16), the patches after 2.0.51 in the 2.0 line.

### Findings

No security advisory for 2.0.51 or greenlet 3.5.2 in OSV, the GitHub Advisory Database or the
repository. NVD's `sqlalchemy` matches are other products (SQLAdmin, Snowflake SQLAlchemy, Chainlit,
Langroid, …). None of 2.0.52–2.0.55 is marked as a security fix or as fixing a regression from
2.0.51. Bug fixes that bear on the controls this record supports:

| Fix | In | MedHub affected? |
|---|---|---|
| Literal-execute processors audited so string input is escaped or rejected (MSSQL `Uuid`, PostgreSQL `JSONPATH`, numeric types) | 2.0.52 | No: this is literal rendering. Runtime queries send bound parameters through psycopg2; `literal_binds` appears only in Alembic's offline mode (`app/db/alembic/env.py`), which MedHub does not run |
| A single quote in a sequence, table or schema name breaks `nextval()` | 2.0.52 | No: MedHub's identifiers contain no quotes |
| Text resembling a `pyformat` parameter rewritten as a bound parameter under positional paramstyles | 2.0.55 | No: psycopg2 uses the `pyformat` paramstyle, not a positional one |
| Wrong column keys in ORM UPDATE with `synchronize_session="fetch"` and `.returning()`; `supplemental_cols` missing from the cache key; `with_expression()`, `aliased()`, `CTE.alias()` and `MutableDict`/`MutableList` fixes; multi-object UPDATE expiring one object (regression since 2.0.36) | 2.0.52–2.0.55 | No: none of these constructs appears in `app/` or `modules/` (checked 2026-10-22) |
| Pool connection leak when a `connect` event handler raises | 2.0.53 | No: MedHub registers no pool event handlers |

### MedHub use and judgement

MedHub relies on SQLAlchemy for parameterized queries only (SQL-injection mitigation, SR-031.1),
transactions and constraints, which also bear on correct patient attribution (RISK-002). Its
repositories use plain ORM queries with bound parameters. No anomaly applies to those paths. Not
hazard-relevant; no RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 2.0.51 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): no advisory for 2.0.51; later 2.0.x bug fixes reviewed, none on MedHub's query paths; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
- 2026-11-13 — 2.0.51 (unchanged). Relied-on behaviour added: `QueuePool` sizing (`pool_size`, `max_overflow`, `pool_timeout`) from settings, matched to the API thread limit (SR-026 AC 5, ADR-0022; CR-006 TASK-136, D-24/D-25). No version change, no new anomaly review. Record 1.1 → 1.2; approval record removed for re-review. Same day, TASK-136 round 2: corrected the relied-on wording (a connection belongs to the request, not the thread, so the limit is about threads + connections concurrent requests per worker, PRB-081); still 1.2, `in_review`.
