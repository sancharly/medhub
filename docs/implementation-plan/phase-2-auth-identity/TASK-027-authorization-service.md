# TASK-027 — AuthorizationService (RBAC + ownership)

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-AUTHZ / U-AUTHZ-Policy
- **Implements:** SR-005 (deny-by-default RBAC), SR-006 (doctor↔patient scoping), SR-007 (patient
  self-access); ADR-0006
- **Depends on:** TASK-014 (AuditService), TASK-025 (API deps that invoke the guard)
- **Branch:** `feature/authorization-service`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Implement the single, central, deny-by-default decision engine invoked from every protected
endpoint (ADR-0006, §8.2). It decides `authorize(actor, action, resource)` from user type
(RBAC base layer), resource ownership/relationship, and — for doctor↔patient clinical access —
the **union of active consent grants** (`effective_access`, the consent inputs maintained by
TASK-028). It records the authorization basis / denial in the audit log. This is the
highest-blast-radius unit in the system and gets the most thorough negative-case suite (ADR-0006
"Consequences").

## Interfaces to honor

Provided interface (from [12-interfaces.md](../../design/12-interfaces.md), SI-AUTHZ
`AuthorizationService`), signatures verbatim:

```python
class AuthorizationService:
    def authorize(self, actor, action, resource) -> Decision: ...        # raises AuthorizationError on deny
    def effective_access(self, doctor_id, patient_id) -> bool: ...        # union of active grants (SR-036)
```

`actor = (account_id, role)` where `role ∈ {PATIENT, DOCTOR, ADMIN, SYSADMIN}` (SR-004, exactly
one type per account). `action` is a verb string (e.g. `clinical:read`, `clinical:write`,
`account:read`, `account:create`, `module:use`). `resource` carries the target type, owner id, and
patient id where relevant. `Decision` carries the allow plus the **basis** for audit (SR-006 AC-4).
Consumers: SI-API, SI-CLINICAL, SI-ATTACH, SI-APPT, SI-MOD-DICOM-BE, SI-MODHOST.

`effective_access` reads **live** consent on each call (immediate revocation, SR-008 AC-4) — it
delegates to the `ConsentService` union query (TASK-028); this task defines the contract and the
RBAC/ownership layers, TASK-028 supplies the grant union and TASK-029 the admin projection.

Must **not**: cache a stale access decision across requests (live read each time, SR-008 AC-4);
expose protected data on deny (raise only, SR-005 AC-4); implement consent-row logic itself (that
is `ConsentService`, ADR-0006); be bypassable — it is the only decision point (no per-feature
checks, §12.3.1).

## Implementation detail

- Files to create:
  - `backend/app/authz/service.py` — `AuthorizationService`, `Decision`, `Actor`, `Resource`,
    `Action` constants.
  - `backend/app/authz/__init__.py`.
- Decision algorithm (deny-by-default — default branch is **deny**; only explicit rules allow):
  1. **RBAC base (SR-004/005):** dispatch on `actor.role`.
  2. **PATIENT:** allow `account:read`/`clinical:read` only when `resource.owner_id ==
     actor.account_id` (self only, SR-007 AC-1/AC-2/AC-3). Deny all other patients' data.
  3. **DOCTOR:** allow `clinical:read`/`clinical:write` for a patient **iff**
     `effective_access(doctor_id=actor.account_id, patient_id=resource.patient_id)` is True
     (SR-006 AC-2/AC-3); else deny (SR-006 AC-3). The patient list a doctor can see (SR-006 AC-1)
     is the set of patients with an active grant.
  4. **ADMIN (administrative personnel):** clinical actions are **always denied** (SR-009 AC-2/AC-3);
     non-clinical reads go through the projection (TASK-029). This task denies `clinical:*` for
     ADMIN and delegates the allowed non-clinical projection to U-AUTHZ-AdminProjection.
  5. **SYSADMIN:** account-lifecycle/group/module-admin actions allowed per SR-032/034/014/015;
     **not** a backdoor to clinical PHI (SYSADMIN administers, does not read clinical records unless
     the same ownership/consent rules would apply).
  6. Anything not explicitly allowed → deny.
- Audit (SR-005 "decisions recorded", SR-006 AC-4, §8.4): on allow, record the action, target, and
  **basis** (`OWNER` | `CONSENT:MANUAL` | `CONSENT:APPOINTMENT:{id}` | `ROLE`); on deny, record
  `AUTHZ_DENIED` with actor/action/target — never the protected payload (runtime §6.2).
- Performance (ADR-0006 negatives): the consent union query is indexed on
  `ConsentGrant(patient_id, doctor_id, active)` (TASK-028/011); user-type/role comes from the
  session (cached per session, invalidated on deactivation per TASK-033).
- Error cases: deny → raise `AuthorizationError` → 403 `/errors/forbidden` (TASK-026), no data
  (SR-005 AC-4).

## Tests (write first — TDD, CLAUDE.md §4)

Negative cases are first-class (ADR-0006, SR-005 control measure "cover with negative tests").

- Unit (`backend/tests/authz/test_authorization_service.py`):
  - Default deny: an unmapped action/role raises `AuthorizationError` (SR-005 AC-2).
  - PATIENT reads own profile/clinical (allow) but another patient's (deny) (SR-007 AC-1/2/3).
  - DOCTOR with an active grant reads the patient's clinical data (allow), basis recorded;
    DOCTOR with no grant is denied, audited, no data (SR-006 AC-2/3/4, runtime §6.2).
  - DOCTOR's clinical access flips to deny the instant the grant is revoked (live read) (SR-008 AC-4).
  - ADMIN clinical action denied in every case (SR-009 AC-2/3).
  - SYSADMIN can perform account-admin actions but is not auto-granted clinical reads (SR-009 intent).
  - Allow decisions audit the basis; deny decisions audit `AUTHZ_DENIED` (SR-006 AC-4, §8.4).
- Integration (`backend/tests/authz/test_authz_with_consent.py`, after TASK-028): `effective_access`
  reflects the union of a manual + an appointment grant; declining one leaves the other (SR-036).

## Acceptance criteria

Distilled from SR-005 / SR-006 / SR-007:

- [x] Every protected decision passes through this service; default is deny (SR-005 AC-1/AC-2).
- [x] Decision accounts for user type, ownership/relationship, consent, and module enablement
      (module via `ModuleAccessGuard`, SR-005 AC-3).
- [x] Doctor sees only patients with an active grant; others denied (SR-006 AC-1/AC-3).
- [x] Patient sees only their own data; cross-patient denied (SR-007 AC-3).
- [x] Admin clinical access denied; SYSADMIN not a clinical backdoor (SR-009).
- [x] Denials return 403 with no protected data; basis/denial audited (SR-005 AC-4, SR-006 AC-4).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit (and required integration) tests pass; coverage target met (high — critical component)
- [x] OpenAPI regenerated and re-linted (N/A — internal service)
- [x] Audit events emitted for security-relevant actions (authorization basis & denials — SR-023)
- [x] Traceability matrix row updated (SR-005, SR-006, SR-007, ADR-0006 → TASK-027 → tests)
- [x] Security review completed (auth/session/authz task — SR-031.6)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
