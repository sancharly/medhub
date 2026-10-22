---
id: "PRB-001"
type: problem-report
title: "Container images use floating tags, so builds are not reproducible"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-22"
criticality: major
links: []
tags: ["soup", "regulatory", "configuration-management"]
---

# PRB-001 — Container images use floating tags

## Observed

Every container image is referenced by a moving tag rather than a unique designation:

- `infra/docker-compose.yml`: `minio/minio:latest`, `minio/mc:latest`, `nginx:alpine`,
  `redis:7-alpine`, `postgres:16`
- `backend/Dockerfile`: `python:3.12-slim` (builder and runtime stages)
- `frontend/Dockerfile`: `node:20-slim` (build stage), `nginx:alpine` (runtime)

Two identical `docker compose up` runs on different days can therefore produce different software.

## Impact

- **IEC 62304 §8.1.2** requires each SOUP item to carry a unique designation (exact version).
  `latest` and `alpine` are not versions, so the container SOUP records (SOUP-001, SOUP-020..024 in
  [`../soup/`](../soup/)) cannot state what is actually deployed.
- **§5.8.5–5.8.7** require the released software to be reproducible and archived. A floating tag
  breaks that claim for a release.
- **§7.1.2** anomaly review is meaningless against a version that can change without notice, and a
  silent MinIO or nginx upgrade can invalidate a verified risk control (TLS/HSTS headers, SSE-AES256).
- No patient-facing failure has been observed; this blocks a release claim, not current use, hence
  `major` rather than `critical`.

## Investigation

The Docker Compose topology and Dockerfiles were written in phase 0 (TASK-004) for local
development convenience, before a SOUP list existed to require exact versions. Nothing in the
repository checked an image reference afterwards, so the floating tags stayed. The references, as
of commit `0fba8af` (before CR-001):

- `infra/docker-compose.yml:20` (`nginx:alpine`), `:69` (`postgres:16`), `:84` (`redis:7-alpine`),
  `:96` (`minio/minio:latest`), `:114` (`minio/mc:latest`)
- `backend/Dockerfile:1` and `:9` (`python:3.12-slim`)
- `frontend/Dockerfile:1` (`node:20-slim`) and `:11` (`nginx:alpine`)
- `.github/workflows/ci.yml:47` (`postgres:16`) and `:60` (`redis:7-alpine`), the CI service
  containers, which the Observed list above did not name

Two defects, therefore: the references themselves (fixed by TASK-155), and the absence of any
control that stops a floating reference from returning (fixed by TASK-156).

## Safety evaluation

No hazard is realized. The hazard is indirect: an unreviewed upgrade of nginx (TLS termination,
security headers) or MinIO (server-side encryption) could weaken a risk control without anyone
noticing. RISK-010 assesses that hazard; its control table names this PRB's resolution as the
implementation of "every image and dependency pinned to an immutable version", and SR-028 AC-5
(exact versions, images pinned by tag and digest, CI failing on an unpinned reference) is the
requirement that now covers it. No data integrity, safety-related function or clinical decision is
affected, which supports `major` rather than `critical`. No `release` record exists
(`docs/releases/` is absent), so no released version in use is affected and no notification is
needed (§9.3).

## Resolution

Resolved by CR-001 (`resolves` link on the CR), in two tasks on branch `bug/soup-pinning`:

1. **Pinning (TASK-155, commit `a2b3dee`).** Every reference above is now
   `<repository>:<full release tag>@sha256:<index digest>`: `infra/docker-compose.yml`,
   `backend/Dockerfile`, `frontend/Dockerfile` and the CI service containers in
   `.github/workflows/ci.yml`. Duplicated SOUP items use identical references. SOUP-001 and
   SOUP-020..024 record the release version, the full references with digests and the files that use
   them. The pins record the version in use when the change was made; no component was upgraded
   (CR-001 A-4).
2. **Pin check (TASK-156).** `infra/check_image_pins.py` (Python standard library only) fails,
   naming `file:line`, for any Compose `image:`, Dockerfile `FROM` (earlier stages and `scratch`
   excepted) or workflow `services.*.image`, `container.image` or `container: <ref>` value, or an empty `image:`, without `@sha256:<64 hex>`. It
   runs on every push and pull request as the `image-pins` job of `.github/workflows/ci.yml`
   (ADD-024 `U-INF-CIPipeline`). Tests: `infra/tests/test_check_image_pins.py` with fixtures in
   `infra/tests/fixtures/`.

Approach: the digest is the immutable designation §8.1.2 asks for and keeps the build reproducible
(§5.8.5); the check keeps it that way. The tag stays in the reference so that the version is
readable.

Verification (TS-013, [TC-013.5 and TC-013.6](../design-outputs/tests-specifications/TS-013-lifecycle-record-and-traceability.md)),
reproducible from the repository root:

```sh
python3 -m unittest discover -s infra/tests -v   # TC-013.6: 9 tests, OK
python3 infra/check_image_pins.py; echo "exit=$?" # TC-013.5: no output, exit=0
sed -i.bak 's/@sha256:[0-9a-f]*//' infra/docker-compose.yml
python3 infra/check_image_pins.py; echo "exit=$?" # exit=1, five lines "infra/docker-compose.yml:<line>: image reference without @sha256 digest: <ref>"
mv infra/docker-compose.yml.bak infra/docker-compose.yml
```

The AC-5 smoke run of the pinned stack (CR-001 AC-5, TASK-155): `docker compose build`, `up -d` and
`bash infra/smoke-test.sh` gave 16 passed and 1 failed, identical to the floating-tag baseline; the
failing check is PRB-037, independent of pinning. The `image-pins` job on the branch head is
confirmed after the push (not run locally; GitHub Actions cannot be run here).

Not covered by this fix: the PostgreSQL image started by the database tests
(`backend/tests/db/conftest.py:14`, `backend/tests/db/test_migration.py:26`) is outside the files
the check scans; tracked as PRB-040.
