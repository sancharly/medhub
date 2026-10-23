---
id: SOUP-009
type: soup
title: Alembic
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: SQLAlchemy authors
soup_version: 1.18.4
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: 7d74c8920b9c798f8696420133b6d3146c5cf5c9f27e488fd26bd2151a31a0c1
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-009 — Alembic 1.18.4

## Functional and performance requirements

Schema migrations applied at bring-up, giving a reproducible database state.

## Required hardware and software environment

Python 3.12; SQLAlchemy (SOUP-008); PostgreSQL 16.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for Alembic 1.18.4 and the Mako 1.3.12 and MarkupSafe 3.0.3 it pulls in, the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database, https://github.com/sqlalchemy/alembic/security/advisories and https://github.com/sqlalchemy/mako/security/advisories; NVD; https://alembic.sqlalchemy.org/en/latest/changelog.html

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `alembic` 1.18.4, `mako` 1.3.12, `markupsafe` 3.0.3.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `alembic@1.18.4`, `mako@1.3.12`.
- Repository advisories — https://github.com/sqlalchemy/alembic/security/advisories and https://github.com/sqlalchemy/mako/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `alembic`.
- Changelog — https://alembic.sqlalchemy.org/en/latest/changelog.html, for 1.18.5 (2026-06-25), the only later patch in the 1.18 line (1.19.x and 1.20.x read for security notes: none).

### Findings

**Alembic 1.18.4: none found.** No advisory in OSV, GitHub or the repository; NVD's one `alembic`
match is another product (SQLBot). 1.18.5 fixes autogenerate rendering, MySQL `ENUM` comparison
and `add_column(inline_references=...)` foreign-key options.

**Mako 1.3.12: one advisory.** GHSA-5639-2j2p-m4mx / CVE-2026-102991 / PYSEC-2026-4243
(CVSS 3.1 AV:N/AC:H, high confidentiality impact): on **Windows**, a `TemplateLookup` URI with a
drive designator escapes the template directory. Affected < 1.4.2, fixed in 1.4.2 (2026-09-22).
The two earlier variants, GHSA-v92g-xgxw-vvmm (fixed in 1.3.11) and GHSA-2h4p-vjrc-8xpq /
CVE-2026-44307 (fixed in 1.3.12), are fixed in the locked version. MarkupSafe 3.0.3: none found.

### MedHub use and judgement

MedHub runs `alembic upgrade head` at bring-up (`backend/entrypoint.sh`) in a Linux container.
Mako only renders `script.py.mako` when a developer generates a new revision, with no untrusted
template URI, and the flaw needs Windows path semantics. The 1.18.5 fixes concern autogenerate and
MySQL, not applying existing migrations to PostgreSQL. Not hazard-relevant, MedHub not affected:
no RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 1.18.4 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): Alembic none found; Mako 1.3.12 GHSA-5639-2j2p-m4mx (Windows-only) does not apply; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
