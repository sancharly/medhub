---
id: "PRB-044"
type: problem-report
title: "openapi-fetch is declared as a runtime dependency but MedHub does not use it"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-29"
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

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12, frontend slice), on
2026-10-22. The evidence is in SOUP-033's "Anomaly list review" section. Outside CR-001 (A-4).
