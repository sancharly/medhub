---
id: "TASK-229"
type: task
title: "Clear message and exit 1 when the bundle budget check has no manifest"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-16"
updated: "2026-11-16"
links:
  - target: "SR-026"
    relation: implements
  - target: "CR-007"
    relation: relates_to
  - target: "PRB-093"
    relation: relates_to
  - target: "TS-018"
    relation: relates_to
  - target: "ADD-018"
    relation: relates_to
tags: ["cr:CR-007", "tooling", "frontend"]
---

# TASK-229 — Clear message and exit 1 when the bundle budget check has no manifest

- **Software items / units:** SI-FE-SHELL build check `frontend/scripts/check-bundle-budget.mjs` (ADD-018;
  TS-018 TC-018.10). Build-time only, not deployed.
- **PRB:** PRB-093. **CR:** CR-007 (D-1, fix option (a)).
- **Depends on:** none. Parallel with TASK-230 and TASK-231.
- **Branch:** `fix/cr-007-review-followups`.
- **Size:** XS (`frontend/scripts/check-bundle-budget.mjs`, `frontend/scripts/check-bundle-budget.test.mjs`;
  records). No `package.json`, API, schema or OpenAPI change.

## Objective

SR-026 AC 7 is checked by this script. Run on its own after `npm run build` (which removes `dist/.vite`
with `--clean`), it crashes with an uncaught ENOENT stack trace (`measureInitial`,
`check-bundle-budget.mjs:36`). It must instead give a verdict: a clear message that the manifest is
missing and how to produce it, and exit 1. The check stays fail closed: a missing manifest is never a
pass.

## Design

- In the command-line block (the `if (process.argv[1] ...)` branch), before `checkBudget(dist)`, check
  that `join(dist, ".vite", "manifest.json")` exists (`existsSync`). If not: print to stderr one message
  naming the missing path and saying "run `npm run build` (it runs this check), or `npx vite build`
  first to keep the manifest for a standalone check"; `process.exit(1)`. No stack trace.
- `measureInitial` and `checkBudget` stay unchanged (the unit tests import them; a programmatic caller
  still gets the exception). The missing `chunk-modules.json` with a present manifest is not a case
  `vite build` produces; it is left to the existing exception.
- Rejected: option (b), making `check:budget` build first (changes `package.json`; not chosen, D-1).

## Steps

1. Write the test below first; record it failing on `f47d617` (negative control: today it prints a
   stack trace).
2. Add the existence check and the message (Design).
3. Run the verification below.
4. Records (below), `graphify update .`.

## Tests (write first)

In `frontend/scripts/check-bundle-budget.test.mjs` (TS-018 TC-018.10):

- `a missing manifest gives a clear message and exit 1`: an empty temporary directory as `distDir`;
  `spawnSync(process.execPath, [script, dir])` → `status === 1`; stderr contains `manifest.json` and
  `npm run build`; stdout and stderr contain neither `within the budget` nor `ENOENT` nor `    at `
  (a stack frame).
- `a missing manifest with --clean removes nothing`: same with `--clean` → exit 1, the directory is
  unchanged.

## Verification

- `cd frontend && npx vitest run scripts/check-bundle-budget.test.mjs` — all tests pass, the new ones
  included.
- Reproducible command: `cd frontend && npm run build; echo "build=$?"; npm run check:budget; echo "check=$?"`
  → the build ends with "within the budget" and `build=0`; the check prints the message and `check=1`,
  with no stack trace. Record the output in the task.
- `npm run test -- --run`, `npm run lint` (frontend) green. Test on Node 20 or later as well as the
  local Node, since CI runs Node 24 (project memory).

## Records to update (developer)

- **TS-018** (approved 1.9 → 1.10, approval record removed, `in_review`): TC-018.10 lists the two new
  tests and the reproducible command.
