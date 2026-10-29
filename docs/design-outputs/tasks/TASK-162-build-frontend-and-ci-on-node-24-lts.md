---
id: "TASK-162"
type: task
title: "Build the frontend and run CI on Node 24 LTS"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-29"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-003"
    relation: relates_to
  - target: "PRB-035"
    relation: relates_to
  - target: "RISK-005"
    relation: relates_to
tags: ["configuration-management", "maintenance", "cr:CR-003", "issue:sancharly/medhub#32", "control:design"]
---

# TASK-162 — Build the frontend and run CI on Node 24 LTS

- **Software item / unit:** SI-DEVINFRA `U-INF-Toolchain` and `U-INF-CIPipeline` (ADD-024); the
  `frontend/Dockerfile` build stage, which builds the SI-FE-* bundle
- **Depends on:** none. Commit it after TASK-161, because both edit `.github/workflows/ci.yml`
  (in different jobs).
- **Branch:** `bug/soup-upgrades`
- **Size:** M (two code files, plus the same one-line record edit in TS-001..TS-013)
- **Needs:** a Docker host for the local image build (CI's `build` job also covers it), and
  network access (Docker Hub, npm registry)

## Objective

Resolve PRB-035: the shipped bundle is built on Node 20, which reached end of life on 2026-04-30.

- Move the build stage, the CI frontend jobs and `openapi-lint` to Node 24 LTS (Q-2, Q-3, D-2).
  Node 24 is in Maintenance LTS until 2028-04-30.
- Re-pin the build image by digest. This keeps RISK-010's pinning control for the build image.

The build image stays tooling, not SOUP (A-3), so it gets no SOUP record.

## Interfaces to honor

- `npm ci` and `npm run build` in the build stage, and `COPY --from=build /app/dist` into the nginx
  stage, do not change. The nginx runtime stage
  (`nginx:1.31.8-alpine@sha256:e2d97c2b…77a8`) does not change (AC-3).
- `frontend/package-lock.json` must not change (AC-5). Do not run `npm install`.
- Out of scope (PRB-034): pinning `node-version` to a patch, pinning actions by SHA, `engines` or
  `.nvmrc` (CR-003 Out of scope).

## Implementation detail

1. **Resolve the image.** Value selected on 2026-10-29:
   `node:24.22.2-trixie-slim@sha256:54f84b4cf8432b21aaffd5d3ce8d41e12cea0d10d33c09d2f3c9879d49d6b446`.
   Re-resolve it with `docker buildx imagetools inspect node:24.22.2-trixie-slim` (`Digest:`
   line). Use the explicit `-trixie-slim` tag, because the bare `-slim` alias resolves to
   bookworm for Node 24 (D-2).
2. `frontend/Dockerfile:1` → `FROM node:24.22.2-trixie-slim@sha256:<digest> AS build`.
3. `.github/workflows/ci.yml`:
   - In `frontend-quality` and `frontend-tests`, rename the step "Set up Node.js 20" to
     "Set up Node.js 24" and set `node-version: "24"`. The `cache` settings stay.
   - In `openapi-lint` (Q-3), add this step after "Install uv" and before "Export OpenAPI
     schema", so it runs before the first `npx` or `npm` step:

     ```yaml
     - name: Set up Node.js 24
       uses: actions/setup-node@v4
       with:
         node-version: "24"
         cache: npm
         cache-dependency-path: frontend/package-lock.json
     ```

   - Check: `grep -n 'node-version\|Node.js' .github/workflows/ci.yml` shows only `24`.
4. **Support evidence (AC-3).** Record the Node.js release schedule, with the date of the check:
   https://github.com/nodejs/Release (`schedule.json`), v24 in maintenance from 2026-10-20, end
   2028-04-30. Also record that every locked frontend toolchain package declares a `node` engine
   range that includes 24 (`frontend/package-lock.json`, checked 2026-10-29).
5. **TS-001..TS-013** (AC-6). Each is `approved`, so bump its `version` (TS-007 1.1 → 1.2,
   TS-013 1.3 → 1.4, the rest 1.0 → 1.1), remove its approval record and set `in_review`. In
   "Preconditions and environment", replace `frontend Node 20` with `frontend Node 24 LTS
   (build stage node:24.22.2-trixie-slim; CI node-version 24)`. Change nothing else.
   - TS-008 and TS-013 are changed again by TASK-163 and TASK-168. Those tasks keep the version
     set here.
   - TP-001, TR-001 and TR-002 are not changed.
6. **PRB-035** → `status: resolved`, `version: "1.2"`, with a `## Resolution`. It names the changed
   files, the selected image, the CI settings and the verification below.

## Acceptance criteria

- [x] CR-003 **AC-3**: the build stage is `FROM node:24.22.2-trixie-slim@sha256:<64 hex> AS build`.
      The Node 24 LTS status and its 2028-04-30 end of life are recorded with their source. The
      nginx stage is unchanged.
- [x] CR-003 **AC-4**: `frontend-quality` and `frontend-tests` use `node-version: "24"`.
      `openapi-lint` runs `actions/setup-node` with `"24"` before its first `npx` or `npm` step.
      No step name says "Node.js 20", and no job installs Node 20.
- [x] CR-003 **AC-5**: the frontend image builds, `npm ci` and `npm run build` succeed in it, and
      `git diff --exit-code frontend/package-lock.json` is clean.
- [x] CR-003 **AC-6**: TS-001..TS-013 name Node 24 in their environment line. TP-001, TR-001 and
      TR-002 are untouched.
- [x] CR-003 **AC-19** (PRB-035 part): PRB-035 is `resolved` with its `## Resolution`.

## Verification

```sh
python3 infra/check_image_pins.py                                      # exit 0
docker build -t medhub-frontend:ci ./frontend                          # AC-5
git diff --exit-code frontend/package-lock.json                        # AC-5
grep -n 'node-version\|Node.js' .github/workflows/ci.yml               # AC-4
grep -ln 'frontend Node 20' docs/design-outputs/tests-specifications/  # no output (AC-6)
cd frontend && npm ci && npm run lint && npm run typecheck && npm test -- --run   # on Node 24 locally
```

CI on the branch head: `frontend-quality`, `frontend-tests`, `openapi-lint` (types in sync) and
`build` pass, and their logs show Node v24 (AC-18).

## Definition of Done

- [ ] All frontend CI jobs and `build` are green. The frontend suite passes locally on Node 24.
- [x] TS-001..TS-013 are `in_review` and PRB-035 is `resolved`.
- [x] `traceability-check` shows no error for the touched records.

## QA review (2026-10-29)

**Verdict: APPROVED** (`in_review → approved`). No CRITICAL, HIGH or MEDIUM finding. QA re-ran each
claim on the reference workstation (`desktop-linux` context, arm64), on clean scratch copies of
`frontend/` (no `node_modules`, no `dist`), the way CI checks out the repository.

The first Definition of Done item stays unticked. CI on the branch head cannot run before the
commit exists. CR-003 assigns AC-18, and the CI `build` job part of AC-5, to TASK-168. The local
half of that item (frontend suite on Node 24) passed.

TS-001..TS-013 are sound, but QA leaves them `in_review`. CR-003 AC-19 requires every record the
CR changes to be `in_review`, and the human approves them at CR close. This is the same decision as
under CR-001.

### Findings

- **[LOW] PRB-035's "byte-identical" claim cannot be reproduced as written.**
  `docs/problem-reports/PRB-035-frontend-build-on-end-of-life-node.md:111-112` infers that the
  emitted `dist` is byte-identical from a cached `COPY --from=build` layer. In BuildKit, that cache
  hit is content-keyed, so the inference is sound. But it cannot be reproduced on a host without the
  developer's cache, and it does not name the build it was compared with. The context of that
  build also included the host's `frontend/node_modules` (darwin-arm64) and `frontend/dist`. QA
  confirmed the claim directly (see below). Fix: replace the parenthesis with "(checked by building
  `--target build` from clean copies with the Node 20 and the Node 24 Dockerfile and comparing the
  SHA-256 of every file under `/app/dist`: 16 files, identical)".

