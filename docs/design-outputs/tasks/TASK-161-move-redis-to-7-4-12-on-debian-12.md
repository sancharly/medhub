---
id: "TASK-161"
type: task
title: "Move Redis to 7.4.12 on Debian 12, pinned by tag and digest"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-29"
links:
  - target: "SR-028"
    relation: implements
  - target: "SR-030"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-003"
    relation: relates_to
  - target: "PRB-045"
    relation: relates_to
  - target: "SOUP-021"
    relation: relates_to
  - target: "RISK-005"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "RISK-009"
    relation: relates_to
tags: ["soup", "maintenance", "configuration-management", "cr:CR-003", "issue:sancharly/medhub#32", "control:design", "control:protective"]
---

# TASK-161 — Move Redis to 7.4.12 on Debian 12, pinned by tag and digest

- **Software item / unit:** deployment topology (`infra/docker-compose.yml`, service `redis`);
  SI-AUTH `U-AUTH-Session` (ADD-006, SR-030) and SI-WORKER broker (ADD-017) run on it;
  SI-DEVINFRA `U-INF-CIPipeline` (ADD-024, the `backend-tests` service container)
- **Depends on:** none. This is the first task of CR-003, as Q-1 requires.
- **Branch:** `bug/soup-upgrades`
- **Size:** M
- **Needs:** a Docker host (image inspection, Compose run, existing-volume check) and network
  access (Docker Hub, OSV, the Debian security tracker, Redis advisories)

## Objective

Resolve PRB-045. The pinned Redis image is built on Alpine 3.21, which reaches end of support on
2026-11-01. Upstream builds Redis 7.4 on Alpine 3.21 only, so the human chose the official Debian
12 variant (CR-003 D-1).

- Move both references to `redis:7.4.12-bookworm` pinned by digest.
- Re-review SOUP-021 at the new version, base-OS packages included.
- Show that the session store and the broker still work on the real server.

This re-implements RISK-010's design control (an immutable, reviewed version) and its
protective control (anomaly review) for SOUP-021.

## Interfaces to honor

- `command: redis-server --appendonly yes` and the `redis_data:/data` volume do not change.
  Neither do the network, the `expose` entry or the restart policy.
- `REDIS_URL=redis://redis:6379/0` and the CI `--health-cmd "redis-cli ping"` do not change.
  `redis-cli` is in the Debian image.
- The digest is the **multi-arch image index** digest (the `Digest:` line of
  `docker buildx imagetools inspect`), never a per-platform digest. Developers run arm64 and CI
  runs amd64.
- Out of scope: Redis 8.x, any other variant, and any Redis configuration change (CR-003
  Boundaries).

## Implementation detail

1. **Resolve and confirm the image.** Value selected on 2026-10-29 (CR-003 "Selected versions"):
   `redis:7.4.12-bookworm@sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5`.
   Re-resolve it. If the digest has changed, use the new one and say so in the SOUP-021 change log.

   ```sh
   docker buildx imagetools inspect redis:7.4.12-bookworm                      # Digest: line
   docker buildx imagetools inspect redis:7.4.12-bookworm --format '{{json .Image}}' | grep -o 'REDIS_VERSION=[^"]*'
   ```

2. **AC-2 evidence without starting Redis.**

   ```sh
   REF='redis:7.4.12-bookworm@sha256:<digest>'
   docker pull "$REF" && cid=$(docker create "$REF")
   docker cp "$cid:/etc/os-release" - | tar -xO          # VERSION_ID="12", VERSION_CODENAME=bookworm
   docker cp "$cid:/etc/debian_version" - | tar -xO      # point release, e.g. 12.x
   docker cp "$cid:/var/lib/dpkg/status" - | tar -xO > "$SCRATCH/redis-dpkg-status"   # for step 5
   docker rm "$cid"
   ```

   Record the Debian support status with the date of the check:
   - regular security support ended 2026-07-11;
   - Debian LTS runs until 2028-06-30.

   The sources are https://www.debian.org/security/, https://wiki.debian.org/LTS and
   endoflife.date/debian.

