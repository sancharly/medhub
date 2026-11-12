---
id: "TASK-210"
type: task
title: "Install one exact uv version in the backend image and in every CI job"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-12"
updated: "2026-11-12"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-005"
    relation: relates_to
  - target: "PRB-034"
    relation: relates_to
  - target: "ADD-024"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
  - target: "TASK-209"
    relation: relates_to
tags: ["ci", "reproducibility", "build", "cr:CR-005", "control:design"]
---

# TASK-210 — Install one exact uv version in the backend image and in every CI job

- **Software items / units:** SI-DEVINFRA `U-INF-CIPipeline` (ADD-024); the backend image build
  stage (`backend/Dockerfile`, SI-DEPLOY, ADD-026).
- **PRB:** PRB-034. **CR:** CR-005 (AC-3, AC-10).
- **Depends on:** TASK-209 (same workflow file). Ordered before TASK-214 (same Dockerfile) and
  TASK-211.
- **Branch:** `bug/build-hygiene`.
- **Size:** S (`backend/Dockerfile`, `.github/workflows/ci.yml`).
- **Needs:** a Docker daemon (AC-10).

## Objective

SR-028 AC-8, package manager: `uv` is installed as `uv==X.Y.Z` in the backend image build and in
the four CI jobs that install it, the same version everywhere, and the shipped image content does
not change (CR-005 §7.4: a wrong pin must not change the image).

## Implementation detail

1. Version: **`0.13.7`**, the version every Python job of hosted run 42779806388 (2026-11-10)
   installed ("Successfully installed uv-0.13.7"), with which `uv lock --check` last passed on
   hosted CI (CR-005 A-5). If `uv lock --check` fails with it locally, stop and ask.
2. `backend/Dockerfile:3`: `RUN pip install uv==0.13.7`.
3. `.github/workflows/ci.yml`: `pip install uv==0.13.7` in `backend-quality`, `backend-tests`,
   `openapi-lint` and `object-store-integration`.
4. No change to `uv.lock`, `pyproject.toml` or the `uv sync` flags.

## Tests (write first)

AC-10 is a before/after comparison. Before editing, build the image at HEAD and freeze its
installed set into a scratch directory:

```sh
docker build -t medhub-backend:before ./backend
docker run --rm --entrypoint /app/.venv/bin/python medhub-backend:before -c \
  "import importlib.metadata as m; print('\n'.join(sorted(f'{d.metadata[\"Name\"].lower()}=={d.version}' for d in m.distributions())))" > before.txt
```

## Acceptance criteria

- [ ] CR-005 AC-3: `uv==0.13.7` in `backend/Dockerfile` and in all four CI jobs; no other uv
      install form remains; `uv lock --check` passes with uv 0.13.7.
- [ ] CR-005 AC-10: the backend image built after the change has exactly the same distributions
      and versions in `/app/.venv` as the image built before it (`diff` empty), for the same
      `backend/uv.lock`.

## Verification

```sh
grep -rnE 'pip install uv' backend/Dockerfile .github/workflows/ci.yml   # 5 lines, all uv==0.13.7
uvx --from uv==0.13.7 uv --version && (cd backend && uvx --from uv==0.13.7 uv lock --check)
docker build -t medhub-backend:after ./backend
docker run --rm --entrypoint /app/.venv/bin/python medhub-backend:after -c "<same one-liner>" > after.txt
diff before.txt after.txt     # empty
python3 -m unittest discover -s infra/tests
```

Remove the two scratch images afterwards (`docker image rm medhub-backend:before medhub-backend:after`).

## Records

PRB-034 (resolution by TASK-211), CR-005. ADD-024 and ADD-026 are updated by TASK-211 and
TASK-214 (no unit description changes here beyond the version).

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
