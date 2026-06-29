# TASK-086 — Account activation / set-password UI

- **Phase:** 6 — Frontend foundation
- **Software item / unit:** SI-FE-AUTH / U-FEA-Activation
- **Implements:** SR-033 (AC-2 the activation link validates the token; AC-3 password set must satisfy SR-025; AC-4 password entered twice and mismatch rejected with a non-disclosing message; AC-5 on success the account becomes active)
- **Depends on:** TASK-080 (typed `ApiClient` + cookie/CSRF + Query) — must be merged first
- **Branch:** `feature/fe-activation-ui`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Build the **account-activation screen** a newly created user reaches by following the emailed activation link: it validates the activation token (`GET /activation/{token}`), then presents a set-password form requiring the password **twice** ("Password" and "Confirm password") that the user submits (`POST /activation/{token}`) to set their password and activate the account (SR-033 AC-2/3/4/5). On success the account transitions to active and the user can log in. This is an unauthenticated flow keyed solely by the single-use token. Traces to SR-033.

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2):

```ts
// generated from OpenAPI (TASK-080)
await apiClient.validateActivation(token);                       // GET  /activation/{token}
await apiClient.activate(token, { password, confirmPassword });  // POST /activation/{token}
```

- `GET /activation/{token}` (api-design.md "Account activation", SR-033.2) validates the token before showing the form; an expired/used/invalid token shows a clear message and the option to request a new link from an administrator (resend is an admin action, SR-033.7 / TASK-095) — the form is not shown.
- `POST /activation/{token}` (SR-033.3/4/5) submits the two password fields; the **server** enforces all SR-025 complexity rules and the match check authoritatively (SR-031.5). The UI shows the server's field-level `errors[]` (via TASK-084) identifying the violated rule (SR-033.3 → SR-025.5).
- Must **not**: implement the SR-025 policy as the authoritative check (server is authoritative, SR-031.5) — client hints are convenience only; reveal which of the two password fields is "wrong" on a mismatch — the message indicates only that the values do not match (SR-033.4, no information leakage); auto-login the user (SR-033.6: activation enables login, it does not itself create a session); send the token anywhere except these two endpoints.

## Implementation detail

- Files to create:
  - `frontend/src/auth/ActivationPage.tsx` — the route component for `/activation/:token`; on mount runs `validateActivation(token)` (TanStack Query). On a valid token, renders the set-password form; on an invalid/expired token, renders the "link no longer valid — ask an administrator to resend" message (SR-033.2/7).
  - `frontend/src/auth/SetPasswordForm.tsx` — reusable two-field password form ("Password", "Confirm password") with optional live policy hints (shared with TASK-087); calls `activate(token, ...)`.
  - `frontend/src/auth/passwordHints.ts` — convenience-only client hints mirroring SR-025 (min 12, four classes, no email/username substring) — **labelled clearly as non-authoritative**; the server decides (SR-031.5).
  - `frontend/src/auth/useActivate.ts` — the activation mutation hook (success → route to `/login` with a "account activated, please log in" notice, SR-033.6).
  - `frontend/src/auth/index.ts` — export additions.
  - Register the public route `/activation/:token` in the shell router.
- Libraries (exact stack): React 18, React Router (`useParams` for the token), TanStack Query (validate query + activate mutation), MUI form components, TASK-084 error surface, TypeScript.
- Mismatch handling: if the two values differ, show a single non-disclosing "passwords do not match" message and do not submit (SR-033.4); on submit, server `400 /errors/validation-error` field messages are shown next to the form (SR-033.3 → SR-025.5).
- On success the screen confirms activation and directs the user to the login flow (TASK-085); it does **not** establish a session itself (SR-033.6).
- This screen handles no PHI; the token is the only credential and is used only against the two activation endpoints.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + React Testing Library + MSW), `frontend/src/auth/ActivationPage.test.tsx`:
  - a **valid** token (`GET /activation/{token}` → `200`) renders the two-field set-password form (SR-033.2/4).
  - an **expired/used** token (`GET` → `400`/`404`) renders the "link no longer valid — ask an administrator to resend" message and **no** form (SR-033.2/7).
  - entering two **different** values shows the non-disclosing "passwords do not match" message and does not submit; neither field is singled out (SR-033.4).
  - a server `400 /errors/validation-error` for a weak password shows the field-level rule message (SR-033.3 → SR-025.5).
  - a successful `POST /activation/{token}` routes to `/login` with an "activated" notice and establishes **no** session (SR-033.5/6).
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] Following the activation link validates the token before showing the form; invalid/expired tokens are rejected with a clear resend hint (SR-033.2/7).
- [ ] The form requires the password twice; a mismatch is rejected with a message that does not disclose which field is wrong (SR-033.4).
- [ ] Password complexity is enforced server-side; the UI surfaces the violated-rule message and treats client hints as non-authoritative (SR-033.3 → SR-025, SR-031.5).
- [ ] A valid, confirmed submission activates the account and directs the user to log in without auto-creating a session (SR-033.5/6).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-033 → TASK-086 → tests)

## Audit verdict (2026-06-29)

- **Verdict:** FAIL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-086a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
