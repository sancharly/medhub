---
id: "TASK-155"
type: task
title: "Pin every container image by release tag and digest"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
tags: ["soup", "configuration-management", "regulatory", "cr:CR-001", "issue:sancharly/medhub#26", "control:design"]
---

# TASK-155 — Pin every container image by release tag and digest

- **Software item / unit:** deployment topology (`infra/docker-compose.yml`), SI-API / SI-WORKER
  runtime image (`backend/Dockerfile`), SI-FE-SHELL static image (`frontend/Dockerfile`),
  SI-DEVINFRA `U-INF-CIPipeline` (CI service containers)
- **Depends on:** none (first task of CR-001)
- **Branch:** `bug/soup-pinning`

## Objective

Resolve PRB-001's root defect: every container image is referenced by a moving tag, so the SOUP
records cannot state what is deployed and a release is not reproducible (SR-028 AC-5, RR-010,
IEC 62304 §8.1.2, §5.8.5). Replace every reference with `<repository>:<full release tag>@sha256:<index
digest>` at the version the floating tag resolves to when the pin is made (CR-001 A-4: no
upgrade), use identical references wherever one SOUP item appears more than once, and record each
pinned reference in its `soup` record. This implements RISK-010's design control "every image and
dependency pinned to an immutable version".

## Interfaces to honor

- No runtime behaviour change is intended: same images, same major.minor lines, same configuration.
- The digest is the **multi-arch image index** digest (the `Digest:` line of
  `docker buildx imagetools inspect <ref>`), never a per-platform manifest digest: developers run
  arm64, CI runs amd64.
- Out of scope (CR-001): GitHub Actions tags, `python-version`/`node-version`, `pip install uv`
  (PRB-034); moving off Node 20 (PRB-035). `node:20-slim` is still pinned here (D-3).

## Implementation detail

1. **Resolve each reference.** For each floating tag, read its release version from the image
   config and then the digest of the full-release tag:

   ```sh
   docker buildx imagetools inspect <floating-tag> --format '{{json .Image}}'   # version env (NGINX_VERSION, PG_VERSION, …)
   docker buildx imagetools inspect <repository>:<full-release-tag>             # Digest: line = index digest
   ```

   Confirm the per-platform config of the full-release tag reports the same version as the
   floating tag. Values resolved at the Risk stage on 2026-10-22 (re-resolve; if a digest changed,
   use the new one and say so in the SOUP change log):

   | Floating tag | Pinned reference (2026-10-22) | SOUP |
   |---|---|---|
   | `python:3.12-slim` | `python:3.12.15-slim@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2` | SOUP-001 |
   | `postgres:16` | `postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97` | SOUP-020 |
   | `redis:7-alpine` | `redis:7.4.11-alpine@sha256:892022f9f18c26c92c30e15194d132f90044af87b94a491a75429bbc3982eab1` | SOUP-021 |
   | `nginx:alpine` | `nginx:1.31.8-alpine@sha256:e2d97c2b8c016f12c2f1a27d095685063b2f281c4edf2babfde6001cf4fb77a8` | SOUP-024 |
   | `node:20-slim` | `node:20.20.2-slim@sha256:2cf067cfed83d5ea958367df9f966191a942351a2df77d6f0193e162b5febfc0` | none (A-3, build only) |
   | `minio/minio:latest` | `minio/minio:RELEASE.2025-09-07T16-13-09Z@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e` | SOUP-022 |
   | `minio/mc:latest` | `minio/mc:RELEASE.2025-08-13T08-35-41Z@sha256:a7fe349ef4bd8521fb8497f55c6042871b2ae640607cf99d9bede5e9bdf11727` | SOUP-023 |

   On 2026-10-22, `nginx:alpine` and `nginx:1.31.8-alpine` had the same image config but different
   index digests; pin the **full-release tag's** digest.

   **MinIO:** the registry refused `minio/minio` and `minio/mc` on 2026-10-22 (Docker Hub
   "pull access denied", quay.io 401). The two references above come from the locally cached
   images (`docker image inspect --format '{{json .RepoDigests}}'`, release from
   `minio --version` / `mc --version`) and could not be checked against a registry. Pin them as the
   version in use (A-4, D-4: the component is not changed), and state in SOUP-022/023 that the
   digest is the cached RepoDigest, not registry-verified, and that the image could not be pulled
   on that date. TASK-154 confirms the distribution status and escalates it.
