# ADR-0011: Defense-in-depth security and compliance approach

## Status

Accepted

## Context

MedHub is a medical device processing special-category PHI and must satisfy a dense set of security/compliance requirements: TLS + encryption at rest (SR-022), password complexity and lifecycle (SR-025), account lockout (SR-029), session management (SR-030), OWASP Top 10 mitigations with a mandatory security-review gate (SR-031), append-only audit logging (SR-023), erasure/anonymization (SR-024), and the GDPR/MDR/FDA/IEC-62443 framing of NFR-004/005/006/007. These cut across every module, so they must be **cross-cutting concepts**, not per-feature afterthoughts.

## Decision

Adopt a **defense-in-depth** approach built from centralized, reusable controls:

1. **Transport & storage crypto** — TLS everywhere via the reverse proxy with HSTS (SR-001/SR-022); object-store SSE and DB volume encryption at rest (SR-022, ADR-0009).
2. **Centralized authorization** — deny-by-default `AuthorizationService` (ADR-0006) is the single enforcement point (SR-005); enforced **server-side** for every request (SR-031 AC-5).
3. **Credential & session hardening** — Argon2id password hashing (SR-002 AC-4); server-side password policy validator (SR-025); lockout counter with audit (SR-029); server-side session store with role-based inactivity timeouts, absolute lifetime, concurrent-session cap, and `Secure`/`HttpOnly`/`SameSite=Strict` cookies (SR-030, ADR-0012).
4. **Web-vulnerability middleware** — a single security middleware sets CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` on all responses; CSRF protection via SameSite + tokens on state-changing requests; ORM-only parameterized queries; output encoding in the SPA (SR-031 AC-1–4).
5. **Append-only audit log** — a centralized `AuditService` writes immutable entries for authentication, clinical-data access, consent changes, and administrative actions, with actor/action/target/timestamp/outcome and no plaintext secrets (SR-023). Ordinary users cannot modify it.
6. **Data-subject rights** — deletion is implemented as anonymization into a 5-year retained dataset with a user-held, never-stored retrieval code (only a salted KDF hash is kept), then permanent erasure at 5 years (SR-024, SR-034; ADR-0013).
7. **Process controls** — version-controlled requirements/design/ADRs/tests with bidirectional traceability and a security-review gate before merging auth/session code (SR-028, SR-031 AC-6; NFR-005/006).

The security framing references **OWASP Top 10** (web controls) and **IEC 62443-3-3 SL 2** (the standard the SRs cite for credentials/lockout/session), supporting the MDR Article 10(2) / FDA cybersecurity case file (SR-031 rationale).

## Consequences

### Positive

- Cross-cutting controls are implemented once (middleware, services) and inherited by every module including plugins (ADR-0005) → uniform coverage, fewer gaps (SR-031 AC-4 "uniform coverage").
- A single audit log gives one coherent forensic/accountability trail across GDPR, cybersecurity, and MDR/FDA (SR-023, NFR-004/005/007).
- The mandatory security-review gate ties implementation to requirements, feeding IEC 62304 traceability (SR-031 AC-6, NFR-006).

### Negative

- Centralized controls are high-value targets and high-blast-radius; they need the most rigorous testing and review (accepted; aligned with NFR-006).
- Strict session timeouts and lockout can disrupt clinical workflow; mitigated by the requirement-mandated warnings/thresholds (SR-029 5-attempt/30-min, SR-030 2-min warning).

### Neutral

- Full IEC 62443 / penetration testing and formal threat modeling expand post-MVP; the MVP implements the specified technical controls and the review gate.

## Alternatives Considered

**Per-feature security implementations.** Rejected: inconsistent, unauditable, the classic broken-access-control source (SR-031 rationale).

**Third-party IdP/IAM (e.g., Keycloak, Auth0) for the MVP.** Considered for offloading auth/session/lockout. Deferred (not rejected long-term): adds an external dependency and integration/regulatory surface; the SRs specify precise behaviors (SR-025/029/030) that are straightforward to implement and audit in-process at MVP scale (see ADR-0012). Flagged as a future option in the Arc42 risks.

## References

- Requirements: SR-001, SR-002, SR-005, SR-022, SR-023, SR-024, SR-025, SR-028, SR-029, SR-030, SR-031, SR-034; NFR-004, NFR-005, NFR-006, NFR-007
- Related: ADR-0006, ADR-0009, ADR-0010, ADR-0012
