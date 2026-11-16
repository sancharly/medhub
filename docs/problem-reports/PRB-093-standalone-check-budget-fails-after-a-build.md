---
id: "PRB-093"
type: problem-report
title: "Standalone check:budget fails with a stack trace after a build"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-15"
updated: "2026-11-15"
criticality: minor
links: []
tags: ["tooling", "frontend", "found-in:TASK-226", "outside:CR-006"]
---

# PRB-093 — Standalone check:budget fails with a stack trace after a build

## Observed

After `npm run build` in `frontend/`, `npm run check:budget` exits 1 with an uncaught ENOENT stack trace for `dist/.vite/manifest.json`. `package.json` defines `build` as `tsc && vite build && node scripts/check-bundle-budget.mjs --clean`, and `--clean` removes `dist/.vite` (the manifest) once the check has passed. The script (`frontend/scripts/check-bundle-budget.mjs`, `measureInitial`) reads the manifest without checking that it exists. Found by the Software Developer in TASK-226 (2026-11-15), who ran both commands in sequence.

## Impact

A developer who runs the documented `check:budget` script after a build sees a crash, not a verdict, and may read it as a failed budget or skip the check. The build's own run of the check is unaffected.

## Investigation

Reproduced in TASK-226 (`v226/r-budget.log`): `build` passed ("initial JavaScript 160.06 kB gzip ... within the budget"), then `check:budget` failed on the missing manifest. The script fails closed (exit 1). CI does not call `check:budget` on its own, and the `frontend/Dockerfile` runs `npm run build`, so no pipeline is affected. Two candidate fixes, to be chosen in a later change: (a) print a clear message when the manifest is missing ("run `npx vite build` first, or use `npm run build`") and exit 1; (b) make `check:budget` build first (`vite build` with the manifest, then check). Not fixed in TASK-226 (outside CR-006).

## Safety evaluation

No safety impact and no contribution to a RISK. The failure is closed: a missing manifest never reports "within the budget", so there is no false green. SR-026 AC 7 is verified by `npm run build` (TS-018 TC-018.10).

## Resolution

Not resolved. Needs a task and a change request.

## Source

TASK-226 round 1 QA review, LOW 3 (2026-11-15).

## Version history

- 1.0 (2026-11-15) — Created from the TASK-226 QA review. `open`, `minor`, outside CR-006.
