# TASK-083 — Reusable confirmation dialog for destructive actions

- **Phase:** 6 — Frontend foundation
- **Software item / unit:** SI-FE-SHELL / U-FE-Confirm
- **Implements:** SR-027 (AC-2 destructive or safety-relevant actions require an explicit confirmation step before execution); NFR-009 (AC-3 explicit confirmation of destructive/safety-relevant actions)
- **Depends on:** TASK-081 (AppLayout + MUI theme) — must be merged first
- **Branch:** `feature/fe-confirm-dialog`
- **Status:** Completed

## Objective

Provide the **single reusable confirmation dialog** that gates every destructive or safety-relevant action in the SPA so the user must explicitly confirm before it executes (SR-027 AC-2, NFR-009 AC-3). Centralizing it guarantees consistent wording, button placement, and behavior across all such actions — consent revoke (SR-008.3 / TASK-094), account deletion (SR-034.6 / TASK-095), appointment decline (TASK-093), and any future destructive operation. The dialog displays the consequence and requires a deliberate confirm; cancel is the safe default. It performs the action only via a caller-supplied callback — it owns no domain logic. Traces to SR-027, NFR-009.

## Interfaces to honor

Provides the confirmation half of `ShellServices` from [12-interfaces.md](../../design/12-interfaces.md) §12.2 (provider SI-FE-SHELL; consumers SI-FE-CORE, modules):

```ts
interface ConfirmOptions {
  title: string;
  description: React.ReactNode;   // states the consequence (e.g. "cannot be undone")
  confirmLabel?: string;          // defaults to a clear verb, never just "OK"
  destructive?: boolean;          // styles confirm as a destructive action
}
// resolves true if the user confirmed, false if cancelled/dismissed
function confirm(options: ConfirmOptions): Promise<boolean>;
```

- Exposed through a `useConfirm()` hook / `ShellServices.confirm(...)` so any view requests a confirmation without rendering its own dialog (SR-027 AC-1 consistency, AC-2 confirmation).
- Renders into the shell (TASK-081) as a single mounted dialog instance; uses MUI `Dialog` (accessible focus trap, ADR-0003 / NFR-009).
- Must **not**: execute any domain mutation itself — the caller runs the action only after the promise resolves `true`; default the focus/primary action to **confirm** for a destructive action (cancel must be the low-friction default); be bypassable for the SR-008 revoke and SR-034.6 delete flows (those callers must route through it).

## Implementation detail

- Files to create:
  - `frontend/src/core/confirm/ConfirmDialog.tsx` — the MUI `Dialog` rendering title, description, cancel + confirm buttons; `destructive` styles confirm with the theme's error color; accessible (labelled, focus-trapped, `Esc`/backdrop = cancel).
  - `frontend/src/core/confirm/ConfirmProvider.tsx` — context provider holding a single dialog instance; exposes the imperative `confirm(options): Promise<boolean>` that opens the dialog and resolves on the user's choice.
  - `frontend/src/core/confirm/useConfirm.ts` — hook returning `confirm(...)`.
  - `frontend/src/core/confirm/index.ts` — exports provider, hook, types.
  - Mount `ConfirmProvider` at the shell root (TASK-081) so it is available app-wide.
- Libraries (exact stack): React 18 (context + promise-based imperative API), MUI `Dialog`/`Button`, TypeScript.
- Behavior: opening returns a promise; **Confirm** resolves `true`, **Cancel**/`Esc`/backdrop resolves `false`; the dialog closes either way. The caller performs the mutation (e.g. `apiClient.revokeConsent(id)`) only on `true`. For irreversible actions (account deletion, SR-034.6) the `description` states it cannot be undone and the deleted account's email/type are shown by the caller (SR-034.6 detail lives in TASK-095, surfaced via this dialog).
- Consistent wording/styling for all destructive actions satisfies SR-027 AC-1/AC-2 and NFR-009 AC-3 in one place.
- This unit owns no routes, no API calls, no PHI.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + React Testing Library), `frontend/src/core/confirm/ConfirmDialog.test.tsx`:
  - `confirm({...})` opens a dialog showing the title and consequence description (SR-027 AC-2).
  - clicking **Confirm** resolves the promise `true`; clicking **Cancel** (and pressing `Esc`, and backdrop click) resolves `false` (SR-027 AC-2, NFR-009 AC-3).
  - the destructive variant styles the confirm action with the error color and the dialog is dismissible to a safe cancel default.
  - the dialog is accessible: labelled, focus moves into it on open, focus is trapped (NFR-009).
  - no mutation runs unless the caller acts on a `true` result — asserted with a spy callback invoked only after confirm (SR-027 AC-2).
- Hook test, `frontend/src/core/confirm/useConfirm.test.tsx`: `useConfirm()` returns a function whose promise reflects the user's choice.
- Each test names the SR/NFR AC it verifies.

## Acceptance criteria

- [x] A single reusable dialog gates destructive/safety-relevant actions; the action runs only after explicit confirmation (SR-027 AC-2, NFR-009 AC-3).
- [x] Cancel / `Esc` / backdrop are the safe default and resolve `false`; nothing executes (SR-027 AC-2).
- [x] The destructive variant is visually distinct and states the consequence (e.g. "cannot be undone") (NFR-009 AC-3).
- [x] Exposed via `ShellServices.confirm(...)` / `useConfirm()` so consent revoke (SR-008.3) and account deletion (SR-034.6) route through it consistently (SR-027 AC-1).
- [x] The dialog is accessible (labelled, focus-trapped) (NFR-009).

## Definition of Done

- [x] Lint + type-check pass (`eslint`/`tsc`)
- [x] Unit/component tests pass; coverage target met
- [x] Traceability matrix row updated (SR-027, NFR-009 → TASK-083 → tests)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL → Remediated 2026-06-30
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Fix:** `autoFocus` moved to Cancel button when `destructive=true`; test added to verify Cancel receives focus in destructive variant.

## QA sign-off (2026-06-30)

- All acceptance criteria met.
- `autoFocus` is now on Cancel (not Confirm) for destructive dialogs.
- Test "destructive variant autofocuses Cancel, not Confirm" added and passes.

**Status:** Completed
