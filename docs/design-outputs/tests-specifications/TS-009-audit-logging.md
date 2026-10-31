---
id: TS-009
type: test-specification
title: Audit logging verification
status: approved
version: "1.8"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-31"
links:
  - target: SR-023
    relation: verifies
  - target: SR-042
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-009 — Audit logging verification

## Scope

Software requirements covered: SR-023, SR-042 (AC 2, at the audit row).
Software items under test: SI-AUDIT.
Levels: unit, integration.

## Preconditions and environment

Build: branch `fix/review-2026-07-security`, the commit that carries TASK-192 (TC-009.12); TC-009.10 at the commit that carries TASK-189; TC-009.9 at the commit that carries TASK-137; TC-009.1 to TC-009.8 last verified at the commit that carries TASK-183. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repository). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-009.1 | SR-023 | `backend/tests/audit/test_audit_writer.py` | Every security-relevant action writes one entry with actor, action, target, outcome and timestamp | Entry asserted per action type |
| TC-009.2 | SR-023 | `backend/tests/audit/test_audit_writer.py` | Credentials and secrets never appear in an audit entry | Secret-shaped values scrubbed |
| TC-009.3 | SR-023 | `backend/tests/db/test_models.py` *(real DB)* | Audit rows persist and are not updated by the application | Insert and select asserted |
| TC-009.4 | SR-023 | `backend/tests/audit/test_failure_audit_persistence.py::test_authz_denied_persists_after_403` *(real DB)* | `AUTHZ_DENIED` (FAILURE, actor, target) is in `audit_log` after the 403, read on a separate session | Row asserted; fails if events are written back into the request transaction |
| TC-009.5 | SR-023 | `backend/tests/audit/test_failure_audit_persistence.py::test_login_failure_*` *(real DB)* | `LOGIN_FAILURE` persists after the 401 for unknown email, wrong password, inactive account and locked account; `ACCOUNT_LOCKOUT` (outcome SUCCESS) persists after the 5th wrong password | Rows asserted per branch |
| TC-009.6 | SR-023 | `backend/tests/audit/test_failure_audit_persistence.py::test_activation_failed_persists_after_401` *(real DB)* | `ACTIVATION_FAILED` persists after the 401 on a wrong token | Row asserted |
| TC-009.7 | SR-023 | `backend/modules/dicom_viewer/tests/test_failure_audit_persistence.py` *(real DB; run apart from `backend/tests`)* | `DICOM_STUDY_READ` FAILURE persists after the 403 | Row asserted |
| TC-009.8 | SR-023 | `backend/tests/audit/test_failure_audit_persistence.py::test_failure_row_persists_while_business_row_and_success_event_roll_back`, `backend/tests/audit/test_audit_writer.py` *(real DB for the first)* | A business row and a SUCCESS event added in a failing request are rolled back while its FAILURE row persists; `record` has no `durable` parameter and the repository has no session-wide commit | Business row and SUCCESS row absent, FAILURE row present |
| TC-009.9 | SR-023 AC 6, SR-042 AC 2 | `backend/tests/audit/test_audit_client_address.py` *(real DB)*, `backend/tests/audit/test_audit_writer.py::test_explicit_ip_wins_over_request_address`, `::test_request_address_used_when_ip_is_none`, `::test_no_request_context_records_no_address` | A request-caused row (`AUTHZ_DENIED`, `CONSENT_GRANTED`, `LOGIN_FAILURE`) records the originating client address (trusted peer with `X-Forwarded-For`: the client; untrusted peer with a forged header: the peer); an explicit `ip` wins; a row written with no request (worker) records no address and is written | Row `ip` asserted per case; the address tests fail if `record` ignores the client-address variable |
| TC-009.10 | SR-023 AC 7 (on a request that completes; an allowed row is lost when the request then fails, PRB-060) | `backend/tests/audit/test_authz_decision_audit.py` *(real DB)*, `backend/tests/authz/test_authorization_service.py` (`appointment_scope`, `module:access`), `backend/tests/api/test_appointments_router.py::TestGetAppointment`, the identity tests `test_denied_creation_admin_to_sysadmin_writes_one_row`, `test_denied_deactivation_by_non_sysadmin_writes_one_row`, `test_denied_self_deactivation_writes_one_row`, `test_allowed_deletion_of_own_account_writes_one_row`, `test_denied_activation_resend_writes_one_row`, and the router decisions `test_denied_unlock_writes_one_row`, `test_denied_module_list_writes_one_row`, `test_denied_consent_grant_by_doctor_writes_one_row`, `test_denied_consent_revoke_by_doctor_writes_one_row`, `test_denied_roster_by_patient_writes_one_row`, `test_allowed_consent_list_writes_one_row`; `test_allowed_row_is_lost_when_the_handler_then_fails_prb_060` documents the limitation | Every appointment, module, identity and router authorization decision, allowed or denied, on a request that completes, writes one row with actor, action (`AUTHZ_ALLOWED`/`AUTHZ_DENIED`), target (appointment id, or module key), outcome, timestamp and client address: an allowed and a denied appointment list, an allowed and a denied single read (404 to the client), an allowed and a denied module access, a denied account creation (ADMIN to SYSADMIN; target `user_type:SYSADMIN`), a denied activation resend, a denied unlock, module list, consent grant and revoke, and patient roster, a denied deactivation (non-SYSADMIN), a denied self-deactivation, an allowed deletion of one's own account | One row per decision with all fields asserted; the list tests fail if the scope is decided outside `AuthorizationService`; the identity rows carry the account id as target (`user_type:<type>` for a creation) |
| TC-009.12 | SR-023 AC 5, AC 9 | `backend/tests/audit/test_audit_no_secrets.py` (`test_secret_under_any_field_is_refused`, `test_secret_as_target_id_is_refused_for_every_target_type`, `test_secret_with_key_value_form_is_refused`, `test_target_id_without_target_type_is_refused`, `test_error_names_the_field_not_the_value`; *real DB*: `test_refused_record_writes_no_row`, `test_flow_rows_hold_no_session_token_and_logout_records_the_address`, `test_flow_scan_catches_a_configured_secret_written_into_an_audit_row`), `backend/tests/api/test_auth_router.py::TestLogoutEndpoint::test_logout_audits_the_account_not_the_session_token`, `backend/tests/audit/test_audit_writer.py::test_valid_caller_shapes_are_recorded`, `::test_action_with_embedded_credential_is_refused`, `backend/modules/dicom_viewer/tests/test_audit_module_key.py` (real `dicom-viewer` key: discovery, `sync_installed`, denied `require_module_enabled` with one AUTHZ_DENIED row *(real DB)*, MODULE_ENABLE), `backend/tests/auth/test_login_service.py::test_known_account_failure_counts_before_a_refused_audit_write`, `::test_unknown_email_failure_counts_before_a_refused_audit_write`, `backend/tests/modules/test_discovery.py::TestModuleKeyShape` | No kind of secret listed in SR-023 AC 9 (policy-compliant password, session token, activation token, anonymized-data retrieval code, base64 32-byte key, object-store access key) can be stored under `action`, `target_type`, `target_id` or `target_id` as `<uuid>:<secret>`, nor as the `target_id` of any closed target type: `AuditService.record` raises `AuditFieldError` (message names the field, not the value) and nothing is added; no row is written in a real database. The logout row carries the account id and the client address, not the session token. The rows written by a login, a second login, a password change and a logout contain no session token, CSRF token, password or any configured secret (the database password, `AT_REST_ENCRYPTION_KEY`, `SMTP_PASSWORD` when set and the object-store keys, taken from `app.core.secret_settings.SECRET_SETTINGS` so the scan and the start-up rule share one list). Every shape a current caller passes is recorded | Refusal and absence of any row asserted per kind and field; negative controls: logout reverted to `target_id=session.session_id`, and the `target_id` check removed, each fail the tests; a configured secret written into an audit row around the service is found by the flow scan |

