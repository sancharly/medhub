---
id: "TASK-221"
type: task
title: "Module gating in the UI refreshes for every affected user within 60 seconds"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
links:
  - target: "SR-015"
    relation: implements
  - target: "RISK-004"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-015"
    relation: relates_to
  - target: "ADD-020"
    relation: relates_to
  - target: "ADD-021"
    relation: relates_to
  - target: "TS-005"
    relation: relates_to
  - target: "TASK-144"
    relation: relates_to
tags: ["cr:CR-006", "frontend", "modules", "control:design"]
---

# TASK-221 — Module gating in the UI refreshes for every affected user within 60 seconds

- **Software item / unit:** SI-FE-CORE `core/clinical/AttachmentItem.tsx` (ADD-020); SI-FE-MODREG module query
  (ADD-021).
- **PRB:** PRB-015 (split from TASK-144 1.0). **CR:** CR-006 (D-4; change-analysis cause 8).
- **Depends on:** TASK-144 (`queryKeys.ts`). TASK-146 adds the unit tests of `AttachmentItem`.
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S (`frontend/src/modules/useMyModules.ts` (new) or the registry's existing hook,
  `frontend/src/core/clinical/AttachmentItem.tsx`, `frontend/src/api/queryKeys.ts`, admin group/module
  mutation hooks; tests; records TS-005).

## Objective

SR-015 AC 5 (D-4): a change of a module's enablement reaches the module-dependent UI of every affected user
without a reload, within 60 s or on the next navigation to the affected view, including users who did not make
the change. `["myModules"]` (`AttachmentItem.tsx:18-19`) is never invalidated or refetched. A failed refetch
keeps the last known value (RISK-004, cause 8); the server guard (SR-015 AC 3) stays the authority.

## Implementation detail

- `useMyModules()`: `queryKey: queryKeys.myModules`, `staleTime: 30_000`, `refetchInterval: 60_000`,
  `refetchOnWindowFocus: true`, `refetchOnMount: "always"` (next navigation), `retry: 1`; TanStack Query keeps
  the previous `data` on error (no `placeholderData` reset). Every module-dependent reader uses it.
- Admin group and module mutations also invalidate `queryKeys.myModules` (the administrator's own UI).

## Tests (write first)

- `module disabled elsewhere disappears within 60 s` (SR-015 AC 5): fake timers, MSW returns the new list after
  the change; the viewer link is gone by 60 s.
- `remount (next navigation) refetches` (SR-015 AC 5).
- `failed refetch keeps the last known modules` (SR-015 AC 5; RISK-004).
- `admin mutation invalidates myModules` (SR-015 AC 5).
- TS-005 (version raised by TASK-220): TC-005.y module refresh.

## Acceptance criteria

- [ ] SR-015 AC 5: refresh within 60 s or next navigation for a user who did not make the change.
- [ ] A failed refetch never hides an enabled module.

## Definition of Done

- [ ] Frontend lint, type check, suite green
- [ ] TS-005, ADD-020/ADD-021 consistent; `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) from the PRB-015 part of TASK-144 1.0.
