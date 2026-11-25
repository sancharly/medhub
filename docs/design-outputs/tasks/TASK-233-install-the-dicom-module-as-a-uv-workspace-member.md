---
id: "TASK-233"
type: task
title: "Install the DICOM viewer module as a uv workspace member in every environment"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-25"
links:
  - target: "SR-017"
    relation: implements
  - target: "SR-016"
    relation: implements
  - target: "SR-028"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-008"
    relation: relates_to
  - target: "PRB-048"
    relation: relates_to
  - target: "ADD-015"
    relation: relates_to
  - target: "SOUP-015"
    relation: relates_to
  - target: "SOUP-037"
    relation: relates_to
  - target: "TS-010"
    relation: relates_to
tags: ["cr:CR-008", "control:protective", "backend", "configuration-management"]
---

# TASK-233 — Install the DICOM viewer module as a uv workspace member in every environment

- **Software items / units:** SI-MOD-DICOM-BE packaging (ADD-015, ADR-0024); host build files
  (`backend/pyproject.toml`, `backend/uv.lock`, `backend/Dockerfile`). No `backend/app` source change.
- **PRB:** PRB-048. **CR:** CR-008 (D-1 (a), D-2, D-7; decision D-A).
- **Depends on:** none. First task: every later task needs the installed module and NumPy.
- **Branch:** `bug/dicom-module-install`.
- **Size:** M (`backend/pyproject.toml`, `backend/uv.lock`, `backend/Dockerfile`,
  `backend/modules/dicom_viewer/pyproject.toml`, `backend/modules/dicom_viewer/tests/conftest.py`, new
  `backend/modules/dicom_viewer/tests/test_installed_package.py`; records).

## Objective

The `medhub-dicom-viewer` package is installed from `backend/uv.lock` in the development environment, the
CI test environment and the production image; its `medhub.modules` entry point `dicom-viewer` is
discovered; NumPy 2.5.5 is installed with it; the module tests import the installed package with no
`sys.path` insertion (SR-017 AC 7, test-environment half; the image check is TASK-236).

Note on slicing: the D-7 conftest change and guard test sit here rather than in TASK-234, because they
are this task's proof that the installation works in the test environment.

## Design

Per [ADR-0024](../../design/adr/0024-backend-modules-installed-as-uv-workspace-members.md):

