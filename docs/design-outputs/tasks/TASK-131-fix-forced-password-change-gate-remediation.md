---
id: "TASK-131"
type: task
title: "Fix forced-password-change gate (remediation)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-025"
    relation: implements
  - target: "TASK-087"
    relation: relates_to
tags: ["phase:6-frontend-foundation", "remediation-of:TASK-087", "original-id:TASK-087a"]
---

- **Phase:** 6 — Frontend foundation
- **Implements / restores:** SR-025; remediates TASK-087
- **Depends on:** TASK-087
- **Branch:** `feature/forced-password-gate`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-087 verdict **FAIL**

*Originally filed as TASK-087a.*

## Objective

`ForcedPasswordGate` reads `me.mustChangePassword`, but neither `GET /me` (`MeResponse`) nor the cached
`LoginResponse.user` (`MeSummary`) contains that field — it lives only top-level on `LoginResponse`. So
the persistent gate always sees `undefined` and never redirects; only the one-shot login redirect works.
A user who navigates away or refreshes is no longer forced to change an expired/temporary password.

## Implementation detail

- Choose one source of truth: either add `mustChangePassword` to `MeResponse` (backend + regenerate
  types) so the gate can read it from `/me`, OR cache `LoginResponse.mustChangePassword` under a
  dedicated query key and have `ForcedPasswordGate` read that.
- Remove the `Record<string,unknown>` cast smell in `ForcedPasswordGate.tsx` once the field is real.
- Update tests to the real `/me` shape (they currently mock a non-existent field).

## Acceptance criteria

- [x] After login with a must-change password, all routes redirect to `/password` until changed —
  including after a page refresh / direct navigation.
- [x] The gate reads a field the real backend actually returns.
- [x] Tests assert against the real contract shape.

## Definition of Done

- [x] Lint + type-check pass; types regenerated if `MeResponse` changes
- [x] Tests pass against contract-accurate mocks; verified end-to-end
- [x] OpenAPI regenerated if backend schema changed
- [x] Traceability row updated (SR-025 → TASK-087a → tests)
- [x] Security review N/A

## QA sign-off (2026-06-30)

- `must_change_password: bool` added to backend `MeResponse` schema; computed from `PasswordService().is_expired(actor)`.
- `GET /me` router now injects `PasswordService` and sets `must_change_password` before returning.
- OpenAPI regenerated; frontend types regenerated — `MeResponse.mustChangePassword` is now a real typed field.
- `ForcedPasswordGate.tsx` unsafe cast removed; reads `me?.mustChangePassword` directly.
- Backend `test_me_router.py` updated to set `password_changed_at = None` on mock account.
- All 2 gate tests pass; all 485 backend tests pass.

**Status:** Completed