3. **Edit the two references** so they are identical (AC-1):
   - `infra/docker-compose.yml:84`, the `redis` service `image:`;
   - `.github/workflows/ci.yml`, `jobs.backend-tests.services.redis.image`.

   The Compose comment "Redis 7 (sessions + Celery broker)" stays.

4. **Existing-volume and real-server check** (§7.4.3; CR-003 A-5). Run it on a host whose
   `redis_data` volume was written by the old image.
   1. With the old stack up, write a marker:
      `docker compose -f infra/docker-compose.yml exec redis redis-cli SET cr003:marker ok`.
   2. Switch the image (step 3), then run `docker compose -f infra/docker-compose.yml up -d redis`.
   3. Check:
      - `redis-cli GET cr003:marker` returns `ok`;
      - `redis-cli INFO server` has `redis_version:7.4.12` and `os:Linux`;
      - `redis-cli INFO persistence` has `aof_enabled:1`, `loading:0` and
        `aof_last_write_status:ok`.
   4. Run `DEL cr003:marker`.

   If the AOF does not load, stop and ask. The fallback is to recreate `redis_data` only, which
   needs the human's agreement: the data is sessions and queue state, not PHI.
5. **Session round trip on the real server** (SR-030, RISK-005). The backend suite uses
   fakeredis, so it does not exercise the server.
   1. On the running stack, create a test user with `backend/scripts/setup_test_data.py`. Use
      test credentials generated for this session, and keep them out of the records.
   2. Through `https://localhost`:
      - `POST /api/v1/auth/login` returns 200 and a session cookie;
      - an authenticated `GET /api/v1/me` returns 200;
      - `POST /api/v1/auth/logout`, with the CSRF header that CSRF enforcement requires, returns
       204;
      - the same cookie on `GET /api/v1/me` returns 401.
   3. Record the status codes in the evidence.
