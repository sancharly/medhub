# TASK-110 — Integration tests for the seven runtime flows

- **Phase:** 9 — Integration, system testing, compliance hardening
- **Software item / unit:** (cross-item integration) — exercises SI-AUTH, SI-AUTHZ, SI-APPT, SI-CLINICAL, SI-ATTACH, SI-IDENTITY, SI-MODHOST, SI-MOD-DICOM-BE, SI-AUDIT through SI-API
- **Implements:** the seven runtime flows of [06-runtime-views.md](../../design/06-runtime-views.md) (§6.1–6.7) and the §12.3 item-dependency rules; SR-002, SR-005, SR-006, SR-008, SR-029, SR-030, SR-035, SR-036, SR-015, SR-016, SR-017, SR-023, SR-024, SR-033, SR-034
- **Depends on:** the per-flow backend tasks must be merged first — TASK-060 (auth/session endpoints), TASK-024 (lockout), TASK-027/028 (authorization + consent), TASK-064 (consent endpoints), TASK-065 (appointment endpoints), TASK-049/050 (confirm→grant / decline→revoke + notify), TASK-066 (clinical + attachment endpoints), TASK-072/073 (router mount + DICOM backend), TASK-061/062 (account + lifecycle/retrieval endpoints), TASK-035/036 (erasure + retention worker), TASK-014 (AuditService)
- **Branch:** `enabler-story/integration-tests-runtime-flows`
- **Status:** Not started

## Objective

Author backend **integration tests** that drive each of the seven critical runtime scenarios in §06 end-to-end across the real item boundaries (HTTP → DI-wired services → repositories → Postgres/Redis/object-store test doubles), verifying that the item **interfaces** in [12-interfaces.md](../../design/12-interfaces.md) behave as specified when composed. Unlike the per-unit tests written in earlier tasks, these tests assert cross-item behavior: deny-by-default propagation, the consent **union**, per-source revoke scoping, the module guard + consent ordering, session-kill propagation, and audit side effects. They are the integration-level evidence that the architecture's runtime views are correctly realized; they do **not** replace the per-SR system tests in TASK-111.

## Interfaces to honor

Tests exercise the real interfaces; they must assert the contracts, not re-implement them:

- `AuthorizationService.authorize(actor, action, resource)` raises on deny; `effective_access(doctor_id, patient_id)` is the **union of active grants** (§12.1, SR-036.3).
- `ConsentService.grant/revoke/list_grants` — per-source `ConsentGrant` rows (`MANUAL`, `APPOINTMENT:{id}`) (SR-008, SR-036).
- `SessionService.create_session/resolve/invalidate/invalidate_all` (SR-030, SR-034).
- `AppointmentService.create/confirm/decline/list_for` (SR-010, SR-035).
- `RouterRegistry` mounts module routers under `/api/v1/modules/{key}`; `PlatformServices` is the **only** PHI path for the DICOM module; `ModuleAccessGuard.is_module_enabled` runs **before** `AuthorizationService` on module byte requests (§6.4, SR-016.3, SR-015).
- `AuditService.record(...)` append-only side effect on every security-relevant action (SR-023).

Tests must **not**: stub `AuthorizationService` or `ConsentService` (the point is to verify them composed); call repositories to fabricate consent state that bypasses the service layer; assert on implementation internals rather than observable HTTP/interface outcomes.

## Implementation detail

