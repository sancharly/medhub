---
id: "TASK-146"
type: task
title: "Unit tests for the session provider, attachment gating and the CSRF helper"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-14"
links:
  - target: "NFR-006"
    relation: implements
  - target: "SR-030"
    relation: implements
  - target: "SR-015"
    relation: implements
  - target: "SR-031"
    relation: implements
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-017"
    relation: relates_to
  - target: "RISK-005"
    relation: relates_to
  - target: "RISK-004"
    relation: relates_to
  - target: "TS-001"
    relation: relates_to
  - target: "TS-005"
    relation: relates_to
  - target: "TS-011"
    relation: relates_to
  - target: "TASK-143"
    relation: relates_to
  - target: "TASK-144"
    relation: relates_to
  - target: "TASK-221"
    relation: relates_to
  - target: "TASK-222"
    relation: relates_to
  - target: "TASK-111"
    relation: relates_to
tags: ["phase:review-2026-07", "cr:CR-006", "verification", "frontend"]
---

# TASK-146 — Unit tests for the session provider, attachment gating and the CSRF helper

- **Software item / unit:** SI-FE-AUTH `SessionActivityProvider` (ADD-019); SI-FE-CORE `AttachmentItem`
  (ADD-020); SI-FE-APICLIENT `api/csrf.ts` (ADD-023).
- **PRB:** PRB-017 (narrowed: `AttachmentUpload.test.tsx` exists since TASK-206). **CR:** CR-006 (D-9).
- **Depends on:** TASK-143, TASK-144, TASK-221, TASK-222 (tests target their final shape).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S. Three new test files: `frontend/src/core/clinical/AttachmentItem.test.tsx`,
  `frontend/src/api/csrf.test.ts`, `frontend/src/api/generated/openapiDrift.test.ts`. The planned
  `SessionActivityProvider.test.tsx` already existed when the task started (written by TASK-144, TASK-221 and
  TASK-222), so it is mapped, not rewritten. Records: TS-001, TS-005, TS-011 (unit acceptance criteria, new
  cases), PRB-017. No production code change; no defect found, so no new PRB.

## Objective

IEC 62304 §5.5 (class B unit verification) and NFR-006 AC 3, AC 4 for three security-relevant units that have no
unit test. D-9: unit tests suffice at the unit level; system-level evidence stays in TS-001 and TS-005.

## Tests (write first; behavioural, no snapshots)

- `SessionActivityProvider`: warning dialog 2 min before the server-derived deadline (SR-030 AC 4, AC 8); extend
  re-derives the deadline from the response (SR-030 AC 8); expiry redirects once to `/login?timeout=1`
  (SR-030 AC 1, AC 2, AC 8); logout clears the query cache (SR-030 AC 5).
- `AttachmentItem`: viewer link present iff the DICOM module is in the user's modules (SR-015 AC 3); absent after
  disable (SR-015 AC 4, AC 5); non-DICOM attachments unaffected.
- `csrf.ts`: header set from the cookie for POST/PUT/PATCH/DELETE, not for GET (SR-031 AC 3); absent cookie
  tolerated (no header, no throw).
- Unit acceptance criteria written in TS-001, TS-005, TS-011 (same versions as the tasks that raised them);
  coverage of the three units reported in TASK-226's TR input (figures in the mapping above).

## Mapping of the test items to tests (2026-11-14)

Checked against the tree before writing: TASK-143 (`2d409ca`), TASK-144 (`b54ea9f`), TASK-221 (`bce75e3`) and TASK-222 (`eadaa2a`) left most of the planned cases in place.

