---
id: "TASK-167"
type: task
title: "Correct the API-client description in arc42 and the building-block diagram"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-30"
links:
  - target: "SR-031"
    relation: implements
  - target: "CR-003"
    relation: relates_to
  - target: "PRB-044"
    relation: relates_to
  - target: "TASK-166"
    relation: relates_to
tags: ["documentation", "architecture", "arc42", "cr:CR-003", "issue:sancharly/medhub#32"]
---

# TASK-167 — Correct the API-client description in arc42 and the building-block diagram

- **Software item / unit:** SI-FE-APICLIENT. arc42 narrative only; no code and no design element.
- **Depends on:** TASK-166 (`relates_to`). The arc42 text follows ADD-023's corrected wording.
- **Branch:** `bug/soup-upgrades`
- **Size:** S
- **Needs:** nothing beyond the repository. Optionally a PlantUML renderer to check that the
  diagram still compiles.
- **Role:** the Document Writer may do this task, because arc42 is the Document Writer's narrative
  (the `arc42` skill, `arc42-root: docs/design/`).

## Objective

Finish PRB-044. The arc42 sections and the building-block diagram repeat the claim that the
SPA's API client is "generated from OpenAPI". Make them say what the code does, in the same
words as ADD-023 (TASK-166): a hand-written `ApiClient` with generated types. Then resolve
PRB-044.

## Implementation detail

Change only the lines below, and match each file's existing table and line format:

- `docs/design/03-context-and-scope.md:31` (SPA ↔ Backend API row): "Hand-written typed client
  (`ApiClient`) with types generated from OpenAPI (api-design.md)".
- `docs/design/05-building-blocks.md:33` (SI-FE-APICLIENT row): "Hand-written typed `ApiClient`
  (types generated from OpenAPI); session/CSRF handling".
- `docs/design/05-building-blocks.md:124` (`U-FEAPI-Client`): the same text as ADD-023's unit line.
- `docs/design/12-interfaces.md:48` (SI-FE-APICLIENT row): replace "methods generated from
  OpenAPI" with "hand-written methods; request/response types generated from OpenAPI".
- `docs/specifications/diagram-building-blocks.puml:14`: the label becomes
  `"API Client\n(hand-written; types from OpenAPI)"`. Keep the alias and the colour tag, as the
  house PlantUML style requires.

`docs/design/adr/0003-frontend-stack.md:15` ("via generated client types") is accurate and is
not changed.

**PRB-044** → `status: resolved`, `version: "1.2"`, with a `## Resolution`. It names:

- the files of TASK-165, TASK-166 and this task;
- the AC-10 checks and the `dist/` checksum result;
- the record checks below.

## Acceptance criteria

- [x] CR-003 **AC-12** (arc42 part): no statement in `03-context-and-scope.md`,
      `05-building-blocks.md` (table row and unit), `12-interfaces.md` (SI-FE-APICLIENT row) or
      `diagram-building-blocks.puml` says that the client or its methods are generated.
- [x] CR-003 **AC-19** (PRB-044 part): PRB-044 is `resolved` with its `## Resolution`.

## Verification

```sh
grep -n -i 'client generated\|generated typed client\|methods generated\|(generated from OpenAPI)' \
  docs/design/03-context-and-scope.md docs/design/05-building-blocks.md \
  docs/design/12-interfaces.md docs/specifications/diagram-building-blocks.puml       # no output
```

If a renderer is available, run `plantuml -checkonly docs/specifications/diagram-building-blocks.puml`.

## Definition of Done

- [x] PRB-044 is `resolved`.
- [x] `traceability-check` shows no error for PRB-044 and CR-003.

## QA review (2026-10-29)

**Verdict: CHANGES REQUESTED** (`in_review → draft`). There is one HIGH finding.

The arc42 part is correct. The three sections and the diagram now agree with ADD-023, and
`plantuml -checkonly` passes. The PRB-044 `## Resolution` does not yet meet CR-003 AC-19, and it
does not meet this task's instruction to name "the AC-10 checks and the `dist/` checksum result".
QA unticked the AC-19 box. The AC-12 box and both Definition of Done items hold, so they stay
ticked: PRB-044 has `status: resolved`, and the parser shows 0 errors for PRB-044 and CR-003.

### Findings

