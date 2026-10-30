---
id: "PRB-050"
type: problem-report
title: "Frontend image build copies the host's node_modules and dist because there is no .dockerignore"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-30"
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
it in a CR of its own; it is outside CR-003. (Superseded on 2026-10-30: CR-003 D-7 brought it into CR-003.)

## Resolution

Resolved by CR-003 (`resolves` link on the CR, decision D-7) in
[TASK-170](../design-outputs/tasks/TASK-170-add-frontend-dockerignore.md), on branch
`bug/soup-upgrades`. The proposal was carried out as written. `frontend/Dockerfile` and
`infra/docker-compose.yml` are unchanged.

Changes:
- `frontend/.dockerignore` (new) excludes `node_modules`, `dist` and `.env*` from the build
  context. Every file the build needs (`package*.json`, `index.html`, `public/`, `src/`, the
  TypeScript and Vite configs, `nginx.conf`) stays in it.

Verification, 2026-10-30, Docker Desktop (`DOCKER_CONTEXT=desktop-linux`, linux/arm64). Three
copies of `frontend/` were made from `git archive HEAD frontend`:

- **clean:** the archive plus the new `.dockerignore`;
- **dirty:** the same, plus the host's `frontend/node_modules` (339 entries, 394 MB, with the macOS
  packages `@esbuild/darwin-arm64` and `@rollup/rollup-darwin-arm64`), a stale
  `dist/STALE-HOST-BUILD.txt` and a `.env.local`;
- **dirty, no `.dockerignore`:** the dirty tree without the new file, as a control.

```sh
docker build --target build -t fe:<copy>-build <copy>/frontend   # build stage
docker build -t fe:<copy> <copy>/frontend                        # final image
docker run --rm --entrypoint sh fe:<copy>-build -c 'ls /app/node_modules/@esbuild /app/node_modules/@rollup; ls -a /app'
docker run --rm --entrypoint sh fe:<copy> -c 'cd /usr/share/nginx/html && find . -type f | sort | xargs sha256sum'
```

| Copy | Build-stage image ID | Final image ID | `@esbuild` / `@rollup` in `/app/node_modules` | `.env.local` in `/app` |
|---|---|---|---|---|
| clean | `sha256:5b76b792…7081` | `sha256:3be4792a…f6e1` | `linux-arm64` / `rollup-linux-arm64-gnu`, `-musl` | no |
| dirty | `sha256:5b76b792…7081` (same) | `sha256:3be4792a…f6e1` (same) | same as clean | no |
| dirty, no `.dockerignore` | `sha256:eed5a47d…da65` | not built | **`darwin-arm64`**, `linux-arm64` / **`rollup-darwin-arm64`**, `-gnu`, `-musl` | **yes** |

- With the file, the dirty tree gives the same build-stage and final image IDs as the clean tree.
  The IDs are content hashes over every layer, so the images are byte-identical. The 17 files
  under `/usr/share/nginx/html` also have identical SHA-256 sums (`diff` prints nothing).
- Without the file, the control reproduces the defect: the host's macOS packages and
  `.env.local` are copied into the build stage over the `npm ci` install. The stale `dist/` file
  does not survive, because `vite build` empties `dist/` first.
- The CI `build` job builds from a fresh checkout, which has no `node_modules`, `dist` or `.env*`,
  so its build context is the same with or without the file.
