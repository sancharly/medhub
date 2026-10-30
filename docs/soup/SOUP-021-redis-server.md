---
id: SOUP-021
type: soup
title: Redis server
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-30"
manufacturer: Redis Ltd.
soup_version: 7.4.12
anomaly_review: "2026-10-29"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-30"
approved_digest: 19e5c4f2aa91e11eed97d45ed80862b8baffbf8af4114bda5f4b772fe30a2860
approval_note: self-approved
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-021 — Redis server 7.4.12

## Functional and performance requirements

Session store with TTL eviction (SR-030) and Celery broker/result backend.

## Required hardware and software environment

`redis:7.4.12-bookworm` container image (the official Debian 12 variant); base OS Debian GNU/Linux
12 (bookworm), point release 12.15 (A-5, CR-003 D-1).

| Full image reference | Used by |
|---|---|
| `redis:7.4.12-bookworm@sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5` | `infra/docker-compose.yml`: `redis` service; `.github/workflows/ci.yml`: `backend-tests` job, `redis` service container (identical reference) |

The digest is the multi-arch image index digest (the `Digest:` line of
`docker buildx imagetools inspect redis:7.4.12-bookworm`, 2026-10-29). It equals the digest CR-003
selected on the same day. `REDIS_VERSION=7.4.12` is in the image configuration, and
`redis-server --version` in the running container reports `v=7.4.12`.

Base OS, read from the pinned image without starting Redis (`docker create` + `docker cp`, 2026-10-29):

- `/etc/os-release` (a symlink to `/usr/lib/os-release`): `PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"`,
  `VERSION_ID="12"`, `VERSION_CODENAME=bookworm`.
