---
id: "PRB-035"
type: problem-report
title: "Frontend bundle is built on end-of-life Node 20"
status: open
version: "1.1"
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
