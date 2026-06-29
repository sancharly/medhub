# TASK-095a — Admin accounts view completeness (remediation)

- **Phase:** 7 — Frontend core
- **Implements / restores:** SR-032, SR-034, ADR-0013; remediates TASK-095
- **Depends on:** TASK-095, TASK-035a (erasure delivery)
- **Branch:** `feature/admin-accounts-completeness`
- **Status:** Not started
- **Source:** `AUDIT-LEDGER.md` — TASK-095 verdict **PARTIAL** (phase-7 QA, confirmed)

## Objective

Two acceptance criteria are unmet in the admin accounts view:
- `DeleteConfirmDialog.tsx` shows a generic "unrecoverable" message but not the ADR-0013 specifics the AC
  requires: that deletion **anonymizes** data into a 5-year-retained dataset and emails a one-time
  **retrieval code that is never stored**, and that the email is released for reuse.
- `resendActivation` exists in the API client (`client.ts:221`) but **no UI control invokes it** — the
  resend-activation action listed in the spec is unreachable.

## Implementation detail

- Update `DeleteConfirmDialog` copy to state the ADR-0013 anonymization + one-time retrieval-code +
  email-release semantics so the admin understands the irreversible action.
- Add a "Resend activation" control (for INACTIVE accounts) wired to `apiClient.resendActivation(id)`,
  with success/error feedback.

## Acceptance criteria

- [ ] The delete confirmation states the ADR-0013 anonymization + retrieval-code + email-release behavior.
- [ ] An admin can resend an activation email for an inactive account from the UI.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Component tests assert the delete-warning content and the resend-activation call
- [ ] Traceability row updated (SR-032/SR-034 → TASK-095a → tests)
