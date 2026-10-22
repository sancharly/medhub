---
id: "TASK-157"
type: task
title: "Declare boto3 as a required runtime dependency"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
links:
  - target: "SR-013"
    relation: implements
  - target: "SR-028"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
tags: ["soup", "configuration-management", "cr:CR-001", "issue:sancharly/medhub#26", "control:design"]
---

# TASK-157 — Declare boto3 as a required runtime dependency

- **Software item / unit:** SI-ATTACH (`ObjectStorageClient`, `U-ATT-Upload`, `U-ATT-Fetch`,
  ADD-012); SI-DEVINFRA `U-INF-Toolchain`, `U-INF-CIPipeline` (ADD-024)
- **Depends on:** none. It can run in parallel with TASK-155/156 (no shared files except
  `.github/workflows/ci.yml`, in a different job). It must merge before TASK-158, which edits the
  same manifest, lock file and CI step.
- **Branch:** `bug/soup-pinning`

## Objective

Resolve PRB-002: `ObjectStorageClient` imports `boto3`, which no manifest declares, so attachment
storage (SR-013 AC-3) fails in every environment built from the declared dependencies and SOUP-019
has no version. Declare `boto3` as a required runtime dependency, lock it, and prove in CI that the
production dependency set can import and instantiate the client. This implements RISK-007's
control "object storage dependency declared and verified", which lists the PRB-002 resolution as
its implementer.

## Interfaces to honor

- `ObjectStorageClient()` — constructor reads `get_settings()` (`object_store_endpoint`,
  `object_store_access_key`, `object_store_secret_key`, `object_store_bucket`). Unchanged.
- `boto3.client("s3", …)` creates no network connection, so the test needs no reachable endpoint
  (CR-001 AC-7). CI has no MinIO service and none is added.
- Not an optional extra and not a dependency group (CR-001 scope item 4).

## Implementation detail

- `backend/pyproject.toml`: add `"boto3>=<locked major.minor>"` to `[project] dependencies`, the
  same lower-bound style as the other entries.
- `cd backend && uv lock` — **without** `--upgrade`, so existing pins stay. Inspect
  `git diff backend/uv.lock`: only `boto3`, `botocore`, `s3transfer` and `jmespath` (and any
  transitive package not yet locked) may be added; `urllib3` (2.7.0) and `python-dateutil` are
  already locked and must keep their versions. Any other version change is out of scope (CR-001
  A-4): revert it and constrain the resolution instead.
- `backend/app/core/object_storage.py`: correct the module docstring, which says boto3 is optional.
  Keep the lazy import and the `ImportError`. They are harmless, and `deps.py` and
  `routers/attachments.py` import the module lazily.
- New test `backend/tests/test_object_storage.py`:
  - `get_settings.cache_clear()` before and after (it is an `lru_cache`); the autouse fixture in
    `tests/conftest.py` provides the `OBJECT_STORE_*` variables.
  - Instantiate `ObjectStorageClient()` with **no** patch, stub, `importorskip` or `sys.modules`
    entry for `boto3` (CR-001 AC-7). Assert `client._bucket == "medhub"` and that
    `client._client.meta.endpoint_url` equals the test endpoint, so the real SDK built a real S3
    client.
