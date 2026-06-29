# TASK-096a — Manual add-member UI for groups (remediation)

- **Phase:** 7 — Frontend core
- **Implements / restores:** SR-014.3; remediates TASK-096
- **Depends on:** TASK-096, TASK-070a (module registry sync, for the module-toggle path)
- **Branch:** `feature/group-add-member`
- **Status:** Not started
- **Source:** `AUDIT-LEDGER.md` — TASK-096 verdict **PARTIAL** (phase-7 QA, confirmed)

## Objective

SR-014.3 requires sysadmins to **add and remove** manual group members. The UI implements removal only;
**add-member is missing** — `apiClient.addGroupMember` (`client.ts:234`) is dead code with no control
invoking it. (Module toggles also render empty until TASK-070a syncs the registry.)

## Implementation detail

- Add an add-member control to `GroupMembers.tsx` (account picker or id/email input) wired to
  `apiClient.addGroupMember(groupId, accountId)`, invalidating the group/members query on success.
- AUTO members remain read-only; only manual members can be removed.

## Acceptance criteria

- [ ] A sysadmin can add a manual member to a group from the UI; the list refreshes.
- [ ] AUTO members stay read-only; manual members can be added and removed.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Component test covers add-member (mock matches real route) and AUTO read-only invariant
- [ ] Traceability row updated (SR-014 → TASK-096a → tests)
