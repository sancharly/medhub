# TASK-087a — Fix forced-password-change gate (remediation)

- **Phase:** 6 — Frontend foundation
- **Implements / restores:** SR-025; remediates TASK-087
- **Depends on:** TASK-087
- **Branch:** `feature/forced-password-gate`
- **Status:** Not started
- **Source:** `AUDIT-LEDGER.md` — TASK-087 verdict **FAIL**

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

- [ ] After login with a must-change password, all routes redirect to `/password` until changed —
  including after a page refresh / direct navigation.
- [ ] The gate reads a field the real backend actually returns.
- [ ] Tests assert against the real contract shape.

## Definition of Done

- [ ] Lint + type-check pass; types regenerated if `MeResponse` changes
- [ ] Tests pass against contract-accurate mocks; verified end-to-end
- [ ] OpenAPI regenerated if backend schema changed
- [ ] Traceability row updated (SR-025 → TASK-087a → tests)
- [ ] Security review N/A
