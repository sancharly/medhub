# TASK-029a — Wire admin non-clinical projection into account endpoints (remediation)

- **Phase:** 2 — Auth & identity
- **Implements / restores:** SR-009; remediates TASK-029
- **Depends on:** TASK-029, TASK-061 (account endpoints)
- **Branch:** `feature/admin-projection-wiring`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-029 verdict **PARTIAL** (PII over-exposure)

## Objective

`project_for_admin` is implemented and unit-tested but **never called by any router**.
`GET /accounts` and `GET /accounts/{id}` return the full `AccountResponse` for all roles, so an ADMIN
(and a DOCTOR, who is allowed `account:list`) receives every account's full profile. Apply the
non-clinical whitelist server-side where it matters.

## Implementation detail

- In `app/api/routers/accounts.py`, call `project_for_admin(account)` (or restrict the response schema)
  when the actor is ADMIN, returning only the permitted fields (name/family/DOB whitelist per SR-009).
- Re-evaluate whether DOCTOR should hold `account:list` at all (`app/authz/service.py`) — likely scope
  it down so doctors don't receive a full account roster.

## Acceptance criteria

- [x] An ADMIN listing/reading accounts receives only the SR-009 whitelist fields, server-enforced.
- [x] No role receives clinical fields via account endpoints.
- [x] DOCTOR does not receive a full PII account roster (scope reviewed; DOCTOR has `account:read` own only, not `account:list`).

## Definition of Done

- [x] Lint + type-check pass
- [x] Tests assert the projected shape per role (admin vs sysadmin vs doctor)
- [x] OpenAPI regenerated if the admin response schema changes
- [x] Traceability row updated (SR-009 → TASK-029a → tests)
- [x] Security review completed
