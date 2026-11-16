---
id: "PRB-015"
type: problem-report
title: "Module list query is never invalidated, so DICOM gating goes stale"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-14"
criticality: major
links: []
tags: ["correctness", "hazard:denial-of-care"]
---

# PRB-015 — Module list query is never invalidated, so DICOM gating goes stale

## Observed

`core/clinical/AttachmentItem.tsx:19` reads the `["myModules"]` query, which is never invalidated after an administrator changes module enablement — the UI keeps the old gating until a reload.

## Impact

SR-015 per-group module enablement is not reflected promptly: a viewer stays hidden after being enabled, or offered after being disabled.

## Safety evaluation

Contributes to RISK-004 (legitimate access wrongly denied).

## Resolution

TASK-221, change request CR-006 (verified in the working tree, 2026-11-14). The query was never invalidated because no code touched the `["myModules"]` key, and nothing refetched it either (default stale time, no interval, no focus refetch).

- `frontend/src/modules/useMyModules.ts` (new) is the only reader of the module list: `queryKey: queryKeys.myModules` (`frontend/src/api/queryKeys.ts`), `staleTime` 30 s, `refetchInterval` 50 s (the interval restarts when a response arrives, so the 60 s bound of SR-015 AC 5 keeps room for the round trip and a retry), `refetchOnWindowFocus`, `refetchOnMount: "always"` (next navigation), `retry: 1`. TanStack Query keeps the last `data` when a refetch fails, so an enabled module is never hidden by a transient error (RISK-004); the server guard stays the authority (SR-015 AC 3).
- `core/clinical/AttachmentItem.tsx` uses the hook. `GroupModules.tsx` (toggle) and `GroupMembers.tsx` (add, remove) also invalidate `queryKeys.myModules`, so the administrator's own UI changes at once.
- Verified by `frontend/src/modules/useMyModules.test.tsx` (11 tests; TS-005 TC-005.5), `backend/tests/auth/test_session_no_slide.py` (the poll validates the session without extending it; SR-030, RISK-005) and the frontend and backend suites. Negative controls, each reverted by hand: no `refetchInterval`, no `refetchOnMount`, an error swallowed into `[]`, no invalidation in `GroupModules`, none in `GroupMembers`, and the key spelled inline each fail a test.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding P.