2. **Edit the references.**
   - `infra/docker-compose.yml`: `reverse-proxy`, `postgres`, `redis`, `minio`, `createbuckets`
     `image:` lines.
   - `backend/Dockerfile`: both `FROM python:…` lines (builder and runtime) use the identical
     reference (AC-2).
   - `frontend/Dockerfile`: `FROM node:… AS build` and `FROM nginx:…`. The nginx reference is
     identical to the Compose `reverse-proxy` one (AC-2).
   - `.github/workflows/ci.yml`: `jobs.backend-tests.services.postgres.image` and
     `services.redis.image` use exactly the Compose references (AC-2, A-2).
3. **Update the SOUP records** SOUP-001, SOUP-020, SOUP-021, SOUP-022, SOUP-023, SOUP-024:
   - `soup_version` = the release version only (A-1): `3.12.15`, `16.15`, `7.4.11`,
     `RELEASE.2025-09-07T16-13-09Z`, `RELEASE.2025-08-13T08-35-41Z`, `1.31.8`; body heading
     updated to the same version.
   - Remove the "Floating tag (PRB-001)" note.
   - "Required hardware and software environment": list every full image reference with its
     digest and the file(s) that use it, the base OS of the image (A-5; Debian release for
     `python`/`postgres`, Alpine release for `*-alpine`), and the date and command used to
     resolve it.
   - Leave "Anomaly list review" as it is; TASK-154 performs it against these versions.
   - Change log: `2026-10-22 — <old floating tag> → <pinned reference>; pinned at the version the
     tag resolved to, no upgrade (CR-001 A-4); PRB-001`.
   - Content changes: bump `version` to `1.1`, remove `approved_by`/`approved_on`/
     `approved_digest`/`approval_note`, `status: in_review` at handoff (soup-management).
   - Record convention for CR-001: one version bump per record for the whole CR. TASK-154 adds the
     review under the same `1.1` and extends this change-log entry rather than bumping again.

## Tests (write first)

No code under test: verification is configuration inspection, the pin check of TASK-156 and the
integration run below. Before editing, run the smoke test once on the floating tags and keep the
output, so the pinned run can be compared with it.

## Acceptance criteria

- [x] CR-001 **AC-1**: every Compose `image:` and Dockerfile `FROM` naming an image has the form
      `<repository>:<tag>@sha256:<64 hex>`, tag = full release (`major.minor.patch`, or
      `RELEASE.<timestamp>` for MinIO); no `latest`, no tag without a patch component.
- [x] CR-001 **AC-2**: Python builder and runtime references identical; nginx reverse-proxy and
      frontend runtime references identical; CI `postgres`/`redis` service images identical to the
      Compose services.
- [x] CR-001 **AC-4**: `soup_version` of SOUP-001, SOUP-020..024 equals the release in the pinned
      tag; each body lists every full reference with digest and the file using it; no "Floating
      tag" note remains.
- [x] CR-001 **AC-5**: the pinned stack builds, starts and passes `infra/smoke-test.sh`.
      Met with a recorded deviation: 16/17, with check 9 failing as it does on the floating-tag
      baseline (PRB-037). See "QA review" below. The human acknowledges it at Checkpoint A.

## Verification

```sh
# AC-1 / AC-2: no floating reference remains, duplicates are identical
grep -nE '^\s*(image:|FROM )' infra/docker-compose.yml backend/Dockerfile frontend/Dockerfile .github/workflows/ci.yml
docker compose -f infra/docker-compose.yml config --quiet
# AC-5
docker compose -f infra/docker-compose.yml build
docker compose -f infra/docker-compose.yml up -d
bash infra/smoke-test.sh
docker compose -f infra/docker-compose.yml down
# Regression
cd backend && uv run pytest
cd frontend && npm test -- --run
```

