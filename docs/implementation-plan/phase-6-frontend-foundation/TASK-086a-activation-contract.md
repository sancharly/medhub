# TASK-086a — Fix activation UI to match the real contract (remediation)

- **Phase:** 6 — Frontend foundation
- **Implements / restores:** SR-033; remediates TASK-086
- **Depends on:** TASK-086, TASK-061 (activation endpoints)
- **Branch:** `feature/activation-contract`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-086 verdict **FAIL**

## Objective

The activation flow is broken against the real backend despite green tests: (1) `getActivation()` treats
any 2xx as valid, but the backend returns `200 {valid:false}` for expired/invalid tokens — so the
password form is shown for invalid tokens; (2) the POST sends only `{password}` but the backend requires
`accountId` (+ password), so a real activation returns 422. Tests mock a 404 the backend never sends.

## Implementation detail

- Type `getActivation()` to the real `ActivationTokenStatus` response; gate the form on `valid === true`.
- Carry `accountId` from the GET response into the POST body (`activate`), per the generated types.
- Rewrite the MSW mocks to the real OpenAPI shapes (200 `{valid:false}` for bad tokens; required `accountId`).

## Acceptance criteria

- [x] An invalid/expired token shows an error, not the password form.
- [x] A valid activation submits `accountId` + password and succeeds against the real backend.
- [x] Tests mock the real contract shapes (no fabricated 404).

## Definition of Done

- [x] Lint + type-check pass; types regenerated/aligned
- [x] Component tests pass against contract-accurate mocks; verified end-to-end against the running backend
- [x] Traceability row updated (SR-033 → TASK-086a → tests)
- [x] Security review N/A

## QA sign-off (2026-06-30)

- `getActivation()` now returns `ActivationTokenStatus` (typed); form is gated on `status.valid === true`.
- `activate()` now sends `{ accountId, password, confirmPassword }` per real backend contract.
- `SetPasswordForm.onSubmit` signature updated to pass `confirmPassword`.
- MSW mocks updated: valid token → `{ valid: true, accountId: "..." }`; invalid token → `{ valid: false }` (200, not 404).
- All 5 activation tests pass.

**Status:** Completed
