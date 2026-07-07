---
id: "TASK-113"
type: task
title: "Security review of auth/session/authz + dependency vulnerability scan"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-031"
    relation: implements
  - target: "NFR-007"
    relation: implements
  - target: "TASK-060"
    relation: relates_to
  - target: "TASK-069"
    relation: relates_to
  - target: "TASK-028"
    relation: relates_to
  - target: "SR-025"
    relation: relates_to
  - target: "SR-029"
    relation: relates_to
  - target: "SR-030"
    relation: relates_to
tags: ["phase:9-integration-system-testing-compliance"]
---

- **Phase:** 9 — Integration, system testing, compliance hardening
- **Software item / unit:** (process / cross-cutting) — reviews SI-AUTH, SI-AUTHZ, SI-API security middleware
- **Implements:** SR-031.6 (documented security review gate before merge to main; signed record in repo), SR-031.1–5 (OWASP mitigations checklist), NFR-007 (cybersecurity); ADR-0011
- **Depends on:** TASK-060 (auth/session endpoints), TASK-069 (security middleware + CSRF enforcement), TASK-028 (consent service) must be merged first; references SR-025 (password policy), SR-029 (lockout), SR-030 (session) implementations from Phase 2
- **Branch:** `enabler-story/security-review-gate`
- **Status:** Not started

## Objective

Perform and **document** the mandatory security review of the authentication, session-management, and authorization code, and run an automated **dependency / vulnerability scan**, producing the signed review record SR-031.6 requires **before** that code is merged to main. The review verifies compliance with SR-025, SR-029, SR-030, and SR-031, and confirms the SR-031.1–5 OWASP mitigations (CSP, CSRF, injection, XSS, security headers, server-side access control) are present and uniformly applied. This is the §8.3 / ADR-0011 "review gate" process control that feeds the IEC 62304 / MDR Article 10(2) / FDA cybersecurity case file (SR-031 rationale, NFR-006). It produces a controlled document, not application code.

## Interfaces to honor

- Reviews the implemented security choke points against their specifications: the deny-by-default `AuthorizationService` (single enforcement point, §12.3 rule 1), the server-side `SessionService` (opaque tokens, role timeouts, absolute lifetime, concurrency cap, hardened cookies — SR-030, ADR-0012), `PasswordService` (Argon2id + policy/history/age — SR-025), the lockout counter (SR-029), and the single security middleware (CSP + headers + CSRF, §8.3).
- Confirms the §12.3 invariants hold in code: data items always call `AuthorizationService` before returning protected data and never re-implement checks (rule 1); security-relevant ops call `AuditService` (rule 2); ORM-only parameterized queries (SR-031.1, rule via SI-PERSIST).
- Verifies access control is enforced **server-side for every request** and that no client-side-only gate is the sole control (SR-031.5).

This task must **not**: modify the reviewed code as part of the review (findings are filed back to the owning task for correction per the dev-plan code-review cycle); approve a merge while any SR-025/029/030/031 criterion is unmet; treat the SPA's UI hiding as an access control.

## Implementation detail

- Files to create:
  - `docs/security/security-review-auth-session.md` — the **signed review record** (SR-031.6): scope (commits/files reviewed), reviewer identity and date, the checklist below with pass/fail and evidence (test ids, code refs), findings, and the merge decision. Stored under version control in the project repository (SR-031.6 "signed record stored in the project repository").
  - `docs/security/owasp-checklist.md` — the SR-031 mitigations checklist mapped to OWASP Top 10 and to verifying evidence:
    - **Injection (SR-031.1):** ORM-only/parameterized queries; no string-concatenated SQL anywhere — confirmed by lint rule + code grep.
    - **XSS (SR-031.2):** `Content-Security-Policy` set on all pages; SPA output encoding (React default escaping) — confirmed by middleware test + header assertion.
    - **CSRF (SR-031.3):** anti-CSRF token and/or `SameSite=Strict` on all state-changing requests — confirmed by TASK-069 enforcement tests.
    - **Security headers (SR-031.4):** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` on all responses — header assertion tests.
    - **Broken access control (SR-031.5):** server-side enforcement on every request; client gate never sole control — verified against TASK-110 deny-by-default tests and TASK-111 bypass test.
    - **Credentials/lockout/session (SR-025/029/030):** policy, history/age, Argon2id, 5/30-min lockout, role timeouts + absolute lifetime + concurrency cap + hardened cookies — verified against the Phase 2 unit/integration tests.
  - `docs/security/dependency-scan-report.md` — the recorded output of the dependency/vulnerability scan with triage of any findings (accepted/fixed/deferred with rationale).
  - CI wiring (extends TASK-005): dependency scanning for both stacks — Python (`pip-audit`) and JS (`npm audit` and/or an SCA tool) — failing the build on unresolved high/critical advisories (NFR-007).
- The review is a **gate**: per the dev-plan code-review cycle, findings are reported back to the implementing task and the cycle repeats until no issues remain; only then is the auth/session/authz code merged to main (SR-031.6).
- No threat-modeling / penetration-testing beyond the specified technical controls is in MVP scope (post-MVP, ADR-0011) — the record states this scope boundary explicitly.

## Tests (write first — TDD, CLAUDE.md §4)

This is a review-and-scan task; its "tests" are the automated checks the review **relies on as evidence** and which must be green before the gate passes:

- Security-header and CSP middleware tests assert the SR-031.2/4 headers on representative routes including a module route (uniform coverage, SR-031 AC-4).
- CSRF enforcement tests assert state-changing requests without a valid token are rejected (SR-031.3).
- A lint/grep check asserts there is no string-concatenated SQL (SR-031.1).
- The bypass test (TASK-111) confirms server-side 403 when client gating is removed (SR-031.5).
- The dependency scan exits non-zero on unresolved high/critical advisories (NFR-007).
- Each evidence check is referenced from the checklist by id.

## Acceptance criteria

- [ ] A signed, version-controlled security review record of the auth/session/authz code exists before that code is merged to main (SR-031.6).
- [ ] The record verifies SR-025, SR-029, SR-030, and SR-031 compliance with cited evidence (SR-031.6).
- [ ] The OWASP checklist confirms injection (031.1), CSP/XSS (031.2), CSRF (031.3), headers (031.4), and server-side access control (031.5), each with verifying evidence.
- [ ] A dependency/vulnerability scan is recorded for both stacks and gates CI on high/critical advisories (NFR-007).
- [ ] Any findings are filed back to the owning task; the merge decision reflects the resolved state (dev-plan code-review cycle).

## Definition of Done

- [ ] Lint + type-check pass on any CI config added (`ruff`/`eslint` as applicable)
- [ ] Evidence checks (header/CSRF/SQL-lint/bypass) and the dependency scan pass in CI
- [ ] OpenAPI regenerated and re-linted (N/A)
- [ ] Audit events: N/A (review artifact; verifies that audited actions are audited)
- [ ] Traceability matrix rows updated (SR-031, NFR-007 → TASK-113 → review record + evidence checks)
- [ ] **Security review completed and signed** — this task **is** the SR-031.6 gate; the record is the deliverable