Record in the task body at handoff which host ran AC-5 and whether the MinIO images came from the
local cache (expected, see step 1).

## Definition of Done

- [x] All references pinned; the six SOUP records updated and `in_review`
- [x] Compose build, start and smoke test pass; backend and frontend suites pass (smoke test: AC-5
      deviation, PRB-037)
- [x] `traceability-check` shows no error for the touched records

## Implementation notes and evidence

Handed to QA on 2026-10-22 (status `in_review`). Checkboxes are left for QA.

**Pinned references.** Digests re-resolved on 2026-10-22 with `docker buildx imagetools inspect`;
all equal the planning table, none changed. Redis and PostgreSQL floating and full-release tags
share one index digest; nginx differs (floating `nginx:alpine` = `sha256:060849a1...`), so the
full-release digest is pinned. Python, PostgreSQL, Redis and nginx per-platform configs
(amd64, arm64) report the same version as the floating tag.

| Image | Pinned reference | Files |
|---|---|---|
| Python | `python:3.12.15-slim@sha256:cb33f7f7...611d2` | `backend/Dockerfile` (builder, runtime) |
| PostgreSQL | `postgres:16.15@sha256:9e2cf628...a0a97` | `infra/docker-compose.yml`, `.github/workflows/ci.yml` |
| Redis | `redis:7.4.11-alpine@sha256:892022f9...eab1` | `infra/docker-compose.yml`, `.github/workflows/ci.yml` |
| nginx | `nginx:1.31.8-alpine@sha256:e2d97c2b...b77a8` | `infra/docker-compose.yml`, `frontend/Dockerfile` |
| Node (no SOUP) | `node:20.20.2-slim@sha256:2cf067cf...bfc0` | `frontend/Dockerfile` |
| MinIO | `minio/minio:RELEASE.2025-09-07T16-13-09Z@sha256:14cea493...936e` | `infra/docker-compose.yml` |
| mc | `minio/mc:RELEASE.2025-08-13T08-35-41Z@sha256:a7fe349e...1727` | `infra/docker-compose.yml` |

**AC-5 run.** Host: the reference workstation (macOS, Docker Desktop, arm64), 2026-10-22. The MinIO
images came from the local cache: Compose resolved them by digest without a pull. Docker Hub rate
limited the anonymous pulls of the other images; the run was repeated after the human signed in.
Baseline on the floating tags (before editing): 16 passed, 1 failed. Pinned run: `docker compose
-f infra/docker-compose.yml config --quiet` valid; `up -d --build` built backend, celery-worker and
frontend and started all 7 services on the pinned images; `bash infra/smoke-test.sh`: **16 passed, 1
failed**, the same result as the baseline. The failing check 9 (login endpoint) posts to
`localhost:8000`, a port the stack does not publish (PRB-037); the same request through the proxy
(`https://localhost/api/v1/auth/login`) returns 401, i.e. migrated schema. Running images report
Python 3.12.15, PostgreSQL 16.15, Redis 7.4.11, nginx 1.31.8, MinIO RELEASE.2025-09-07T16-13-09Z.
Stack torn down with `docker compose down` (volumes kept).

**Regression.** `cd backend && uv run pytest`: 495 passed. `cd frontend && npm test -- --run`: 27
files, 155 tests passed.

**Defects found outside this task (PRBs, not fixed):** PRB-037 (smoke test check 9 unreachable,
so AC-5 "passes" cannot be met literally), PRB-038 (`POSTGRES_PASSWORD` missing from
`.env.example`), PRB-039 (`createbuckets` starts before MinIO is ready).

**SOUP records.** SOUP-001, 020, 021, 022, 023, 024 set to `soup_version` = release, version `1.1`,
approval record removed, `in_review`; environment section lists reference, digest and file; change
log entry added; anomaly-review sections untouched for TASK-154. SOUP-022/023 state that the digest
is the cached RepoDigest, not registry-checked, and that AC-5 is reproducible only on a host holding
the images (Q-2).

## QA review (2026-10-22)

**Verdict: APPROVED** (`in_review → approved`). The SOUP records stay `in_review` for the human.

