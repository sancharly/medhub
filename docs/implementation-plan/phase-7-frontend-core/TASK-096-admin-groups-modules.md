# TASK-096 — Admin groups & module-enablement UI

- **Phase:** 7 — Frontend core views
- **Software item / unit:** SI-FE-CORE / U-FEC-AdminGroupsModules
- **Implements:** SR-014 (group create/list, manual membership), SR-015 (per-group module enable/disable); ADR-0003, ADR-0005
- **Depends on:** TASK-063 (groups + module-enablement API, SI-GROUPS endpoints) — must be merged first
- **Branch:** `feature/fe-admin-groups-modules`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Build the **system-administrator** view for managing user groups and per-group module enablement: create/list groups (SR-014), add/remove members manually (SR-014.3), and enable/disable installed modules for a group (SR-015). This is the control surface that decides which users see which modules — it directly feeds the nav gating (TASK-101) and the DICOM viewer's availability. Sysadmin-only; the server enforces the same.

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2) and `ShellServices`:

```ts
apiClient.listGroups();                                   // GET /groups (SR-014)
apiClient.createGroup({ name });                          // POST /groups (SR-014.1)
apiClient.addGroupMember(groupId, accountId);             // POST /groups/{id}/members (SR-014.3)
apiClient.removeGroupMember(groupId, accountId);          // DELETE /groups/{id}/members/{accountId} (SR-014.3)
apiClient.listModules();                                  // GET /modules — installed module registry (SR-016)
apiClient.setGroupModuleEnabled(groupId, moduleKey, enabled);  // PUT /groups/{id}/modules/{moduleKey} (SR-015)
```

- All operations are **sysadmin-only** (api-design.md "Groups & module enablement — sysadmin only"); the view is reachable only for that role and the server enforces it (SR-031.5).
- Automatic-by-user-type membership (SR-014.2) is computed server-side; the UI **displays** auto-membership read-only and only edits **manual** membership (SR-014.3).
- `GET /modules` is the installed-module registry (SR-016); the enable/disable toggles operate per group via `PUT /groups/{id}/modules/{moduleKey}` (SR-015). Disabling for all of a user's groups removes their access (SR-015.4) — enforced server-side and reflected by TASK-101 nav gating.
- Cookie + CSRF via `ApiClient` (SR-031.3).

## Implementation detail

- Files to create:
  - `frontend/src/core/admin/groups/GroupsPage.tsx` — route `/admin/groups`; `useQuery(['groups'])` and `useQuery(['modules'])`.
  - `frontend/src/core/admin/groups/GroupList.tsx` — list of groups; select a group to manage.
  - `frontend/src/core/admin/groups/CreateGroupForm.tsx` — name field; `useMutation` → `createGroup`; invalidate `['groups']` (SR-014.1).
  - `frontend/src/core/admin/groups/GroupMembers.tsx` — members of the selected group, distinguishing **auto** (read-only, SR-014.2) from **manual** (add/remove, SR-014.3); `useMutation` for add/remove.
  - `frontend/src/core/admin/groups/GroupModules.tsx` — for the selected group, list installed modules (from `GET /modules`) each with an enable/disable toggle calling `PUT /groups/{id}/modules/{moduleKey}` (SR-015.1/2); optimistic toggle reconciled on response.
  - `frontend/src/core/admin/groups/index.ts` — route export.
- Libraries: React 18, TanStack Query, MUI (list, form, switch/toggle, transfer-list for members), React Router.
- Empty/loading/error states per the shared conventions (skeletons; error toast with `detail`, SR-027.3).
- Error cases: `400` create group (empty/duplicate name) → field error; `403` if a non-sysadmin reaches the view → access denied; `404` operating on a removed group → refetch.
- Edge cases / SR rules quoted:
  - SR-014.2: "The system can assign users to a group automatically based on their user type." — auto-members shown read-only.
  - SR-014.3: "A system administrator can manually add or remove a user from a group." — only manual members editable.
  - SR-015.3/4: "A user can access a module only if it is enabled for at least one group they belong to … When a module is disabled for all of a user's groups, the user can no longer access it." — the toggle is the source of this; the effect is verified end-to-end with TASK-101.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + RTL + MSW), `frontend/src/core/admin/groups/GroupsPage.test.tsx`:
  - list groups; create a group → `POST /groups` and list refetch (SR-014.1).
  - members panel shows auto-members read-only and manual members with remove; add a manual member → `POST /groups/{id}/members` (SR-014.2/3).
  - modules panel lists installed modules from `GET /modules`; toggling the DICOM viewer on → `PUT /groups/{id}/modules/dicom-viewer` with `enabled: true`; toggling off → `enabled: false` (SR-015.1/2).
  - `400` on duplicate group name → field error; `403` for non-sysadmin → access denied.
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] A system administrator can create and name a group and list groups (SR-014.1).
- [ ] Auto-by-type membership is shown read-only; manual members can be added/removed (SR-014.2/3).
- [ ] Installed modules are listed per group with working enable/disable toggles (SR-015.1/2).
- [ ] Enabling/disabling a module for a group changes module availability for its members, verified end-to-end with nav gating (SR-015.3/4, handoff to TASK-101).
- [ ] The view and all operations are restricted to system administrators; the server enforces it (SR-031.5).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-014, SR-015 → TASK-096 → tests)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-070a (module registry sync), **TASK-096a** (FE: manual add-member UI, SR-014.3). Unchecked items reflect the gaps the audit found; stays **In Progress** until addressed.
