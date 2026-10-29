---
id: "TASK-162"
type: task
title: "Build the frontend and run CI on Node 24 LTS"
status: draft
version: "1.0"
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

- [ ] CR-003 **AC-3**: the build stage is `FROM node:24.22.2-trixie-slim@sha256:<64 hex> AS build`.
      The Node 24 LTS status and its 2028-04-30 end of life are recorded with their source. The
      nginx stage is unchanged.
- [ ] CR-003 **AC-4**: `frontend-quality` and `frontend-tests` use `node-version: "24"`.
      `openapi-lint` runs `actions/setup-node` with `"24"` before its first `npx` or `npm` step.
      No step name says "Node.js 20", and no job installs Node 20.
- [ ] CR-003 **AC-5**: the frontend image builds, `npm ci` and `npm run build` succeed in it, and
      `git diff --exit-code frontend/package-lock.json` is clean.
- [ ] CR-003 **AC-6**: TS-001..TS-013 name Node 24 in their environment line. TP-001, TR-001 and
      TR-002 are untouched.
- [ ] CR-003 **AC-19** (PRB-035 part): PRB-035 is `resolved` with its `## Resolution`.

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
- [ ] TS-001..TS-013 are `in_review` and PRB-035 is `resolved`.
- [ ] `traceability-check` shows no error for the touched records.
