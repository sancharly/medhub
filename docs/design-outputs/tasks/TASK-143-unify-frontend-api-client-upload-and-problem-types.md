---
id: "TASK-143"
type: task
title: "Attachment upload through the shared request helper; ProblemError derived from the schema"
status: approved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-14"
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

- SR-030 AC 8 and the RISK-005 control: a 401 during an upload raises `AuthError` like any other request
  (the single redirect on a mutation's `AuthError` is TASK-144). `uploadAttachment` (`api/client.ts:136-160`) has its own `fetch` without the
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

- [x] One fetch and problem-parsing path; a 401 during upload raises `AuthError`.
- [x] `ProblemError` derived from the generated schema, outside generated files; regeneration leaves no diff.

## Definition of Done

- [x] `npm run lint`, `npm run typecheck`, `npm test -- --run` green
- [x] TS-011, ADD-023 consistent; `traceability-check` no error for this record

## QA review — round 1 (2026-11-14): CHANGES REQUESTED

Verification run by QA: `npm run typecheck`, `npm run lint`, `npm test -- --run` (32 files, 322 passed), `npm run build`
green; `npm run generate:types` leaves `openapi.ts` unchanged; traceability script 0 errors, 27 warnings (87 records).
Mutants killed: JSON content type on a `FormData` body, CSRF header dropped for `FormData`, 401 branch skipped for
`FormData` (one upload test fails each); schema losing `instance` fails `npm run typecheck`. Trace negative control:
removing CR-006 `resolves` PRB-019 gives E9.

- **R1-1 [HIGH] Upload 401 now shows a less clear message than before (SR-027 AC 3 regression).**
  `frontend/src/core/clinical/AttachmentUpload.tsx:28-31` shows `problem.detail` only for `ApiError`; `AuthError`
  (`api/client.ts:25`) does not extend `ApiError`. Checked with a temporary test that was then removed: at HEAD a 401
  problem during upload shows "Authentication is required."; with this change it shows "The file could not be
  uploaded.", and nothing redirects (no global mutation handler; `RequireAuth` only watches `["me"]`). Fix: in
  `AttachmentUpload` treat `AuthError` like `ApiError` for the message (for example `mutation.error instanceof ApiError
  || mutation.error instanceof AuthError`, or a "your session has ended, sign in again" text), and add an
  `AttachmentUpload.test.tsx` case for a 401 problem.
- **R1-2 [MEDIUM] SR-030 AC 8 is claimed beyond what this task delivers.** The objective, ADD-023
  (`ADD-023-frontend-api-client.md:39`, "ends the session once"), TC-011.7 and the PRB-019 Resolution say a 401 during
  upload ends the session. The task raises `AuthError`; the single redirect does not exist for any mutation yet. Fix:
  narrow the wording in ADD-023 and TC-011.7 to "raises `AuthError` (redirect: TASK-144)", and add to TASK-144 an
  explicit step and test that an `AuthError` from a mutation (the upload included) redirects once.
- **R1-3 [LOW] The type-level test does not catch loss of `detail` or `errors`.** Deleting `detail` or `errors` from
  `ProblemDetail` in `api/generated/openapi.ts` still type-checks (`problem.test-d.ts` picks only `type`, `title`,
  `status`, `instance`). Fix: add a `Pick<Schema, "detail" | "errors">` assertion, or narrow the TS-011/TASK wording to
  the four fields actually checked.
- **R1-4 [LOW] Records.** The plan said "`types.ts` regenerated, not edited"; `generate:types` writes only
  `openapi.ts` (`package.json:13`, CI `openapi-lint` diffs only `openapi.ts`), so `types.ts` was edited by hand. That is
  correct, but record it in 1.2 as a deviation. "the five importers" should read six (`client.ts`, `client.test.ts`,
  `ErrorToastProvider.tsx`, `context.ts`, `problemToMessage.ts`, `problemToMessage.test.ts`) plus `index.ts`. PRB-085's
  tag `found-in:TASK-143-sanity-run` disagrees with its body ("QA reproduced it at commit `b2e7a1c` (TASK-141
  review)"). Make the two agree.

Not blocking (pre-existing): the OpenAPI `ProblemDetail.errors.items` is hand-written as `{"type": "object"}`
(`backend/app/api/openapi.py:78`), while the backend always emits `{field, rule, message}` (required strings;
`backend/app/api/errors.py:22-25,55,189-193`). The schema is the defect and needs its own PRB (minor; contract only).
Once it is fixed, the `errors` override in `api/problem.ts` can go. The `types.ts` header ("Re-generate with: npm run
generate:types") and the CLAUDE.md rule "never hand-edit either generated file" both treat a hand-maintained file as
generated.

## QA review — round 2 (2026-11-14): APPROVED

QA re-ran `npm run typecheck`, `npm run lint`, `npm test -- --run` (32 files, 323 passed) and `npm run build`; all green.
`generate:types` leaves `openapi.ts` unchanged. Traceability script over TASK-143, TASK-144, TS-011, ADD-023, PRB-019,
PRB-085, PRB-086 and CR-006: 0 errors, 29 warnings (93 records). R1-1 negative control: with `|| instanceof AuthError`
removed, the 401 test in `AttachmentUpload.test.tsx` fails. R1-3: deleting `detail` or `errors` from `ProblemDetail`
fails typecheck. Files restored byte-identical. R1-2 and R1-4 are closed in the records; PRB-086 is well formed (open,
minor). Carried LOWs, not blocking:

- PRB-019 Resolution still says "322 passed" (now 323), and its first bullet reads as one run-on clause ("`AttachmentUpload`
  shows its detail and a problem+json refusal ... gives"). Split the sentence and update the count when PRB-019 is next edited.
- `problem.test-d.ts:11`: the comment says "ProblemError exposes all of them", but the assignment checks the reverse
  (every `ProblemError` key is a schema key). Fix the comment, or add `[] as (keyof SchemaFields)[]` assigned to
  `(keyof ProblemError)[]`.

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect). Re-based on SR-030 AC 8 (401 on upload ends the
  session; RISK-005 control) and SR-027 AC 3; `mitigates` RISK-005 added; `ProblemError` moved out of the
  generated-alias file.
- 1.2 (2026-11-14) — Implemented (Software Developer), handed to QA (`draft → in_review`). Deviation: `ProblemError` also overrides `errors`
  (`Array<{ field?, rule?, message?}>`), because the schema types its items as `Record<string, never>` and
  `problemToMessage` / its tests read `field` and `message`. `types.ts` no longer defines `ProblemError` (deviation from "`types.ts` regenerated, not edited": `generate:types` writes only `openapi.ts`, so the hand-maintained alias file was edited by hand to delete the override);
  the six other importers (`client.ts`, `client.test.ts`, `ErrorToastProvider.tsx`, `context.ts`, `problemToMessage.ts`, `problemToMessage.test.ts`) and `api/index.ts` now import it from `api/problem.ts`. Type-level test is
  `api/problem.test-d.ts` (run by `npm run typecheck`). `generate:types` round trip: no diff.
- 1.2 (2026-11-14) — QA review round 1: CHANGES REQUESTED (`in_review → draft`); findings R1-1 to R1-4 above.
- 1.3 (2026-11-14) — QA round 1 fixed, handed back (`draft → in_review`). R1-1: `AttachmentUpload.tsx` shows the problem `detail`
  for `AuthError` as well as `ApiError` (test `shows the server's detail when the session has ended (401)`; negative control: reverting
  the fix fails it). R1-2: wording narrowed here, in ADD-023, TS-011 TC-011.7 and PRB-019 (raises `AuthError`; redirect: TASK-144), and a
  step plus test added to TASK-144. R1-3: `problem.test-d.ts` also covers `detail` and `errors`; deleting each of `detail`, `errors`,
  `instance` from `ProblemDetail` in `openapi.ts` fails typecheck, and the restored file is byte-identical (`cmp`). R1-4: this history
  corrected; PRB-085 tag fixed. The untyped `errors` items are raised as PRB-086 (not fixed here).
- 1.3 (2026-11-14) — QA review round 2: APPROVED (`in_review → approved`, status only).