QA re-ran the verification on the reference workstation (macOS, arm64, Docker Hub signed in):

- **AC-1/AC-2.** All 11 `image:`/`FROM` references in the four files have the form
  `<repo>:<full-release>@sha256:<64 hex>`. The duplicates are identical: Python builder and runtime,
  nginx proxy and frontend, CI postgres and redis versus Compose. `docker buildx imagetools inspect`
  returned the pinned OCI index digest for `nginx:1.31.8-alpine`, `postgres:16.15`,
  `redis:7.4.11-alpine`, `python:3.12.15-slim` and `node:20.20.2-slim`. The floating tags report the
  same version env (A-4: no upgrade). Only `nginx:alpine` has a different index digest. MinIO: the
  pinned digests equal the cached `RepoDigests`, and `minio --version` / `mc --version` match the
  pinned releases (Q-2).
- **AC-4.** `soup_version` values are quoted release strings. Each body has the reference, digest
  and files. The floating notes are gone, the version is `1.1`, the approval record is cleared, the
  status is `in_review` and the change log is updated. The base OS claims were checked inside the
  images: Debian 13 for python and postgres, Alpine 3.21 for redis, Alpine 3.24 for nginx.
- **AC-5.** `up -d --build`: all 7 services started on the pinned images and the backend was healthy.
  `infra/smoke-test.sh`: 16 passed, 1 failed (check 9, HTTP 000 on unpublished `localhost:8000`),
  the same as the developer's baseline. Extra probes through the published proxy:
  - login POST returned 401 (schema migrated);
  - `http://` returned 301 to `https://`;
  - the HSTS, `X-Content-Type-Options` and `X-Frame-Options` headers were present;
  - TLS ≤ 1.1 was refused;
  - the running versions match the pins.

  Judgement: AC-5 is met in substance. The pinned stack builds, starts and behaves as the floating
  stack did, and the one failure is a pre-existing script defect that is independent of pinning and
  tracked as PRB-037. Because the approved AC-5 text and Checkpoint A say "passes", the human must
  acknowledge this deviation at Checkpoint A. Alternatively, PRB-037 is fixed before TASK-159 so that
  CR-001's end-to-end verification can show a literal pass. Torn down with `down`, volumes kept.
- **Regression.** Backend `uv run pytest -q`: 495 passed. Frontend `npm test -- --run`: 27 files,
  155 tests passed.
- **PRB-037/038/039.** The records are valid, the claims were checked in the source, and `minor` is
  appropriate. PRB-039's `connection refused` was reproduced in the QA run. All three are outside
  this task.
- **traceability-check** (scope: TASK-155, SOUP-001/020..024, PRB-037..039, CR-001): 0 errors. The
  only warnings are 6 × `soup_anomaly_review_stale`, which are expected until TASK-154. TASK-155's
  `mitigates` RISK-010 reaches TR-001/TR-002 through SR-028.

Non-blocking findings:

- **MEDIUM**: SOUP-022/023 do not name the base OS. The MinIO images are built on Red Hat Universal
  Base Image 9 micro (RHEL 9.6, image label `ubi9-micro-container`). A-5 and step 3 ask for the base OS
  in the environment section. Fix: add "base OS Red Hat Enterprise Linux 9.6 (UBI 9 micro) (A-5)" to
  both records. This can be done before this commit or in TASK-154 under the same `1.1`.
- **LOW**: the SOUP-022/023 change-log entries say "pinned at the version the tag resolved to", but
  for MinIO the registry could not resolve the tag. Fix: say "pinned at the locally cached `latest`
  (registry refused, Q-2)".
- **MEDIUM (outside this task)**: `backend/tests/db/conftest.py:14` and
  `backend/tests/db/test_migration.py:26` start `PostgresContainer("postgres:16")`, a floating tag. The
  DB and migration tests therefore do not run against the shipped SOUP-020 version (contrary to the
  A-2 rationale). Neither AC-1/AC-3 nor PRB-034 covers this. Fix: raise a PRB, and pin to the Compose
  reference in a later task or CR.
