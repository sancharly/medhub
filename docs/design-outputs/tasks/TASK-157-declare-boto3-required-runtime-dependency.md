---
id: "TASK-157"
type: task
title: "Declare boto3 as a required runtime dependency"
status: approved
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

- [x] CR-001 **AC-6**: `boto3` under `[project] dependencies`; `uv.lock` resolves it to exactly one
      version; `uv lock --check` succeeds; SOUP-019 `soup_version` = locked `boto3`, body records the
      locked `botocore`.
- [x] CR-001 **AC-7**: the instantiation test runs in CI (`backend-tests`), does not stub the
      import, needs no endpoint, and fails when `boto3` is missing.
- [x] CR-001 **AC-8**: `import boto3` succeeds in the `--no-dev` environment (CI step and local
      check below).
- [x] CR-001 **AC-17** (PRB-002 part): PRB-002 `resolved` with its `## Resolution`.

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

- [x] `ruff`, `black --check`, `mypy app` pass; backend suite passes with coverage ≥ 85 %
- [x] SOUP-019, TS-007, TS-013, ADD-024 (and RISK-007 if approved) `in_review`; PRB-002 `resolved`
- [x] `traceability-check` shows no error for the touched records

## Implementation notes and evidence

Handed to QA on 2026-10-22 (status `in_review`). Checkboxes are left for QA.

**Files.** New: `backend/tests/test_object_storage.py`. Changed: `backend/pyproject.toml`
(`"boto3>=1.43.0"`), `backend/uv.lock` (51 lines added, none removed), `backend/app/core/object_storage.py`
(module docstring only), `.github/workflows/ci.yml` (step "Check production dependency set" in job
`build`), SOUP-019 (1.1, `in_review`), TS-007 (1.1, `in_review`, TC-007.5), TS-013 (extends its 1.2
entry: TC-013.7, TC-013.8), ADD-024 (extends its 1.1 entry), RISK-007 (1.3, `in_review`, control row
rewritten, scores unchanged), PRB-002 (`resolved`, 1.1).

**Lock diff.** `uv lock` without `--upgrade` resolved 86 packages and added exactly four:
`boto3` 1.43.117, `botocore` 1.43.117, `s3transfer` 0.19.3, `jmespath` 1.1.0. Besides those entries,
the diff holds the `boto3` lines in the `medhub-backend` package's dependency list and its
`requires-dist` specifier. No existing package changed version (`urllib3` 2.7.0 and
`python-dateutil` 2.9.0.post0 are untouched). The lower bound is the locked major.minor.