### Observations (not findings)

- **Position of the `openapi-lint` step.** `.github/workflows/ci.yml:187-192` places `setup-node`
  after "Install backend dependencies", not after "Install uv" as step 3 says. The two backend steps
  do not use Node. The step still runs before the first `npx` (`:200`) and `npm` (`:206`) call, so
  AC-4 and Q-3 hold.
- **TS environment lines.** The TS records now name Node 24 next to a build commit (for example
  TS-001 `40401a1`) whose recorded run used Node 20. No TR records a Node 24 run yet. This follows
  AC-6 as written. The TASK-168 end-to-end run and its report close the gap.
- The running Compose `frontend` container serves a bundle identical to the clean Node 24 build
  (16 of 16 files; nginx's `50x.html` is extra). So the 17/17 smoke result covers the Node 24
  bundle.

### Pre-existing issues (not blocking)

- **`frontend/` has no `.dockerignore`.** `frontend/Dockerfile:8` runs `COPY . .` after `npm ci`. A
  local or Compose build therefore copies the host's `node_modules` (here darwin-arm64 `@esbuild`
  and `@rollup` binaries, installed 2026-07-17) and `dist` over the container's install. CI is not
  affected, because a fresh checkout has neither. Today's output is unaffected: the clean-context
  image has the same ID as the developer's `medhub-frontend:ci` (`sha256:3be4792a…52f6e1`).
  Recommended: a PRB for a `frontend/.dockerignore` that excludes `node_modules` and `dist`.
