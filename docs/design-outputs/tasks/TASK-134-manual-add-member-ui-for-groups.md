---
id: "TASK-134"
type: task
title: "Manual add-member UI for groups (remediation)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-014"
    relation: implements
  - target: "TASK-096"
    relation: relates_to
  - target: "TASK-129"
    relation: relates_to
tags: ["phase:7-frontend-core", "remediation-of:TASK-096", "original-id:TASK-096a"]
---

- **Phase:** 7 — Frontend core
- **Implements / restores:** SR-014.3; remediates TASK-096
- **Depends on:** TASK-096, TASK-070a (module registry sync, for the module-toggle path)
- **Branch:** `feature/group-add-member`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-096 verdict **PARTIAL** (phase-7 QA, confirmed)

*Originally filed as TASK-096a.*

## Objective

SR-014.3 requires sysadmins to **add and remove** manual group members. The UI implements removal only;
**add-member is missing** — `apiClient.addGroupMember` (`client.ts:234`) is dead code with no control
invoking it. (Module toggles also render empty until TASK-070a syncs the registry.)

## Implementation detail

- Add an add-member control to `GroupMembers.tsx` (account picker or id/email input) wired to
  `apiClient.addGroupMember(groupId, accountId)`, invalidating the group/members query on success.
- AUTO members remain read-only; only manual members can be removed.

## Acceptance criteria

- [x] A sysadmin can add a manual member to a group from the UI; the list refreshes.
- [x] AUTO members stay read-only; manual members can be added and removed.

## Definition of Done

- [x] Lint + type-check pass
- [x] Component test covers add-member (mock matches real route) and AUTO read-only invariant — `GroupsPage.test.tsx`
- [x] Traceability row updated (SR-014 → TASK-096a → tests)

## Implementation notes (2026-06-30)

- `GroupMembers.tsx`: added an "Account ID or email" text input + "Add member" button, wired to
  `apiClient.addGroupMember(groupId, accountId)` (`POST /groups/{id}/members`); on success invalidates
  `["groups"]` so the member list refetches. AUTO members continue to render without a remove control;
  only MANUAL members get the existing remove icon button.
- `GroupList.tsx`: the add-member form is now always rendered (previously the whole `GroupMembers`
  subtree was skipped when a group had zero members), so a sysadmin can add the first member to an
  empty group.
