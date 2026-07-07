---
id: "TASK-133"
type: task
title: "Admin accounts view completeness (remediation)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-032"
    relation: implements
  - target: "SR-034"
    relation: implements
  - target: "TASK-095"
    relation: relates_to
  - target: "TASK-121"
    relation: relates_to
tags: ["phase:7-frontend-core", "remediation-of:TASK-095", "original-id:TASK-095a"]
---

- **Phase:** 7 — Frontend core
- **Implements / restores:** SR-032, SR-034, ADR-0013; remediates TASK-095
- **Depends on:** TASK-095, TASK-035a (erasure delivery)
- **Branch:** `feature/admin-accounts-completeness`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-095 verdict **PARTIAL** (phase-7 QA, confirmed)

*Originally filed as TASK-095a.*

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

- [x] The delete confirmation states the ADR-0013 anonymization + retrieval-code + email-release behavior.
- [x] An admin can resend an activation email for an inactive account from the UI.

## Definition of Done

- [x] Lint + type-check pass
- [x] Component tests assert the delete-warning content and the resend-activation call — `AccountsPage.test.tsx`
- [x] Traceability row updated (SR-032/SR-034 → TASK-095a → tests)

## Implementation notes (2026-06-30)

- `DeleteConfirmDialog.tsx`: replaced the generic "unrecoverable" copy with ADR-0013-specific language —
  anonymization into a 5-year-retained dataset, a one-time retrieval code emailed to the user that is
  never stored by the system, and release of the email address for reuse.
- `LifecycleActions.tsx`: added a "Resend activation" button shown for `INACTIVE` accounts, wired to
  `apiClient.resendActivation(id)`, with a success/error `Alert` after the mutation settles.
