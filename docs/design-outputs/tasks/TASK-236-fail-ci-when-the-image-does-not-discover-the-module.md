---
id: "TASK-236"
type: task
title: "Fail CI when the production image does not discover the module; smoke test answers 401"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-26"
links:
  - target: "SR-017"
    relation: implements
  - target: "SR-028"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-008"
    relation: relates_to
  - target: "PRB-048"
    relation: relates_to
  - target: "TASK-233"
    relation: relates_to
  - target: "ADD-015"
    relation: relates_to
  - target: "TS-013"
    relation: relates_to
  - target: "TS-010"
    relation: relates_to
tags: ["cr:CR-008", "control:protective", "ci", "infra"]
---

# TASK-236 — Fail CI when the production image does not discover the module; smoke test answers 401

- **Software items / units:** CI workflow (`.github/workflows/ci.yml`, Docker Build job), started-stack
  smoke test (`infra/smoke-test.sh`). No application code.
- **PRB:** PRB-048. **CR:** CR-008 (D-6; decision D-A).
- **Depends on:** TASK-233 (the image installs the module). Can run in parallel with TASK-234 and TASK-235.
- **Size:** S (`ci.yml`, `infra/smoke-test.sh`, possibly `infra/tests/` if a test reads the workflow; records).

## Objective

SR-017 AC 7, image and started-stack halves: a production image in which the `dicom-viewer` entry point is
not discovered, `dicom_viewer.manifest` does not import or `numpy` does not import fails the Docker Build
job; on a started stack an unauthenticated `GET /api/v1/modules/dicom-viewer/studies/<random uuid>` answers
401, not 404.

## Steps

1. `ci.yml`, Docker Build job, a step right after "Check production dependency set", named "Check the
   production image discovers the DICOM module":
   `docker run --rm --entrypoint python medhub-backend:ci -c "import sys; from importlib.metadata import entry_points; names=[e.name for e in entry_points(group='medhub.modules')]; import dicom_viewer.manifest, numpy, pydicom; sys.exit(0 if names == ['dicom-viewer'] else 1)"`
   (or a short script under `backend/scripts/` copied into the image, if quoting gets fragile; the
   check must run inside the image, from `/app`). Keep the existing step unchanged.
2. `infra/smoke-test.sh`: one check, in the style of the existing ones, that
   `curl -s -o /dev/null -w '%{http_code}' https://…/api/v1/modules/dicom-viewer/studies/$(uuid)` through the
   proxy is `401`, with a failure message saying "module route not mounted (404)" when it is 404.
3. If `infra/tests/` has a test that parses `ci.yml` or `smoke-test.sh` (e.g. a step list or pin check),
   update it; `python3 infra/check_image_pins.py` must stay clean (no new `uses:` or tool pins).
4. Records (same commit): **TS-013** (approved 1.6 → 1.7, `in_review`, remove the approval record): new
   **TC-013.15** — Verifies SR-017 (AC 7), SR-028; the CI step; "fails on the pre-TASK-233 image (no entry point;
   QA's run on `infra-backend:latest`), passes after TASK-233". **TS-010** (1.5 from TASK-233, stays `in_review`): new **TC-010.9** — the smoke
   check, system level, SR-017 AC 7. Version-history lines.

## Verification

- Locally, the step's command against `docker build -t medhub-backend:ci ./backend` built before TASK-233
  (QA ran it on the pre-TASK-233 image `infra-backend:latest`; hosted CI never builds 396e9de): exit 1; built on the branch after TASK-233: exit 0. Record both.
- `python3 -m unittest discover -s infra/tests -v` and `python3 infra/check_image_pins.py`: pass.
- The smoke check is executed on a started stack in TASK-239 (not here); here run `bash -n infra/smoke-test.sh`.
- `traceability-check` on TASK-236, TS-013, TS-010, CR-008: 0 errors.

## Acceptance criteria

