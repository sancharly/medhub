---
id: "TASK-119"
type: task
title: "Password-policy errors as 400 + activation confirm-match (remediation)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-025"
    relation: implements
  - target: "SR-027"
    relation: implements
  - target: "SR-033"
    relation: implements
  - target: "TASK-026"
    relation: relates_to
  - target: "TASK-032"
    relation: relates_to
tags: ["phase:2-auth-identity", "remediation-of:TASK-026", "original-id:TASK-026a"]
---

- **Phase:** 2 — Auth & identity
- **Implements / restores:** SR-025, SR-027.3, SR-033; remediates TASK-026, TASK-032
- **Depends on:** TASK-026, TASK-032
- **Branch:** `feature/password-policy-problem`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-026/032 verdict **PARTIAL**

*Originally filed as TASK-026a.*

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
- [x] Traceability row updated (SR-025/SR-033 → TASK-026a → tests)
- [x] Security review completed
