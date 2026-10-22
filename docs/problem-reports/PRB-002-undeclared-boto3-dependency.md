---
id: "PRB-002"
type: problem-report
title: "boto3 is imported at runtime but declared nowhere, so attachment storage fails"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-22"
criticality: major
links: []
tags: ["soup", "configuration-management"]
---

# PRB-002 — boto3 is imported at runtime but declared nowhere

## Observed

`ObjectStorageClient.__init__` imports `boto3` lazily and raises `ImportError` with the message
"boto3 is required for object storage" when it is missing
(`backend/app/core/object_storage.py:17-21`). `boto3` appears in no manifest: not in
`backend/pyproject.toml` (runtime or dev group), not in `backend/uv.lock`, and not installed by
`backend/Dockerfile`. A grep over the repository finds it only in that module, in review notes and
in the SOUP list.

## Impact

- Any environment built from the declared dependencies has no `boto3`, so the first attachment
  upload or download raises `ImportError` — **SR-013 (clinical entry attachments) and the DICOM
  path that depends on it are non-functional in a real deployment**. Unit tests pass because they
  substitute a fake storage client.
- **IEC 62304 §8.1.2**: a SOUP item that is not declared has no title/manufacturer/version record
  and cannot be version-controlled or anomaly-reviewed. Its record,
  [SOUP-019](../soup/SOUP-019-boto3.md), is the one with no version.

## Root cause

TASK-045 introduced the storage client with an intentionally lazy import (documented in the module
docstring) so that unit tests and non-storage deployments would not need the SDK, but the
corresponding dependency declaration — as a required dependency or an extra — was never added.

## Investigation

Mechanism. `ObjectStorageClient.__init__` imports `boto3` inside the constructor
(`backend/app/core/object_storage.py:17`, as of commit `cebe2d1`, before CR-001) and builds the S3
client at `:24`. The module docstring (`:3-4`) declared the SDK "optional", and the optional
declaration it implied was never written: no manifest names the package. The constructor is reached
only lazily, from `backend/app/api/deps.py:166,185` and `backend/app/api/routers/attachments.py:29,39`,
so importing the application, starting it and running the whole backend suite all succeed without
the SDK; the first attachment request in a deployment is the first place the missing package shows.
`backend/Dockerfile:7` installs with `uv sync --frozen --no-dev`, which installs only what
`backend/uv.lock` locks, and `uv.lock` had no `boto3`. The production image therefore could not
import it.

Why no test caught it. The attachment tests substitute a fake storage client, and no test built the
real one. Root cause: the lazy import was treated as a license to omit the declaration (TASK-045),
and no control compared the code's imports with the declared dependency set.

Reproduction on the unfixed tree: `cd backend && uv sync --frozen && uv run python -c "import boto3"`
raises `ModuleNotFoundError`; `ObjectStorageClient()` raises `ImportError: boto3 is required for
object storage`.

## Safety evaluation

No direct hazard: the failure is loud (an exception) and cannot mis-attribute or corrupt clinical
data. The consequence is unavailability of attachments, which delays access to clinical
information; assessed in the RISK register as an availability contribution, not a data-integrity one
(RISK-007, whose cause already lists "a missing storage SDK (PRB-002)").

`criticality: major` stands: no data integrity, safety-related function or clinical decision is
affected directly, but a core function (SR-013) is unavailable until fixed. The fix changes no
behavior of the client; it makes the SDK the code already requires installable. One consequence
for the record: the attachment write path now reaches an object store in a real deployment, so the
`ServerSideEncryption="AES256"` request is exercised live for the first time; a misconfigured
store rejects it and the upload fails loudly, and no object is stored unencrypted silently. The
missing end-to-end SSE check is tracked as PRB-036.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

Declare `boto3` with a pinned lower bound in `backend/pyproject.toml`, refresh `uv.lock`, record the
locked version in SOUP-019, and add a smoke check that instantiates `ObjectStorageClient` against
the MinIO service in CI so a missing SDK fails the build rather than a user request. Alternatively,
keep it optional but declare an extra and fail fast at application startup when object storage is
configured. Requires a CR that links `resolves` → PRB-002.

## Resolution

Resolved by CR-001 (`resolves` link on the CR) in TASK-157, on branch `bug/soup-pinning`. The
first option of the proposed resolution was taken (declare the dependency); the "fail fast at
startup" alternative was not, and the smoke check against MinIO was replaced by a CI check that
needs no service, as follows.

Changes:
- `backend/pyproject.toml`: `"boto3>=1.43.0"` added to `[project] dependencies` (a required
  dependency, not an extra or a dependency group).
- `backend/uv.lock`: refreshed with `uv lock` (no `--upgrade`). Added only `boto3` 1.43.117,
  `botocore` 1.43.117, `s3transfer` 0.19.3 and `jmespath` 1.1.0; no existing package changed
  version. `python-dateutil` and `urllib3` were already locked.
- `backend/app/core/object_storage.py`: the module docstring now states that boto3 is a required
  dependency; the lazy import and the `ImportError` are kept (they are harmless, and the importers
  are lazy).
- `backend/tests/test_object_storage.py` (new): instantiates `ObjectStorageClient()` with no patch,
  stub or `importorskip` for `boto3`, and asserts the bucket and the S3 endpoint URL. It needs no
  reachable endpoint, because `boto3.client("s3", ...)` opens no connection.
- `.github/workflows/ci.yml`, job `build`: step "Check production dependency set" runs
  `docker run --rm --entrypoint python medhub-backend:ci -c "import boto3"` against the image built
  just before it.
- `docs/soup/SOUP-019-boto3.md`: `soup_version` 1.43.117, botocore, s3transfer and jmespath
  recorded. TS-007 gains TC-007.5, TS-013 gains TC-013.7 and TC-013.8, ADD-024 and RISK-007 updated.

Why a CI check rather than a check at startup: the backend image is built only with
`uv sync --frozen --no-dev` from the committed lock, so once `boto3` is locked the SDK cannot be
missing at startup. The Docker Build job proves it on every push and pull request, so a regression
fails the build instead of a user request, and the application gains no startup code.

Verification (TS-007 TC-007.5, TS-013 TC-013.7 and TC-013.8), reproducible from the repository
root:

```sh
cd backend
uv lock --check                                    # TC-013.7: exit 0
uv run pytest tests/test_object_storage.py -v      # TC-007.5: 1 passed
UV_PROJECT_ENVIRONMENT="$(mktemp -d)/venv" sh -c \
  'uv sync --frozen --no-dev && "$UV_PROJECT_ENVIRONMENT/bin/python" -c "import boto3; print(boto3.__version__)"'   # 1.43.117
cd .. && docker build -t medhub-backend:ci ./backend
docker run --rm --entrypoint python medhub-backend:ci -c "import boto3"   # TC-013.8: exit 0
```

Negative check: with `boto3` removed from `pyproject.toml` and the environment synced,
`tests/test_object_storage.py` failed with `ImportError: boto3 is required for object storage`;
restoring the manifest and the lock made it pass again. The Docker Build job itself cannot be run
locally; it is confirmed on the branch head after the push.
