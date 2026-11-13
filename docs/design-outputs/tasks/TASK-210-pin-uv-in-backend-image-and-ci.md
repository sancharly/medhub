---
id: "TASK-210"
type: task
title: "Install one exact uv version in the backend image and in every CI job"
status: approved
version: "1.1"
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

- [x] CR-005 AC-3: `uv==0.13.7` in `backend/Dockerfile` and in all four CI jobs; no other uv
      install form remains; `uv lock --check` passes with uv 0.13.7.
- [x] CR-005 AC-10: the backend image built after the change has exactly the same distributions
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

## Build evidence (2026-11-12)

- Changed: `backend/Dockerfile:3` and `.github/workflows/ci.yml` lines 23, 93, 191, 287
  (`backend-quality`, `backend-tests`, `openapi-lint`, `object-store-integration`), each now
  `pip install uv==0.13.7`. `grep -rnE 'pip install uv'` returns exactly those 5 lines.
- `uvx --from uv==0.13.7 uv --version` prints `uv 0.13.7`; `uv lock --check` in `backend/`
  passes ("Resolved 86 packages"). No change to `uv.lock`, `pyproject.toml` or `uv sync` flags.
- AC-10: `medhub-backend:before` (built from HEAD 2f68c42, Dockerfile unchanged) and
  `medhub-backend:after` (built with the pin) were each frozen with the one-liner from *Tests*
  (57 distributions in `/app/.venv`). `diff before.txt after.txt` is empty. Both builds also
  produced the same image ID (`sha256:e3abceb37d35...`): `uv` lives only in the builder stage,
  which is not copied into the final stage. Scratch images removed.
- `python3 -m unittest discover -s infra/tests`: 114 tests, OK. `python3 infra/check_image_pins.py`:
  exit 0. Backend lint/type checks not run: no Python source changed.

## QA review (2026-11-12): APPROVED

No CRITICAL or HIGH finding.

### Findings

1. **LOW: SOUP-001 still calls the image's uv install unpinned.** `docs/soup/SOUP-001-python.md:67`
   (pip anomaly row, "Build time only" column): "`backend/Dockerfile` runs `pip install uv` ... The
   unpinned `pip install uv` is already PRB-034". After this task the install is `uv==0.13.7`. CR-005
   decided "SOUP-001 ... no record change", so this is outside TASK-210's files. → When PRB-034's
   `## Resolution` is written (TASK-211/CR-005 closure), change that cell to "runs
   `pip install uv==0.13.7` (pinned by CR-005)" and bump SOUP-001's version.
2. **Observation (not a finding): the "identical image ID" in Build evidence depended on when the
   build ran.** uv 0.13.8 was published on PyPI at 2026-11-12T16:48:15Z. A `--no-cache` rebuild of
   2f68c42 after that installs uv 0.13.8, and `/app/.venv/pyvenv.cfg` (shipped in the final image)
   then reads `uv = 0.13.8` against `uv = 0.13.7` after the change, so the image IDs differ. The
   distribution list is still identical, which is what AC-10 asks. The developer's identical ID is
   plausible: a "before" build made before 16:48Z also got 0.13.7, the builder's `.venv` was then
   byte-identical, and BuildKit reused the cached final-stage `COPY --from=builder` layer and every
   layer after it. The re-run shows the PRB-034 hazard the pin removes: the same commit built
   twice on one day got two uv versions.

### Verification run

- Scope: `git status --porcelain --untracked-files=all` and `git diff --stat` show only
  `backend/Dockerfile` (1 line), `.github/workflows/ci.yml` (4 lines, only the `run:` of the four
  "Install uv" steps) and this record. `backend/uv.lock` and `backend/pyproject.toml` are unchanged
  against 2f68c42.
- Every uv install in the repo: a `git grep` over Dockerfiles, workflows, shell/Python scripts,
  `*.toml`/`*.yml` and the non-record Markdown (README, CLAUDE.md, arc42) for `pip|pipx|uv tool|brew
  install uv`, `astral.sh`, `setup-uv` and `ghcr.io/astral-sh/uv` finds exactly the five
  `uv==0.13.7` lines (`backend/Dockerfile:3`; `ci.yml:23,93,191,287` = `backend-quality`,
  `backend-tests`, `openapi-lint`, `object-store-integration`). No other Dockerfile, script or
  how-to installs uv. Only records mention the old form (finding 1; CR, PRB and TASK history text).
- `uvx --from uv==0.13.7 uv --version`: `uv 0.13.7 (316c827e0 2026-11-03)`. `uv lock --check` in
  `backend/` with it: "Resolved 86 packages", exit 0.
- AC-10, re-run independently with `--no-cache`: context = `git archive 2f68c42 backend`, "after"
  context = the same plus the working-tree `Dockerfile`. Frozen list of `/app/.venv` (the *Tests*
  one-liner): 57 distributions each, `diff` empty. A sha256 of every file in `/app/.venv` (5981
  files) differs only in `pyvenv.cfg` (`uv = 0.13.8` vs `uv = 0.13.7`, see 2). Scratch images
  removed.
- `python3 -m unittest discover -s infra/tests`: 114 tests, OK. `python3 infra/check_image_pins.py`:
  exit 0.
- Workflow: `uv run --no-project --with pyyaml` loads it (8 jobs); the four "Install uv" `run:`
  values are `pip install uv==0.13.7`. `rhysd/actionlint:1.7.7` (Docker, shellcheck and pyflakes
  off): exit 0.
- RISK-010 control claimed by this task: implemented (one exact uv everywhere) and verified by the
  AC-10 comparison. CI enforcement is TASK-211's.
- `traceability-check` (fallback parser, scope CR-005 with two link hops, 171 records): 0 errors;
  7 W6 and 2 W5, all on older records (ADD-003, CR-002, TASK-142, 148, 165, 175, 176, 202), none
  on a CR-005 record. Scope TASK-210 with two hops (113 records): 0 errors, the 6 known W6.

## Records

PRB-034 (resolution by TASK-211), CR-005. ADD-024 and ADD-026 are updated by TASK-211 and
TASK-214 (no unit description changes here beyond the version).

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
- 1.0 (2026-11-12) — Built (Software Developer role); evidence below; `in_review`.
- 1.1 (2026-11-12) — QA review: APPROVED (1 LOW, 1 observation). `in_review → approved`; AC-3 and
  AC-10 ticked.
