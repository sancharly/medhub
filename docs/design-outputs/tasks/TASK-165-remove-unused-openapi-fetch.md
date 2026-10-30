---
id: "TASK-165"
type: task
title: "Remove the unused openapi-fetch dependency"
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

- [x] CR-003 **AC-10**: `openapi-fetch` appears in no section of `frontend/package.json`. The lock
      diff is exactly the three removals. `npm ci`, `npm run lint`, `npm run typecheck` and
      `npm run build` succeed.
- [x] CR-003 **AC-11** (SOUP-033 part): SOUP-033 is `obsolete`, with its version bumped and a
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
- [x] SOUP-033 is `obsolete`.
- [x] `traceability-check` shows no error for the touched records.

## Evidence (developer handoff, 2026-10-29)

All commands ran inside `node:24.22.2-trixie-slim@sha256:54f84b4cf8432b21aaffd5d3ce8d41e12cea0d10d33c09d2f3c9879d49d6b446`
(Node v24.22.2, npm 11.19.1, the CI image), on a scratch copy of `frontend/` without `node_modules`
or `dist`. Only `package.json` and `package-lock.json` were copied back into the repo.

- **Baseline** (unchanged tree): `npm ci` then `npm run build` succeed. `dist/` has 16 files.
- **Change**: `npm uninstall openapi-fetch`.
  - `frontend/package.json`: one line removed (`"openapi-fetch": "^0.17.0"`).
  - `frontend/package-lock.json`: 14 deletions, 0 insertions. They are the root-package
    `dependencies` entry for `openapi-fetch`, the `node_modules/openapi-fetch` block and the
    `node_modules/openapi-typescript-helpers` block. `lockfileVersion` and every other version are
    unchanged, so there was no need to rebuild the lock.
- **Grep**: `grep -c openapi-fetch frontend/package.json frontend/package-lock.json` gives 0 and 0.
  No file under `frontend/src`, `frontend/tests`, the root config files, `frontend/Dockerfile` or
  `.github` mentions `openapi-fetch` or `openapi-typescript-helpers`. `openapi-typescript` (the
  `generate:types` dev tool) is untouched.
- **After** (clean `node_modules`): `npm ci` (466 packages) succeeds, as does `npm run lint`
  (0 warnings) and `npm run typecheck`. `npm test -- --run`: 27 files, 155 tests passed.
  `npm run build` succeeds.
- **`dist/` checksum**: `sha256sum` of the 16 files (sorted, relative paths) before and after is
  identical (`diff` prints nothing), so the bundle is byte-identical.
- **Records**: SOUP-033 is `obsolete` 1.2 with a change-log entry citing PRB-044 and CR-003.
  CR-003's `relates_to` SOUP-033 link is removed (D-6; status unchanged). The only non-obsolete
  record that still links SOUP-033 is this task, as CR-003 D-6 intends. PRB-044 is not changed
  here: it resolves in TASK-167.
- **Not run**: the CI frontend jobs and `openapi-lint` (they need the pushed branch), and
  `traceability-check` (left to QA).

## QA review (2026-10-29)

**Verdict: APPROVED** (`in_review → approved`). There is no CRITICAL, HIGH or MEDIUM finding. QA
re-ran every claim in the pinned CI image, on clean copies of `frontend/` with no `node_modules`
and no `dist`. The baseline copy is `git archive HEAD` (4df23d2), and the changed copy is the
working tree.

The first Definition of Done item stays unticked. The CI frontend jobs and `openapi-lint` cannot
run before the branch is pushed, and CR-003 assigns AC-18 to TASK-168. The local half of the item
(the frontend suite) passed.

**`anomaly_review` on an obsolete record.** Keeping `anomaly_review: "2026-10-22"` is correct.
design-record-structure defines the field as optional, the "date of the last anomaly-list review".
SOUP-033 was reviewed on that date (TASK-154), so the value is a true historical fact. SOUP-018 did
not drop the field: it never had one, because it was obsoleted (TASK-158) before its first review,
and the field has been absent since 388ddf8. The two records are consistent. Neither needs a future
review, and the fallback parser skips obsolete SOUP.

**D-6.** After this task, TASK-165 is the only record that is not `obsolete` and still links
SOUP-033 (`relates_to`, one W6). That is what D-6 intends. AC-11's literal wording ("no record that
is not `obsolete` keeps a `relates_to` link to SOUP-033") does not allow it, so the TASK-168 AC-11
check should apply the D-6 reading, and the human should confirm that reading at CR close.

### Findings

- **[LOW] SOUP-033's banner gives the wrong reason.** `docs/soup/SOUP-033-openapi-fetch.md:22`
  copies SOUP-018's "Development tooling that is not shipped is not SOUP". `openapi-fetch` was a
  runtime `dependencies` entry, not development tooling. It is no longer SOUP because it is no
  longer a dependency at all. Fix: replace that sentence with "It is no longer a dependency, so it
  is not SOUP; it was never imported."
- **[LOW] SOUP-033's requirements section is still in the present tense.** `:26-27` says "It is
  declared in `frontend/package.json` `dependencies` (`^0.17.0`, locked at 0.17.0)". That is no
  longer true. SOUP-018 rewrote the same section in the past tense when it became obsolete. Fix:
  "It was declared in `frontend/package.json` `dependencies` (`^0.17.0`, locked at 0.17.0) until
  CR-003 (TASK-165) removed it." The dated anomaly-review text can stay as it is.

### Verification run (QA, 2026-10-29)

| Check | Result |
|---|---|
| `git diff --numstat frontend/` | `package.json` 0/1, `package-lock.json` 0/14. The removed lock lines are the root-package `"openapi-fetch": "^0.17.0"` entry, the `node_modules/openapi-fetch` block (0.17.0) and the `node_modules/openapi-typescript-helpers` block (0.1.0). `lockfileVersion`, every other entry and `openapi-typescript` 7.13.0 are unchanged |
| `git grep -nE 'openapi-fetch\|openapi-typescript-helpers' -- . ':!docs'` | No match (exit 1). `frontend/src` uses only `./csrf` and `./generated/types` in `client.ts` |
| Baseline in `node:24.22.2-trixie-slim@sha256:54f84b4c…b6d446` (v24.22.2, npm 11.19.1): `npm ci`, `npm run build` | Succeeded. `dist/` has 16 files |
| Changed tree, same image: `npm ci`, then `lint`, `typecheck`, `test -- --run`, `build` | `npm ci` added 466 packages. `node_modules/openapi-fetch` and `openapi-typescript-helpers` are absent, and `openapi-typescript` is present. Lint gave 0 warnings, and typecheck exited 0. Vitest: 27 files, 155 tests passed. Build succeeded |
| SHA-256 of every `dist/` file, sorted relative paths, before and after | 16 files each. `diff` prints nothing, so the bundle is byte-identical |
| SOUP-033 frontmatter and change log | `obsolete` 1.2, `updated` 2026-10-29, approval record removed, `soup_version` 0.17.0 kept. The change-log entry cites PRB-044 and CR-003 |
| `grep -rlE 'target: "?SOUP-033"?$' docs` | Only TASK-165. CR-003, ADD-023 and RISK-010 no longer link it (RISK-010, approved, `:246`) |
| `bash infra/smoke-test.sh` (running stack) | 17 passed, 0 failed |
| `traceability-check` (fallback parser), whole project | 0 errors. 1 × W6 (TASK-165 → SOUP-033 obsolete, intended by D-6), plus the W5s expected under CR-003 AC-19. No `soup_*` warning for any non-obsolete SOUP |
