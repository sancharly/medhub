---
id: "TASK-164"
type: task
title: "Upgrade anyio to 4.14.2 and urllib3 to 2.8.0"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-29"
links:
  - target: "SR-028"
    relation: implements
  - target: "SR-031"
    relation: implements
  - target: "SR-013"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-003"
    relation: relates_to
  - target: "PRB-047"
    relation: relates_to
  - target: "TASK-163"
    relation: relates_to
  - target: "SOUP-003"
    relation: relates_to
  - target: "SOUP-019"
    relation: relates_to
  - target: "RISK-005"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
tags: ["soup", "maintenance", "security", "cr:CR-003", "issue:sancharly/medhub#32", "control:protective"]
---

# TASK-164 — Upgrade anyio to 4.14.2 and urllib3 to 2.8.0

- **Software item / unit:** SI-API middleware chain (ADD-005; `SecurityHeadersMiddleware` and
  `CsrfEnforcementMiddleware` on Starlette `BaseHTTPMiddleware`, which runs on anyio); SI-ATTACH
  object-storage path (ADD-012; boto3/botocore over urllib3); SI-DEVINFRA `U-INF-Toolchain`
  (`backend/uv.lock`)
- **Depends on:** TASK-163, which changes the same lock file and must be merged first
  (`relates_to`)
- **Branch:** `bug/soup-upgrades`
- **Size:** M
- **Needs:** a Docker host (the AC-8 image check and the attachment round trip on the Compose
  stack) and network access (PyPI, OSV, GitHub Advisory Database, NVD)

## Objective

Complete PRB-047 by moving the two transitive packages to the releases that fix its advisories
(CR-003 D-3):

- anyio 4.14.0 → **4.14.2**, pinned explicitly. 4.14.2 is the smallest move that fixes the
  advisories, so do not let the resolver pick 4.15.1.
- urllib3 2.7.0 → **2.8.0**.

Then re-review SOUP-003 and SOUP-019 at the new versions, run the AC-8 check on the built image
(D-4), and resolve PRB-047.

## Interfaces to honor

- Neither package is declared in `backend/pyproject.toml`, and neither gets a declaration. They
  stay transitive (A-4). `soup_version` of SOUP-003 (Starlette 1.3.1) and SOUP-019 (boto3
  1.43.117) stays, unless the lock changes those packages too (AC-13).
- Lock scope (AC-7, Boundaries): only `anyio` and `urllib3` change, plus any package that the new
  versions require, each named with its old and new versions.

## Implementation detail

1. Run:

   ```sh
   cd backend && uv lock --upgrade-package anyio==4.14.2 --upgrade-package urllib3==2.8.0
   ```

   Inspect `git diff backend/uv.lock`: only `anyio` (4.14.0 → 4.14.2) and `urllib3`
   (2.7.0 → 2.8.0) may change. `idna` 3.18 and `typing-extensions` 4.15.0 stay unless anyio 4.14.2
   requires otherwise. Revert any other change and constrain the resolution. Then run
   `uv lock --check`.
2. Run `uv sync --frozen`, then the full suite. TS-011 checks the headers and CSRF over the anyio
   middleware path. TS-007 TC-007.5 checks that the object-storage client is built from the
   declared SDK.
3. **AC-8, all three packages, on the built image (D-4, run once).**

   ```sh
   docker build -t medhub-backend:ci ./backend
   docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.metadata as m; print({p: m.version(p) for p in ('anyio','urllib3','cryptography')})"
   ```

   The expected output is `{'anyio': '4.14.2', 'urllib3': '2.8.0', 'cryptography': '50.0.2'}`.
   Record it in the evidence, and add it to the next TR. The CI step "Check production dependency
   set" is not changed (D-4).
4. **Attachment round trip on the real object store** (§7.4.3; RISK-007, RISK-011). No CI test
   reaches MinIO (PRB-036), so do this on the Compose stack at Checkpoint A, with the user created
   in TASK-161 or a new test user:
   - upload an attachment to a clinical entry through `https://localhost`;
   - download it, and check that the bytes are identical;
   - record the HTTP statuses.

   This confirms that the SSE request path still works over urllib3 2.8.0. End-to-end proof of
   SSE on the stored object stays PRB-036's.
