---
id: "PRB-017"
type: problem-report
title: "Security-relevant frontend units have no unit tests"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-14"
criticality: major
links: []
tags: ["verification", "regulatory"]
---

# PRB-017 — Security-relevant frontend units have no unit tests

## Observed

`SessionActivityProvider`, `AttachmentItem` (module-gated DICOM link), `AttachmentUpload` with `client.uploadAttachment`, and `api/csrf.ts` have no unit tests; only `useIdleTimer` is covered.

## Impact

IEC 62304 §5.5 requires unit verification for class B software. These units implement SR-030, SR-015 and SR-031 behaviour and are currently verified by manual testing only.

## Safety evaluation

Contributes to RISK-005, RISK-004 and RISK-001 indirectly: an unverified control is not a control (PLAN-005).

## Investigation

Narrowed on 2026-11-13 (CR-006 D-1, D-9). `core/clinical/AttachmentUpload.test.tsx` now exists (added with TASK-206), so the upload unit has a test. **Remaining gap:** no test file exists for `auth/SessionActivityProvider.tsx` (SR-030 AC 1 to AC 4) or `core/clinical/AttachmentItem.tsx` (SR-015 AC 3, AC 4), and `api/csrf.ts` (SR-031 AC 3) has no dedicated test (`api/client.test.ts` only uses the CSRF cookie as a fixture). Unit tests are sufficient at the unit level (D-9); the system-level evidence stays in TS-001 and TS-005.

## Resolution

TASK-146 (CR-006, D-9) closed the gaps without a production code change. Between the Investigation of 2026-11-13 and TASK-146, `auth/SessionActivityProvider.test.tsx` was written by TASK-144, TASK-221 and TASK-222 (21 tests: reported deadline, 2-minute warning, extend, one redirect to `/login?timeout=1`, cache clear, a mutation's `AuthError` including the upload), so it needed no new case. TASK-146 added:

- `frontend/src/core/clinical/AttachmentItem.test.tsx` (8 tests, SR-015 AC 3, AC 4): viewer link only for a DICOM attachment with `dicom-viewer` in the user's list; absent for an empty list, other modules only, a list still loading and a list that failed to load; non-DICOM unaffected; Download always present (TS-005 TC-005.6).
- `frontend/src/api/csrf.test.ts` (11 tests, SR-031 AC 3): `withCsrf` reads exactly the `medhub_csrf` cookie, keeps `=` inside the value, tolerates an absent cookie, keeps the given headers; the client sends the header on POST, PUT, PATCH, DELETE and never on GET, with the cookie present (TS-011 TC-011.8).
- `frontend/src/api/generated/openapiDrift.test.ts` (2 tests): `openapi.ts` equals the generator output for `backend/openapi/openapi.json` (TS-011 TC-011.9).

The upload 401 path already had tests from TASK-143 (`client.test.ts`, `AttachmentUpload.test.tsx`) and TASK-144/222 (`SessionActivityProvider.test.tsx`). Verified on 2026-11-14: `npm test -- --run` 412 passed (41 files), `typecheck`, `lint` and `build` clean; coverage of the three units: `csrf.ts` and `AttachmentItem.tsx` 100 % statements, branches and lines, `SessionActivityProvider.tsx` 100 % statements and lines, 94.73 % branches. Each new test was run against hand-made mutants of the unit and failed (listed in TASK-146).

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding T′.

## Version history

- 1.0 (2026-09-17) — Created from the July 2026 code review. `open`.
- 1.1 (2026-11-13) — CR-006: Investigation added; scope narrowed to the three units still without tests (D-9). Stays `open`.
- 1.2 (2026-11-14) — TASK-146 (CR-006): Resolution written; `resolved` (the `resolves` link is on CR-006). Closes with the release that ships it.