- [x] The Docker Build job fails on an image without the module entry point or NumPy, and passes on the
  branch image (SR-017 AC 7; TC-013.15).
- [x] The smoke test checks that the module route answers 401 unauthenticated (TC-010.9).

## Definition of Done

- [x] Negative and positive runs of the step recorded; infra tests and pin check green
- [x] TS-013 and TS-010 updated; `traceability-check` 0 errors

## Carried from TASK-233 (QA, 2026-11-25)

TASK-233 R1-2: the manual image check (`docker build` and the `docker run` probe) was not run; Docker
Desktop stalled at `load metadata for docker.io/library/python:3.12.15-slim@sha256:cb33f7f7...`. Unless the
human decides otherwise, this task's Docker Build step is the image evidence for SR-017 AC 7, and it should
also check that `/app/modules` does not exist in the image and that `dicom_viewer.__file__` starts with
`/app/.venv/lib/python3.12/site-packages/`.

## Implementation record (2026-11-25)

Files: `.github/workflows/ci.yml` (Docker Build job, new step after "Check production dependency set"),
`backend/scripts/check_image_modules.py` (new; `backend/scripts/` is already copied into the image, so the
step runs from `/app` with no change to the Dockerfile), `infra/smoke-test.sh` (section 9b), TS-013 1.7
(TC-013.15), TS-010 1.7 (TC-010.9), this record. No `infra/tests/` test reads the step list or the smoke
script's checks, so none changed.

- **Step:** `docker run --rm --entrypoint python medhub-backend:ci scripts/check_image_modules.py /app`. A script
  instead of `python -c`, because four checks (entry points exactly `['dicom-viewer']`; `dicom_viewer.manifest`,
  `numpy`, `pydicom` import; `/app/modules` absent; `dicom_viewer.__file__` under
  `/app/.venv/lib/python3.12/site-packages/`) make the one-liner fragile (TASK step 1 allows this). The last two are
  the TASK-233 R1-2 carry-over. No new `uses:` or tool pin: `python3 infra/check_image_pins.py` exit 0.
- **Smoke check:** unauthenticated `GET https://localhost/api/v1/modules/dicom-viewer/studies/<uuid4>` through the
  proxy, status from `curl -w '%{http_code}'`. PRB-059 (Compose 5.x prints `:0` where 2.x prints nothing) is about
  parsing Compose presentation text for a port; this check never asks Compose anything, so it does not depend on
  Compose output. 404 gives "module route not mounted (404)"; any other non-401 gives the code. Requests without a
  token fail in `get_current_user` before the module-enablement gate, so 401 is expected when the router is mounted.

### Verification results

- `python3 -m unittest discover -s infra/tests`: 178 tests OK. `python3 infra/check_image_pins.py`: exit 0.
  `bash -n infra/smoke-test.sh`: ok (`shellcheck`, `actionlint` not installed; workflow parsed with PyYAML).
  `ruff format` and `ruff check` on the new script: clean.
