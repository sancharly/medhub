---
id: SOUP-021
type: soup
title: Redis server
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Redis Ltd.
soup_version: 7.4.11
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-021 — Redis server 7.4.11

## Functional and performance requirements

Session store with TTL eviction (SR-030) and Celery broker/result backend.

## Required hardware and software environment

`redis:7.4.11-alpine` container image; base OS Alpine Linux v3.21 (A-5).

| Full image reference | Used by |
|---|---|
| `redis:7.4.11-alpine@sha256:892022f9f18c26c92c30e15194d132f90044af87b94a491a75429bbc3982eab1` | `infra/docker-compose.yml`: `redis` service; `.github/workflows/ci.yml`: `backend-tests` job, `redis` service container (identical reference) |

Resolved on 2026-10-22 with `docker buildx imagetools inspect redis:7-alpine` and `docker buildx imagetools inspect redis:7.4.11-alpine`; both reported the same image configuration (Redis 7.4.11). The digest is the multi-arch image index digest (`Digest:` line of the second command).

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) by the Software Architect role, at the pinned
version `redis:7.4.11-alpine@sha256:892022f9…eab1` (Redis 7.4.11; base OS Alpine Linux 3.21.9).

Sources checked:

| Source | URL | What was checked |
|---|---|---|
| Redis GitHub Security Advisories (vendor) | https://github.com/redis/redis/security/advisories | All 48 published advisories; the newest are of 2026-05-05 (CVE-2026-25243, CVE-2026-23631, CVE-2026-23479) |
| Redis 7.4 release notes (vendor) | https://github.com/redis/redis/releases/tag/7.4.11 (and 7.4.9, 7.4.10) | Security fixes per patch release; 7.4.11 (2026-08-17) is the newest 7.4 release |
| NVD CVE API 2.0 | https://services.nvd.nist.gov/rest/json/cves/2.0 | Keyword `redis`, published 2026-07-01..2026-10-22 (69 results, filtered to the Redis server) |
| Debian security tracker (fixed-in commit for CVE-2026-92925) | https://security-tracker.debian.org/tracker/CVE-2026-92925 | Affected range of the one server CVE published after 7.4.11 |
| Alpine Linux releases | https://alpinelinux.org/releases/ | Support end of the base-OS branch |
| OSV (Alpine:v3.21) | https://api.osv.dev/v1/querybatch | Every source package of the image (13) at its installed version |

Method for the base OS: `/lib/apk/db/installed` was copied out of the pinned image without running
it (`docker create` + `docker cp`), and each source package was queried in OSV at its installed
version. `docker scout cves` was tried (CLI 0.20.0) and crashed, so no image scanner was used. The
Redis binary is built from source in the image and is covered by the vendor sources, not by OSV
Alpine.

How MedHub uses the item: `redis-server --appendonly yes` with no password and no ACL
(`REDIS_URL=redis://redis:6379/0`), reachable only on the internal `medhub` network by the backend
and the Celery worker. No TLS, no cluster mode, no replicas. The vendor's "authenticated user"
precondition therefore holds for any client on that network.

Findings:

| ID | Summary | Fixed in | Applies to 7.4.11 | MedHub affected | Hazard relevance |
|---|---|---|---|---|---|
| CVE-2026-92925 | Cluster-bus packet parser: missing null-termination check on PING/PONG/MEET extensions, out-of-bounds read (disclosure or DoS) | 8.10.0 (Debian tracker: commit 37894fae, 8.10-rc1); no 7.4 fix published | Yes (affected ≥ 7.0.0 < 8.10.0) | No: cluster mode is off, so the cluster bus port is not opened | None |
| GHSA-2r7g-8hpc-rpq9 (no CVE) | Authenticated client can exhaust memory with multi-bulk commands (DoS). The vendor treats it as within the Redis security model and plans no fix | none planned | Yes (≤ 8.0) | Only to a client on the internal network. Without a password, any process on the `medhub` network counts as authenticated | Availability only (RISK-007): needs a foothold on the internal network first. Not raised; covered by the network isolation already assumed |
| CVE-2026-81934 | Use-after-free in `tlsProcessPendingData()` with TLS enabled | 7.4.11 | No | No (no TLS on Redis) | None |
| CVE-2026-66373 | `RESTORE` stream payload with a shared NACK leads to a double free (incomplete fix of CVE-2026-25243) | 7.4.10 | No | — | None |
| CVE-2026-25243, CVE-2026-23631, CVE-2026-23479 | `RESTORE` invalid memory access; Lua use-after-free; unblock-client use-after-free (RCE) | 7.4.9 | No | — | None |

Every earlier advisory with a 7.4 fixed version is fixed at or below 7.4.9. Advisories whose
structured "patched" field reads "TBD" were checked against the 7.4 release notes:
CVE-2024-51741 (7.4.2), CVE-2025-21605 (7.4.3), CVE-2025-27151 (7.4.4), CVE-2025-32023 and
CVE-2025-48367 (7.4.5), CVE-2025-46817, CVE-2025-46818 and CVE-2025-46819 (7.4.6). Base OS: OSV returned no entry for
any of the 13 source packages (OpenSSL 3.3.7-r2, musl 1.2.5-r12, zlib 1.3.2-r1, busybox
1.37.0-r14).

Hazard relevance: none at this version. RISK-005 (session integrity and revocation, SR-030) and
RISK-007 (availability of sessions and the Celery broker) depend on key TTLs, `DEL` and persistence,
none of which is anomalous at 7.4.11.

Observation for monitoring: the base-OS branch Alpine 3.21 reaches end of support on
**2026-11-01**, ten days after this review. After that date the pinned image stops receiving
base-OS security fixes. It holds no hazard-relevant anomaly today. Raised as
[PRB-045](../problem-reports/PRB-045-redis-image-base-os-end-of-support.md) (minor, 2026-10-22).
Upgrading within the 7.4 line to an image on a supported Alpine branch is a separate CR (CR-001
A-4). Redis 7.4 does not receive the CVE-2026-92925 fix, which MedHub does not
need.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — `redis:7-alpine` → `redis:7.4.11-alpine@sha256:892022f9f18c26c92c30e15194d132f90044af87b94a491a75429bbc3982eab1`; pinned at the version the tag resolved to, no upgrade (CR-001 A-4, TASK-155); PRB-001.
- 2026-10-22 — Version 1.2: first anomaly-list review at 7.4.11 (TASK-154, CR-001 AC-11): two
  applicable anomalies, no hazard-relevant one. CVE-2026-92925 (cluster bus) does not affect
  MedHub. GHSA-2r7g-8hpc-rpq9 (authenticated DoS, no fix planned) needs a foothold on the internal
  network. Base OS Alpine 3.21 ends support on 2026-11-01 (PRB-045, minor).
  `anomaly_review` set. No version change. Approval record cleared for re-approval.