6. **SOUP-021**. It is approved, so bump `version` to 1.3, remove the approval record and set
   `in_review`.
   - `soup_version: "7.4.12"`, and update the heading.
   - **Environment section:**
     - the full reference with its digest and both files that use it;
     - the base OS, "Debian GNU/Linux 12 (bookworm), point release <from step 2>": regular
       security support ended 2026-07-11, Debian LTS until 2028-06-30 (D-1), with the sources;
     - the variant change from Alpine 3.21 (CR-003 D-1) and the reason for it;
     - a note that upstream rebuilt `redis:7.4.11-alpine` under the same tag on 2026-10-26 (CR-003
       observation).

     No sentence may still state Alpine 3.21 or 7.4.11 as current (AC-13).
   - **Anomaly list review**, dated on or after 2026-10-29, at 7.4.12 and the pinned digest (AC-14).
     Cite each source by name and URL:
     - Redis GitHub Security Advisories and the 7.4.12 release notes;
     - NVD (keyword `redis`, published since the last review);
     - **OSV, ecosystem `Debian:12`**, for every source package in the copied `dpkg/status` at
       its installed version (`api.osv.dev/v1/querybatch`, as TASK-154 did for Alpine);
     - the Debian security tracker (https://security-tracker.debian.org/tracker/) for anything OSV
       reports;
     - `debian-security-support`'s lists of packages with limited or ended support
       (https://salsa.debian.org/debian/debian-security-support, `security-support-limited` and
       `security-support-ended.deb12`), checked against the installed packages;
     - the Debian LTS advisories (DLA) list.

     List each applicable anomaly with a hazard-relevance judgement, or state "none found". Show
     the PRB-045 end-of-support finding as cleared.
   - Set `anomaly_review` to the review date.
   - Change-log entry: `2026-10-29 — 7.4.11 (redis:7.4.11-alpine, Alpine 3.21) →
     7.4.12 (redis:7.4.12-bookworm@sha256:…, Debian 12); PRB-045, CR-003 (D-1)`.
   - Hazard-relevant findings become RISK records, and MedHub-affecting defects become PRBs. Add
     each one to CR-003 "Escalations" (AC-14).
7. **PRB-045** → `status: resolved`, `version: "1.2"`, with a `## Resolution`. It names:
   - the changed files (`infra/docker-compose.yml`, `.github/workflows/ci.yml`, SOUP-021);
   - the selected image and the D-1 decision;
   - the reproducible verification (steps 2, 4 and 5, the pin check, and CI).

## Acceptance criteria

- [x] CR-003 **AC-1**: both references are the identical `redis:7.4.12-bookworm@sha256:<64 hex>`.
      No `7-alpine`, `7.4-alpine`, `7`, `7.4`, `bookworm` or `latest` reference remains.
- [x] CR-003 **AC-2**: `/etc/os-release` read from the pinned image shows Debian 12 bookworm.
      The support status (Debian LTS until 2028-06-30) is recorded with sources and the date of
      the check.
- [x] CR-003 **AC-13** and **AC-14** for SOUP-021, as in step 6.
- [x] CR-003 **AC-17** (Redis part): the running container reports 7.4.12, an existing
      `redis_data` volume loads, and the session round trip passes.
- [x] CR-003 **AC-19** (PRB-045 part): PRB-045 is `resolved` with its `## Resolution`.

## Verification

```sh
python3 infra/check_image_pins.py                                    # exit 0 (AC-16)
python3 -m unittest discover -s infra/tests -v
grep -n 'redis:' infra/docker-compose.yml .github/workflows/ci.yml   # identical references
docker compose -f infra/docker-compose.yml build && docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml exec redis redis-cli INFO server | grep redis_version
bash infra/smoke-test.sh                                             # 17/17
cd backend && uv run pytest                                          # regression
```

Steps 2, 4 and 5 above are recorded with their output. CI on the branch head: `backend-tests`
starts the new service container, and `image-pins` passes.

## Definition of Done

- [x] The pin check and its unit tests pass. The backend suite passes with coverage ≥ 85 %.
- [x] SOUP-021 is `in_review` and PRB-045 is `resolved`.
- [x] `traceability-check` shows no error for the touched records.

## Implementation evidence

Done 2026-10-29 on the reference workstation (Docker Desktop, `desktop-linux` context, arm64) by
the Software Developer role. Status `in_review` for QA. The acceptance checkboxes above are left
for QA.

**Digest (step 1).** `docker buildx imagetools inspect redis:7.4.12-bookworm` returned
`Digest: sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5` (media type
`application/vnd.oci.image.index.v1+json`) and `REDIS_VERSION=7.4.12`. It equals the digest in
CR-003 "Selected versions", so nothing changed. Pinned reference:
`redis:7.4.12-bookworm@sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5`.

**Image evidence (step 2, AC-2).** Pulled by digest, then `docker create` and `docker cp`, without
starting Redis. `/etc/os-release` is a symlink, so `docker cp -L` (or `/usr/lib/os-release`) is
needed to read it:

```
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"   VERSION_ID="12"   VERSION_CODENAME=bookworm
/etc/debian_version: 12.15
```

Support status (checked 2026-10-29, endoflife.date/debian API): bookworm `support: 2026-07-11`,
`eol: 2028-06-30`, latest point release 12.15 (2026-07-11). Also https://wiki.debian.org/LTS and
https://www.debian.org/security/. `/var/lib/dpkg/status` was copied for the SOUP review (89 binary
packages, 64 source packages).

**Edits (step 3, AC-1).** `infra/docker-compose.yml:84` and `.github/workflows/ci.yml:64` hold the
identical reference above. Nothing else in either file changed.