- `npm ci` reports 16 npm audit findings (4 moderate, 9 high, 3 critical). They are unchanged by
  this task, which leaves the lock untouched. They are an input to the frontend SOUP anomaly
  reviews.

### Verification run (QA, 2026-10-29)

| Check | Result |
|---|---|
| `docker buildx imagetools inspect node:24.22.2-trixie-slim` | `Digest: sha256:54f84b4c…b6d446`, equal to `frontend/Dockerfile:1`. OCI index for amd64 and arm64/v8, base `debian:trixie-slim` |
| `git diff` on `frontend/Dockerfile` | Only line 1 changes. nginx stage `nginx:1.31.8-alpine@sha256:e2d97c2b…77a8` unchanged |
| `python3 infra/check_image_pins.py`; `python3 -m unittest discover -s infra/tests` | exit 0; 11 tests OK |
| `grep -n 'node-version\|Node.js\|setup-node\|npx\|npm' .github/workflows/ci.yml` | `node-version: "24"` at `:117`, `:143`, `:190`. No "Node.js 20" and no `"20"`. In `openapi-lint`, setup-node (`:187`) comes before `npx` (`:200`) and `npm ci` (`:206`) |
| nodejs/Release `schedule.json`; nodejs.org `dist/index.json` | v24 Krypton: LTS 2025-10-28, maintenance 2026-10-20, end 2028-04-30. v20 end 2026-04-30. v24.22.2 released 2026-10-27 |
| Engine ranges in `frontend/package-lock.json`, checked with `semver.satisfies('24.22.2', …)` | 303 packages declare `engines.node`, and none excludes 24.22.2 |
| `docker build --no-cache --target build`, clean copy, Node 24 | `npm ci` added 468 packages, with no `EBADENGINE`. `npm run build` succeeded |
| `--target build` with the Node 20 (HEAD) and the Node 24 Dockerfile, clean copies; SHA-256 of `/app/dist` | 16 files each, identical |
| `docker build -t medhub-frontend:qa162` (full image, clean copy) | Succeeded. The image ID equals the developer's `medhub-frontend:ci`. No `node` in the runtime image; nginx 1.31.8 |
| In `node:24.22.2-trixie-slim@sha256:54f84b4c…` (v24.22.2, npm 11.19.1), clean copy: `npm ci`, `lint`, `typecheck`, `test -- --run`, `build` | All exit 0. Vitest: 27 files, 155 tests passed |
| `git diff --exit-code frontend/package-lock.json`; `git status --short frontend/` | Clean. Only `frontend/Dockerfile` is modified |
| `grep -rln 'Node 20' docs/design-outputs/tests-specifications/`; `git diff` of TS-001..013 | No output. Each TS changes only status, version (TS-007 1.2, TS-013 1.4, the rest 1.1), `updated`, the removed approval record and the environment line. TP-001, TR-001 and TR-002 unchanged |
| PRB-035 | `resolved` 1.2. `## Resolution` names the files, the image, the CI settings and the verification. `## Safety evaluation` has the §9.3 released-version statement. CR-003 carries `resolves` → PRB-035. RISK-010 `:175` already cites the resolution |
| `bash infra/smoke-test.sh` (running stack) | 17 passed, 0 failed |
| `traceability-check` (fallback parser), scope TASK-162, PRB-035, CR-003, TS-001..013 | 0 errors. 14 × W5: TASK-161 → SOUP-021, and TP-001 → TS-001..013 (approved → `in_review`, expected under CR-003 AC-19). Whole project: 0 errors, 21 × W5, plus `soup_without_risk` on SOUP-033 (TASK-165 scope) |
