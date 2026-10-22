---
id: "PRB-044"
type: problem-report
title: "openapi-fetch is declared as a runtime dependency but MedHub does not use it"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
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

## Safety evaluation

No hazard: the package is not in the bundle and no code path runs it. It affects no data
integrity, safety-related function or clinical decision, so the criticality is `minor`. The
anomaly review of 0.17.0 found no advisory (SOUP-033).

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

In a separate CR, as for PRB-033:

- Remove `openapi-fetch` from `frontend/package.json` `dependencies` and refresh
  `frontend/package-lock.json` with no other version change.
- Set SOUP-033 to `obsolete`, with a change-log entry.
- Correct ADD-004's SI-FE-APICLIENT row to name the hand-written `ApiClient` and the generated
  types, and drop the SOUP row.
- Check that the frontend suite and build still pass.

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12, frontend slice), on
2026-10-22. The evidence is in SOUP-033's "Anomaly list review" section. Outside CR-001 (A-4).