```
$ grep -n 'image: redis' infra/docker-compose.yml .github/workflows/ci.yml
infra/docker-compose.yml:84:    image: redis:7.4.12-bookworm@sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5
.github/workflows/ci.yml:64:        image: redis:7.4.12-bookworm@sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5
$ python3 infra/check_image_pins.py          -> exit 0
$ python3 -m unittest discover -s infra/tests -v   -> Ran 11 tests ... OK
```

**Existing-volume check (step 4, AC-17).** The Compose volume `infra_redis_data` was created on
2026-06-20 and holds an AOF written by earlier images (files owned by uid 999, gid 1000). Run with
the old reference first, then the new one, via `docker compose -f infra/docker-compose.yml up -d redis`:

| Step | Result |
|---|---|
| Old image: `INFO server` / `/etc/alpine-release` | `redis_version:7.4.11`, Alpine `3.21.9` |
| Old image: `DBSIZE`, `SET cr003:marker ok`, `GET cr003:marker` | `1`, `OK`, `ok` |
| Switch to the new reference, recreate `redis` | container recreated |
| New image: `GET cr003:marker` | `ok` |
| New image: `DBSIZE` | `2` (the one existing key plus the marker) |
| `INFO server` | `redis_version:7.4.12`, `os:Linux 5.15.49-linuxkit-pr aarch64` |
| `INFO persistence` | `aof_enabled:1`, `loading:0`, `aof_last_write_status:ok` |
| `/etc/os-release` read inside the running container | `Debian GNU/Linux 12 (bookworm)`; `redis` is uid 999, gid 999 |
| `/data` after the switch | still `redis`-owned (uid 999), group gid 1000, modes 600 / 700 |
| `DEL cr003:marker`, `DBSIZE` | `1`, `1` (back to the original key) |

The AOF loaded without the fallback. An earlier first pass of this check lost its `GET` to a
quoting mistake in the command, so the marker was written and checked again from the old image,
as recorded above. `docker compose` printed a warning that `POSTGRES_PASSWORD` is unset in
`infra/.env` (blank default); it is unrelated to this task.

**Session round trip (step 5, SR-030, RISK-005).** On the rebuilt stack (`docker compose build`
then `up -d`, all seven services up, `backend` healthy), with a test patient account
`cr003-roundtrip@example.invalid` and a password generated for the run (not recorded here), through
`https://localhost` with `curl -k`:

| Request | Status |
|---|---|
| `POST /api/v1/auth/login` | 200 (cookies `medhub_session`, `medhub_csrf`) |
| `GET /api/v1/me` with the session cookie | 200 |
| `POST /api/v1/auth/logout` with `X-CSRF-Token` equal to the `medhub_csrf` cookie | 204 |
| `GET /api/v1/me` with the cookie saved before logout | 401 |
| Negative control: `POST /api/v1/auth/logout` on a fresh login without the CSRF header | 403 |

The test account was removed from the database afterwards (`account` count back to 6, as before).

Deviation: `backend/scripts/setup_test_data.py` cannot create or update an account, because it calls
`datetime.now(datetime.UTC)` on the class (`AttributeError`, reproduced). It also hard-codes its
passwords and needs an existing SYSADMIN. The account was created with the script's own
`create_patient` and `set_password` functions, with `datetime` replaced in memory by a subclass
that has `UTC`, and a generated password. The script file was not edited (outside this task). Raised as
[PRB-049](../../problem-reports/PRB-049-setup-test-data-script-fails-on-datetime-utc.md) (minor)
and listed in CR-003 "Escalations". A first run created the account and logged in, but the cookie
jar was overwritten at logout, so the last check could not use the earlier cookie. The flow was run again from a clean login with a
new password; the table above is that second, complete run.

**Smoke test and regressions.**

```
$ bash infra/smoke-test.sh      -> === Results: 17 passed, 0 failed ===
$ cd backend && uv run pytest --cov=app --cov-fail-under=85
  -> 496 passed, 50 warnings; total coverage 91.71 % (required 85 %)
```

