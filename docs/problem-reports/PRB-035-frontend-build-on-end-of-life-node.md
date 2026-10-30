---
id: "PRB-035"
type: problem-report
title: "Frontend bundle is built on end-of-life Node 20"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-29"
criticality: minor
links: []
tags: ["configuration-management", "maintenance"]
---

# PRB-035 — Frontend bundle is built on end-of-life Node 20

## Observed

`frontend/Dockerfile` builds the shipped bundle in a `node:20-slim` stage, and
`.github/workflows/ci.yml` runs the frontend jobs on `node-version: "20"`. Node.js 20 reached end
of life on 2026-04-30 and no longer receives security fixes.

## Impact

- The build runtime is not shipped, so it is not SOUP, but it produces the shipped bundle. A
  defect or compromise in an unsupported toolchain cannot be fixed upstream.
- CR-001 pins `node:20-slim` by digest, which makes the build reproducible but freezes it on the
  unsupported runtime.

## Investigation

Where Node 20 runs (checked 2026-10-29):

- **Image build.** `frontend/Dockerfile:1` is the build stage
  `FROM node:20.20.2-slim@sha256:2cf067cfed83d5ea958367df9f966191a942351a2df77d6f0193e162b5febfc0 AS build`.
  It runs `npm ci` (`:6`) and `npm run build` (`:9`). Only `/app/dist` is copied into the nginx
  runtime stage (`:11-12`), so Node is not in the shipped image. CI builds this image in the
  `build` job (`.github/workflows/ci.yml:216-217`).
- **CI lint, type check and tests.** `frontend-quality` (`.github/workflows/ci.yml:114-117`) and
  `frontend-tests` (`:140-143`) install Node with `actions/setup-node@v4` and
  `node-version: "20"`. ESLint, `tsc` and Vitest therefore run on Node 20.
- **CI contract check.** `openapi-lint` has no `setup-node` step. It runs
  `npx --yes @redocly/cli` (`:193`) and `npm ci` / `npm run generate:types` (`:199-200`) on
  whatever Node the `ubuntu-latest` runner image provides. The repository does not set that
  version (the same class of finding as PRB-034).
- **Local development.** `frontend/package.json` has no `engines` field and there is no
  `.nvmrc`, so nothing constrains the Node version developers use.
- **Records.** TS-001 to TS-013 name "frontend Node 20" as their verification environment
  (for example `TS-001-authentication-password-policy-lockout-and-session.md:39`).

Root cause. `node:20-slim` was chosen when the frontend image was added (commit `2d095f8`,
TASK-004, 2026-06-20), after Node 20's end of life on 2026-04-30, and CI copied the same major.
The support status of the build runtime was not checked when it was chosen. Because the build
image is tooling, not SOUP (CR-001 A-3), it is also outside the SOUP review cadence of PLAN-002,
so nothing would have flagged it. CR-001 pinned it by digest (TASK-155, D-3). That made the build
reproducible but froze it on the unsupported runtime.

## Safety evaluation

No hazard is realized: the bundle's runtime dependencies are fixed by `frontend/package-lock.json`
and verified by the frontend suite. The concern is maintainability of the build chain (PLAN-002),
hence `minor`.

The build toolchain produces the bundle that carries the client-side parts of risk controls: the
CSRF header that `withCsrf` adds (`frontend/src/api/csrf.ts:1`, applied in
`frontend/src/api/client.ts:55`, SR-031, RISK-005), the RFC 7807 error handling, and idle-timeout
handling. A defect in Node 20 that changed the emitted bundle would weaken those controls without
any change to MedHub's code. No such defect is known. Exploiting an unpatched Node 20 flaw at
build time would need hostile input to the build, and `npm ci` installs only the locked,
integrity-checked packages. Data integrity, safety-related functions and clinical decisions are
not affected today, so the criticality stays `minor`.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

Move the build stage and the CI frontend jobs to a supported Node LTS, re-pin the image by digest
and re-run the frontend suite and the Compose smoke test. Needs a task and a CR (CR-003).

## Source

Raised during the Specify stage of CR-001 (2026-10-22), which leaves it out of scope.

## Resolution

Resolved by TASK-162 under CR-003 (2026-10-29).

- **`frontend/Dockerfile:1`** build stage is now
  `FROM node:24.22.2-trixie-slim@sha256:54f84b4cf8432b21aaffd5d3ce8d41e12cea0d10d33c09d2f3c9879d49d6b446 AS build`.
  The digest is the index digest from `docker buildx imagetools inspect` on 2026-10-29 and equals the
  one selected in CR-003. The explicit `-trixie-slim` tag is used because the bare `-slim` alias
  resolves to bookworm for Node 24 (D-2). The nginx runtime stage is unchanged, and the image pin
  check (`infra/check_image_pins.py`, RISK-010) still passes.
- **`.github/workflows/ci.yml`**: `frontend-quality` and `frontend-tests` use `node-version: "24"`
  (step renamed "Set up Node.js 24"). `openapi-lint` gains an `actions/setup-node@v4` step with
  `node-version: "24"` before its first `npx` or `npm` step (Q-3), so it no longer runs on the
  runner's default Node. No job installs Node 20.
- **Support evidence.** Node.js release schedule (https://github.com/nodejs/Release, `schedule.json`,
  checked 2026-10-29): v24 "Krypton" Active LTS from 2025-10-28, Maintenance LTS from 2026-10-20,
  end of life 2028-04-30. v20 end of life 2026-04-30. Every locked frontend package that declares a
  `node` engine range (303 entries in `frontend/package-lock.json`, checked 2026-10-29) has a range
  that includes 24.
- **Records.** TS-001..TS-013 name "frontend Node 24 LTS" in their environment line and are
  `in_review` (new versions). TP-001, TR-001 and TR-002 are unchanged: they are evidence of past
  runs on Node 20.

Verification (2026-10-29):

- `docker build -t medhub-frontend:ci ./frontend` succeeded: `npm ci` and `npm run build` ran in the
  Node 24 stage, and the emitted `dist` was byte-identical to the previous build (checked by
  building `--target build` from clean copies with the Node 20 and the Node 24 Dockerfile and
  comparing the SHA-256 of every file under `/app/dist`: 16 files, identical).
- `git diff --exit-code frontend/package-lock.json` is clean (AC-5).
- In `node:24.22.2-trixie-slim` (Node v24.22.2, npm 11.19.1): `npm ci`, `npm run lint`,
  `npm run typecheck` and `npm test -- --run` passed (27 files, 155 tests).
- `infra/smoke-test.sh` against the running Compose stack: 17 passed, 0 failed.
- CI logs on the branch head showing Node v24 (CR-003 AC-18) are pending the push.