- **[HIGH] PRB-044's Resolution records no results, and its verification cannot be repeated
  after the commit.**
  - `docs/problem-reports/PRB-044-openapi-fetch-declared-but-unused.md:159-160` says the `dist/`
    checksum result and the CI jobs "belong to TASK-165's evidence" and are covered "by
    reference". The PRB therefore states no outcome for the bundle check, which is the main
    evidence that removing the package changed nothing at runtime.
  - `:143` (`git diff --stat frontend/package-lock.json`) prints nothing once TASK-165 is
    committed.
  - `:145` diffs `$SCRATCH/dist-*.sha256` files that are not in the repository, and nothing says
    how to make them.
  - `:141-142` run `cd frontend` twice in sequence, so in one shell the second line fails.

  Fix: rewrite the AC-10 part of the verification block so that it works from any later commit.
  Then state the results that QA confirmed for TASK-165.
  - Lock diff:
    `git diff --numstat 4df23d2 "$(git log -1 --format=%H --grep='(TASK-165)')" -- frontend/package.json frontend/package-lock.json`.
    Expected: `0 1` and `0 14`, which are the root-package entry and the
    `node_modules/openapi-fetch` and `node_modules/openapi-typescript-helpers` blocks only.
  - Bundle: build `git archive 4df23d2 frontend` and the TASK-165 commit in
    `node:24.22.2-trixie-slim@sha256:54f84b4cf8432b21aaffd5d3ce8d41e12cea0d10d33c09d2f3c9879d49d6b446`.
    Then compare the sorted SHA-256 of each `dist/` file. Expected and observed: 16 files,
    identical.
  - Results to state: `npm ci` added 466 packages; lint gave 0 warnings; typecheck passed; Vitest
    ran 27 files and 155 tests, all passed; build passed.
  - Use one `cd frontend` (or subshells).
  - Say plainly that the CI frontend jobs are verified in TASK-168 (CR-003 AC-18).
- **[LOW] The RISK-010 bullet in the Resolution reads as future work.** `PRB-044…md:135` says
  "is removed at the Risk stage of CR-003, not here". It has already been removed: RISK-010 is
  approved without the link (`RISK-010-unreviewed-soup-change.md:246`). Fix: "was removed at the
  Risk stage of CR-003 (RISK-010 change log)".
- **[LOW] `docs/design/04-solution-strategy.md:11` still says "typed client from OpenAPI".**
  AC-12 does not list this file, so it does not block the task. But ADD-023 names section 04 as
  part of its narrative, and the phrase reads as "the client comes from OpenAPI". Fix, while the
  task is open: "hand-written typed `ApiClient` with types generated from OpenAPI".

### Pre-existing issues (not blocking)

