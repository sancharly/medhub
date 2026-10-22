---
id: SOUP-020
type: soup
title: PostgreSQL server
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: PostgreSQL Global Development Group
soup_version: "16.15"
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-020 — PostgreSQL server 16.15

## Functional and performance requirements

Relational storage of all PHI and records, constraints, and transactional integrity.

## Required hardware and software environment

`postgres:16.15` container image with a persistent volume; base OS Debian GNU/Linux 13 (trixie) (A-5).

| Full image reference | Used by |
|---|---|
| `postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97` | `infra/docker-compose.yml`: `postgres` service; `.github/workflows/ci.yml`: `backend-tests` job, `postgres` service container (identical reference) |

Resolved on 2026-10-22 with `docker buildx imagetools inspect postgres:16` and `docker buildx imagetools inspect postgres:16.15`; both reported the same image configuration (`PG_VERSION=16.15-1.pgdg13+2`). The digest is the multi-arch image index digest (`Digest:` line of the second command).

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) by the Software Architect role, at the pinned
version `postgres:16.15@sha256:9e2cf628…0a97` (PostgreSQL 16.15, package `16.15-1.pgdg13+2`; base
OS Debian GNU/Linux 13, `base-files` 13.8+deb13u7).

Sources checked:

| Source | URL | What was checked |
|---|---|---|
| PostgreSQL security information (vendor) | https://www.postgresql.org/support/security/ | Every CVE listing major version 16 (40 from Nov 2025 on), with its fixed-in version |
| PostgreSQL 16.15 release notes (vendor) | https://www.postgresql.org/docs/release/16.15/ | Release date (2026-08-13), security fixes, post-upgrade actions |
| PostgreSQL versioning policy and roadmap (vendor) | https://www.postgresql.org/support/versioning/, https://www.postgresql.org/developer/roadmap/ | 16.15 is the current 16.x minor; 16 is supported until 2028-11-09; next minor release 2026-11-12 |
| NVD CVE API 2.0 | https://services.nvd.nist.gov/rest/json/cves/2.0 | Keyword `postgresql`, published 2026-07-01..2026-10-22 (138 results, none against the PostgreSQL server beyond the vendor list) |
| OSV (Debian:13), from the Debian security tracker | https://api.osv.dev/v1/querybatch | Every source package of the image (95) at its installed version |

Method for the base OS: `/var/lib/dpkg/status` was copied out of the pinned image without running
it (`docker create` + `docker cp`), and each source package was queried in OSV at its installed
version. `docker scout cves` was tried (CLI 0.20.0) and crashed, so no image scanner was used.
PostgreSQL itself comes from the PGDG repository, so it is covered by the vendor sources above.

Findings for PostgreSQL 16.15: **none found**. Every CVE on the vendor page that lists 16 is fixed
in 16.15 or earlier; the newest (CVE-2026-19385, CVE-2026-18408 and the other August 2026 fixes)
are fixed in 16.15. The 16.15 post-upgrade actions do not apply to MedHub: it uses no logical
decoding output plugin, `pgcrypto`, `btree_gist` or `ltree` (no `CREATE EXTENSION` in the backend
or its migrations).

Findings for the base OS: OSV lists 115 entries against 28 of the 95 source packages (for example
`glibc` 2.41-12+deb13u4, `libxml2` 2.9.14 +deb13u3, `gnutls28`, `krb5`, `openldap`, `systemd`).
**None has a fix in Debian 13** at the date of the review: the Debian tracker marks each one
"unimportant" or "not yet assigned" (no fixed version), apart from the 2011 BEAST entry (CVE-2011-3389),
which it marks unimportant. The image therefore carries every security update Debian 13 had
published. OpenSSL 3.5.7-1~deb13u3 has no open entry (it includes the fix for CVE-2026-84782).

Hazard relevance: none. RISK-002 (constraints and transactional integrity) and RISK-007
(availability) rely on core storage, constraints and transactions. The 2026 server CVEs need an
authenticated SQL session that can call the affected functions. The database is reachable only on
the internal `medhub` network, and only the backend, through SQLAlchemy with parameterized
queries (SR-031), holds credentials. The unfixed base-OS entries concern utilities and libraries
the server does not expose to clients (XML catalog tools, `iconv` of Japanese encodings, `nscd`,
`wordexp`), or have no published fix.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — `postgres:16` → `postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97`; pinned at the version the tag resolved to, no upgrade (CR-001 A-4, TASK-155); PRB-001.
- 2026-10-22 — Version 1.2: first anomaly-list review at 16.15 (TASK-154, CR-001 AC-11): none
  found for PostgreSQL. Base-OS entries have no Debian 13 fix and are not hazard-relevant.
  `anomaly_review` set. No version change. Approval record cleared for re-approval.