- **PRB-093:** Resolution written (files, approach, verification); `resolved` once verified in the
  working tree (QA confirms). Version 1.1.

## Acceptance criteria

- [x] SR-026 AC 7 (check): run without a manifest, the budget check prints a message naming the missing
  manifest and `npm run build`, exits 1, and prints no stack trace and no "within the budget".
- [x] `npm run build` still runs the check and ends with "within the budget", exit 0; the existing
  TC-018.10 tests stay green.

## Definition of Done

- [x] Frontend tests, lint and build green
- [x] TS-018 and PRB-093 updated; `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-16) — Created at the CR-007 Plan stage (Software Architect role), D-1 fix option (a). `draft`.
- 1.0 (2026-11-16) — Developer handoff: implemented; `in_review`.
- 1.0 (2026-11-16) — QA review round 1: APPROVED, `in_review` to `approved`; acceptance criteria and Definition of Done ticked. TS-018 1.10 `approved`, PRB-093 1.2 `resolved`.

## Implementation record

- Negative control (`f47d617`, before the fix): the new test `a missing manifest gives a clear message and exit 1` failed (stderr held the uncaught ENOENT stack trace from `measureInitial` and no `npm run build`); the `--clean` test already passed, as the crash precedes any removal.
- Changed: `frontend/scripts/check-bundle-budget.mjs` (existence check, message, exit 1), `frontend/scripts/check-bundle-budget.test.mjs` (two tests).
- Node 20.19.0: `npx vitest run scripts/check-bundle-budget.test.mjs` 13 passed; `npm test -- --run` 41 files, 414 tests passed; `npm run typecheck` and `npm run lint` clean.
- Reproduction: `npm run build` -> "initial JavaScript 160.44 kB gzip (504.51 kB raw), budget 165.00 kB gzip: within the budget", exit 0. `npm run check:budget` -> "bundle budget check: no manifest at <frontend>/dist/.vite/manifest.json. Run `npm run build` (it runs this check), or `npx vite build` first to keep the manifest for a standalone check." exit 1, no stack trace.

## QA review round 1 (qa-engineer, 2026-11-16) — APPROVED

0 CRITICAL, 0 HIGH, 0 MEDIUM, 1 LOW (not blocking).

- **LOW-1** — TS-018 TC-018.10 cites the block as `describe("budget check without a manifest")`; the
  title in `frontend/scripts/check-bundle-budget.test.mjs:204` is
  `"budget check without a manifest (TC-018.10, PRB-093)"`. The test names match. Fix: quote the full
  title the next time TS-018 is changed.
- Pre-existing (not this task): TC-018.10's pass criteria still quote 160.06 kB gzip from the
  2026-11-15 build; the build measures 160.44 kB (TASK-226 R2 L-1 moved the AC 7 evidence to 160.44).

Verification (Node 20.19.0, working tree): `npx vitest run scripts/check-bundle-budget.test.mjs`
13 passed; `npm run test -- --run` 41 files, 414 tests passed; `npm run typecheck`, `npm run lint`
exit 0; Prettier check clean on both scripts. `npm run build` → "initial JavaScript 160.44 kB gzip
(504.51 kB raw), budget 165.00 kB gzip: within the budget", exit 0; `npm run check:budget` → the
missing-manifest message, exit 1, no stack trace, no `dist/.vite`. After `npx vite build`,
`npm run check:budget` passes (exit 0). Negative control: script at `HEAD` → the message test fails
and the `--clean` test passes (as recorded). Mutants: `process.exit(0)` → both new tests fail;
"within the budget" printed before `exit(1)` → the message test fails. Script restored, byte-identical
(`cmp`). TS-018: at `HEAD` it was `approved` 1.9 with no approval fields (they were removed in
`5207504`; the 1.9 approval was status only), so the developer's "nothing to strip" holds.
`traceability-check` on CR-007, TASK-229, TS-018, PRB-093, SR-026: 0 errors, 0 warnings.
