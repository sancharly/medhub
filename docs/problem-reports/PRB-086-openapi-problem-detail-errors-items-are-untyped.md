---
id: "PRB-086"
type: problem-report
title: "OpenAPI ProblemDetail errors items are untyped, so the frontend overrides them"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["contract", "openapi", "found-in:TASK-143-qa"]
---

# PRB-086 — OpenAPI ProblemDetail errors items are untyped, so the frontend overrides them

## Observed

Found by QA in the TASK-143 review (2026-11-14). The OpenAPI document declares `ProblemDetail.errors` as an array of
`{"type": "object"}` (`backend/app/api/openapi.py:78`), which `openapi-typescript` generates as `Record<string, never>[]`.
The backend always emits `{field, rule, message}`, all required strings (`backend/app/api/errors.py:22-25, 55, 189-193`).

## Impact

The contract does not describe the field-level errors the API sends. The frontend cannot use the generated type for them and
carries a hand-written override of `errors` in `frontend/src/api/problem.ts` (TASK-143). If the backend shape changes, nothing
fails the contract check. Contract documentation only; no behaviour is wrong.

## Investigation

`openapi.py:70-80` replaces `components.schemas.ProblemDetail` by hand with an inline dictionary, and the `errors` items are
left as a bare object. The item model exists in code (`class ProblemDetail(BaseModel)` with `field`, `rule`, `message` at
`errors.py:22`) but is never registered in the OpenAPI components. Note the naming clash: the Pydantic class `ProblemDetail`
is the error item, while the OpenAPI schema `ProblemDetail` is the whole problem document. A fix has to avoid registering the
item under the name `ProblemDetail`.

## Safety evaluation

No data integrity, safety-related function or clinical decision is involved: the responses are correct, only their description
is loose. No released version's behaviour is affected, so no notification is needed. Criticality `minor`.

## Resolution

Not fixed here, and outside CR-006. Fix to apply later: register an item schema under a non-clashing name (for example
`ProblemFieldError`, renaming the Pydantic item class to match), `$ref` it from `errors.items`, regenerate `openapi.json` and
`openapi.ts` (CLAUDE.md OpenAPI workflow), then drop the `errors` override from `frontend/src/api/problem.ts` and its comment.
Verify with `npm run typecheck`, the frontend suite and the `openapi-lint` check.
