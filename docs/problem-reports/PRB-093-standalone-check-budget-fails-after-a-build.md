---
id: "PRB-093"
type: problem-report
title: "Standalone check:budget fails with a stack trace after a build"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-15"
updated: "2026-11-16"
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

Fix option (a) chosen (CR-007 D-1), implemented in TASK-229. `frontend/scripts/check-bundle-budget.mjs`: the command-line block checks that `dist/.vite/manifest.json` exists before `checkBudget`; if not, it prints to stderr a message naming the path and saying to run `npm run build` (which runs the check) or `npx vite build` first to keep the manifest, and exits 1. `measureInitial` and `checkBudget` are unchanged (a programmatic caller still gets the exception); no `package.json` change. The check stays fail closed.

Verification (Node 20.19.0, working tree): two new tests in `frontend/scripts/check-bundle-budget.test.mjs` (TS-018 TC-018.10), first recorded failing on `f47d617` (stack trace, no `npm run build` in stderr), now passing; frontend suite 414 passed, `typecheck` and `lint` clean. Reproduction after the fix: `npm run build` ends with "initial JavaScript 160.44 kB gzip ... within the budget" and exit 0; `npm run check:budget` then prints "bundle budget check: no manifest at .../dist/.vite/manifest.json. Run `npm run build` ..." and exits 1, no stack trace.

QA confirmation (TASK-229 review, 2026-11-16, Node 20.19.0, working tree): the two new tests pass and the full suite passes (41 files, 414 tests); `typecheck`, `lint` and Prettier clean. `npm run build` → "160.44 kB gzip ... within the budget", exit 0; `npm run check:budget` → the missing-manifest message, exit 1, no stack trace. After `npx vite build` the standalone check passes (exit 0). With the script at `HEAD` the message test fails; with the exit code changed to 0, or with "within the budget" printed before the exit, the new tests fail. `resolved` (CR-007 holds the `resolves` link).

## Source

TASK-226 round 1 QA review, LOW 3 (2026-11-15).

## Version history

- 1.0 (2026-11-15) — Created from the TASK-226 QA review. `open`, `minor`, outside CR-006.
- 1.1 (2026-11-16) — TASK-229: investigation updated with the CR-007 choice; resolution written. `investigating`.
- 1.2 (2026-11-16) — QA approved TASK-229: Resolution confirmed in the working tree; status `investigating` → `resolved` (CR-007 D-1). Criticality unchanged.
