---
id: "TASK-236"
type: task
title: "Fail CI when the production image does not discover the module; smoke test answers 401"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-25"
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
   **TC-013.15** — Verifies SR-017 (AC 7), SR-028; the CI step; "fails on `HEAD` 396e9de (no entry point),
   passes after TASK-233". **TS-010** (1.5 from TASK-233, stays `in_review`): new **TC-010.9** — the smoke
   check, system level, SR-017 AC 7. Version-history lines.

## Verification

- Locally, the step's command against `docker build -t medhub-backend:ci ./backend` built at `HEAD` 396e9de
  (before TASK-233): exit 1; built on the branch after TASK-233: exit 0. Record both.
- `python3 -m unittest discover -s infra/tests -v` and `python3 infra/check_image_pins.py`: pass.
- The smoke check is executed on a started stack in TASK-239 (not here); here run `bash -n infra/smoke-test.sh`.
- `traceability-check` on TASK-236, TS-013, TS-010, CR-008: 0 errors.

## Acceptance criteria

- [ ] The Docker Build job fails on an image without the module entry point or NumPy, and passes on the
  branch image (SR-017 AC 7; TC-013.15).
- [ ] The smoke test checks that the module route answers 401 unauthenticated (TC-010.9).

## Definition of Done

- [ ] Negative and positive runs of the step recorded; infra tests and pin check green
- [ ] TS-013 and TS-010 updated; `traceability-check` 0 errors

## Carried from TASK-233 (QA, 2026-11-25)

TASK-233 R1-2: the manual image check (`docker build` and the `docker run` probe) was not run; Docker
Desktop stalled at `load metadata for docker.io/library/python:3.12.15-slim@sha256:cb33f7f7...`. Unless the
human decides otherwise, this task's Docker Build step is the image evidence for SR-017 AC 7, and it should
also check that `/app/modules` does not exist in the image and that `dicom_viewer.__file__` starts with
`/app/.venv/lib/python3.12/site-packages/`.

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
