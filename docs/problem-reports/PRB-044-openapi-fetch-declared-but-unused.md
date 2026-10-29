---
id: "PRB-044"
type: problem-report
title: "openapi-fetch is declared as a runtime dependency but MedHub does not use it"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["soup", "configuration-management", "documentation"]
---

# PRB-044 — openapi-fetch is declared as a runtime dependency but MedHub does not use it

## Observed

- `frontend/package.json:23` declares `"openapi-fetch": "^0.17.0"` under `dependencies`, and
  `frontend/package-lock.json` locks 0.17.0 with `openapi-typescript-helpers` 0.1.0.
- No file in `frontend/src` or `frontend/tests` imports `openapi-fetch` or
  `openapi-typescript-helpers`, so Vite leaves it out of the production bundle.
- MedHub's HTTP client is the hand-written `ApiClient` over the browser `fetch`
  (`frontend/src/api/client.ts`). It takes its types from `frontend/src/api/generated/types.ts`.
- ADD-004's SOUP table (row `openapi-fetch`, used by SI-FE-APICLIENT) says it is the "typed HTTP
  client generated from the OpenAPI contract, RFC 7807 handling". That is wrong.
- [SOUP-033](../soup/SOUP-033-openapi-fetch.md) records an item that the product does not use.
  TASK-154 corrected its functional-requirements section.

## Impact

- The SOUP list and the architecture description disagree with the code. A reviewer of ADD-004
  would attribute the typed client and the RFC 7807 handling to a SOUP item that is not in the
  product.
- A declared but unused dependency keeps getting reviewed and monitored, and it could be wired in
  later without a change analysis. This is the same class of finding as PRB-033 (fakeredis).

## Investigation

Mechanism, in the code (checked 2026-10-29):

- `frontend/package.json:23` lists `"openapi-fetch": "^0.17.0"` in `dependencies` (`:15-25`).
  `frontend/package-lock.json:4863-4870` locks it at 0.17.0 with one dependency,
  `openapi-typescript-helpers` `^0.1.0`. That dependency is locked at `:4891-4895`, without the
  `dev` flag, and `:4868` is the only entry that references it. Removing `openapi-fetch`
  therefore removes both packages and nothing else.
- Nothing references either package outside the manifest and the lock: grep of `frontend/src`,
  `frontend/tests` and the root config files (`vite.config.ts`, `vitest` and `tsconfig` files)
  finds nothing. `git log -S createClient -- frontend/src` is empty, so the client this package
  provides has never been used.
- The package arrived in commit `30748ca` (phase-6 frontend foundation, TASK-080..088,
  2026-06-23). That same commit added the hand-written `ApiClient`
  (`frontend/src/api/client.ts:41`), which imports only `./csrf` (`:1`) and types from
  `./generated/types` (`:2-21`). The dependency was declared for a design that was not built.

Mechanism, in the records. The design text describes the intended generated client, not the
implemented one, in more places than ADD-004:

- ADD-004 (`ADD-004-soup-list.md:93`) has been `obsolete` since 2026-10-21. It is superseded by
  the SOUP records, so it is no longer the live description.
- The live architecture record for SI-FE-APICLIENT is **ADD-023**
  (`ADD-023-frontend-api-client.md`). It links `relates_to` SOUP-033 (`:21-22`), and both its
  Responsibility (`:33`, "Typed client generated from OpenAPI") and its unit `U-FEAPI-Client`
  (`:37`, "generated typed client") describe a generated client.
- arc42 says the same in `docs/design/05-building-blocks.md:33` and `:124`,
  `docs/design/12-interfaces.md:48` ("methods generated from OpenAPI"),
  `docs/design/03-context-and-scope.md:31` and `docs/specifications/diagram-building-blocks.puml:14`.
- RISK-010 also links `relates_to` SOUP-033 (`RISK-010-unreviewed-soup-change.md:85-86`).