- `.github/workflows/ci.yml`, job `build`: after "Build backend image", add the step
  "Check production dependency set":
  `docker run --rm --entrypoint python medhub-backend:ci -c "import boto3"`. The image is built
  with `uv sync --frozen --no-dev`, so this is the CR-001 AC-8 check, run in CI on every pull
  request (the Plan-stage decision on CR-001's open verification point). TASK-158 extends the
  same step.
- **SOUP-019**: `soup_version` = the locked `boto3` version; heading and title note updated;
  remove the "undeclared" note; environment lists the locked `botocore`, `s3transfer` and
  `jmespath` versions (transitives covered by this record); change log
  `2026-10-22 — undeclared → <version>; declared as a required dependency (PRB-002, CR-001)`.
  `version` 1.1, approval record removed, `in_review`. TASK-154 adds the review under the same 1.1.
- **TS-007** (verifies SR-013; approved, so: `version` 1.1, approval record removed, `in_review`):
  add `TC-007.5` | SR-013 | `backend/tests/test_object_storage.py` | the object-storage client is
  built from the declared SDK | test passes with the real `boto3` import.
- **TS-013** (already at 1.2 from TASK-156): add
  - `TC-013.7` | SR-028 | `uv lock --check` (CI `backend-quality` installs with `--frozen`) |
    every Python runtime dependency, `boto3` included, resolves to one locked version | exit 0;
    `boto3` declared under `[project] dependencies`
  - `TC-013.8` | SR-028 | Docker Build job, step "Check production dependency set" | the
    production image (`uv sync --frozen --no-dev`) contains every runtime SDK the code imports |
    `import boto3` succeeds
- **ADD-024** (already at 1.1 from TASK-156): mention the dependency-set step under
  `U-INF-CIPipeline`.
- **RISK-007** (Q-3 in CR-001; **only if the human approves**): rewrite the control row "Object
  storage dependency declared and verified at startup" to "Object storage SDK declared as a
  required runtime dependency and verified in CI", implemented by TASK-157 (CR-001), verified by
  TS-007 TC-007.5 and TS-013 TC-013.8. Residual unchanged (3 × 2, `alarp`). `version` 1.3,
  approval record removed, `in_review`.
- **PRB-002** → `status: resolved`, `version` 1.1, with `## Resolution`: the changed files, the
  verification (TC-007.5, TC-013.7, TC-013.8), and why the CI-only verification replaces the
  "verified at startup" option in the proposed resolution (the image is built only from the
  frozen lock, so the SDK cannot be missing at startup).

## Tests (write first)

Write `backend/tests/test_object_storage.py` first and run it before changing the manifest: it
must fail with `ImportError` (boto3 not installed in a clean `uv sync --frozen`). After the
dependency is declared and locked, it passes.

## Acceptance criteria

- [ ] CR-001 **AC-6**: `boto3` under `[project] dependencies`; `uv.lock` resolves it to exactly one
      version; `uv lock --check` succeeds; SOUP-019 `soup_version` = locked `boto3`, body records the
      locked `botocore`.
- [ ] CR-001 **AC-7**: the instantiation test runs in CI (`backend-tests`), does not stub the
      import, needs no endpoint, and fails when `boto3` is missing.
- [ ] CR-001 **AC-8**: `import boto3` succeeds in the `--no-dev` environment (CI step and local
      check below).
- [ ] CR-001 **AC-17** (PRB-002 part): PRB-002 `resolved` with its `## Resolution`.

## Verification

```sh
cd backend && uv lock --check
cd backend && uv run pytest tests/test_object_storage.py -v
cd backend && uv run pytest
# AC-8 locally, the same dependency set the Dockerfile installs:
cd backend && UV_PROJECT_ENVIRONMENT="$(mktemp -d)/venv" sh -c 'uv sync --frozen --no-dev && "$UV_PROJECT_ENVIRONMENT/bin/python" -c "import boto3; print(boto3.__version__)"'
docker build -t medhub-backend:ci ./backend && docker run --rm --entrypoint python medhub-backend:ci -c "import boto3"
```

Negative check, recorded at handoff: temporarily remove `boto3` from the manifest, `uv sync`, and
show that `tests/test_object_storage.py` fails. Then restore.

## Definition of Done

- [ ] `ruff`, `black --check`, `mypy app` pass; backend suite passes with coverage ≥ 85 %
- [ ] SOUP-019, TS-007, TS-013, ADD-024 (and RISK-007 if approved) `in_review`; PRB-002 `resolved`
- [ ] `traceability-check` shows no error for the touched records
