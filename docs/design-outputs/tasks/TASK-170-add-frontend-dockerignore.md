---
id: "TASK-170"
type: task
title: "Exclude host build output from the frontend image context"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-003"
    relation: relates_to
  - target: "PRB-050"
    relation: relates_to
  - target: "TASK-162"
    relation: relates_to
tags: ["build", "configuration-management", "reproducibility", "cr:CR-003", "issue:sancharly/medhub#32", "control:design"]
---

# TASK-170 — Exclude host build output from the frontend image context

- **Software item / unit:** SI-DEVINFRA `U-INF-Toolchain` (ADD-024): the frontend image build
  (`frontend/Dockerfile`, build context `frontend/`)
- **Depends on:** none. TASK-162 set the build stage this task builds with (`relates_to`).
- **Branch:** `bug/soup-upgrades`
- **Size:** XS
- **Needs:** a Docker host (`DOCKER_CONTEXT=desktop-linux`) and network access (registry, npm).

## Objective

Resolve PRB-050 (CR-003 D-7). With no `.dockerignore`, `COPY . .` (`frontend/Dockerfile:8`)
copies a working tree's `node_modules` and `dist` over what `npm ci` installed from the lock. A
local or Compose image can then depend on the developer's disk instead of only on
`package-lock.json` and the pinned base image (SR-028 AC-5, RISK-010). Exclude those paths from
the build context, so a local build gets the same inputs as the CI build from a clean checkout.

## Interfaces to honor

- `frontend/Dockerfile` and `infra/docker-compose.yml` are not changed.
- Nothing the build needs is excluded: `package*.json`, `index.html`, `public/`, `src/`, the
  TypeScript and Vite configs and `nginx.conf` stay in the context.

## Implementation detail

1. Create `frontend/.dockerignore` with `node_modules`, `dist` and `.env*` (git-ignored local
   environment files; none is committed under `frontend/`).
2. Verify on a scratch copy of the tree:
   - **Clean:** `git archive HEAD frontend` extracted to a scratch directory, image built from it.
   - **Dirty:** the same tree plus the host's `frontend/node_modules` (macOS binaries) and a stale
     `dist/` with a marker file, image built from it with the new `.dockerignore`.
   - Compare SHA-256 per file of `/usr/share/nginx/html` in the two images, and check that the
     build stage of the dirty build holds no host-only file (the `dist` marker, a macOS-only
     package such as `@esbuild/darwin-arm64`).
   - Optionally build the dirty tree without the `.dockerignore` to show the defect (expected:
     the darwin packages appear in the build stage).

## Acceptance criteria

- [x] CR-003 **AC-21**: `frontend/.dockerignore` excludes `node_modules`, `dist` and `.env*`. The
      dirty-tree image serves the same files, byte for byte, as the clean image, and its build
      stage holds only what `npm ci` installed.

## Verification

```sh
cat frontend/.dockerignore
# clean and dirty builds, then per-file checksums of /usr/share/nginx/html (see Implementation detail)
DOCKER_CONTEXT=desktop-linux docker build -t medhub-fe:clean "$SCRATCH/clean/frontend"
DOCKER_CONTEXT=desktop-linux docker build -t medhub-fe:dirty "$SCRATCH/dirty/frontend"
```

## Definition of Done

- [x] Both images build. The per-file checksums match.
- [x] PRB-050 is `resolved`, with a `## Resolution`.
- [x] `traceability-check` shows no error for the touched records.

## Evidence (developer handoff, 2026-10-30)

Docker Desktop (`DOCKER_CONTEXT=desktop-linux`, linux/arm64). The clean, dirty and control trees
and the commands are in PRB-050 `## Resolution`, with the results table. In short:

- `frontend/.dockerignore` lists `node_modules`, `dist`, `.env*`, with a two-line comment.
- Dirty tree (host `node_modules`, 339 entries, 394 MB, macOS esbuild and rollup binaries; stale
  `dist/`; `.env.local`) with the file: build stage `sha256:5b76b792…7081` and final image
  `sha256:3be4792a…f6e1`, both identical to the clean `git archive` tree. The 17 served files have
  identical SHA-256 sums.
- Control without the file: build stage `sha256:eed5a47d…da65`, with `@esbuild/darwin-arm64`,
  `@rollup/rollup-darwin-arm64` and `.env.local` in `/app`. That is the PRB-050 defect.
- **Incident during the run:** the first control build failed with "no space left on device":
  Docker Desktop's disk was full (14 GB of build cache). With the human's approval,
  `docker builder prune -f` freed 13.83 GB of unused build cache (no image, container or volume
  removed), and the builds were re-run. The test image tags were removed afterwards.
- PRB-050 is `resolved` 1.1 with its `## Resolution`.
- **Not run:** the CI `build` job (needs the pushed branch). Its context is a fresh checkout,
  which the clean tree reproduces.

## QA review (2026-10-30)

**Verdict: APPROVED** (`in_review → approved`). There is no CRITICAL, HIGH, MEDIUM or LOW finding.
QA rebuilt the clean and dirty trees itself, with fresh scratch copies, and did not rebuild the
no-`.dockerignore` control. The control result is the developer's, in PRB-050 `## Resolution`.

**Review notes.**
- `frontend/.dockerignore` holds `node_modules`, `dist` and `.env*`, which are all git-ignored
  (`.gitignore` `node_modules/`, `frontend/dist/`, `.env.*`). `git ls-files frontend` has no `.env*`
  file, so nothing committed is excluded. Everything the Dockerfile and `npm run build` (`tsc && vite
  build`) need stays in the context. `frontend/Dockerfile` and `infra/docker-compose.yml` are unchanged.
- PRB-050 proposed to check `docker compose build` too. The Compose `frontend` service builds
  `context: ../frontend` with `dockerfile: Dockerfile`, no target and no build args
  (`infra/docker-compose.yml:58-60`). That is the same build as `docker build frontend`, so the
  result below covers it.
- The dirty build hit the build cache at `COPY . .` and gave the same build-stage image ID as the
  clean one. BuildKit keys that step on the content of the copied files, so the two contexts were
  identical.

### Findings

None.

### Verification run (QA, 2026-10-30)

Docker Desktop, `DOCKER_CONTEXT=desktop-linux` (linux/arm64). Scratch trees: `git archive HEAD
frontend` plus the working-tree `frontend/.dockerignore`. The dirty tree also holds a copy of the
host `frontend/node_modules` (`@esbuild/darwin-arm64`, `@rollup/rollup-darwin-arm64`),
`dist/STALE-HOST-BUILD.txt` and `.env.local`. The image tags were removed afterwards.

| Check | Result |
|---|---|
| `docker build --target build` clean / dirty | Both `sha256:5b76b792…7081` |
| `docker build` (final image) clean / dirty | Both `sha256:3be4792a…f6e1` |
| Build stage: `ls /app/node_modules/@esbuild /app/node_modules/@rollup; ls -a /app` | Both: `linux-arm64` / `rollup-linux-arm64-gnu`, `rollup-linux-arm64-musl`. No darwin package, no `.env.local`, no `dist/STALE-HOST-BUILD.txt` |
| `find /usr/share/nginx/html -type f \| sort \| xargs sha256sum`, clean vs dirty | 17 files each; `diff` prints nothing |
| PRB-050 | `resolved` 1.1. `## Resolution` names the file and the commands, and the results match. CR-003 1.4 has `resolves` PRB-050 |
| `traceability-check` (fallback parser, whole project) | 0 errors. No warning names TASK-170, PRB-050 or CR-003 |
