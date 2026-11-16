---
id: "PRB-019"
type: problem-report
title: "Upload bypasses the shared request helper and `ProblemError` is hand-written in a generated file"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-15"
criticality: minor
links: []
tags: ["correctness"]
---

# PRB-019 — Upload bypasses the shared request helper and `ProblemError` is hand-written in a generated file

## Observed

`frontend/src/api/client.ts:136-160` re-implements fetch and RFC 7807 handling instead of routing through `request<T>()` — and already lacks its 401→`AuthError` branch. `ProblemError` lives in `api/generated/types.ts:17`, a file whose header says it is generated and must not be hand-edited.

## Impact

Divergent error handling between upload and every other call, and a hand-written type that regeneration can clobber. Touches the SR-031 error contract.

## Safety evaluation

No hazard: failures surface as errors, not as wrong data.

## Resolution

TASK-143, change request CR-006 (verified in the working tree, 2026-11-14):

- `frontend/src/api/client.ts`: `request<T>()` accepts a `FormData` body (no JSON `Content-Type`, so the browser sets the multipart boundary; `withCsrf` kept), and `uploadAttachment` is now one call to `request()`. The duplicate fetch and problem parsing are gone.
  - A 401 `/errors/unauthenticated` during an upload now raises `AuthError` (SR-030 AC 8; RISK-005; the redirect on a mutation's `AuthError` is TASK-144), and `AttachmentUpload` shows its detail.
  - A problem+json refusal (413, 400) or a non-problem 500 gives the same `ApiError` as every other call (SR-027 AC 3, SR-031).
- `frontend/src/api/problem.ts` (new): `ProblemError` derived from the generated `ProblemDetail` schema; the hand-written copy is removed from `api/generated/types.ts`, and its importers read it from `api/problem.ts`.
- Verified by `frontend/src/api/client.test.ts` (`ApiClient uploadAttachment`, 5 cases; the 401 case failed before the change), `AttachmentUpload.test.tsx` (401 message), `frontend/src/api/problem.test-d.ts` (typecheck fails when `ProblemDetail` loses `detail`, `errors` or `instance`, checked by hand), and `npm run generate:types` leaving no diff. `npm run typecheck`, `npm run lint`, `npm test -- --run` (322 passed when TASK-143 landed; 412 at HEAD `9a352bb`, after later tasks) and `npm run build` are green. Recorded in TS-011 TC-011.7.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` findings M and N.