- `backend/pyproject.toml`: add `"medhub-dicom-viewer"` to `[project] dependencies`;
  `[tool.uv.workspace] members = ["modules/*"]`; `[tool.uv.sources] medhub-dicom-viewer = { workspace = true }`;
  `pythonpath = ["."]` in `[tool.pytest.ini_options]` (so `app` resolves for the module suite as it does in
  the image's working directory). The host stays virtual (no `[build-system]`).
- `backend/modules/dicom_viewer/pyproject.toml`: `dependencies = ["numpy>=2.5", "pydicom>=3.0.2"]`;
  `[build-system] requires = ["hatchling==1.33.0"]`; `[tool.hatch.build.targets.wheel] packages = ["dicom_viewer"]`
  (hatchling cannot infer the package from the name `medhub-dicom-viewer`; without it the wheel build fails).
- `backend/uv.lock`: `cd backend && uv lock`. Expected diff (probe of 2026-11-25 on a scratch copy): adds
  `medhub-dicom-viewer 0.1.0` (editable source `modules/dicom_viewer`) and `numpy 2.5.5`, and changes no
  other locked version. **Any other version change: stop and report** (SOUP impact).
- `backend/Dockerfile`: builder `RUN uv sync --frozen --no-dev --no-editable`; remove
  `COPY --from=builder /app/modules/ ./modules/` from the runtime stage. Keep the builder's `COPY modules/`.
- `backend/modules/dicom_viewer/tests/conftest.py`: remove the `sys.path` insertion and its comment; keep
  the settings fixture.

## Steps

Test first: write the guard test (step 1) and run it on `HEAD` before the packaging change; it must fail.

1. New `backend/modules/dicom_viewer/tests/test_installed_package.py`:
   - `test_entry_point_is_discovered`: `importlib.metadata.entry_points(group="medhub.modules")` has exactly
     one entry named `dicom-viewer`, value `dicom_viewer.manifest:manifest`; `ep.load()` returns an object
     with `module_key == "dicom-viewer"`; `app.modules.discovery.discover_modules()` returns it.
   - `test_distribution_declares_its_runtime_dependencies`: `importlib.metadata.requires("medhub-dicom-viewer")`
     names `numpy` and `pydicom`; `import numpy` succeeds and `numpy.__version__ == "2.5.5"` is **not**
     asserted (the lock is the authority; assert only that it imports).
   - `test_module_is_not_put_on_sys_path_by_conftest`: no entry of `sys.path` ends with
     `modules/dicom_viewer` because of the conftest (read `conftest.py` source and assert it has no
     `sys.path` mutation), so the suite cannot pass on a non-installed module again.
2. Packaging changes (Design above), then `cd backend && uv lock && uv sync --frozen`.
3. Run the whole backend suite. Discovery now finds a module in the test environment: any test that
   assumed "no module installed" (lifespan, registry sync, `GET /me/modules`, OpenAPI export) must be fixed
   by patching discovery in that test, **not** by uninstalling the module. List each such test in the
   Implementation record. If a `backend/app` change looks necessary: stop and ask (CR-008 boundary).
4. Records (same commit):
   - **TS-010** (approved 1.4 → 1.5, `in_review`, remove `approved_by`, `approved_on`, `approved_digest`,
     `approval_note`): new **TC-010.8** — Verifies SR-017 (AC 7), SR-016; the three tests of step 1;
     negative control "`uv pip uninstall medhub-dicom-viewer` (then `uv sync --frozen` to restore): the
     guard tests fail"; fails on `HEAD` 396e9de. Update TC-010.2's note that the module tests no longer need
     their own import root. Version-history line.
   - **SOUP-037**: change-log line "locked by TASK-233" confirmed with the resolved version; if uv resolved
     anything other than 2.5.5, update `soup_version` and re-review. Do not touch SOUP-015 (done at Plan).
   - `.github/workflows/ci.yml`: update the comment above "Run DICOM viewer module tests" (the module is
     installed; no separate import root). No step change here (TASK-236 adds the image check).

## Verification

- `cd backend && uv lock --check` (lock consistent) and `git diff --stat backend/uv.lock` (only the two
  added packages).
- `cd backend && uv sync --frozen && uv run python -c "from importlib.metadata import entry_points; print([e.name for e in entry_points(group='medhub.modules')])"`
  prints `['dicom-viewer']`.
- `cd backend && uv run pytest modules/dicom_viewer/tests -q` (all pass, including the 31 existing tests);
  `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85` (whole backend suite);
  `uv run ruff check . && uv run black --check . && uv run mypy app` (CI runs Black).
- Negative control, recorded: `uv pip uninstall medhub-dicom-viewer`, the guard tests fail; `uv sync --frozen`
  restores.
- Image: `docker build -t medhub-backend:task233 ./backend` succeeds, then
  `docker run --rm --entrypoint python medhub-backend:task233 -c "from importlib.metadata import entry_points; import dicom_viewer, numpy; print([e.name for e in entry_points(group='medhub.modules')], dicom_viewer.__file__)"`
  prints `['dicom-viewer']` and a path under `/app/.venv/lib/python3.12/site-packages/`; `ls /app/modules`
  in the image fails (not copied). The automated CI step is TASK-236.
- `traceability-check` on TASK-233, TS-010, SOUP-037, CR-008: 0 errors. `graphify update .` after the change.

## Acceptance criteria

- [ ] The module is installed from the lock in the dev and CI test environments and in the image, its entry
  point is discovered, and NumPy imports (SR-017 AC 7; TC-010.8, manual image check).
- [x] The module suite passes with no `sys.path` insertion and fails when the package is uninstalled
  (CR-008 D-7; TC-010.8).
- [x] `backend/uv.lock` adds only `medhub-dicom-viewer` and `numpy 2.5.5`; the whole backend suite, Ruff,
  Black and mypy pass (SR-028).

## Definition of Done

- [x] Guard tests written first and seen failing on `HEAD`; all suites and linters green; negative control recorded
- [x] TS-010 updated; SOUP-037 confirmed; `traceability-check` 0 errors; `graphify update .` run

## Implementation record

Implemented 2026-11-25 (Software Developer role).

- Guard tests written first (`backend/modules/dicom_viewer/tests/test_installed_package.py`); on `HEAD` 396e9de all
  3 failed. After the change: 3 passed.
- `backend/pyproject.toml`: `medhub-dicom-viewer` dependency, `[tool.uv.workspace]`, `[tool.uv.sources]`,
  `pythonpath = ["."]`. Module `pyproject.toml`: `numpy>=2.5`, `pydicom>=3.0.2`, `hatchling==1.33.0`, wheel
  `packages`. `Dockerfile`: `--no-editable`, runtime `COPY modules/` removed. Module `conftest.py`: `sys.path`
  insertion removed.
- `backend/uv.lock` (`uv lock`): adds only `medhub-dicom-viewer 0.1.0` (editable, `modules/dicom_viewer`) and
  `numpy 2.5.5` (+ the workspace `[manifest]`); no other locked version changed (`git diff --stat`: 96 insertions,
  0 deletions). `uv lock --check` passes.
- Tests that assumed "no module installed": `backend/tests/api/test_anonymized_retrieve.py`, fixture `rate_env`
  (5 tests of `TestRetrievalRateLimitPerAddress`; the lifespan registry sync tried to reach PostgreSQL on
  localhost). Fixed by patching `app.modules.discovery.discover_modules` to `[]` in the fixture. No other test
  changed behaviour; no `backend/app` change.
- Records: TS-010 1.5 `in_review` (TC-010.8, TC-010.2 note); SOUP-037 change-log line; `ci.yml` comment.
- Verification (run 2026-11-25): module suite 34 passed; whole backend suite 1748 passed, 10 skipped, coverage
  95.18% (gate 85%); Ruff, Black, mypy clean. Negative control: after `uv pip uninstall medhub-dicom-viewer` the
  entry-point and dependency guard tests fail (2 failed; the conftest test still passes); `uv sync --frozen`
  restores (3 passed). Image check (`docker build` and the `docker run` probe): **not completed** - the build hung for over 10 minutes at
  `load metadata for docker.io/library/python:3.12.15-slim@sha256:...` (Docker Desktop was started for this run; the
  registry answers HTTP 401 to curl, so the stall is inside Docker Desktop's network). To be run by QA or the human; the
  Dockerfile change is the one the task specifies.

## QA review — round 1 (2026-11-25): CHANGES REQUESTED

Re-run by QA on the working tree of `bug/dicom-module-install`: `uv lock --check` 0 (88 packages);
`git diff --stat backend/uv.lock` 96 insertions, 0 deletions (only `medhub-dicom-viewer 0.1.0`, `numpy 2.5.5`
and the workspace `[manifest]`); `uv sync --frozen` then the entry-point probe prints `['dicom-viewer']`
(numpy 2.5.5, pydicom 3.0.2); module suite 34 passed; whole suite 1748 passed, 10 skipped (all
`OBJECT_STORE_INTEGRATION`), coverage 95.18%; `ruff check .` 0, `ruff format --check` (3 changed files) 0,
`black --check .` 0, `mypy app` 0. OpenAPI export is byte-identical to `backend/openapi/openapi.json`
(the export does not run the lifespan). `traceability-check` on the CR-008 records: 0 errors.

- **R1-1 [HIGH] The module tests still import the module source, not the installed package; TC-010.8
  states otherwise** — `backend/modules/dicom_viewer/tests/__init__.py` (exists) with no `__init__.py` in
  `backend/modules/dicom_viewer/`; TS-010 TC-010.8 ("the module `conftest.py` has no `sys.path` mutation,
  so the suite cannot pass on a module that is not installed"). pytest's default `--import-mode=prepend`
  inserts the first directory above the `tests` package that is not a package, i.e.
  `backend/modules/dicom_viewer`, into `sys.path`. Probe with the package uninstalled
  (`uv pip uninstall medhub-dicom-viewer`): a session-finish plugin prints `dicom_viewer` imported from
  `backend/modules/dicom_viewer/dicom_viewer/__init__.py` and `sys.path` containing
  `.../backend/modules/dicom_viewer`; 32 of 34 tests pass, only the two guard tests fail;
  `test_module_is_not_put_on_sys_path_by_conftest` passes and protects nothing beyond the old conftest
  text. So CR-008's verification approach ("uninstalling the package ... makes the guard test **and the
  import** fail"), ADR-0024 decision 5 ("Module tests import the installed package; no test puts a module
  on `sys.path`") and the TC-010.8 rationale are not met. The entry-point guard does make the suite fail,
  so the RISK-007 control for the CI test environment holds; the defect is that the verification record
  claims a property the run disproves. With `--import-mode=importlib` the uninstalled run stops at
  collection (5 errors: `dicom_viewer` not importable) and the installed run passes 34/34.
  → Run the module suite with `--import-mode=importlib` (the CI step "Run DICOM viewer module tests", and
  this task's verification command; or `addopts = "--import-mode=importlib"` in
  `[tool.pytest.ini_options]`, which QA checked: whole suite 1748 passed, 10 skipped in that mode, and it
  then also applies to a local `uv run pytest modules/dicom_viewer/tests`); replace `test_module_is_not_put_on_sys_path_by_conftest` with a check that
  `dicom_viewer.__file__` is the one `importlib.metadata.distribution("medhub-dicom-viewer")` installs
  (or that no `sys.path` entry ends with `modules/dicom_viewer`, asserted from inside a test); reword
  TC-010.8 to name what fails the suite; record the negative control again (imports fail, not only the
  two guard tests).
- **R1-2 [MEDIUM] Image check not run; TASK-236's planned step covers only part of it** — the task's
  Verification "Image" bullet and AC 1 ("and in the image"). QA's `docker build -t medhub-backend:task233qa
  ./backend` (Docker Desktop 24.0.5, `DOCKER_HOST=unix:///Users/carlos.santiago/.docker/run/docker.sock`)
  stalled at `#3 [internal] load metadata for docker.io/library/python:3.12.15-slim@sha256:cb33f7f7...`, as
  for the developer; the pinned base image is not in the local cache. Host-side substitute (not the image,
  uv 0.11.23 on macOS instead of 0.13.7 on Linux): a scratch copy of `pyproject.toml`, `uv.lock`,
  `alembic.ini` and `modules/` synced with `uv sync --frozen --no-dev --no-editable`, the `.venv` moved
  away and the source copy deleted: entry points `['dicom-viewer']`, `dicom_viewer.__file__` under
  `.venv/lib/python3.12/site-packages/`, numpy 2.5.5, and `register_all_modules` mounts
  `/api/v1/modules/dicom-viewer/studies/{attachment_id}`. `uv build --wheel --package medhub-dicom-viewer`
  ships `dicom_viewer/{__init__,dicom,manifest,router}.py` and the entry point, no tests. The Dockerfile
  has no `COPY` into `/app/modules` in the runtime stage (static check). TASK-236's step (entry point
  equals `['dicom-viewer']`, `dicom_viewer.manifest`, `numpy`, `pydicom` import) will cover discovery and
  imports on hosted CI, but not "`/app/modules` absent" or "module runs from `site-packages`".
  → Run the image build and the `docker run` probe where the registry is reachable (hosted CI or after
  Docker Desktop's network is fixed) and record the output here, or have the human accept TASK-236's step
  as the image evidence and extend it with `ls /app/modules` failing and `dicom_viewer.__file__` starting
  with `/app/.venv/lib/python3.12/site-packages/`.
- **R1-3 [LOW] Requirement-name parsing by string splits** — `backend/modules/dicom_viewer/tests/test_installed_package.py:21-24`.
  `split(">")`, `split("=")`, `split("<")` miss `~=`, `!=`, extras and spaces before markers.
  → `packaging.requirements.Requirement(r).name` (`packaging` 26.2 is in the lock).

Checked and not findings: the `rate_env` fix in `backend/tests/api/test_anonymized_retrieve.py:113-117`
patches discovery for a fixture that tests the retrieval rate limit; the pre-change fixture, run with
the module installed, fails 5 tests on `OperationalError` from `sync_installed` in `_lifespan`
(`backend/app/main.py:75-90`), which is the designed start-up behaviour (sync failure stops start-up), not
a hidden defect. Every other test that enters the lifespan already patches discovery
(`tests/core/test_pool_settings.py:81`, `tests/workers/test_api_celery_broker.py:41`,
`tests/modules/test_discovery.py:208`) or stops before the module sync (`tests/test_lifespan.py:49`,
`tests/core/test_pool_settings.py:60`); `tests/test_lifespan.py:26` uses httpx `ASGITransport`, which
does not run the lifespan. `tests/api/test_db_dependency_scope.py:58` now also walks the module router.
The SR-017 `verifies` link on TS-010 is correct: TC-010.8 verifies SR-017 AC 7 (test-environment half)
and TC-010.4 already claimed SR-017 without the link. The negative control of the two guard tests is
real (re-run: 2 failed, 32 passed; restored with `uv sync --frozen`: 34 passed).

Pre-existing (not blocking): TS-010 Preconditions still name build `doc/agentic-os-migration` `40401a1`;
`backend/` has no `.dockerignore`, so `COPY modules/` sends local `__pycache__` and tests to the builder
(the wheel excludes them).

## Implementation record — round 2 (2026-11-25)

Fixes for QA round 1 (R1-1, R1-3). R1-2 (image check) left unverified as instructed; no `docker build` retried.

- **R1-1:** `backend/pyproject.toml` `[tool.pytest.ini_options]` gains `addopts = "--import-mode=importlib"`, so the
  module's `tests/` package no longer puts `backend/modules/dicom_viewer` on `sys.path`. CI's module step
  (`uv run pytest modules/dicom_viewer/tests`, `backend` working directory) passes no override and picks it up.
  `test_module_is_not_put_on_sys_path_by_conftest` is replaced by
  `test_module_is_imported_from_the_installed_distribution`: `dicom_viewer.__file__` is one of the distribution's
  files, or, for the editable install uv makes of a workspace member, lies under the editable source directory in
  `direct_url.json`. A `sys.path` assertion was not usable: the editable install itself adds the module directory
  to `sys.path` through its `.pth` file. TC-010.8 reworded (TS-010 1.6).
- **R1-3:** dependency names parsed with `packaging.requirements.Requirement(r).name`.
- **Negative control (real output):** `uv pip uninstall medhub-dicom-viewer` then
  `uv run --no-sync pytest modules/dicom_viewer/tests -q`: `5 errors in 0.77s`, "Interrupted: 5 errors during
  collection" (`test_audit_module_key`, `test_failure_audit_persistence`, `test_module_integration`,
  `test_size_bounds`, `test_studies_endpoint`); `uv sync --frozen` restores.
- **Results:** module suite 34 passed; whole backend suite 1748 passed, 10 skipped, coverage 95.18%; Ruff, Black
  (291 files unchanged) and mypy (137 files) clean; `uv lock --check` passes (88 packages).

## QA review — round 2 (2026-11-25): APPROVED

Re-run by QA on the working tree: `uv lock --check` 0 (88 packages); `ruff check .` 0; `ruff format --check
modules/dicom_viewer/tests/test_installed_package.py` 0; `black --check .` 0 (291 files); `mypy app` 0
(137 files); whole suite with coverage 1748 passed, 10 skipped, 95.18%; module suite 34 passed.
`traceability-check` on the CR-008 records: 0 errors (5 warnings, all in planning records).

- **R1-1: fixed.** `addopts = "--import-mode=importlib"` (`backend/pyproject.toml`). Negative control
  reproduced: with `uv pip uninstall medhub-dicom-viewer`, collection stops with 5 errors (the five files
  TC-010.8 names); after `uv sync --frozen`, 34 passed. Round-1 mode re-checked (`-o addopts=""`, package
  uninstalled): 3 failed (the three guard tests, including the new one), 31 passed, so even without the
  import mode the suite cannot pass on an uninstalled module. The developer's reason for not asserting on
  `sys.path` holds: `.venv/lib/python3.12/site-packages/_editable_impl_medhub_dicom_viewer.pth` contains
  `backend/modules/dicom_viewer`, and `sys.path` holds that entry in the installed state. The new test's
  non-editable branch was checked in a scratch `uv sync --frozen --no-editable` environment: 3 passed; with
  the module source put first on `PYTHONPATH` (source shadowing the installed wheel)
  `test_module_is_imported_from_the_installed_distribution` fails. Limit, accepted: in the editable dev/CI
  install, source and installed package are the same files, so a `sys.path` insertion of the source cannot
  be told apart there; the import mode is the control for that case.
- **R1-3: fixed.** `Requirement(r).name`; `packaging` 26.2 is in the lock.
- **R1-2: open, unverified, carried forward to TASK-236.** No `docker build` in round 2 (coordinator
  instruction; the base image is being pulled separately). AC 1 stays unticked for its image half: the
  dev and CI test environment halves are verified (TC-010.8); the image half rests on TASK-236's Docker
  Build step and the human's decision on whether hosted CI covers it, with the extension named in R1-2
  (`ls /app/modules` fails; `dicom_viewer.__file__` under `/app/.venv/lib/python3.12/site-packages/`).

Observation: the first module-suite run of this round (started while the whole suite was running and
Docker Desktop was pulling an image) reported 1 failed, 33 passed; it did not recur in 21 further runs,
alone or concurrent with the whole suite. Two module files start PostgreSQL through testcontainers
(`test_audit_module_key.py`, `test_failure_audit_persistence.py`); a busy Docker daemon is the likely
cause. Not attributed to this change.

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
- 1.1 (2026-11-25) — Implemented (Software Developer role). `draft` → `in_review`.
- 1.1 (2026-11-25, QA) — Round 1 CHANGES REQUESTED (R1-1 HIGH, R1-2 MEDIUM, R1-3 LOW). Status `draft`.
- 1.2 (2026-11-25) — Round 2 (Software Developer role): R1-1 and R1-3 fixed, R1-2 left unverified. `draft` → `in_review`.
- 1.2 (2026-11-25, QA) — Round 2 APPROVED; R1-1 and R1-3 fixed; R1-2 (image check) unverified and carried to TASK-236. Status `approved`.