## Acceptance criteria (class B unit level, §5.5.3)

- Self-diagnostics: an audit write failure must not silently drop the event.
- Data validation: an audit field outside its closed shape is refused before a row is built, so a secret cannot be stored under any field (TC-009.12).
- Data flow: every appointment, module, identity and router authorization decision, allowed or denied, on a request that completes, is an entry (TC-009.10; PRB-060 for the failing request); the originating client address (SR-042) is part of every request-caused entry; an entry with no request records none (TC-009.9, PRB-010).

## Notes

TC-007.6's persistence test (TS-007) now runs without `durable`: the FAILURE row is committed by the writer itself (ADR-0016).

Append-only is a convention, not a database grant (PRB-005); TC-009.3 therefore verifies persistence, not immutability. The target-id module key is checked for shape only (`^[a-z][a-z0-9_-]{0,63}$`, the one pattern in `backend/app/core/module_key.py`, also enforced by module discovery; the real key is `dicom-viewer`), not against the module registry: a lowercase identifier-shaped secret in a module-key position is not distinguishable by shape (TC-009.12 uses secrets with upper-case or punctuation characters).

## Version history

- 1.8 (2026-10-31) — QA review (TASK-197): approved (`in_review → approved`).
- 1.8 (2026-10-31) — TASK-197 (QA finding on TASK-140): the TC-009.12 flow scan checks every configured secret, not a signing key that no longer exists; a negative control writes each configured secret into an audit row. Returned to `in_review`.
- 1.7 (2026-10-31) — QA review (TASK-192 round 2): approved (`in_review → approved`).
- 1.7 (2026-10-31) — TASK-192 round 2: module-key pattern allows `-` (real key `dicom-viewer`); real-key tests and lockout-order tests added to TC-009.12. Stays `in_review`.
- 1.7 (2026-10-31) — TASK-192: TC-009.12 added (typed audit fields; no secret under any field; logout row carries the account, not the session token; flow scan for tokens, SR-023 AC 5, AC 9). Returned to `in_review`.
- 1.4 (2026-10-31) — TASK-187: TC-009.10 added (appointment and module decisions audited, SR-023 AC 7); TC-009.9 evidence citation corrected (the no-request evidence is `test_audit_writer.py::test_no_request_context_records_no_address`, not `tests/workers/test_email_tasks.py`). Returned to `in_review`.
- 1.4 (2026-10-31) — TC-009.10 narrowed to a request that completes (PRB-060); the lost-row behaviour is pinned by a test.
- 1.4 (2026-10-31) — QA review (TASK-187 round 2): approved (`in_review → approved`).
- 1.5 (2026-10-31) — TASK-188: TC-009.10 extended with the identity decisions (account creation, deactivation, self-deactivation, own-account deletion; SR-023 AC 7, same "on a request that completes" limit, PRB-060). Returned to `in_review`.
- 1.5 (2026-10-31) — QA review (TASK-188): approved (`in_review → approved`).
- 1.6 (2026-10-31) — TASK-189: TC-009.10 extended with the router decisions (unlock, module list, consent grant, roster; allowed consent list), a denied activation resend, and the `user_type:<type>` target of a creation (TASK-188 QA findings 3, 4). Returned to `in_review`.
- 1.6 (2026-10-31) — TASK-189 round 2: real-DB test for a denied consent revoke added to TC-009.10.
- 1.6 (2026-10-31) — QA review (TASK-189 round 2): approved (`in_review → approved`).