- Probe against a stand-in (scratch copy of `backend/`, `uv sync --frozen --no-dev --no-editable --python 3.12`,
  `modules/` then deleted as in the image's final stage): exit 0, `ok: dicom-viewer is discovered from the installed
  package`. Negative controls, each exit 1: `/app/modules` present (`FAIL: .../modules exists; the module source tree
  must not be in the image`); source tree on `PYTHONPATH` (`FAIL: dicom_viewer is imported from .../off/dicom_viewer/__init__.py,
  expected under .../.venv/lib/python3.12/site-packages/`); package uninstalled (entry points `[]`, `import
  dicom_viewer.manifest` failed); NumPy uninstalled (`import numpy failed`, with the package also gone because the
  re-sync could not run without `modules/`).
- Image evidence (local, branch working tree, one build, no retry): `docker build -t medhub-backend:ci ./backend` completed
  (exit 0; image 57e3d35a9b47). `docker run --rm --entrypoint python medhub-backend:ci scripts/check_image_modules.py /app`:
  exit 0, `ok: dicom-viewer is discovered from the installed package`; `ls -d /app/modules` in the image: no such file.
  Image-level negative control: the same command with `/nonexistent-app` exits 1 (`dicom_viewer is imported from
  /app/.venv/lib/python3.12/site-packages/dicom_viewer/__init__.py, expected under ...`), which shows the path rule fires.
  Not run locally: the Docker Build job itself (verified on hosted CI after push). The negative run on an image with no entry point is QA's run on the pre-TASK-233 image `infra-backend:latest` (exit 1), repeated in TASK-239 (2026-11-26).
- The negative run on an image with no entry point is reproduced by the "package uninstalled" control
  on the stand-in and by QA's run on the pre-TASK-233 image `infra-backend:latest`; the CI job result is verified on hosted CI after push.

## QA review — round 1 (2026-11-25): APPROVED

Re-run by QA on the working tree of `bug/dicom-module-install`: `python3 -m unittest discover -s infra/tests`
178 OK; `python3 infra/check_image_pins.py` 0; `bash -n infra/smoke-test.sh` 0; `ruff format --check`, `ruff check`,
`black --check` on `backend/scripts/check_image_modules.py` 0; workflow parsed with PyYAML: the build job's steps are
checkout, "Build backend image", "Check production dependency set", the new step, "Build frontend image", none with
`if:`, so the step runs only after the image is built and tagged `medhub-backend:ci`; the diff adds no `uses:` line
(`actionlint` and `shellcheck` not installed). `traceability-check` on the 40 CR-008 records: 0 errors, 27 warnings
(W5/W6, all on planning records or other tasks; none on TASK-236, TS-010 or TS-013).

**Image evidence (closes TASK-233 R1-2 locally).** Image `57e3d35a9b47` (`medhub-backend:ci`, linux/arm64, built
2026-11-25 18:39 UTC from the working tree, not from a clean commit; `backend/Dockerfile`, `pyproject.toml`, `uv.lock`
and the module `pyproject.toml` are unchanged from `HEAD` d576494, so the packaging inputs are those of the commit;
the module source carried TASK-235's uncommitted edits). `/app/scripts/check_image_modules.py` in the image is
byte-identical to the working-tree file (`cmp` 0). The probe exits 0 (`ok: ...`); `ls -d /app/modules`: no such file;
`dicom_viewer.__file__` is `/app/.venv/lib/python3.12/site-packages/dicom_viewer/__init__.py`; the entry point is
`dicom-viewer = dicom_viewer.manifest:manifest`; `direct_url.json` says `editable: false`; `discover_modules()` in the
image returns `[('dicom-viewer', '0.1.0')]`. Negative controls on this image, each exit 1 with one `FAIL:` line:
NumPy deleted from site-packages; the `medhub_dicom_viewer` dist-info deleted (entry points `[]`); `/app/modules`
created. Negative control on a real pre-TASK-233 image: `infra-backend:latest` (built 2026-11-10, old Dockerfile layout
with `/app/modules`) with the script mounted in: exit 1, five `FAIL:` lines (entry points `[]`, `dicom_viewer.manifest`
and `numpy` not importable, `/app/modules` exists, `dicom_viewer` not imported). This is the negative run (hosted CI never builds 396e9de, only the branch).

Still only "to be verified on hosted CI": the Docker Build job running this step on the pushed commit (clean checkout,
linux/amd64 runner) and passing. The started-stack 401 (TC-010.9) is TASK-239.

Stand-in venv (`uv sync --frozen --no-dev --no-editable --python 3.12`, `modules/` removed): positive exit 0; source
on `PYTHONPATH` exit 1; `modules/` present exit 1; a second distribution adding entry point `other`, or `dicom_viewer`
(underscore), exit 1; the package's own entry point renamed to `dicom_viewer`, exit 1. Smoke 9b logic checked
in-process (`httpx.ASGITransport`, no lifespan, DB and Redis unreachable): app without modules registered answers 404
`Not Found`; after `register_all_modules(app, discover_modules())` it answers 401 `Unauthenticated` (also with a bogus
cookie and a non-UUID id), and an unknown module key still 404. 401 comes from `get_current_user`, which is a
sub-dependency of the router-level gate `require_module_enabled` (`backend/app/api/deps.py:179-181`), so it resolves
before the gate whatever the order of router and endpoint dependencies. 9b reads only `curl -w '%{http_code}'`
(no Compose output, PRB-059); a connection failure gives `000`, which is a FAIL, not a skip.

- **R1-1 [MEDIUM] The probe does not load the entry point, so it passes an image whose module is not discovered** —
  `backend/scripts/check_image_modules.py:26-28`. Only entry-point *names* are compared; with the name right and the
  value wrong (stand-in: `dicom-viewer = dicom_viewer.manifest:nope`) the script exits 0 and prints "dicom-viewer is
  discovered from the installed package", while `discover_modules()` would skip it and the route would answer 404.
  Mitigated today by TC-010.8 (`test_entry_point_is_discovered` loads the entry point; CI runs the module suite) and
  by smoke 9b, so not blocking. → Also assert that `[m.module_key for m in app.modules.discovery.discover_modules()]
  == ["dicom-viewer"]` (run with `/app` on `sys.path`, or `python -c`/`-m` from `/app`; QA ran it in the image:
  `[('dicom-viewer', '0.1.0')]`), or `ep.load().module_key == "dicom-viewer"`. Carried to TASK-239.
- **R1-2 [LOW] Records say the `HEAD` 396e9de negative run is "to be verified on hosted CI"** — this record's
  Verification results, last bullet; TS-013 TC-013.15 pass criteria. Hosted CI builds the branch only. → Cite the
  pre-TASK-233 image run above as the negative evidence. Carried to TASK-239.
- **R1-3 [LOW] TS-010 scope does not name the system level or its environment** — TS-010 "Levels: unit, integration",
  tag `level:unit`, Preconditions. TC-010.9 is system level and needs a started stack, `curl` and `python3`. → Add
  "system (TC-010.9)" to Levels and the started-stack precondition. Carried to TASK-239.
- **R1-4 [LOW] Smoke 9b gives a misleading 404 message when `python3` is missing** — `infra/smoke-test.sh:175`. An empty
  `STUDY_ID` requests `/studies/`, which is not the route, and reports "module route not mounted". The script already
  needs `python3` elsewhere (sections 7, 11, 14); fail-loud, no false pass. → Fall back to a fixed UUID literal, or check
  `STUDY_ID` is non-empty. Carried to TASK-239.

Style: no violation in the changed lines (`project-style`: Ruff and Black configs in `backend/pyproject.toml`; no text
style guide declared).

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
- 1.1 (2026-11-25) — Implemented (software developer role): CI step, `backend/scripts/check_image_modules.py`, smoke check 9b, TS-013 1.7 / TS-010 1.7. `in_review`.
- 1.1 (2026-11-25, QA) — Round 1 APPROVED (R1-1 MEDIUM, R1-2 to R1-4 LOW, carried to TASK-239); TASK-233 R1-2 image check run on image `57e3d35a9b47`. Status `approved`.
- 1.2 (2026-11-26) — TASK-239 (QA R1-1, R1-2, R1-4): the HEAD-396e9de wording replaced by QA's run on the pre-TASK-233 image `infra-backend:latest`; the image check also asserts `discover_modules()` (negative control: entry-point target `dicom_viewer.manifest:nope`, exit 1); smoke check 9b uses a fixed UUID. Content change on an approved record, so the status returns to `in_review`.
- 1.2 (2026-11-26, QA) — QA review of TASK-239 (round 1): R1-1 (`discover_modules()` assertion) and the R1-2 / R1-4 corrections verified; `approved` (status only; content unchanged).