Only the request and response types are generated, by the dev tool `openapi-typescript`
(`frontend/package.json:13`, `generate:types`). The methods, the CSRF handling and the RFC 7807
handling are hand-written.

Root cause: nothing compares what the frontend declares as runtime dependencies with what it
imports. This is the gap behind PRB-033 (backend, declared but unused) and PRB-002 (imported but
undeclared). The architecture text was also written from the design intent and never checked
against the code.

## Safety evaluation

No hazard: the package is not in the bundle and no code path runs it. It affects no data
integrity, safety-related function or clinical decision, so the criticality is `minor`. The
anomaly review of 0.17.0 found no advisory (SOUP-033).

The record error is not harmless. ADD-023 implements SR-031, and SR-031.3's client-side control
(the CSRF header, `frontend/src/api/csrf.ts:1`, applied at `frontend/src/api/client.ts:55`,
RISK-005) is in-house code. ADD-023 attributes it to a "generated" client that is backed by a SOUP
item. A reviewer reading that could assume vendor code carries the control and skip reviewing the
hand-written client. This is a documentation defect with no effect at runtime, so the criticality
stays `minor`.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

In CR-003, a separate CR as for PRB-033:

- Remove `openapi-fetch` from `frontend/package.json` `dependencies` and refresh
  `frontend/package-lock.json` with no other version change.
- Set SOUP-033 to `obsolete`, with a change-log entry.
- Correct ADD-004's SI-FE-APICLIENT row to name the hand-written `ApiClient` and the generated
  types, and drop the SOUP row. *Superseded by the Investigation (2026-10-29):* ADD-004 is
  `obsolete`, so the correction applies to ADD-023 and the arc42 text listed there. ADD-004 only
  gets a correction note in its obsolete banner, as was done for `fhir.resources`. The `relates_to`
  links to SOUP-033 from ADD-023 and RISK-010 are removed.
- Check that the frontend suite and build still pass.

## Resolution

Resolved by CR-003 (`resolves` link on the CR) in TASK-165, TASK-166 and TASK-167, on branch
`bug/soup-upgrades`. The proposal was carried out as amended by the Investigation: the dependency
is removed, SOUP-033 is retired, and the live design text (ADD-023 and arc42) is corrected instead
of ADD-004, which only gets a note in its obsolete banner. The defect was in the records and in an
unused manifest entry. No runtime code changed (`frontend/src/api/client.ts` and
`frontend/src/api/generated/*` are untouched).

Changes:
- [TASK-165](../design-outputs/tasks/TASK-165-remove-unused-openapi-fetch.md):
  `frontend/package.json` loses the `"openapi-fetch"` dependency; `frontend/package-lock.json` loses
  `node_modules/openapi-fetch`, `node_modules/openapi-typescript-helpers` and the root-package
  dependency entry, with no other change. `docs/soup/SOUP-033-openapi-fetch.md` is `obsolete`
  (version 1.2, change-log entry citing PRB-044 and CR-003), and CR-003's `relates_to` link to
  SOUP-033 is removed (CR-003 D-6).
- [TASK-166](../design-outputs/tasks/TASK-166-correct-add-023-api-client-description.md):
  `docs/design-outputs/architecture/ADD-023-frontend-api-client.md` (version 1.1, `in_review`)
  describes the hand-written `ApiClient` with generated types in its Responsibility and in
  `U-FEAPI-Client`, and no longer links SOUP-033. `docs/design-outputs/architecture/ADD-004-soup-list.md`
  stays `obsolete` (version 1.1) with a correction note on the `openapi-fetch` row in its banner.
- [TASK-167](../design-outputs/tasks/TASK-167-correct-api-client-description-in-arc42.md):
  `docs/design/03-context-and-scope.md`, `docs/design/05-building-blocks.md` (table row and
  `U-FEAPI-Client`), `docs/design/12-interfaces.md` (SI-FE-APICLIENT row) and
  `docs/specifications/diagram-building-blocks.puml` say "hand-written" with types generated from
  OpenAPI. `docs/design/adr/0003-frontend-stack.md` was already accurate and is unchanged.
