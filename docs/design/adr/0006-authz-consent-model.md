# ADR-0006: Centralized deny-by-default RBAC plus per-source consent grants

## Status

Accepted

## Context

Access control is the most safety- and privacy-critical concern. Requirements demand: one user type per account (SR-004); a single, deny-by-default authorization mechanism evaluated on **every** request to data/modules, considering user type, doctor–patient care relationship, patient consent state, and module/group enablement (SR-005). Doctors see only their patients (SR-006); patients see only their own data (SR-007); admin personnel get a non-clinical projection and never clinical data (SR-009); appointment visibility is scoped (SR-011). Patients grant/revoke per-doctor consent with **immediate** effect (SR-008). Critically, SR-036 requires consent grants to be **tracked per source** (per-appointment grant vs. manual grant), with a doctor's effective access being the **union** of all active grants, so that declining one appointment removes only that appointment's contribution.

## Decision

Implement a single **`AuthorizationService`** (a core software item) enforcing **deny-by-default** policy, invoked from every protected endpoint via FastAPI dependency injection. The decision inputs are:

1. **User type** (RBAC base layer; SR-004/SR-005).
2. **Resource ownership / relationship** (e.g., patient owns record; doctor↔patient relationship).
3. **Consent** evaluated against a **`ConsentGrant`** table where each row is `(patient_id, doctor_id, source)` with `source ∈ {MANUAL, APPOINTMENT:{appointment_id}}` and an `active` flag. A doctor's effective clinical-data access to a patient = `EXISTS(any active ConsentGrant for that pair)` (the union, SR-036 AC-3/AC-4).
4. **Module/group enablement** (`ModuleAccessGuard`; SR-015).

Consent transitions are transactional and immediate: revoking a manual grant deactivates the `MANUAL` row; declining a confirmed appointment deactivates only that `APPOINTMENT:{id}` row (SR-036 Cases A/B/C). Every grant/revoke and every clinical-data access is written to the audit log (SR-008 AC-5, SR-023).

Administrative personnel are served by a **field-level projection** (name, family name, date of birth) enforced server-side; any clinical-data operation for that role is denied (SR-009).

## Consequences

### Positive

- One choke point → consistent enforcement, easy to test with negative cases (SR-005 AC-2/AC-4), easy to audit (SR-023), no divergent per-feature checks.
- Per-source `ConsentGrant` model is the exact data shape SR-036 prescribes; the union query makes the three decline cases (A/B/C) fall out naturally and correctly.
- Immediate revocation is guaranteed because authorization reads live consent state on each request (SR-008 AC-4).
- Modules inherit enforcement automatically because they call platform services (ADR-0005).

### Negative

- Every request incurs an authorization query; mitigated by indexing `ConsentGrant(patient_id, doctor_id, active)` and caching user-type/group membership per session (must invalidate on changes, e.g., deactivation SR-034).
- Centralization makes `AuthorizationService` a critical, high-blast-radius component — justifying its own thorough unit/integration test suite (NFR-006).

### Neutral

- **Care-relationship modeling — resolved (no explicit care-team entity).** Doctor access to clinical data is governed **solely** by (a) manual patient-granted consent (SR-008) and (b) confirmed-appointment-derived grants (SR-036). The "care relationship OR granted access" wording of SR-006 is satisfied entirely by these `ConsentGrant` sources; no standalone "care team"/care-relationship entity is introduced now or required for the MVP. This was previously an open assumption and is now a confirmed decision.

## Alternatives Considered

**Single boolean `has_access(doctor, patient)` flag.** Rejected explicitly by SR-036 AC-4 control measure: a blanket flag cannot represent multiple grant sources and would incorrectly strip legitimate access when one appointment is declined.

**Per-feature ad-hoc checks.** Rejected: error-prone, hard to audit, the leading cause of broken access control (SR-005 rationale, OWASP).

**Attribute-based access control (ABAC) policy engine (e.g., OPA).** Powerful but over-engineered for four roles + consent at MVP scale; adds an external decision service contrary to ADR-0001's single-process choke point. Revisit if policy complexity grows.

## References

- Requirements: SR-004, SR-005, SR-006, SR-007, SR-008, SR-009, SR-011, SR-015, SR-023, SR-035, SR-036; NFR-004, NFR-007
- Related: ADR-0001, ADR-0005, ADR-0011, ADR-0012
