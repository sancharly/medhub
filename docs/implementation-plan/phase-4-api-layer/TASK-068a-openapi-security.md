# TASK-068a — Surface the security model in OpenAPI (remediation)

- **Phase:** 4 — API layer
- **Implements / restores:** SR-031, NFR-006; remediates TASK-068
- **Depends on:** TASK-068, TASK-069a
- **Branch:** `feature/openapi-security`
- **Status:** Not started
- **Source:** `AUDIT-LEDGER.md` — TASK-068 verdict **PARTIAL**

## Objective

The OpenAPI `cookieAuth` security scheme is **defined but never applied** to any operation (root
`security` is `[]`), and the `X-CSRF-Token` header is undocumented — so the contract does not surface the
deny-by-default + CSRF model it claims. The contract tests only assert the scheme exists.

## Implementation detail

- In `app/api/openapi.py`, apply the `cookieAuth` requirement to all protected operations (exempt the
  public ones), and document the `X-CSRF-Token` header on state-changing operations.
- Strengthen the contract test to assert protected ops reference the scheme and that state-changing ops
  document the CSRF header.
- Consolidate the duplicate `app/export_openapi.py` / `scripts/export_openapi.py` to the one CLAUDE.md references.

## Acceptance criteria

- [ ] Every protected operation declares the cookie security requirement; public routes do not.
- [ ] State-changing operations document `X-CSRF-Token`.
- [ ] Contract test fails if an operation omits the security requirement.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] OpenAPI regenerated, redocly lint passes, parity check green
- [ ] Contract tests updated and passing
- [ ] Traceability row updated (SR-031 → TASK-068a → tests)
- [ ] Security review completed