**SOUP-021 (step 6, AC-13, AC-14).** Rewritten and left `in_review`, version 1.3:
`soup_version: "7.4.12"`, `anomaly_review: "2026-10-29"`, the approval record removed, the full
reference with digest and both files, the Debian 12.15 base OS with support dates and sources, the
variant change, the 2026-10-26 upstream rebuild note, the anomaly review with each source named
with its URL, and the change-log entry. Review result: no hazard-relevant finding.

- Redis: CVE-2026-92925 and GHSA-2r7g-8hpc-rpq9 carry forward (not affecting MedHub). NVD lists
  7.4.12 in range for CVE-2026-23479, CVE-2026-23631 and CVE-2026-25243; the vendor release notes
  fix them in 7.4.9, so they do not apply. NVD has nothing new for Redis since 2026-10-22.
- Debian 12.15 base OS: OSV `Debian:12` returned 97 entries for 24 of the 64 source packages, none
  with a fix in bookworm, all minor or unassigned and none reachable through the Redis protocol.
  The newest bookworm DLAs for installed packages (openssl, perl, pcre2, xz-utils) are in the
  image; tzdata is one data release behind (no CVE). `debian-security-support` limited and ended
  lists match no installed package.
- Escalations: none (no RISK, no PRB for SOUP-021).

**PRB-045** is `resolved`, version 1.2, with its `## Resolution`. Not run here: CI on the branch
head (`backend-tests` with the new service container, `image-pins`) needs a push; TASK-168 checks it.

**Other places that still show the old image** and were left unchanged because they are historical
records or test fixtures: TASK-154, TASK-155, TASK-156 and CR-001 text, `ADD-004-soup-list.md`
(superseded list that names `redis:7-alpine`), and the `infra/tests/fixtures/*` files that use
`redis:7.4.11-alpine@sha256:aaaa…` as a synthetic pinned example.

## QA review (2026-10-29)

**Verdict: APPROVED** (`in_review → approved`). No CRITICAL, HIGH or MEDIUM finding. QA re-ran each
claim independently on the reference workstation (`desktop-linux` context, arm64).

### Findings