| Item | AC | Test | State |
|---|---|---|---|
| Warning 2 min before the server-derived deadline | SR-030 AC 4, AC 8 | `SessionActivityProvider.test.tsx`: `deadline follows the server-reported expiry (%i min), not 15 min: warning at %i min` (`it.each`: 30 min reported, warning at 28; 7 min, 5), `reading without requests is warned at 13 min and signed out at 15 min`, `the session ends at the reported deadline: warning at 13 min, sign-in at 15 min`; `client clock skew of %i min between request and response does not move the deadline` (+10 and -10); `useIdleTimer.test.ts`: `clinical role: warn fires at 13 min and expire at 15 min`, `admin role: warn at 28 minutes (30 - 2)` | existing |
| Extend re-derives the deadline from the response | SR-030 AC 8 | `SessionActivityProvider.test.tsx`: `Extend re-arms from expiresInSeconds`, `a refreshed me re-arms`; `IdleWarningDialog.test.tsx`: `Stay signed in calls extend and invokes onExtended`; `useIdleTimer.test.ts`: `a new deadline re-arms both timers` | existing |
| Expiry redirects once to `/login?timeout=1` | SR-030 AC 1, AC 2, AC 8 | `an expired session gives one redirect and no repeated me requests`, `a reported expiry of 0 is an expired session: one redirect to sign-in`, `timeout logs out, clears the cache and redirects once`, `clock jump with the warning open: one logout, an empty cache and one redirect`, `the dialog's tick and the expiry timer firing in one pass log out once` | existing |
| Logout clears the query cache | SR-030 AC 5 | `Log out now logs out once, clears the cache and does not ask the server again`, `timeout logs out, clears the cache and redirects once`, `Back after a timeout shows no clinical data`, `extend 401 then Back shows no clinical data` | existing |
| Vitest fake-timer coverage of the client session (RISK-005 row) | SR-030 AC 8 | the four rows above (`vi.useFakeTimers` in `SessionActivityProvider.test.tsx`, `useIdleTimer.test.ts`); `modules/useMyModules.test.tsx` for the module poll | existing |
| Upload 401 path | SR-030 AC 8, SR-027 AC 3 | `client.test.ts`: `raises AuthError on a 401 unauthenticated problem` (`ApiClient uploadAttachment`); `AttachmentUpload.test.tsx`: `shows the server's detail when the session has ended (401)`; `SessionActivityProvider.test.tsx`: `a mutation's AuthError redirects once and clears the cache (the upload included)` | existing |
| Viewer link iff the DICOM module is in the user's list; absent after disable; non-DICOM unaffected | SR-015 AC 3, AC 4, AC 5 | `AttachmentItem.test.tsx` (8 tests, TS-005 TC-005.6). AC 5 (refresh within 60 s): `useMyModules.test.tsx` (TC-005.5), existing | **new** (AC 3, AC 4) |
| CSRF header set from the cookie for POST, PUT, PATCH, DELETE and not for GET; absent cookie tolerated | SR-031 AC 3 | `csrf.test.ts` (11 tests, TS-011 TC-011.8). `client.test.ts` `attaches X-CSRF-Token from cookie on POST` and `sends credentials:include but no X-CSRF-Token` stay (the GET one runs without a cookie, so it cannot catch a header on GET) | **new** |
| Generated types have not drifted (RISK-005 row) | SR-031 AC 3 (contract), Backend/Frontend Contract | `openapiDrift.test.ts` (2 tests, TS-011 TC-011.9); CI `openapi-lint` job repeats it from a fresh export | **new** |
| Unit acceptance criteria in TS-001, TS-005, TS-011 | | TS-001 1.9, TS-005 1.5, TS-011 1.5 (`in_review`) | done |
| Coverage of the three units | | `npm test -- --run --coverage` restricted to the three files: `csrf.ts` 100/100/100 (statements/branches/lines), `AttachmentItem.tsx` 100/100/100, `SessionActivityProvider.tsx` 100 statements, 94.73 branches, 100 lines | done |

## Negative controls (hand-made mutants, each reverted; no `git stash`)

