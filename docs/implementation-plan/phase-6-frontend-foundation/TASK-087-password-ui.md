# TASK-087 — Change-password UI with live policy hints

- **Phase:** 6 — Frontend foundation
- **Software item / unit:** SI-FE-AUTH / U-FEA-PasswordForm
- **Implements:** SR-025 (AC-1 min 12 chars; AC-2 four character classes; AC-3 no username/email substring; AC-4 not one of the last 12; AC-5 violated-rule message; AC-6 forced change on first login before any other action)
- **Depends on:** TASK-080 (typed `ApiClient` + cookie/CSRF + Query) — must be merged first
- **Branch:** `feature/fe-password-ui`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Build the **change-password screen** with **live, client-side policy hints**: a form (current password, new password, confirm new password) that shows the user, as they type, which SR-025 rules are satisfied — minimum 12 characters, all four character classes, no email/username substring — and submits to `POST /auth/password`. The hints are convenience only; the **server is the authoritative validator** (SR-025.5, SR-031.5), including the password-history-of-12 check (AC-4) which the client cannot evaluate. This screen also serves the forced first-login change, which must complete before any other action (SR-025.6 / AC-6). Traces to SR-025.

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2):

```ts
// generated from OpenAPI (TASK-080)
await apiClient.changePassword({ currentPassword, newPassword, confirmNewPassword }); // POST /auth/password
```

- Submits to `POST /auth/password` (api-design.md "Authentication & session", SR-025). The server enforces all four classes, the 12-char minimum, the email/username-substring rejection, the **history of 12** (AC-4 — not checkable client-side), and the 180-day max-age reset (SR-025 AC-1..7); the UI renders the server's field-level `errors[]` (via TASK-084) identifying the violated rule (SR-025.5).
- The live hints are presentational only and **clearly non-authoritative** — they never block submission on their own beyond an obvious empty/mismatch guard, and never claim to evaluate history (AC-4) (SR-031.5).
- When reached as the forced first-login change (entered from TASK-085 on `mustChangePassword`), the screen blocks navigation to any other route until a successful change (SR-025.6 / AC-6).
- Must **not**: reimplement the authoritative policy client-side, especially the last-12-history check which requires server state (SR-025.4, SR-031.5); reveal which of new/confirm is wrong on a mismatch (non-disclosing message, parity with SR-033.4); let the user bypass the forced change (SR-025.6).

## Implementation detail

- Files to create:
  - `frontend/src/auth/ChangePasswordPage.tsx` — the route component for `/password`; three MUI password fields; a TanStack Query mutation calling `apiClient.changePassword`. On success (200) it confirms and routes onward (into the app, or to login if the backend invalidated sibling sessions per ADR-0012).
  - `frontend/src/auth/PolicyHints.tsx` — live checklist reflecting `passwordHints.ts` (shared with TASK-086): ≥12 chars, upper, lower, digit, special, no email/username substring — each a satisfied/unsatisfied indicator, labelled "checked on submit by the server" (SR-031.5). History (AC-4) is explicitly noted as server-checked.
  - `frontend/src/auth/useChangePassword.ts` — mutation hook; maps `400 /errors/validation-error` `errors[]` to the field that violated the rule (SR-025.5).
  - `frontend/src/auth/ForcedPasswordGate.tsx` — when `mustChangePassword` is set on the cached `['me']`, this gate redirects all routes to `/password` until success (SR-025.6 / AC-6).
  - `frontend/src/auth/index.ts` — export additions; mount `ForcedPasswordGate` in the protected route tree (after TASK-085 `RequireAuth`).
- Libraries (exact stack): React 18, React Router, TanStack Query (mutation), MUI form components, TASK-084 error surface, TypeScript; reuses `passwordHints.ts` from TASK-086.
- Live hints update on each keystroke for the locally-checkable rules (length, classes, substring); the history rule (AC-4) and max-age (AC-7) are server-only and surfaced from the response (SR-025.4/5/7).
- Mismatch of new/confirm shows a single non-disclosing message and blocks submit; server policy violations render per-rule next to the new-password field (SR-025.5).
- Forced-change: the gate prevents reaching profile/clinical/appointment routes until the change succeeds (SR-025.6); it relies on the cached `['me'].mustChangePassword` flag returned at login (TASK-085).
- This screen handles no PHI.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + React Testing Library + MSW), `frontend/src/auth/ChangePasswordPage.test.tsx`:
  - typing a new password updates the live hints for length, the four classes, and email/username-substring in real time (SR-025 AC-1/2/3) — labelled non-authoritative.
  - a server `400 /errors/validation-error` rejecting a password reused from the last 12 shows the history message; the client did not pre-block it (SR-025.4, SR-031.5).
  - a server `400` for a weak password shows the violated-rule message next to the field (SR-025.5).
  - new/confirm mismatch shows a single non-disclosing message and does not submit (parity SR-033.4).
  - a successful change confirms and routes onward (200).
- Gate test, `frontend/src/auth/ForcedPasswordGate.test.tsx`: with `mustChangePassword: true`, navigating to any other protected route redirects to `/password`; after a successful change, normal navigation resumes (SR-025.6 / AC-6).
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] Live client hints reflect length, four character classes, and email/username-substring rules as the user types, clearly marked non-authoritative (SR-025 AC-1/2/3, SR-031.5).
- [ ] The server is the authoritative validator; history-of-12 and max-age are surfaced from the response, not pre-checked client-side (SR-025 AC-4/5/7, SR-031.5).
- [ ] A violated-rule message identifies the specific rule; a new/confirm mismatch is non-disclosing (SR-025.5).
- [ ] On first login a forced change blocks all other actions until it succeeds (SR-025.6 / AC-6).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-025 → TASK-087 → tests)

## Audit verdict (2026-06-29)

- **Verdict:** FAIL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-087a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