- RISK-010's `relates_to` link to SOUP-033 was removed at the Risk stage of CR-003 (RISK-010 change
  log). `docs/design/04-solution-strategy.md` (Frontend row) was also corrected, as a small addition
  to the arc42 text, so that section 04 agrees with ADD-023.

Verification, reproducible from the repository root. TASK-165 is commit `89f84c9`; its parent is
`4df23d2`.

```sh
# AC-10 (TASK-165): the package is gone from the manifest and the lock
git diff --numstat 4df23d2 89f84c9 -- frontend/package.json frontend/package-lock.json
#   0  14  frontend/package-lock.json   (root-package entry + two node_modules blocks)
#   0   1  frontend/package.json        (the "openapi-fetch" line)
(cd frontend && grep -c openapi-fetch package.json package-lock.json)      # 0 and 0, at 89f84c9 or later
(cd frontend && npm ci && npm run lint && npm run typecheck && npm run build && npm test -- --run)  # in the pinned node:24.22.2-trixie-slim image; results below are from that image

# Bundle unchanged: build both commits in the pinned image, then compare the SHA-256 of every dist/ file
IMG=node:24.22.2-trixie-slim@sha256:54f84b4cf8432b21aaffd5d3ce8d41e12cea0d10d33c09d2f3c9879d49d6b446
W="$(mktemp -d)"
for c in 4df23d2 89f84c9; do
  mkdir "$W/$c" && git archive "$c" frontend | tar -x -C "$W/$c"
  docker run --rm -v "$W/$c/frontend":/app -w /app "$IMG" sh -c 'npm ci && npm run build'
  (cd "$W/$c/frontend/dist" && find . -type f -print0 | sort -z | xargs -0 shasum -a 256) > "$W/$c.sha256"
done
diff "$W/4df23d2.sha256" "$W/89f84c9.sha256"                              # no output: identical

# AC-11/AC-12 (TASK-166): ADD-023 links no SOUP-033 and calls nothing "generated" but the types
grep -n 'SOUP-033' docs/design-outputs/architecture/ADD-023-frontend-api-client.md        # no link entry
grep -n -i 'generated' docs/design-outputs/architecture/ADD-023-frontend-api-client.md    # types only
grep -n 'PRB-044' docs/design-outputs/architecture/ADD-004-soup-list.md                   # banner note

# AC-12 (TASK-167): no arc42 text or diagram label says the client or its methods are generated
grep -n -i 'client generated\|generated typed client\|methods generated\|(generated from OpenAPI)' \
  docs/design/03-context-and-scope.md docs/design/05-building-blocks.md \
  docs/design/12-interfaces.md docs/specifications/diagram-building-blocks.puml          # no output
plantuml -checkonly docs/specifications/diagram-building-blocks.puml                      # exit 0
```

Results (TASK-165 and QA, 2026-10-29):

- Lock diff: `0 1` for `frontend/package.json` and `0 14` for `frontend/package-lock.json`, so the
  commit contains the removals only.
- `npm ci` added 466 packages. Lint gave 0 warnings, typecheck passed, Vitest passed (27 files, 155
  tests) and the build succeeded.
- Bundle: 16 of 16 `dist/` files are identical between `4df23d2` and `89f84c9`.
- TASK-166 and TASK-167 greps print nothing where "no output" is expected, and
  `plantuml -checkonly` exits 0.

The CI frontend jobs and `openapi-lint` are verified in TASK-168 (CR-003 AC-18). QA reviews
TASK-165, TASK-166 and TASK-167 together.

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12, frontend slice), on
2026-10-22. The evidence is in SOUP-033's "Anomaly list review" section. Outside CR-001 (A-4).
