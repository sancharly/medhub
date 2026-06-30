# TASK-029 — Admin non-clinical projection

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-AUTHZ / U-AUTHZ-AdminProjection
- **Implements:** SR-009 (administrative personnel non-clinical scope)
- **Depends on:** TASK-027 (AuthorizationService)
- **Branch:** `feature/admin-projection`
- **Status:** Completed

## Objective

Enforce least-privilege for administrative personnel (role ADMIN): they may read **only** a
limited set of non-clinical personal fields of patients and doctors (at minimum name, family
name, date of birth) and are **denied any clinical data** (clinical entries, attachments,
imaging). The projection is applied **server-side** so the limitation cannot be bypassed by the
client (SR-009, §8.2, ADR-0006).

## Interfaces to honor

Provides a server-side projection used by SI-API account/listing endpoints and invoked from the
authorization layer:

```python
def project_for_admin(account: Account) -> AdminAccountView: ...   # name, family name, DOB only
```

`AdminAccountView` exposes exactly `{first_name, family_name, date_of_birth}` (and stable
identifiers needed to operate, e.g. account id and type) — **no** clinical fields. Used by
`GET /accounts`, `GET /accounts/{id}` for the ADMIN role (api-design.md SR-009). The clinical-deny
decision itself is made by `AuthorizationService` (TASK-027 rule 4); this unit produces the
allowed non-clinical shape.

Must **not**: include any clinical field in the projection; be the *only* gate — clinical denial
is enforced in `AuthorizationService` too (defense in depth, SR-031.5); be applied to non-admin
roles (doctors/patients use their own authorized views).

## Implementation detail

- Files to create:
  - `backend/app/authz/admin_projection.py` — `project_for_admin`, `AdminAccountView`.
- The projection is a whitelist (allow-list) of fields, never a blacklist, so new clinical fields
  added later are excluded by default (SR-009 AC-1: "at least" name/family-name/DOB — the minimum
  set; extend only via explicit non-clinical additions).
- Wiring: account read/list endpoints (TASK-061/067/095) call `project_for_admin` when
  `actor.role == ADMIN`; doctors/patients/sysadmin get their role-appropriate view. Any
  clinical-data endpoint (clinical entries, attachments, DICOM) is denied for ADMIN by
  `AuthorizationService` (TASK-027) before a handler runs (SR-009 AC-2/AC-3).
- Audit: ADMIN access to the non-clinical projection is a normal authorized read (audited by the
  authorization layer with basis `ROLE`); attempted clinical access is audited as `AUTHZ_DENIED`
  (TASK-027).
- Error cases: an ADMIN request to a clinical endpoint → 403 `/errors/forbidden`, no data
  (SR-009 AC-3, TASK-026).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/authz/test_admin_projection.py`):
  - `project_for_admin` returns exactly name, family name, DOB (+ id/type) and **no** clinical or
    extra PII fields; adding a clinical field to `Account` does not leak (whitelist) (SR-009 AC-1).
  - The projection is identical for patient and doctor targets (both visible to admin) (SR-009 AC-1).
- Integration (`backend/tests/authz/test_admin_clinical_denied.py`, with TASK-027):
  - ADMIN listing accounts gets the projection only (SR-009 AC-1).
  - ADMIN requesting a clinical entry / attachment / DICOM bytes → 403, no data, audited
    (SR-009 AC-2/AC-3).

## Acceptance criteria

Distilled from SR-009:

- [ ] Admin can view at least name, family name, DOB of patients and doctors (AC-1).
- [ ] Admin cannot retrieve clinical entries, attachments, or any clinical data (AC-2).
- [ ] Every admin request for clinical data is denied server-side by the authorization mechanism (AC-3).
- [ ] The projection is a server-side whitelist; new fields excluded by default.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (admin account views reflect the projected schema)
- [ ] Audit events emitted for security-relevant actions (admin reads + clinical denials via TASK-027)
- [ ] Traceability matrix row updated (SR-009 → TASK-029 → tests)
- [ ] Security review completed (auth/session/authz task — SR-031.6)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-029a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
