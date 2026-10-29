---
id: "PRB-050"
type: problem-report
title: "Frontend image build copies the host's node_modules and dist because there is no .dockerignore"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-29"
criticality: minor
links: []
tags: ["build", "configuration-management", "reproducibility", "found-by:TASK-162-qa"]
---

# PRB-050 — Frontend image build copies the host's node_modules and dist because there is no .dockerignore

## Observed

`frontend/` has no `.dockerignore`, and neither has the repository root. The build stage of
`frontend/Dockerfile` runs `npm ci` (line 6) and then `COPY . .` (line 8). Because nothing is
excluded, `COPY . .` copies the build context into `/app` on top of what `npm ci` installed. When
the context is a developer's working tree, that includes:

- `frontend/node_modules/` (339 entries on the reference workstation), installed on the host. On a
  macOS workstation its native packages (for example esbuild and rollup) are macOS binaries, not
  Linux ones. The copy replaces the Linux packages that `npm ci` has just installed from
  `package-lock.json`.
- `frontend/dist/`, a previous host build, which `npm run build` then overwrites.

Both directories are git-ignored (`.gitignore:25`, `.gitignore:26`), so they exist only on a
developer's disk. The QA review of TASK-162 (CR-003) found this. The same Dockerfile line existed
before TASK-162, which did not change it.

Where it applies: a local `docker build ./frontend` and `docker compose -f infra/docker-compose.yml
build` (the `frontend` service uses `context: ../frontend`, `infra/docker-compose.yml:59`). The CI
`build` job builds from a fresh checkout (`.github/workflows/ci.yml:223`), which has no
`node_modules` or `dist`, so CI is not affected. Today's image is identical to a clean build.

## Impact

Reproducibility of local and Compose builds (IEC 62304 §5.8.5, SR-028): the image that a developer
builds can depend on the state of their disk (host `node_modules`, host platform) instead of only on
`package-lock.json` and the pinned base image. The consequences range from a slow build (the whole
`node_modules` tree is sent to the daemon as context) to a build that fails on a native module
built for another platform, or one that bundles with packages that are not the locked ones. Only the
first is certain, and none has been observed to change the shipped bundle's behaviour. The effect is
limited to local, development and pre-release images: the CI image comes from a clean checkout.

## Investigation

Root cause: no `.dockerignore`, so the build context equals the whole `frontend/` directory, and
`COPY . .` (`frontend/Dockerfile:8`) is placed after `npm ci` (line 6) so that it overwrites the
installed `node_modules`. The layer order was meant to cache `npm ci` on `package*.json` (lines
5–6), which it does, but the later `COPY . .` undoes the lock-exact install on any machine whose
working tree already has `node_modules`. The backend image does not have the problem: its
Dockerfile copies named paths only (`backend/Dockerfile:4-6`, `14-16`).

The QA review of TASK-162 reported that today's image is identical to a clean build, so the
defect has not changed any shipped artifact yet. A failing build or an image with non-locked
packages was not reproduced for this report.

## Safety evaluation

No effect on patient data, on a safety-related function or on a clinical decision. The defect is in
how developers build the frontend image locally, not in the application code or in the CI
pipeline that builds what is tested. No released version exists (`docs/releases/` is absent), so no
notification is needed. The risk it touches is RISK-010 (pinned, reproducible dependencies): a
local build can differ from the locked set, but the CI build, which is the reference, cannot.
Criticality `minor`.

## Proposed resolution

Add `frontend/.dockerignore` excluding at least `node_modules`, `dist` and local environment files,
and check that the CI `build` job and `docker compose build` still produce the same image. Resolve
it in a CR of its own; it is outside CR-003.
