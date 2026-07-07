---
id: "TASK-143"
type: task
title: "Unify frontend API client: upload path through request(), ProblemError drift guard"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-031"
    relation: relates_to
  - target: "TASK-080"
    relation: relates_to
  - target: "TASK-127"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:low"]
---

- **Phase:** Review 2026-07 — frontend
- **Depends on:** —
- **Branch:** `chore/api-client-unify`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — findings M + N (Low)

## Objective

1. `uploadAttachment` (`frontend/src/api/client.ts:136-160`) re-implements `fetch` + RFC 7807 error
   handling inline instead of routing through the shared `request<T>()`, duplicating the
   problem-parsing/`AuthError` logic — divergence risk (it already lacks the 401→`AuthError`
   branch `request()` has).
2. `ProblemError` in `api/generated/types.ts:17` is hand-written (deliberate override for optional
   `detail`), inside a file whose header says "do not hand-edit" — silent drift from the backend
   schema is possible and regeneration may clobber it.

## Implementation detail

- Extend `request()` to accept `FormData` bodies (skip JSON `Content-Type`, keep `withCsrf`), and
  route `uploadAttachment` through it so 401/problem handling is single-sourced.
- Derive `ProblemError` from the generated schema with an explicit local override:
  `type ProblemError = Omit<components["schemas"]["Problem"], "detail"> & { detail?: string }` (or
  equivalent), and move it out of the generated-alias file into a hand-maintained module if
  `generate:types` regenerates `types.ts`.

## Acceptance criteria

- [ ] One fetch/problem-parsing path in the client; upload failures produce the same
  `ApiError`/`AuthError` behavior as JSON endpoints (401 during upload triggers auth flow).
- [ ] `ProblemError` breaks the type-check if the backend Problem schema changes incompatibly.
- [ ] `npm run generate:types` round-trip leaves no diff beyond intended.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] `client.test.ts` covers FormData path incl. problem+json and non-problem errors
- [ ] Traceability note updated (relates SR-031 error-handling consistency)
