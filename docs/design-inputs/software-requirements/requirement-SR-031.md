# SR-031 Web vulnerability mitigations

## Summary

The system shall implement technical controls against the OWASP Top 10 web vulnerabilities and gate integration of authentication and session management code on a documented security review.

## Description

Beyond credential and session hardening, the MedHub web application is exposed to a broad class of application-layer attacks (injection, broken access control, XSS, security misconfiguration, and others catalogued in the OWASP Top 10). This requirement specifies the minimum set of technical controls the application must implement and the review gate that verifies them before code is merged. Controls are applied at the application layer; network-layer controls (TLS, firewall) are covered by SR-022 and deployment configuration.

## Acceptance Criteria

1. All database queries are executed through parameterized queries or an ORM that prevents SQL injection; no string-concatenated SQL queries are present in the codebase.
2. A `Content-Security-Policy` HTTP response header is set on all application pages to restrict script sources and mitigate XSS.
3. All state-changing HTTP requests (POST, PUT, PATCH, DELETE) are protected by anti-CSRF tokens or the `SameSite=Strict` cookie attribute (per SR-030 criterion 6).
4. The following security-relevant HTTP response headers are set on all responses: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
5. Access control decisions are enforced server-side for every request; no client-side-only access gate is relied upon as the sole control.
6. A security review of authentication and session management code is completed and documented before merging to the main branch. The review verifies compliance with SR-025, SR-029, SR-030, and this requirement (SR-031), and produces a signed record stored in the project repository.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-007 "Cybersecurity".

## Risk Analysis

### Rationale

Web applications are a primary attack surface for adversaries targeting PHI. The OWASP Top 10 represents the most critical and commonly exploited application-layer vulnerability classes. MDR and FDA cybersecurity pre-market guidance require that software be developed with recognized secure development practices; compliance with OWASP Top 10 controls provides a documented, auditable baseline.

### Potential Risks

- **Security (Injection):** Unparameterized queries allow SQL injection attacks that could expose or corrupt the entire patient database.
- **Security (XSS):** Missing CSP and output encoding allow injection of malicious scripts into clinical user sessions, enabling token theft or fraudulent clinical actions.
- **Security (Broken Access Control):** Client-side-only access checks are trivially bypassed, granting unauthorized access to PHI.
- **Compliance:** Absence of documented security controls and a review gate weakens the cybersecurity case file required under MDR Article 10(2) and FDA guidance on cybersecurity in medical devices.

### Control Measures

- Parameterized queries (criterion 1) are enforced through code review and linting rules that flag raw SQL concatenation.
- CSP (criterion 2) and CSRF protection (criterion 3) are configured at the framework or middleware level and verified in integration tests.
- HTTP security headers (criterion 4) are applied via a centralized middleware to ensure uniform coverage.
- Server-side access control (criterion 5) is the enforceable companion to the RBAC defined in SR-005; client-side rendering logic may hide UI elements but is never the sole control.
- The mandatory security review (criterion 6) creates an auditable record tying implementation to this requirement, supporting IEC 62304 traceability.

## Status

Approved

## Version History

Version 1.0 - Initial creation; split from combined SR-025