5. **SOUP-003.** It is approved, so set `version` 1.2, remove the approval record and set
   `in_review`.
   - In the body, anyio is 4.14.2, plus any other transitive version that step 1 changes. No
     sentence states 4.14.0 as current.
   - **Anomaly list review**, dated on or after 2026-10-29, for Starlette 1.3.1 with anyio 4.14.2
     and idna. Use OSV (PyPI), the GitHub Advisory Database, NVD and the anyio version history
     (https://anyio.readthedocs.io/en/stable/versionhistory.html), by name and URL. Show
     GHSA-3w57-8xmc-8v26, GHSA-5p39-cfhj-2xmp and GHSA-82r6-8w77-94w6 as fixed at 4.14.2.
   - Set `anomaly_review`.
   - Change-log entry `2026-10-29 — anyio 4.14.0 → 4.14.2 (transitive); Starlette 1.3.1 unchanged; PRB-047, CR-003 (D-3)`.
6. **SOUP-019.** It is approved, so set `version` 1.3, remove the approval record and set
   `in_review`.
   - In the body, urllib3 is 2.8.0. No sentence states 2.7.0 as current.
   - **Anomaly list review**, dated on or after 2026-10-29, for boto3 1.43.117 with botocore,
     s3transfer, jmespath and urllib3 2.8.0. Use the same sources, plus the urllib3 `CHANGES.rst`.
     Show GHSA-8988-9cw3-xx77, GHSA-vxq7-64xx-v4gw and GHSA-gh4c-6fx4-qh6g as fixed at 2.8.0.
     Note the 2.8.0 HTTPS-proxy behaviour change as not applicable, because no proxy is
     configured.
   - Set `anomaly_review`.
   - Change-log entry `2026-10-29 — urllib3 2.7.0 → 2.8.0 (transitive); boto3 1.43.117 unchanged; PRB-047, CR-003 (D-3)`.
7. **PRB-047** → `status: resolved`, `version: "1.2"`, with a `## Resolution`. It covers both
   tasks: the lock diff of TASK-163 and of this task, the KAT (TC-008.5), the AC-8 output, the
   suites and the SOUP reviews.
8. **CR-003 Escalations**: add any finding of steps 5 and 6, or "none" for SOUP-003 and SOUP-019.

## Acceptance criteria

- [ ] CR-003 **AC-7**: `uv.lock` resolves anyio 4.14.2, urllib3 2.8.0 and cryptography 50.0.2, and
      `uv lock --check` succeeds. Across TASK-163 and this task, no other package changes, or each
      one is named with its old and new versions and covered by AC-14.
- [ ] CR-003 **AC-8**: the built backend image reports the three AC-7 versions (step 3).
- [ ] CR-003 **AC-13** and **AC-14** for SOUP-003 and SOUP-019, as in steps 5 and 6.
- [ ] CR-003 **AC-19** (PRB-047 part): PRB-047 is `resolved` with its `## Resolution`.

## Verification

```sh
cd backend && uv lock --check && git diff --stat uv.lock
cd backend && uv sync --frozen && uv run pytest --cov=app --cov-fail-under=85
cd backend && uv run ruff check . && uv run black --check . && uv run mypy app
docker build -t medhub-backend:ci ./backend && docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.metadata as m; print({p: m.version(p) for p in ('anyio','urllib3','cryptography')})"
docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"   # the CI step, unchanged
```

Step 4 (the attachment round trip) is recorded at Checkpoint A.

## Definition of Done

- [ ] The backend suite passes with coverage ≥ 85 %, and the CI jobs are green.
- [ ] SOUP-003 and SOUP-019 are `in_review`, and PRB-047 is `resolved`.
- [ ] `traceability-check` shows no error for the touched records.
