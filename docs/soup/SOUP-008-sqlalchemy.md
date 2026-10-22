---
id: SOUP-008
type: soup
title: SQLAlchemy
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
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