- Files to create under `backend/tests/integration/`:
  - `conftest.py` — async `httpx.AsyncClient` against the ASGI app, real DI graph; ephemeral Postgres (migrations applied), Redis, and an in-memory/MinIO test object store; fixtures for seeded accounts per user type (patient, doctor, admin, sysadmin) and an audit-capture helper that reads back recorded events.
  - `test_flow_login_lockout_session.py` — **§6.1 / SR-002, SR-029, SR-030:** valid login sets the hardened session cookie and audits success; invalid credentials and a non-existent username both return the **identical generic 401** (no enumeration, SR-002.2/SR-029.6); **5** consecutive failures lock the account for **30 min** (surfaced as generic 401, audited, SR-029); the 3-session concurrency cap is enforced (SR-030); `POST /auth/logout` invalidates the session immediately (SR-030.5).
  - `test_flow_doctor_access_consent_union.py` — **§6.2 / SR-005, SR-006, SR-036:** with **no** active grant the doctor's `GET /patients/{id}/clinical-entries` is **403** with no data and an audited attempt (SR-005.2/4, SR-023.2); with a `MANUAL` grant it returns entries and audits the access basis; with a `MANUAL` grant **and** a confirmed-appointment grant the doctor still has access (union) — assert `effective_access` is the union.
  - `test_flow_appointment_confirm_decline.py` — **§6.3 / SR-010, SR-035, SR-036:** `POST /appointments` (doctor) creates PENDING and enqueues notification (assert the `Notification` was dispatched, §8.12); **only the patient** can confirm/decline (SR-035.9); confirm creates the `APPOINTMENT:{id}` grant and the doctor gains access (SR-036.1/2); decline deactivates **only that** grant — verify **Case A** (no prior access → returns to no access), **Case B** (pre-existing manual grant untouched), **Case C** (declining a never-confirmed appointment is a no-op) (SR-036.4); every confirm/decline + grant change is audited (SR-035.10, SR-036.6).
  - `test_flow_consent_revoke_immediate.py` — **§6.6 / SR-008:** patient grants then `DELETE /consents/{id}`; the doctor's **immediately subsequent** request is denied because authorization reads live consent each request (SR-008.4); revoke is audited (SR-008.5).
  - `test_flow_dicom_authz_view.py` — **§6.4 / SR-015, SR-016, SR-017:** `GET /api/v1/modules/dicom-viewer/studies/{attachmentId}` returns bytes only when the module is enabled for one of the caller's groups **and** an active consent grant exists; not-enabled → **403** (guard) and not-authorized → **403** (consent), both audited; assert the module reaches the object only via `AttachmentService`/`PlatformServices` (SR-016.3), and that the guard runs before authorization (§6.4 ordering).
  - `test_flow_account_delete_anonymize_retrieve.py` — **§6.7 / SR-024, SR-034, ADR-0013:** sysadmin `DELETE /accounts/{id}` after the confirm step anonymizes into the retained dataset, releases the email for reuse (SR-034.7), and audits with the dataset id **but never the code**; `POST /anonymized-data/retrieve` with the correct code returns the dataset and is audited; a wrong code → generic denial; assert the 5-year retention deadline is set and the `U-WK-RetentionErase` job erases a past-deadline dataset (SR-024.4) — drive the worker task directly.
  - `test_flow_account_activation.py` — **§6.5 / SR-032, SR-033, SR-034:** role-constrained `POST /accounts` (admin cannot create sysadmin) creates an INACTIVE account and triggers the activation email task (SR-032); `GET /activation/{token}` validates and `POST /activation/{token}` sets a policy-compliant password (twice) → ACTIVE (SR-033); deactivate → active sessions invalidated within 30 s (assert via the session-revoke propagation, SR-034.2); reactivate → login works with existing credentials, no new email (SR-034.4).
- Libraries (exact stack): `pytest`, `pytest-asyncio`, `httpx.AsyncClient`, the FastAPI app's real DI; Postgres 16 + Redis test instances (CI services from TASK-005); object store double (MinIO or in-memory).
- Email/notification side effects are asserted via the `Notification` abstraction's `status` and a captured-task spy (§8.12) — these tests verify **dispatch**, not delivery (best-effort MVP scope).
- Time-bound assertions (30 s session kill, 30-min lockout, 5-year retention) use controllable clocks / fast-forwarded TTLs rather than real waits.
- Error cases asserted are RFC 7807 `application/problem+json` with the catalog `type` URIs (api-design.md): `/errors/unauthenticated` (401), `/errors/forbidden` (403), `/errors/validation-error` (400), `/errors/conflict` (409, duplicate email SR-032.3).

## Tests (write first — TDD, CLAUDE.md §4)

This task **is** test code; the "test-first" discipline is that each flow test is written to the runtime view and SR acceptance criteria and is expected to fail until the depended-on backend tasks are merged. Each test names, in its function name and docstring, the §06 flow and the SR acceptance criterion it verifies. Cases to cover are the per-file bullets above (happy path, deny-by-default, enumeration-resistance, per-source revoke scoping Cases A/B/C, guard-before-authz ordering, audit side effects, time-bound behaviors).

## Acceptance criteria

- [ ] All seven §06 flows have an executable integration test driving the real item interfaces end-to-end.
- [ ] Deny-by-default is verified: no active consent → 403, no data disclosed, attempt audited (§6.2, SR-005).
- [ ] The consent **union** and **per-source** revoke scoping are verified, including decline Cases A/B/C (SR-036.4).
- [ ] Manual consent revoke denies the doctor's **immediately** subsequent request (SR-008.4).
- [ ] DICOM byte access passes `ModuleAccessGuard` then `AuthorizationService`, obtains bytes only via platform services, and 403s otherwise — all audited (§6.4, SR-015/016/017).
- [ ] Login generic-error/lockout/session-cap/logout behaviors hold (§6.1, SR-002/029/030).
- [ ] Delete→anonymize→retrieve-by-code→5-year-erase and activation/lifecycle flows hold; the code never appears in DB/logs/audit (§6.5/6.7, SR-024/033/034, ADR-0013).
- [ ] Security-relevant actions in each flow produce the expected `AuditService` entries (SR-023).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Integration tests pass against real Postgres/Redis/object-store test services; coverage target met
- [ ] OpenAPI regenerated and re-linted (N/A — no contract change)
- [ ] Audit events asserted for security-relevant actions in every flow (SR-023)
- [ ] Traceability matrix rows updated (each §06 flow's SRs → TASK-110 → the named test)
- [ ] Security review N/A here (no new auth/session code; auth/session code review is TASK-113)