`csrf.test.ts` (against `api/csrf.ts` and `api/client.ts`): header set with no cookie (3 tests fail); cookie matched by `startsWith("medhub_csrf")` or `includes` (1 each); value taken as `split("=")[1]` (1); header renamed (7); given headers dropped (1); header on every method (1, GET); POST, PUT, PATCH or DELETE removed from `MUTATING_METHODS` (1 each).
`AttachmentItem.test.tsx`: viewer without the module check (5); viewer without the DICOM check (1); unknown list treated as enabled (2); any non-empty list enables it (1); module key `dicom` (3); content type `image/dicom` (3); `rel` without `noopener` (1); module check replaced by `true` (5).
`openapiDrift.test.ts`: `id: string;` made optional in `openapi.ts` (1 fails); a schema renamed in `openapi.json` (2); a type changed at the end of `openapi.ts` (1).

## Acceptance criteria

- [x] Each of the three units has a test file whose cases trace to the AC named above.
- [x] Coverage report shows the three units exercised (lines and branches reported).

## Definition of Done

- [x] `npm run lint`, `typecheck`, `test -- --run --coverage` green
- [x] TS records hold the unit acceptance criteria; `traceability-check` no error for this record

## QA review (2026-11-14, round 1): APPROVED

Verified: typecheck and lint clean; frontend 412 passed (41 files), with no `act` warning from the three new files;
coverage restricted to the three units: `csrf.ts` and `AttachmentItem.tsx` 100 % statements, branches and lines,
`SessionActivityProvider.tsx` 100 % statements and lines, 94.73 % branches; `npm run build` exit 0, 160.06 kB gzip;
trace 0 errors. Mutants rerun (each reverted, `cmp` clean): cookie matched by `startsWith("medhub_csrf")` (1 fails);
PUT removed from `MUTATING_METHODS` (1); unknown module list treated as enabled (2); `id: string` made optional in
`openapi.ts` (1); new mutant for the unverified assertion, `withCsrf` writing the token into the plain object it was
given (1 fails: `keeps the headers it was given and does not change the object passed in`). Mapped tests spot-checked:
the unmount-time `qc.clear()` removed fails 9 `SessionActivityProvider` tests (SR-030 AC 5); the redirect removed from
the mutation `AuthError` handler fails `a mutation's AuthError redirects once and clears the cache (the upload
included)`; warning lead 2 to 1 minute fails the `deadline follows the server-reported expiry` and clock-skew cases
(SR-030 AC 4). Drift test: about 0.7 s, no network (the generator is given the parsed schema), runs in the CI
`frontend-test` job; it cannot pass vacuously (a missing generator fails the import, a missing schema fails the
read, and the second test requires the output to change). It checks `openapi.ts` against the committed
`openapi.json`; CI `openapi-lint` checks a fresh backend export, so the two complement each other.

Carried findings (not blocking):

- LOW: TS-011 TC-011.9 (pass criteria) and the negative-control list above say that a renamed schema in `openapi.json`
  fails both drift tests. With `AccountCreateRequest` renamed consistently (key and `$ref`s) only the first test fails;
  the second still passes, as it should. Fix: say "fails the first".
- LOW: TS-001 Notes says "PRB-017 closed by TASK-146"; PRB-017 is `resolved` (closed with the release). Fix: "resolved".

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect). Narrowed to the three remaining units (D-1, D-9);
  `implements` SR-015 and SR-031 added; the cases follow the shapes of TASK-143, 144, 221 and 222.
- 1.2 (2026-11-14) — Build (software-developer). `SessionActivityProvider.test.tsx` already existed, so the task added `AttachmentItem.test.tsx`, `csrf.test.ts` and `openapiDrift.test.ts`, mapped the remaining items to existing tests, and wrote the unit acceptance criteria and cases into TS-001 1.9, TS-005 1.5 and TS-011 1.5. PRB-017 resolved. `in_review`.
- 1.2 (2026-11-14) — QA review round 1 (QA Engineer): `approved`; carried LOW findings recorded above.
