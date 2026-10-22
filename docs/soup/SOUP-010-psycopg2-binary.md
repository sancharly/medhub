---
id: SOUP-010
type: soup
title: psycopg2-binary
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Daniele Varrazzo
soup_version: 2.9.12
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-010 — psycopg2-binary 2.9.12

## Functional and performance requirements

PostgreSQL driver (synchronous) used by every repository.

## Required hardware and software environment

Python 3.12; bundled libpq; PostgreSQL 16 server (SOUP-020).

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for psycopg2-binary 2.9.12, the version `backend/uv.lock` resolves, with its bundled libpq. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/psycopg/psycopg2/security/advisories; https://www.psycopg.org/docs/news.html; PostgreSQL security information https://www.postgresql.org/support/security/

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `psycopg2-binary` 2.9.12.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `psycopg2-binary@2.9.12`.
- psycopg2 repository advisories — https://github.com/psycopg/psycopg2/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `psycopg2`.
- Release notes — https://www.psycopg.org/docs/news.html, for 2.9.12 and the later patch 2.9.13 (PyPI upload 2026-09-09).
- PostgreSQL security information — https://www.postgresql.org/support/security/ (client-side components) and the 2026-05-14 announcement https://www.postgresql.org/about/news/postgresql-184-1710-1614-1518-and-1423-released-3297/.

### Findings

No advisory for psycopg2-binary 2.9.12 in OSV, the GitHub Advisory Database, the repository or NVD.

- 2.9.12 itself fixes an infinite loop on a malformed interval. 2.9.13 fixes the parsing of
  malformed `bytea` input and of malformed int64 values in arrays. Neither is labelled a security
  fix.
- **Bundled libpq.** The release notes do not name the libpq version in the binary wheels. 2.9.12
  was published on 2026-04-20, before PostgreSQL's 2026-05-14 minor releases, so its libpq cannot
  contain the fix for **CVE-2026-6477** (CVSS 8.8): libpq's `lo_export()`, `lo_read()`,
  `lo_lseek64()` and `lo_tell64()` let a server superuser overwrite client stack memory. The
  other 2026 client-side PostgreSQL CVEs are in `psql`, `pg_dump`, ECPG and `pg_basebackup`, not
  in libpq.

### MedHub use and judgement

psycopg2 is the synchronous driver behind every repository (via SQLAlchemy, SOUP-008). MedHub
connects only to its own PostgreSQL server (SOUP-020) on the internal Compose network. It uses no
large objects (no `lobject` or `lo_*` call; attachments live in MinIO) and no `bytea` columns
(checked 2026-10-22). The parsing fixes concern malformed data from that trusted server.
CVE-2026-6477 needs a hostile server superuser and the large-object API, and MedHub has neither.
Not hazard-relevant, MedHub not affected: no RISK or PRB. At the next dependency change, record
the bundled libpq version (`psycopg2.__libpq_version__` in the built image) in this record.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 2.9.12 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): no advisory for 2.9.12; bundled libpq predates the CVE-2026-6477 fix but MedHub does not use large objects; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
