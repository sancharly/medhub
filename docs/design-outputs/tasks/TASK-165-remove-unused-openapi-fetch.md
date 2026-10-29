---
id: "TASK-165"
type: task
title: "Remove the unused openapi-fetch dependency"
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
  - target: "PRB-044"
    relation: relates_to
  - target: "TASK-162"
    relation: relates_to
  - target: "SOUP-033"
    relation: relates_to
tags: ["soup", "configuration-management", "cr:CR-003", "issue:sancharly/medhub#32", "control:design"]
---

# TASK-165 — Remove the unused openapi-fetch dependency

- **Software item / unit:** SI-FE-APICLIENT (ADD-023), with no runtime change; SI-DEVINFRA
  `U-INF-Toolchain` (`frontend/package.json`, `frontend/package-lock.json`)
- **Depends on:** TASK-162 (`relates_to`). That task's AC-5 check needs an unchanged lock, so this
  task's lock change comes after it, and the two lock diffs stay separate.
- **Branch:** `bug/soup-upgrades`
- **Size:** S
- **Needs:** network access (the npm registry, for `npm ci`). No Docker.

## Objective

Resolve the dependency part of PRB-044. `openapi-fetch` (SOUP-033) is declared as a runtime
dependency but never imported. Remove it from the manifest and the lock, and retire its SOUP
record. The SOUP list then matches what the product contains. That is RISK-010's design control
"SOUP list with exact versions, required functions and required HW/SW".

## Interfaces to honor

- No source file imports `openapi-fetch` or `openapi-typescript-helpers` (PRB-044 Investigation).
  `frontend/src/api/client.ts` and `frontend/src/api/generated/*` are not touched.
- The dev tool `openapi-typescript` (`generate:types`) stays. It is a different package.

## Implementation detail

1. **Baseline.** On Node 24 (after TASK-162), run `cd frontend && npm ci && npm run build`. Then
   record the checksum of the built files:
   `find dist -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$SCRATCH/dist-before.sha256"`.
2. `cd frontend && npm uninstall openapi-fetch`. Inspect `git diff frontend/package.json
   frontend/package-lock.json`:
   - `package.json` loses only the `"openapi-fetch"` line;
   - the lock loses only `node_modules/openapi-fetch`, `node_modules/openapi-typescript-helpers`
     and the root-package `dependencies` entry for `openapi-fetch`.

   Any other change, such as a version bump or a changed `lockfileVersion`, is reverted. Rebuild
   the lock with `npm install --package-lock-only` from a clean tree, and keep it only if the
   diff is the three removals (AC-10).
3. Run `npm ci && npm run lint && npm run typecheck && npm run build && npm test -- --run`. Then
   repeat the checksum into `dist-after.sha256`. The bundle is expected to be byte-identical. If
   it is not, explain the difference in the evidence before handoff.
4. **SOUP-033.** It is approved, so set `version` 1.2, remove the approval record and set
   `status: obsolete`.
   - Add a change-log entry
     `2026-10-29 — removed from frontend/package.json and package-lock.json; never imported (PRB-044, CR-003)`.
   - Add a sentence at the top of the body saying the item is no longer part of MedHub.
5. **CR-003** (D-6): remove the `relates_to` → SOUP-033 entry from `links`. The body keeps naming
   SOUP-033. Do not change CR-003's status.

## Acceptance criteria

- [ ] CR-003 **AC-10**: `openapi-fetch` appears in no section of `frontend/package.json`. The lock
      diff is exactly the three removals. `npm ci`, `npm run lint`, `npm run typecheck` and
      `npm run build` succeed.
- [ ] CR-003 **AC-11** (SOUP-033 part): SOUP-033 is `obsolete`, with its version bumped and a
      change-log entry citing PRB-044 and CR-003. CR-003 no longer links it (D-6). The links from
      ADD-023 and RISK-010 are handled by TASK-166 and the Risk stage.

## Verification

```sh
cd frontend && grep -c openapi-fetch package.json package-lock.json        # 0 and 0
cd frontend && npm ci && npm run lint && npm run typecheck && npm run build && npm test -- --run
git diff --stat frontend/package-lock.json                                 # only removals
diff "$SCRATCH/dist-before.sha256" "$SCRATCH/dist-after.sha256"            # expected: no output
grep -rlE 'target: "?SOUP-033"?$' docs | xargs grep -L '^status: obsolete'   # remaining non-obsolete linkers (ADD-023 until TASK-166)
```

## Definition of Done

- [ ] The frontend suite passes, and the CI frontend jobs and `openapi-lint` are green.
- [ ] SOUP-033 is `obsolete`.
- [ ] `traceability-check` shows no error for the touched records.