- `/etc/debian_version`: `12.15`.
- Support status, checked 2026-10-29: Debian 12 regular security support ended on 2026-07-11 and
  Debian LTS runs until 2028-06-30 (https://endoflife.date/debian, API field `eol: 2028-06-30`,
  `support: 2026-07-11`; https://wiki.debian.org/LTS; https://www.debian.org/security/). The human
  accepted Debian LTS as upstream support for this base OS (CR-003 D-1).

Why the variant changed: upstream builds Redis 7.4 on Alpine 3.21 only (`-alpine3.21`, and the
`-alpine` aliases map to it), and Alpine 3.21 reaches end of support on 2026-11-01. No Redis 7.4
image exists on a later Alpine branch, so PRB-045 could not be fixed inside the Alpine variant.
The official `-bookworm` image is the supported alternative (CR-003 D-1). The image is built
`FROM debian:bookworm-slim`.

Upstream rebuilt `redis:7.4.11-alpine` under the same tag on 2026-10-26 (the tag then resolved to
index digest `sha256:d9436322…3193`). That does not affect MedHub: the digest in the table above
identifies the image, and a tag alone does not (SR-028 AC-5).

Data compatibility (CR-003 A-5, checked 2026-10-29 in TASK-161): `redis` is uid 999 in both
images; the group changes from gid 1000 (Alpine) to gid 999 (Debian). The entrypoint chowns the
`/data` entries that `redis` does not own, so an AOF written by 7.4.11 stays readable. The AOF
loaded under 7.4.12 (see TASK-161 evidence).

## Anomaly list review

**Reviewed 2026-10-29** (TASK-161, CR-003 AC-14) by the Software Developer role, at the pinned
version `redis:7.4.12-bookworm@sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5` (Redis 7.4.12; base OS Debian GNU/Linux 12.15).

Sources checked:

| Source | URL | What was checked |
|---|---|---|
| Redis GitHub Security Advisories (vendor) | https://github.com/redis/redis/security/advisories (API: `repos/redis/redis/security-advisories`) | All 47 published advisories returned on 2026-10-29. The newest are the three of 2026-05-05 (CVE-2026-25243, CVE-2026-23631, CVE-2026-23479). None is newer than the previous review. TASK-154 counted 48; the newest advisories are the same |
| Redis 7.4.12 release notes (vendor) | https://github.com/redis/redis/releases/tag/7.4.12 (and 7.4.9, 7.4.10, 7.4.11) | 7.4.12 (2026-10-26) has one security fix: heap buffer overflow when a `PUBLISH`/`SPUBLISH` message above 4 GB is propagated over the cluster bus. 7.4.9, 7.4.10 and 7.4.11 list the earlier fixes |
| NVD CVE API 2.0 | https://services.nvd.nist.gov/rest/json/cves/2.0 | Keyword `redis`, published 2026-10-22..2026-10-29 (since the last review): 0 results. CPE query for `cpe:2.3:a:redis:redis:7.4.12`: 3 results (CVE-2026-23479, CVE-2026-23631, CVE-2026-25243), discussed below |
| OSV, ecosystem `Debian:12` | https://api.osv.dev/v1/querybatch | All 64 source packages of the 89 installed binary packages, at the installed version. Package list copied from the pinned image's `/var/lib/dpkg/status` without running it. 24 source packages returned 97 entries, all `DEBIAN-CVE-*`, none with a fixed version in bookworm |
| Debian security tracker | https://security-tracker.debian.org/tracker/ (one page per CVE above) | Status of each of the 97 entries for the installed version, the tracker's urgency and its bookworm triage note (`ignored`, `no-dsa`, `postponed`) |
| `debian-security-support` (bookworm package 1:12+2026.06.30) | https://sources.debian.org/data/main/d/debian-security-support/1:12+2026.06.30/ (`security-support-limited`, `security-support-ended.deb12`); source repository https://salsa.debian.org/debian/debian-security-support | Every installed source package checked against both lists (patterns such as `golang.*` and `rust.*` included): no match |
| Debian LTS advisories (DLA) | https://www.debian.org/lts/security/ | 350 advisories listed, 2026-04-08..2026-10-29, compared with the installed source and binary package names; each bookworm DLA for an installed package was compared with the installed version |
| Debian release support | https://endoflife.date/debian, https://wiki.debian.org/LTS | Support dates of the base OS (see Environment) |

`docker scout cves` was not used (it crashed in the CR-001 review). The Redis binary is built from
source in the image and is covered by the vendor sources, not by OSV Debian.

How MedHub uses the item: `redis-server --appendonly yes` with no password and no ACL
(`REDIS_URL=redis://redis:6379/0`), reachable only on the internal `medhub` network by the backend
and the Celery worker. No TLS, no cluster mode, no replicas. The vendor's "authenticated user"
precondition therefore holds for any client on that network. The container runs one program,
`redis-server`, as uid 999 after the entrypoint starts (`dash`, `find`, `chown`, `setpriv`).
Clients speak only the Redis protocol; nothing in it runs a shell or the other installed utilities.

### Redis findings

| ID | Summary | Fixed in | Applies to 7.4.12 | MedHub affected | Hazard relevance |
|---|---|---|---|---|---|
| CVE-2026-92925 | Cluster-bus packet parser: missing null-termination check on PING/PONG/MEET extensions, out-of-bounds read (disclosure or DoS) | 8.10.0 (Debian tracker: commit 37894fae, 8.10-rc1); no 7.4 fix published | Yes (affected ≥ 7.0.0 < 8.10.0) | No: cluster mode is off, so the cluster bus port is not opened | None |
| GHSA-2r7g-8hpc-rpq9 (no CVE) | Authenticated client can exhaust memory with multi-bulk commands (DoS). The vendor treats it as within the Redis security model and plans no fix (affected `<= 8.0`) | none planned | Yes | Only to a client on the internal network. Without a password, any process on the `medhub` network counts as authenticated | Availability only (RISK-007): needs a foothold on the internal network first. Not raised; covered by the network isolation already assumed |
| 7.4.12 security fix (no CVE id in the release notes) | Heap buffer overflow when a `PUBLISH`/`SPUBLISH` message above 4 GB is propagated over the cluster bus | 7.4.12 | No (fixed at the pinned version) | No (cluster mode is off) | None |
| CVE-2026-23479, CVE-2026-23631, CVE-2026-25243 | Unblock-client use-after-free; Lua use-after-free; `RESTORE` invalid memory access (all RCE) | 7.4.9 (vendor release notes). The GitHub advisories read "TBD" for the patched version | No. NVD's CPE data lists 7.4.12 as in range (`7.2.0` up to, not including, `8.6.3`); the vendor's release notes take precedence and put the fix at 7.4.9 | — | None |
| CVE-2026-66373, CVE-2026-81934 and the other fixes in 7.4.10 / 7.4.11 (stream `RESTORE` NACK double free; TLS pending-data use-after-free; ACL key-permission bypass in `SORT`/`GEORADIUS`/`XREAD`; `KEYNUM` argv access; RDB `SLOT_INFO` memory corruption) | See the 7.4.10 and 7.4.11 release notes | 7.4.10 / 7.4.11 | No | — | None |

Every earlier advisory with a 7.4 fixed version is fixed at or below 7.4.9 (CVE-2024-51741 in 7.4.2,
CVE-2025-21605 in 7.4.3, CVE-2025-27151 in 7.4.4, CVE-2025-32023 and CVE-2025-48367 in 7.4.5,
CVE-2025-46817, CVE-2025-46818, CVE-2025-46819 and CVE-2025-49844 in 7.4.6). NVD reports nothing new for Redis
since 2026-10-22.

### Base OS findings (Debian 12.15)

Method: the installed package list was taken from the pinned image (`/var/lib/dpkg/status`,
89 binary packages, 64 source packages) and every source package was queried in OSV `Debian:12` at its
installed version.

**Result.** 24 source packages have 97 open entries. None has a fixed version in bookworm or
bookworm-security, so a newer image digest would not remove any of them today. The tracker's
urgency (from OSV) is `unimportant` for 37, `low` for 1 and `not yet assigned` for 59. The tracker
carries a bookworm note on 46 of the 97: `postponed` 25, `no-dsa` 16 and `ignored` 5 (all "Minor
issue" or not built / not applicable). The other 51 have no bookworm note yet. One entry in the
tracker's own table, CVE-2023-45853 (zlib), has an `ignored` note because `contrib/minizip` is not
built; the OSV row still lists it.

| Source package, installed version | Entries | Role in the container | Bookworm tracker note | CVE ids |
|---|---|---|---|---|
| acl 2.3.1-3 | 2 | Installed, not run | postponed 2 | CVE-2026-54369, CVE-2026-54370 |
| apt 2.6.1 | 1 | Installed, not run | - | CVE-2011-3374 |
| attr 1:2.5.1-4 | 1 | Installed, not run | postponed 1 | CVE-2026-54371 |
| bzip2 1.0.8-5 | 1 | Installed, not run | no-dsa 1 | CVE-2026-42250 |
| coreutils 9.1-1 | 5 | `chown` at start | ignored 1 | CVE-2016-2781, CVE-2017-18018, CVE-2025-5278, CVE-2026-56391, CVE-2026-56392 |
| dash 0.5.12-2 | 2 | Runs `docker-entrypoint.sh` at start | - | CVE-2026-102473, CVE-2026-102474 |
| diffutils 1:3.8-4 | 1 | Installed, not run | - | CVE-2026-53910 |
| gcc-12 12.2.0-14+deb12u1 | 3 | Installed, not run | ignored 1, postponed 1 | CVE-2022-27943, CVE-2026-102010, CVE-2026-95619 |
| glibc 2.36-9+deb12u14 | 23 | Linked by `redis-server` (libc6, libm) | no-dsa 4, postponed 9 | CVE-2010-4756, CVE-2018-20796, CVE-2019-1010022, CVE-2019-1010023, CVE-2019-1010024, CVE-2019-1010025, CVE-2019-9192, CVE-2026-18374, CVE-2026-19499, CVE-2026-19542, CVE-2026-5435, CVE-2026-5450, CVE-2026-5928, CVE-2026-6238, CVE-2026-6368, CVE-2026-6791, CVE-2026-77117, CVE-2026-80489, CVE-2026-8674, CVE-2026-86805, CVE-2026-89092, CVE-2026-95818, CVE-2026-97399 |
| gnupg2 2.2.40-1.1+deb12u2 | 5 | Installed, not run | no-dsa 2, postponed 2 | CVE-2022-3219, CVE-2025-30258, CVE-2025-68972, CVE-2026-105712, CVE-2026-57062 |
| gnutls28 3.7.9-2+deb12u7 | 7 | Installed, not run | - | CVE-2011-3389, CVE-2026-67693, CVE-2026-88647, CVE-2026-88648, CVE-2026-95184, CVE-2026-95209, CVE-2026-95210 |
| gzip 1.12-1 | 2 | Installed, not run | postponed 2 | CVE-2026-41991, CVE-2026-41992 |
| libgcrypt20 1.10.1-3+deb12u1 | 2 | Installed, not run | - | CVE-2018-6829, CVE-2024-2236 |
| libtasn1-6 4.19.0-2+deb12u1 | 1 | Installed, not run | no-dsa 1 | CVE-2025-13151 |
| ncurses 6.4-4 | 3 | Installed, not run | no-dsa 3 | CVE-2023-50495, CVE-2025-6141, CVE-2025-69720 |
| openssl 3.0.22-1~deb12u2 | 1 | Linked by `redis-server` (libssl3, libcrypto) | - | CVE-2025-27587 |
| p11-kit 0.24.1-2 | 2 | Installed, not run | postponed 2 | CVE-2026-13757, CVE-2026-18938 |
| pam 1.5.2-6+deb12u2 | 3 | Installed, not run | ignored 1, postponed 1 | CVE-2024-10041, CVE-2025-8941, CVE-2026-54411 |
| perl 5.36.0-7+deb12u4 | 5 | Installed, not run | postponed 1 | CVE-2011-4116, CVE-2023-31486, CVE-2026-15534, CVE-2026-82560, CVE-2026-9538 |
| shadow 1:4.13+dfsg1-1+deb12u2 | 2 | Installed, not run | no-dsa 1 | CVE-2007-5686, CVE-2024-56433 |
| systemd 252.39-1~deb12u2 | 7 | Installed, not run | no-dsa 1, postponed 2 | CVE-2013-4392, CVE-2023-31437, CVE-2023-31438, CVE-2023-31439, CVE-2026-15059, CVE-2026-16742, CVE-2026-40228 |
| tar 1.34+dfsg-1.2+deb12u1 | 4 | Installed, not run | no-dsa 1, postponed 2 | CVE-2005-2541, CVE-2026-18477, CVE-2026-18508, CVE-2026-5704 |
| util-linux 2.38.1-5+deb12u3 | 11 | `setpriv` at start (only when started as root) | ignored 1, no-dsa 1 | CVE-2022-0563, CVE-2025-14104, CVE-2026-13595, CVE-2026-27456, CVE-2026-3184, CVE-2026-53613, CVE-2026-53615, CVE-2026-76642, CVE-2026-78408, CVE-2026-78409, CVE-2026-78410 |
| zlib 1:1.2.13.dfsg-1 | 3 | Installed, not run | ignored 1, no-dsa 1 | CVE-2023-45853, CVE-2026-27171, CVE-2026-85091 |

**Hazard-relevance judgement.** None of the 97 entries is hazard-relevant for MedHub:

- **Linked by the Redis server (glibc, OpenSSL).** Redis does not feed client data to the
  affected functions as far as these descriptions show, and the container's single running program
  is the Redis server. This is a judgement from the advisory text, not a code audit of Redis. The
  entries are: local `ld.so` and setuid issues (CVE-2026-95818, CVE-2026-86805), which need a local
  process and a setuid program; resolver, `iconv`, `scanf`, `wordexp`, `fopen`, `ungetwc` and
  `nscd` issues, which Redis does not call on request data (Redis does not resolve names for
  client traffic in this topology, and `nscd` is not installed); `strfmon` (CVE-2026-19499,
  described as glibc 2.38 to 2.44, the installed glibc is 2.36); and old, disputed entries from 2010
  to 2019 rated `unimportant`. OpenSSL's only entry, CVE-2025-27587, concerns the PowerPC
  architecture (the image runs on amd64 and arm64), and TLS is not enabled.
- **Run once at start (dash, util-linux `setpriv`, findutils, coreutils `chown`).** These run in the
  entrypoint with fixed arguments before `redis-server` starts. The entries concern other utilities
  of those packages (`sort`, `uniq`, `unexpand`, `mount`, `nsenter`, `login` and the like) or local
  attacks, and no client can reach them.
- **Installed, never run (all other packages).** gnupg2, gnutls28, libgcrypt20, libtasn1-6, p11-kit,
  pam, perl, ncurses, tar, gzip, bzip2, zlib (minizip not built), acl, attr, apt, diffutils,
  systemd (libsystemd0 and libudev1 only, no daemon), shadow and gcc-12's runtime libraries are
  present as part of the Debian base. Reaching any of them needs command execution inside the
  container, which a Redis client does not have.

The step that opens the exposure is the same for all of them: code execution in the container, or a
local account. That is outside the session-store and broker functions, so RISK-005 and RISK-007 are
not affected and nothing is raised as a RISK. No MedHub-affecting defect was found, so no PRB is
opened from this review.

**Monitoring observation.** The Debian image has far more open base-OS entries than the Alpine one
had (97 against none in OSV on 2026-10-22). All of them are minor or unassigned and have no fix in
bookworm, so the count reflects the tracker's open backlog for a larger base, not a MedHub
defect. The `postponed`, `no-dsa` and `ignored` notes are the Debian security team's own triage.
The next review should compare against this list.

**Fixed advisories already in the image (Debian LTS cross-check).** The newest bookworm DLA for
each installed package (up to 2026-10-29) is in the installed version, with one data-only
exception. Earlier DLAs for the same packages are superseded by these:

| DLA | Package | Fixed in | Installed | Status |
|---|---|---|---|---|
| DLA-4859-1 (2026-10-26) | openssl | 3.0.22-1~deb12u2 | 3.0.22-1~deb12u2 | Included |
| DLA-4821-1 (2026-10-05) | perl | 5.36.0-7+deb12u4 | 5.36.0-7+deb12u4 | Included |
| DLA-4816-1 (2026-10-03) | pcre2 | 10.42-1+deb12u2 | 10.42-1+deb12u2 | Included |
| DLA-4783-1 (2026-09-17) | xz-utils | 5.4.1-1+deb12u2 | 5.4.1-1+deb12u2 | Included |
| DLA-4854-1 (2026-10-23) | tzdata | 2026f-0+deb12u1 | 2026e-0+deb12u1 | One data release behind. A time-zone database update with no CVE. The container runs in UTC and Redis uses the zone only for log timestamps, so session TTLs and queue timing (relative seconds) are unaffected. No hazard |

Other DLAs in the list for installed package names (glibc DLA-4621-1, gnutls28 DLA-4595-1, systemd
DLA-4533-1, dpkg DLA-4673-1) are for Debian 11, not bookworm.

**Hazard relevance of the item as a whole: none at this version.** RISK-005 (session integrity and
revocation, SR-030) and RISK-007 (availability of sessions and the Celery broker) depend on key
TTLs, `DEL` and persistence. Those are unchanged between 7.4.11 and 7.4.12 (one fix, in cluster
mode) and none is anomalous at 7.4.12.

**PRB-045 end-of-support finding: cleared.** The base OS is now Debian 12 in Debian LTS until
2028-06-30, and no installed package is on the `debian-security-support` limited or ended lists.
The Alpine 3.21 branch (end of support 2026-11-01) is no longer part of the image.
[PRB-045](../problem-reports/PRB-045-redis-image-base-os-end-of-support.md) is `resolved`.

**Escalations from this review:** none. No RISK was raised and no PRB was opened for SOUP-021.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.
The base OS leaves Debian LTS support on 2028-06-30, and Redis 7.4 reaches end of life on
2029-12-01 (https://endoflife.date/redis): plan the next base or version move before 2028-06-30.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — `redis:7-alpine` → `redis:7.4.11-alpine@sha256:892022f9f18c26c92c30e15194d132f90044af87b94a491a75429bbc3982eab1`; pinned at the version the tag resolved to, no upgrade (CR-001 A-4, TASK-155); PRB-001.
- 2026-10-22 — Version 1.2: first anomaly-list review at 7.4.11 (TASK-154, CR-001 AC-11): two
  applicable anomalies, no hazard-relevant one. CVE-2026-92925 (cluster bus) does not affect
  MedHub. GHSA-2r7g-8hpc-rpq9 (authenticated DoS, no fix planned) needs a foothold on the internal
  network. Base OS Alpine 3.21 ends support on 2026-11-01 (PRB-045, minor).
  `anomaly_review` set. No version change. Approval record cleared for re-approval.
- 2026-10-29 — 7.4.11 (redis:7.4.11-alpine, Alpine 3.21) →
  7.4.12 (redis:7.4.12-bookworm@sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5, Debian 12); PRB-045, CR-003 (D-1).
  Version 1.3: anomaly-list review at 7.4.12 and the pinned digest (TASK-161, CR-003 AC-14):
  CVE-2026-92925 and GHSA-2r7g-8hpc-rpq9 carried forward, not hazard-relevant; 97 open Debian
  base-OS entries in 24 source packages, none fixable in bookworm, none hazard-relevant.
  Impact analysis (§7.4): CR-003 Risk stage; RISK-005, RISK-007, RISK-009 and RISK-010 unchanged.
  Existing `redis_data` volume loaded, session round trip passed on the real server. Digest equals
  the one CR-003 selected. Approval record cleared for re-approval.