- `docs/templates/task.md:76` (`api/(generated client)`) and `:90` ("typed client generated from
  OpenAPI") seed the wrong statement into every new TASK body. The template is not an
  architecture description and is outside AC-12. Recommended: correct both lines in a later
  documentation change. Historical TASK-080..091 bodies say "generated from OpenAPI" too. They
  are approved history and stay as they are.
- CR-003 is still `status: open`, although TASK-161..164 are committed. CR-001 went
  `open → in_progress`. The human should set `in_progress`.

### Verification run (QA, 2026-10-29)

| Check | Result |
|---|---|
| `git diff` of `03-context-and-scope.md:31`, `05-building-blocks.md:33` and `:124`, `12-interfaces.md:48`, `diagram-building-blocks.puml:14` | Each line matches the text in Implementation detail. The puml keeps the `FEApi` alias and `#lightblue` |
| `grep -n -i 'client generated\|generated typed client\|methods generated\|(generated from OpenAPI)'` over the four files | No output |
| `git grep` for generated-client wording across `docs/` | Live text: only `04-solution-strategy.md:11` (LOW above). `adr/0003-frontend-stack.md:15` ("generated client types") is accurate |
| `plantuml -checkonly docs/specifications/diagram-building-blocks.puml` | exit 0 |
| PRB-044 frontmatter and links | `resolved` 1.2, `updated` 2026-10-29. CR-003 carries `resolves` → PRB-044. The Safety evaluation has the §9.3 released-version statement |
| `traceability-check` (fallback parser), whole project | 0 errors |

## Rework after QA round 1 (2026-10-30)

- PRB-044 `## Resolution`: the AC-10 verification now diffs the commits `4df23d2` and `89f84c9`
  (`git diff --numstat`, run again on 2026-10-30: `0 14` for `frontend/package-lock.json` and
  `0 1` for `frontend/package.json`). The bundle comparison builds both commits from `git archive`
  in the pinned `node:24.22.2-trixie-slim` image and no longer refers to files outside the
  repository. The results are stated: `npm ci` 466 packages, lint 0 warnings, typecheck passed,
  Vitest 27 files and 155 tests passed, build passed, 16 of 16 `dist/` files identical, and the
  TASK-166 and TASK-167 greps and `plantuml -checkonly` clean. The CI frontend jobs and
  `openapi-lint` are verified in TASK-168 (CR-003 AC-18). The bundle and unit-test results are
  taken from TASK-165's and QA's runs; I did not rebuild the bundle.
- The double `cd frontend` is fixed (subshells). The RISK-010 bullet is in the past tense.
- Addition beyond AC-12's file list, made on QA's recommendation: `docs/design/04-solution-strategy.md`
  (Frontend row) now says "hand-written typed `ApiClient` with types generated from OpenAPI"
  instead of "typed client from OpenAPI".
- `docs/templates/task.md` is left alone (out of scope; to be raised separately).
- The AC-19 box stays unticked for QA.

## QA review, round 2 (2026-10-30)

**Verdict: APPROVED** (`in_review → approved`). The round-1 HIGH and both LOWs are resolved. QA
ticked the AC-19 box and set `updated` to 2026-10-30 to match version 1.2.

- **HIGH (resolved).** PRB-044's `## Resolution` now states its results. It diffs the fixed
  commits `4df23d2` and `89f84c9` and refers to no file outside the repository. Each command runs
  in one shell after the commit, and the double `cd` is now in subshells. QA ran both recipes as
  written.
- **LOW (resolved).** The RISK-010 bullet is in the past tense ("was removed at the Risk stage").
- **LOW (resolved).** The Frontend row of `docs/design/04-solution-strategy.md:11` now says
  "hand-written typed `ApiClient` with types generated from OpenAPI", the same wording as ADD-023.

### Findings

- **[LOW] PRB-044 `updated` is still 2026-10-29.** `docs/problem-reports/PRB-044-openapi-fetch-declared-but-unused.md:9`.
  The Resolution was rewritten on 2026-10-30. Fix: `updated: "2026-10-30"`. Version 1.2 can stay,
  because 1.2 has not been committed yet.
- **[LOW] The suite line in the Resolution runs on the host's Node.** In the Resolution's
  verification block, `(cd frontend && npm ci && … npm test -- --run)` does not name the pinned
  image, but the recorded results come from `node:24.22.2-trixie-slim@sha256:54f84b4c…`. Fix
  (optional): run it with the same `docker run … "$IMG"` form as the bundle loop, or add
  "(results from the pinned image)".

### Verification run (QA, 2026-10-30)

| Check | Result |
|---|---|
| `git diff --numstat 4df23d2 89f84c9 -- frontend/package.json frontend/package-lock.json` | `0 14 frontend/package-lock.json`, `0 1 frontend/package.json`. These match the Resolution. `git diff --stat 4df23d2 89f84c9` touches only the lock, the manifest, SOUP-033, CR-003 and TASK-165 |
| `git show 89f84c9:frontend/package{,-lock}.json \| grep -c openapi-fetch` | 0 and 0 |
| The Resolution's bundle loop, run verbatim with `DOCKER_CONTEXT=desktop-linux` | Both builds exited 0. `npm ci` added 468 packages at `4df23d2` and 466 at `89f84c9`. 16 `dist/` files each, and `diff` prints nothing. This agrees with QA's round-1 run |
| The AC-12 grep over sections 03-12 and the puml, plus `typed client from OpenAPI` | No output |
| `plantuml -checkonly docs/specifications/diagram-building-blocks.puml` | exit 0 |
| `grep -i 'scratch\|by reference\|is removed at'` in PRB-044 | No output |
| PRB-044 | `resolved` 1.2. CR-003 carries `resolves` → PRB-044 |
| `traceability-check` (fallback parser), whole project | 0 errors. W5 and W6 warnings as in round 1, all expected (CR-003 AC-19, D-6) |
