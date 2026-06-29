# TASK-095 — Admin account management

- **Phase:** 7 — Frontend core views
- **Software item / unit:** SI-FE-CORE / U-FEC-AdminAccounts
- **Implements:** SR-009 (non-clinical projection only), SR-032 (role-constrained create), SR-034 (deactivate/reactivate/delete with confirmation); ADR-0013 (delete = anonymized retention + lost-code warning)
- **Depends on:** TASK-061 (account-create API, SI-API), TASK-062 (account lifecycle API: deactivate/reactivate/delete, SI-API), TASK-083 (auth/session UI + role context) — must be merged first
- **Branch:** `feature/fe-admin-accounts`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Build the **admin account management** view used by administrative personnel and system administrators: list accounts (non-clinical projection only, SR-009), create accounts with role-constrained type selection (SR-032), and — for system administrators — deactivate, reactivate, and delete accounts (SR-034). Create offers only the account types the creator's role may make (admin cannot create sysadmin, SR-032.4). Delete shows an explicit confirmation that surfaces the **ADR-0013 lost-code warning**: deletion anonymizes the user's data into a 5-year-retained dataset and emails the user a retrieval code that is never stored — if lost, the data is unrecoverable.

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2) and `ShellServices`:

```ts
apiClient.listAccounts();                          // GET /accounts — non-clinical projection (SR-009)
apiClient.createAccount({ firstName, surname, email, userType });  // POST /accounts (SR-032)
apiClient.deactivateAccount(id);                   // POST /accounts/{id}/deactivate (sysadmin, SR-034.1/2)
apiClient.reactivateAccount(id);                   // POST /accounts/{id}/reactivate (SR-034.4)
apiClient.deleteAccount(id);                       // DELETE /accounts/{id} (sysadmin, confirm, SR-034.5/6)
apiClient.resendActivation(id);                    // POST /accounts/{id}/resend-activation (SR-033.7)
shell.confirmDialog({...});                        // delete + deactivate confirmation (SR-027.2, SR-034.6)
```

- The account listing is the **non-clinical projection** (SR-009): name, surname, DOB, email, user type, account state — **never** clinical data. The UI renders only these fields; it must not request or display any clinical field.
- Role-constrained create (SR-032.4/5): the type selector offers `Patient | Doctor | Administrative Personnel` for an admin creator, and additionally `System Administrator` only for a sysadmin creator. The server enforces this too (SR-032 control measures) — the UI restriction is convenience, not the control (SR-031.5).
- Lifecycle ops (deactivate/reactivate/delete) are **sysadmin-only** in the UI; rendered conditionally on role; server-enforced.
- Cookie + CSRF via `ApiClient` (SR-031.3).

## Implementation detail

- Files to create:
  - `frontend/src/core/admin/accounts/AccountsPage.tsx` — route `/admin/accounts`; `useQuery(['accounts'])`.
  - `frontend/src/core/admin/accounts/AccountList.tsx` — non-clinical columns + state (Inactive/Active/Deleted) + per-row actions by role (SR-009, SR-034).
  - `frontend/src/core/admin/accounts/CreateAccountForm.tsx` — fields first name, surname, email (all required, SR-032.2) + role-filtered user-type select; `useMutation` → `createAccount`; on success the account is INACTIVE pending activation (SR-032.6) and the activation email is triggered server-side (SR-033.1).
  - `frontend/src/core/admin/accounts/LifecycleActions.tsx` — sysadmin-only Deactivate / Reactivate / Delete / Resend-activation actions.
  - `frontend/src/core/admin/accounts/DeleteConfirmDialog.tsx` — the SR-034.6 confirmation showing the account **email and type**, plus the **ADR-0013 lost-code warning** text: deletion anonymizes the user's data for 5 years and emails them a one-time retrieval code that is never stored; if the user loses the code the dataset is unrecoverable; the email is released for reuse (SR-034.7). Requires explicit confirm; cannot be undone (SR-034.6).
  - `frontend/src/core/admin/accounts/index.ts` — route export.
- Libraries: React 18, TanStack Query, MUI (table, form, select, dialog via ShellServices), React Router.
- Validation: required first name / surname / email (SR-032.2); duplicate email → server `409 /errors/conflict` mapped to the email field (SR-032.3); the UI does not pre-check uniqueness.
- Self-deactivation guard (SR-034.1): the Deactivate action is disabled for the acting administrator's own row (server also rejects).
- Error cases: `403 /errors/forbidden` (admin attempting a sysadmin-only op or sysadmin type) → error surface; `409` duplicate email → field error; `404` acting on a missing account → refetch.
- Edge cases / SR rules quoted:
  - SR-032.4: "An administrative personnel user can create accounts of the following types only: Patient, Doctor, Administrative Personnel. The system prevents selection or submission of the System Administrator type for this creator role."
  - SR-034.6: "Before permanent deletion the system presents a confirmation step that displays the account's email address and type and requires explicit confirmation; deletion cannot be undone."
  - ADR-0013 (lost-code warning surfaced in the delete dialog): the retrieval code is user-held and never stored; a lost code makes the dataset unrecoverable by design.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + RTL + MSW), `frontend/src/core/admin/accounts/AccountsPage.test.tsx`:
  - list renders the **non-clinical projection** only; assert no clinical field is present (SR-009 AC-1/2).
  - create as admin creator: user-type select offers Patient/Doctor/Admin but **not** System Administrator (SR-032.4); create as sysadmin: System Administrator option present (SR-032.5).
  - create with missing first name / surname / email → blocked / server `400` field errors (SR-032.2).
  - duplicate email → `409` mapped to email field (SR-032.3).
  - delete (sysadmin): clicking Delete opens the confirm dialog showing **email + type** and the **ADR-0013 lost-code warning text**; confirming issues `DELETE /accounts/{id}`; cancelling issues nothing (SR-034.6, SR-027.2, ADR-0013).
  - deactivate/reactivate (sysadmin) issue the correct endpoints; Deactivate is disabled on the acting admin's own row (SR-034.1).
  - lifecycle actions absent for a non-sysadmin admin role (SR-034 sysadmin-only).
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] The account list shows only the non-clinical projection; no clinical data is requested or shown (SR-009).
- [ ] Account creation enforces required fields and offers only role-permitted user types (admin cannot create sysadmin) (SR-032.2/4/5).
- [ ] Duplicate email is surfaced as a field error from the server `409` (SR-032.3).
- [ ] System administrators can deactivate, reactivate, and delete accounts; non-sysadmins cannot see these actions (SR-034).
- [ ] Delete shows a confirmation with the account email + type and the ADR-0013 lost-code warning, and cannot proceed without explicit confirmation (SR-034.6, SR-027.2, ADR-0013).
- [ ] An admin cannot deactivate their own account from the UI (SR-034.1).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-009, SR-032, SR-034 → TASK-095 → tests)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-029a (backend admin projection), **TASK-095a** (FE: ADR-0013 delete warning, resend-activation control). Unchecked items reflect the gaps the audit found; stays **In Progress** until addressed.