**Design points.**
- The import in `object_storage.py` stays lazy and the `ImportError` stays; only the docstring
  claiming boto3 is optional was corrected. The `pip install boto3` hint in the message is left
  as is (out of the task's scope).
- The test follows the task: no patch, stub, `importorskip` or `sys.modules` entry; it clears the
  `get_settings` cache before and after, relies on the autouse `OBJECT_STORE_*` environment and
  asserts `_bucket == "medhub"` and `_client.meta.endpoint_url == "http://localhost:9000"`.
- TC-007.5 was put in TS-007 (it verifies SR-013 AC-3); TC-013.7 and TC-013.8 in TS-013
  (SR-028 AC-5), as the task says.
- RISK-007 was updated under CR-001 Plan decision Q-3 (approved 2026-10-22).

**Verification run (2026-10-22, macOS, branch `bug/soup-pinning`).**

| Command | Result |
|---|---|
| `tests/test_object_storage.py` written first, run before the manifest change | 1 failed, `ImportError: boto3 is required for object storage` |
| `cd backend && uv lock` then `uv lock --check` | 86 packages, 4 added; check exit 0 |
| `uv run pytest tests/test_object_storage.py -v` | 1 passed |
| `cd backend && uv run pytest -q` | 496 passed (495 + 1) |
| `uv run pytest --cov=app --cov-fail-under=85 -q` | 496 passed, coverage 91.71 % |
| `uv run ruff check .`, `uv run black --check .`, `uv run mypy app` | all pass (`219 files would be left unchanged`; `no issues found in 124 source files`) |
| `UV_PROJECT_ENVIRONMENT=<tmp>/venv uv sync --frozen --no-dev` then `import boto3` | `1.43.117` (botocore 1.43.117) |
| `docker build -t medhub-backend:ci ./backend` | exit 0 |
| `docker run --rm --entrypoint python medhub-backend:ci -c "import boto3; print(boto3.__version__)"` | `1.43.117`, exit 0 |
| `python3 infra/check_image_pins.py` | no output, exit 0 |
| `python3 -m unittest discover -s infra/tests` | 11 tests, OK |
| Negative check: `boto3` removed from `pyproject.toml`, `uv sync` (boto3 and its three dependencies uninstalled) | `import boto3` raises `ModuleNotFoundError`; `tests/test_object_storage.py` failed. Manifest and lock restored, `uv sync --frozen`, `uv lock --check` exit 0, test passes again |

**Not verified here.** GitHub Actions cannot be run locally: the new step in the `build` job has not
run in CI and is checked only by running its command against the locally built image. The "all jobs
green on the branch head" check happens after the push. `traceability-check` was not run by the
developer role; QA runs it.

**Observation, not changed.** TC-013.7 (`uv lock --check`) is not a CI step: the jobs install with
`uv sync --frozen`, which does not verify that the lock matches the manifest. The task asked for
no such step, so none was added; adding `uv lock --check` to the `backend-quality` job would make
the check automatic (decision for the human or TASK-159). TS-013 says that TC-013.7 is run by hand.

## QA review (2026-10-22)

**Verdict: APPROVED** (`in_review → approved`). No CRITICAL or HIGH finding. RISK-007, SOUP-019
and ADD-024 stay `in_review` for the human. TS-013 stays `in_review` because TASK-158 and TASK-159
extend its 1.2 entry and CR-001 AC-18 requires it. TS-007 also stays `in_review` because of the LOW
finding below. No later task of CR-001 touches TS-007, so it can go to `approved` once that fix is
in. AC-7 and AC-8 are ticked on local evidence and on a check of the CI configuration. Their first
run in CI is Checkpoint A (AC-16).

### Findings

- **[MEDIUM] `uv lock --check` is not run in CI, but CR-001's verification approach says it is.**
  `.github/workflows/ci.yml:25-27` (and `:91-93`, `:179-181`) install with `uv sync --frozen`. That
  command installs the lock as it is and never compares it with `[project] dependencies`. CR-001,
  "Verification approach", says: "Static checks (AC-1, AC-2, AC-4, AC-6, AC-9): … plus the pin check
  (AC-3) and `uv lock --check`, all in CI." TS-013 TC-013.7 records the check as run by hand. AC-6
  holds today: QA ran `uv lock --check` and it exited 0. But a later edit to `pyproject.toml` that
  is not re-locked would pass every job. The production image would then lack the newly declared
  package, which is PRB-002's failure class. The boto3 import step only catches it for boto3. SR-028
  AC-5 ("resolves to exactly one version … through the committed lock files") is then enforced only
  by review. → Add a step to `backend-quality` after "Install uv":
  `working-directory: backend`, `run: uv lock --check`. Alternatively, change that job's
  `uv sync --frozen` to `uv sync --locked`. Then change TC-013.7's procedure to cite the CI step and
  drop "run by hand (review)". It is best done in TASK-158, which edits the same manifest, lock and
  workflow, or before Checkpoint A at the latest. Does not block this task.
- **[LOW] TS-007's preconditions do not cover TC-007.5.**
  `docs/design-outputs/tests-specifications/TS-007-clinical-entries-and-attachment.md:28` names the
  build "branch `doc/agentic-os-migration`, commit `40401a1`". `tests/test_object_storage.py` does not
  exist at that commit. Line 30 says unit tests use "a fake object store", but TC-007.5 builds the
  real boto3 client (with no endpoint reachable). → Name branch `bug/soup-pinning` as the build for
  TC-007.5, or the CR-001 head once it is committed. Add one sentence: "TC-007.5 builds the real
  `boto3` S3 client from the locked SDK; no object-storage service is needed." TS-007 then can go to
  `approved`.

Observations (no action): `ObjectStorageClient`'s `ImportError` message still says
`pip install boto3`. In a uv project the remedy is the lock, but the message cannot be reached in a
correctly built image, and the developer left it out of scope. TC-007.5 cites SR-013 AC-3. The
client also serves AC-1 (upload) and AC-4 (SSE), so AC-3 is a narrow citation, but it matches the
task and PRB-002. The CI step uses `--entrypoint python`, which resolves to `/app/.venv/bin/python`
through the image's `PATH`. If that `PATH` were ever lost, the step would fall back to the system
Python and fail. It fails closed.

### Verification run (QA, 2026-10-22, macOS, uv 0.11.23, Docker)

| Command | Result |
|---|---|
| `tomllib` parse of `backend/pyproject.toml` | `boto3>=1.43.0` in `[project] dependencies`. It is not in the `dev` group, and there are no optional extras |
| `tomllib` comparison of `uv.lock` with `git show HEAD:backend/uv.lock` | added `boto3` 1.43.117, `botocore` 1.43.117, `jmespath` 1.1.0, `s3transfer` 0.19.3. None removed, none changed. One `boto3` entry. All from `https://pypi.org/simple`. `git diff --stat`: 51 insertions, 0 deletions |
| `cd backend && uv lock --check` | `Resolved 86 packages`, exit 0 |
| `uv run pytest tests/test_object_storage.py -v` | 1 passed. The suite has no `sys.modules`, patch or stub of `boto3` anywhere (grep over `backend/tests/`) |
| Negative check in a scratchpad copy of `backend/` (`boto3` line removed, `uv sync` into a scratch venv). The working tree was not touched | `import boto3` → `ModuleNotFoundError`. The test fails with `ImportError` at `app/core/object_storage.py:20` |
| `UV_PROJECT_ENVIRONMENT=<scratch>/venv uv sync --frozen --no-dev`, then `import boto3` | `1.43.117`. `import pytest` fails, which confirms the environment really is `--no-dev` |
| `docker build -t medhub-backend:ci ./backend` and `docker run --rm --entrypoint python medhub-backend:ci -c "import boto3, botocore, s3transfer, jmespath; …"` | build OK. Prints `1.43.117 1.43.117 0.19.3 1.1.0`, exit 0. `sys.executable` is `/app/.venv/bin/python` |
| The CI step's command against an image built from the boto3-less scratch copy | exit 1 (`ModuleNotFoundError`), so the step fails closed |
| `.github/workflows/ci.yml` parsed (Ruby YAML) | valid. `build` steps: checkout, "Build backend image", "Check production dependency set", "Build frontend image". Triggers: `push` on `**`, `pull_request` on `main` |
| `uv run pytest --cov=app --cov-fail-under=85 -q` | `496 passed`, coverage 91.71 % |
| `uv run ruff check .`, `uv run black --check .`, `uv run mypy app` | all checks passed; 219 files unchanged; no issues in 124 source files |
| `python3 infra/check_image_pins.py`, `python3 -m unittest discover -s infra/tests` | exit 0 with no output; 11 tests OK |
| `traceability-check` (fallback parser) on TASK-157, SOUP-019, TS-007, TS-013, ADD-024, RISK-007, PRB-002, CR-001, links resolved against all 329 records | **0 errors.** Two expected warnings: `soup_anomaly_review_stale` for SOUP-019 (until TASK-154) and `risk_control_unverified` for TASK-157 → RISK-007 (no TR until the release). A re-run after this approval adds a third: W5, TASK-157 `approved` → RISK-007 `in_review`. It clears when the human approves RISK-007. E9 holds for PRB-002 (CR-001 `resolves`). `soup_unintegrated` holds (ADD-012 `relates_to` SOUP-019), and so does `soup_without_risk` (RISK-007, RISK-010 and RISK-011) |
| Records review | RISK-007 1.3: control row names TASK-157 (CR-001) and TS-007 TC-007.5 / TS-013 TC-013.8. Scores 3 × 2 are unchanged and `risk_matrix[3][2]` = `alarp`, matching `acceptability`. The ALARP justification is present, the approval record is cleared, and the version history is added. PRB-002: Investigation `file:line` references are checked against `cebe2d1`. The Safety evaluation names RISK-007 and states that no release exists, so no notification is needed. The Resolution lists the files and a reproducible verification. SOUP-019 `soup_version` `"1.43.117"` matches the lock. botocore, s3transfer and jmespath are recorded. The change log is per the task |

Pending, not blocking: the first CI run of "Check production dependency set" and of
`backend-tests` with the new test on the branch head (AC-16, Checkpoint A).
