---
id: "PRB-045"
type: problem-report
title: "Redis image base OS Alpine 3.21 reaches end of support on 2026-11-01"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-29"
criticality: minor
links: []
tags: ["soup", "maintenance", "configuration-management"]
---

# PRB-045 — Redis image base OS Alpine 3.21 reaches end of support on 2026-11-01

## Observed

The pinned Redis image [SOUP-021](../soup/SOUP-021-redis-server.md),
`redis:7.4.11-alpine@sha256:892022f9f18c26c92c30e15194d132f90044af87b94a491a75429bbc3982eab1`, is
built on Alpine Linux 3.21.9. That branch reaches end of support on **2026-11-01**
(https://alpinelinux.org/releases/, checked 2026-10-22). After that date its packages (OpenSSL
3.3.7, musl 1.2.5, busybox, zlib and the rest) receive no security fixes. The image is used by
`infra/docker-compose.yml` (service `redis`) and by `.github/workflows/ci.yml` (`backend-tests`
service container).

## Impact

On 2026-10-22, OSV reports no entry for any of the image's 13 source packages at its installed
version, so there is no open anomaly today. From 2026-11-01 on, new base-OS vulnerabilities will
stay unfixed in the pinned image, and the PLAN-002 review can only detect them.

## Investigation

Mechanism. MedHub does not build the Redis image. It runs the upstream official image, and the
base-OS branch is whatever upstream built that image on. The digest freezes the base layers
together with the Redis binary. The reference is identical in both places that use it:
`infra/docker-compose.yml:84` (service `redis`, started with `--appendonly yes` at `:85` on the
`redis_data` volume at `:87`) and `.github/workflows/ci.yml:64` (`backend-tests` service
container).

- The floating `redis:7-alpine` came in with the Compose topology (commit `2d095f8`, TASK-004,
  2026-06-20). While it floated, it followed upstream rebuilds, base OS included.
- CR-001 TASK-155 pinned it at the release it then resolved to, 7.4.11, without upgrading it
  (CR-001 A-4). Upstream had built that image on Alpine 3.21.9. TASK-154 read this from
  `/etc/alpine-release` of the pinned image and checked the branch's end of support (2026-11-01)
  against endoflife.date and https://alpinelinux.org/releases/ (TASK-154 evidence table, row
  "SOUP-021 / PRB-045").
- After the pin, a base-OS update reaches MedHub only through a commit that changes the digest.
  That is the intended RISK-010 control. It also means a base-OS end of support has to be
  handled by an explicit change.

Root cause. Nothing in the process tracks the support lifecycle of a SOUP item or of an image's
base OS. PLAN-002 "SOUP monitoring (§6.1 f)" (`docs/plans/PLAN-002-maintenance-plan.md:44-49`)
prescribes anomaly-list reviews and their cadence, but it has no end-of-support or obsolescence
criterion. So the end of support was found only because the first review happened to check it.
Under CR-001 A-5 the base OS belongs to the image's own SOUP record, so SOUP-021 is the record the
fix changes.

Re-checked 2026-10-29. Both references above are unchanged since CR-001 (same tag and digest), so
the TASK-154 finding still applies. `/etc/alpine-release` was not read again: this workstation
has no container runtime.

## Safety evaluation

No hazard today: the anomaly review of 7.4.11 found nothing hazard-relevant. Redis carries
SR-030's session store (RISK-005) and the Celery broker (RISK-007). An unfixed base-OS flaw would
need a foothold on the internal `medhub` network to be reached. Criticality is `minor`: this is a
maintenance obligation (§6.1 f), not a realized defect.

Exposure window. On 2026-10-29 the end of support is three days away. From 2026-11-01 until the
fix lands, every Compose deployment and every CI run uses an unsupported base OS. No release is
made before CR-002 (human decision, 2026-10-22), so no released product ships on it. The window
therefore covers development, CI and pre-release environments only, and the criticality stays
`minor`. The fix replaces the image behind SR-030's session store and the Celery broker, so it
needs a regression check of those functions (CR-003 verification). This evaluation stands only
while no release is made before the fix. A release before then would ship a SOUP item with no
upstream security support.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

In CR-003. It is a separate CR because CR-001 A-4 excludes image upgrades, and this fix is its
first task because of the date:

- Move to a `redis:7.4.x-alpine` image built on a supported Alpine branch, pinned by tag and
  digest, in both Compose and CI.
- Review that version's anomaly list and update SOUP-021.
- Re-run the backend suite and the Compose smoke test.

Do this before the first release, or before 2026-11-01 plus the next review, whichever comes
first.

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12), on 2026-10-22. The evidence
is in SOUP-021's "Anomaly list review" section.

## Resolution

Resolved 2026-10-29 by [CR-003](../change-requests/CR-003-upgrade-end-of-life-and-advisory-soup.md),
TASK-161. The proposed Alpine move above was not possible: upstream builds Redis 7.4 on Alpine 3.21
only (`7.4.2-alpine3.21` to `7.4.12-alpine3.21`), and no Redis 7.4 image exists on a later Alpine
branch. The human chose the official Debian 12 variant instead (CR-003 D-1).

Changed files:

- `infra/docker-compose.yml:84` (service `redis`) and `.github/workflows/ci.yml:64`
  (`backend-tests` service container): both now `redis:7.4.12-bookworm@sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5`, an identical reference.
- [SOUP-021](../soup/SOUP-021-redis-server.md): `soup_version` 7.4.12, environment, anomaly-list
  review of 2026-10-29 at the new digest, change log; back to `in_review`.

Selected image: Redis 7.4.12 (released 2026-10-26), Debian GNU/Linux 12 (bookworm) point release
12.15. Debian 12 regular security support ended 2026-07-11 and Debian LTS runs until 2028-06-30,
20 months after the change (https://endoflife.date/debian, https://wiki.debian.org/LTS).

Verification (reproducible, evidence in TASK-161):

1. Image check without starting Redis: `docker create` of the pinned reference, then
   `docker cp -L <id>:/etc/os-release -` shows `VERSION_ID="12"`, `VERSION_CODENAME=bookworm`;
   `/etc/debian_version` is `12.15`.
2. Pin check: `python3 infra/check_image_pins.py` exits 0 and `python3 -m unittest discover -s infra/tests`
   passes (11 tests); the two references are identical.
3. Existing volume: with the old image up, `SET cr003:marker ok` on the `redis_data` volume; after the
   image switch, `GET cr003:marker` returns `ok`, `INFO server` has `redis_version:7.4.12` and
   `os:Linux`, `INFO persistence` has `aof_enabled:1`, `loading:0`, `aof_last_write_status:ok`.
4. Session round trip on the real server through `https://localhost`: login 200 with session
   cookie, authenticated `GET /api/v1/me` 200, logout with the CSRF header 204, the same cookie on
   `GET /api/v1/me` 401.
5. `infra/smoke-test.sh` passes 17/17 on the rebuilt Compose stack; the backend suite passes
   (496 tests, coverage 91.7 %).
6. CI on the branch head (`backend-tests` starting the new service container, `image-pins`) is not
   yet run: it needs a push, and TASK-168 checks it.

Anomaly review of the new image: nothing hazard-relevant (SOUP-021). 97 minor, unfixed Debian
base-OS entries are open in the tracker; none can be reached through the Redis protocol.
