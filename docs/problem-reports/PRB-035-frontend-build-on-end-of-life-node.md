---
id: "PRB-035"
type: problem-report
title: "Frontend bundle is built on end-of-life Node 20"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
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

## Safety evaluation

No hazard is realized: the bundle's runtime dependencies are fixed by `frontend/package-lock.json`
and verified by the frontend suite. The concern is maintainability of the build chain (PLAN-002),
hence `minor`.

## Proposed resolution

Move the build stage and the CI frontend jobs to a supported Node LTS, re-pin the image by digest
and re-run the frontend suite and the Compose smoke test. Needs a task and a CR.

## Source

Raised during the Specify stage of CR-001 (2026-10-22), which leaves it out of scope.