- **[LOW] PRB-045 Investigation still says the workstation has no container runtime.**
  `docs/problem-reports/PRB-045-redis-image-base-os-end-of-support.md:60-62` ("`/etc/alpine-release`
  was not read again: this workstation has no container runtime"). TASK-161 step 4 later read
  Alpine `3.21.9` from the old image on this workstation. Fix: add "Superseded by TASK-161: Alpine
  3.21.9 confirmed from the old pinned image on 2026-10-29" to that paragraph at the next PRB-045 edit.
- **[LOW] PRB-049 cites the wrong line for the import.**
  `docs/problem-reports/PRB-049-setup-test-data-script-fails-on-datetime-utc.md:19` says
  `from datetime import datetime` is at line 5. It is at `backend/scripts/setup_test_data.py:6`.
  Fix: change "line 5" to "line 6".

### Observations (not findings)

- **CI on the branch head was not run.** This is accepted for task approval. The task's own ACs
  (AC-1, AC-2, AC-13, AC-14, AC-17 part, AC-19 part) do not include AC-18, and CR-003 assigns
  AC-18 to TASK-168. The commit has to exist before CI can run. To reduce the gap, QA ran the
  **amd64** manifest of the pinned index (`sha256:a7aad825…c42c`, the one GitHub runners pull) under
  emulation: `uname -m` = `x86_64`, `redis-cli ping` = `PONG` (the CI `--health-cmd`),
  `redis_version:7.4.12`. TASK-168 must still show `backend-tests` and `image-pins` green.
- **The base-OS review is adequately reasoned. It needs no RISK record.** QA re-queried OSV
  `Debian:12` for the 64 source packages in the pinned image's `dpkg/status`. The result matches
  the record exactly: 24 packages, 97 entries, none with a `fixed` event for Debian 12. The
  urgencies are 59 not yet assigned, 37 unimportant and 1 low. Every path to these entries starts
  with code execution or a local account inside the container. Redis clients reach only
  `redis-server` over the internal `medhub` network, with no TLS and no cluster mode. RISK-010
  ("pinning delays security patches") already covers SOUP base-OS exposure. For the human approving
  SOUP-021:
  - The glibc and OpenSSL judgements come from advisory text, not a code audit. The record says so.
  - 51 of the 97 entries have no bookworm triage note yet.
  - The next review should diff against this list. SOUP-021 asks for that.
- **Traceability W5 after approval.** TASK-161 (`approved`) has a `relates_to` link to SOUP-021,
  which stays `in_review` (CR-003 AC-19). W5 is expected until the human approves SOUP-021.

### Verification run (QA, 2026-10-29)

| Check | Result |
|---|---|
| `grep -n 'redis:' infra/docker-compose.yml .github/workflows/ci.yml` | `:84` and `:64` are identical, `redis:7.4.12-bookworm@sha256:b6b6e3dc…82f5`. The diff touches only those two lines. No other Compose, CI, Dockerfile or testcontainers Redis image reference exists |
| `python3 infra/check_image_pins.py` | exit 0 |
| `python3 -m unittest discover -s infra/tests` | 11 tests OK |
| `docker buildx imagetools inspect redis:7.4.12-bookworm` | `Digest: sha256:b6b6e3dc…82f5`, OCI image index (amd64, arm64/v8, arm/v7, 386, ppc64le), `REDIS_VERSION=7.4.12` |
| `docker create` + `docker cp -L` of the pinned reference | `Debian GNU/Linux 12 (bookworm)`, `VERSION_ID="12"`, `VERSION_CODENAME=bookworm`; `/etc/debian_version` 12.15; 89 binary and 64 source packages |
| Running stack `infra-redis-1` | Image `redis:7.4.12-bookworm@sha256:b6b6e3dc…82f5`; `redis_version:7.4.12`, `aof_enabled:1`, `loading:0`, `aof_last_write_status:ok`; `cr003:marker` is gone |
| Independent AOF upgrade check on a scratch volume (old pinned 7.4.11-alpine writes a string, a string with `EX 3600` and a list; 7.4.12-bookworm restarts on the same volume) | Every key loads, TTL kept (3597), list intact, `aof_last_write_status:ok`. The files stay uid 999 / gid 1000, mode 600. The scratch volume was removed |
| Session round trip through `https://localhost` (temporary patient account created with the application's own hasher and deleted afterwards; account count 6 → 7 → 6) | login 200 (`medhub_session`, `medhub_csrf`), `GET /me` 200, logout without the CSRF header 403, logout with `X-CSRF-Token` 204, the pre-logout cookie on `GET /me` 401. The session key is gone from Redis (`REDIS_URL=redis://redis:6379/0`) |
| `bash infra/smoke-test.sh` | 17 passed, 0 failed |
| `cd backend && uv run pytest --cov=app --cov-fail-under=85` | 496 passed, 91.71 % |
| OSV `Debian:12` querybatch and a `/v1/vulns` lookup per entry | 24 / 97 / 0 fixed, matching SOUP-021 |
| `backend/scripts/setup_test_data.py:6,76,100,126` | PRB-049 defect confirmed. `git status` shows no change under `backend/`, so there was no silent fix |
| `traceability-check` (fallback parser) scoped to TASK-161, SOUP-021, PRB-045, PRB-049 and CR-003 | 0 errors; 6 × W5 (approved ADD-006, ADD-017, RISK-005, RISK-007, RISK-009 and RISK-010 → `in_review` SOUP-021, expected under CR-003 AC-19). Whole project: 0 errors, 7 × W5, plus `soup_without_risk` on SOUP-033 (TASK-165 scope) |
