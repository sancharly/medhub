# TASK-026a — Password-policy errors as 400 + activation confirm-match (remediation)

- **Phase:** 2 — Auth & identity
- **Implements / restores:** SR-025, SR-027.3, SR-033; remediates TASK-026, TASK-032
- **Depends on:** TASK-026, TASK-032
- **Branch:** `feature/password-policy-problem`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-026/032 verdict **PARTIAL**

## Objective

`PasswordPolicyError` is a bare `Exception` with no registered RFC 7807 handler, so a policy violation
on the **activation** endpoint (which doesn't manually catch it) returns a generic **500** instead of a
**400 validation-error** naming the failed rule. Also the activation endpoint does not enforce the
password/confirm-password match the AC requires.

## Implementation detail

- Make `PasswordPolicyError` a `ProblemError(status=400, type=/errors/validation-error)` with
  field-level `errors[]`, or register a handler in `app/api/errors.py`.
- Enforce password == confirm at the activation endpoint (`ActivationRequest` should carry both, or the
  service should validate), returning a generic non-disclosing mismatch error.

## Acceptance criteria

- [x] A weak password at activation returns **400** problem+json naming the violated rule (not 500).
- [x] Password/confirm mismatch at activation is rejected with a 400.
- [x] Existing change-password behavior unchanged.

## Definition of Done

- [x] Lint + type-check pass
- [x] Tests cover activation policy-violation → 400 and mismatch → 400
- [x] OpenAPI regenerated if the activation request schema changes
- [ ] Traceability row updated (SR-025/SR-033 → TASK-026a → tests)
- [ ] Security review completed
