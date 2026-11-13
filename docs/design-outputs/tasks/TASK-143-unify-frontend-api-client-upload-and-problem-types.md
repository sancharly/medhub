---
id: "TASK-143"
type: task
title: "Attachment upload through the shared request helper; ProblemError derived from the schema"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-13"
links:
  - target: "SR-030"
    relation: implements
  - target: "SR-031"
    relation: implements
  - target: "SR-027"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-019"
    relation: relates_to
  - target: "ADD-023"
    relation: relates_to
  - target: "TS-011"
    relation: relates_to
  - target: "TASK-080"
    relation: relates_to
  - target: "TASK-127"
    relation: relates_to
tags: ["phase:review-2026-07", "cr:CR-006", "frontend", "control:design"]
---

# TASK-143 — Attachment upload through the shared request helper; ProblemError derived from the schema

- **Software item / unit:** SI-FE-APICLIENT `api/client.ts`, `api/generated/types.ts` aliases (ADD-023).
- **PRB:** PRB-019. **CR:** CR-006.
- **Depends on:** none (parallel; frontend). TASK-146 tests its final shape.
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S (`frontend/src/api/client.ts`, `frontend/src/api/problem.ts` (new, hand-written),
  `frontend/src/api/generated/types.ts` only through `npm run generate:types` if the generator owns it;
  tests `frontend/src/api/client.test.ts`; records TS-011).

## Objective

- SR-030 AC 8 and the RISK-005 control: a 401 during an upload ends the session like any other request
  (`AuthError`, one redirect). `uploadAttachment` (`api/client.ts:136-160`) has its own `fetch` without the
  401 branch.
- SR-031 / SR-027 AC 3: upload failures (the 150 MiB refusal of TASK-135 included) produce the same
  `ApiError` with the server's problem `detail` as JSON endpoints.
- `ProblemError` is hand-written in `api/generated/types.ts:17`, a generated-alias file (CLAUDE.md: never
  hand-edit generated files).

## Implementation detail

- `request<T>()` accepts a `FormData` body: no JSON `Content-Type` (the browser sets the boundary),
  `withCsrf` kept; `uploadAttachment` becomes a call to `request()`.
- `ProblemError` moves to `api/problem.ts`:
  `type ProblemError = Omit<components["schemas"]["ProblemDetail"], "detail"> & { detail?: string }` (name the
  schema as the OpenAPI document does). Imports updated; `types.ts` regenerated, not edited.

## Tests (write first)

- `uploadAttachment sends FormData through request with the CSRF header` (SR-031 AC 3).
- `uploadAttachment 401 raises AuthError` (SR-030 AC 8; RISK-005).
- `uploadAttachment problem+json 413/400 surfaces the server detail` (SR-027 AC 3); non-problem 500 → generic
  `ApiError`.
- `npm run typecheck` fails if the `ProblemDetail` schema loses a field `ProblemError` uses (a type-level test
  file with `// @ts-expect-error` on a removed field).
- `npm run generate:types` round-trip: no diff.
- Recorded in TS-011 (1.3 → 1.4, approval cleared).

## Acceptance criteria

- [ ] One fetch and problem-parsing path; a 401 during upload raises `AuthError`.
- [ ] `ProblemError` derived from the generated schema, outside generated files; regeneration leaves no diff.

## Definition of Done

- [ ] `npm run lint`, `npm run typecheck`, `npm test -- --run` green
- [ ] TS-011, ADD-023 consistent; `traceability-check` no error for this record

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect). Re-based on SR-030 AC 8 (401 on upload ends the
  session; RISK-005 control) and SR-027 AC 3; `mitigates` RISK-005 added; `ProblemError` moved out of the
  generated-alias file.
