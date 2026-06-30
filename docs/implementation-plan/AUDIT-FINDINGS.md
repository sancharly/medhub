# MedHub — Audit Findings (Performance / Security / Simplicity)

Branch: `enabler/audit-and-design-review`. Companion to `AUDIT-LEDGER.md`.

These are improvement proposals surfaced during the phase 0–7 audit. **None are fixed in this branch**
unless they were a basic-functionality showstopper (those are in the `FIX:` commits / new TASK files).
Items tagged **→ TASK-…** were promoted to a tracked remediation task because they are functional or
security defects; the rest are recorded here for prioritisation.

## Security

| Sev  | Location                                                       | Finding                                                                                                                | Recommendation                                                           |
|------|----------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| High | `app/auth/csrf.py`, all mutating routers                       | CSRF enforced on only 3 of ~8 routers; `CsrfError`→401 not 403                                                         | **→ TASK-069a** central CSRF middleware + 403 mapping                    |
| High | `app/auth/login.py`, `app/api/routers/auth.py`                 | Lockout service never wired into login                                                                                 | **→ TASK-024a**                                                          |
| High | `app/identity/erasure.py`                                      | Anonymized-retrieval code never emailed; deadline not enforced on retrieve                                             | **→ TASK-035a**                                                          |
| High | `app/api/routers/accounts.py`, `app/authz/admin_projection.py` | `project_for_admin` unused → ADMIN/DOCTOR get full account PII from `/accounts`                                        | **→ TASK-029a**                                                          |
| Med  | `app/db/crypto.py`                                             | No key-id/version in ciphertext envelope → key rotation silently breaks old rows; no PHI column uses `EncryptedString` | Add version prefix; decide field-level PHI scope (defense-in-depth)      |
| Med  | `app/audit/service.py`                                         | Credential scrub is regex/pattern-limited; append-only enforced by convention, not DB                                  | Document caller contract; consider `REVOKE UPDATE/DELETE` on `audit_log` |
| Med  | `modules/dicom_viewer/.../dicom.py`                            | `pydicom.dcmread(...).pixel_array` on the `?frame=` path has no size/decompression-bomb guard                          | Bound object size + decode                                               |
| Med  | `backend/Dockerfile`, `infra/docker-compose.yml`               | Runtime image runs as root; compose defaults `changeme`/`minioadmin` allow insecure boot                               | Add non-root `USER`; make secrets required (no `:-default`)              |
| Low  | `app/modules/discovery.py`                                     | `_SEMVER_RE` accepts trailing garbage (`1.2.3-evil!`)                                                                  | Anchor full semver                                                       |
| Low  | `app/api/routers/anonymized_data.py`                           | Rate-limit keyed on `request.client.host` (proxy IP)                                                                   | Trust `X-Forwarded-For` from the proxy only                              |
| Low  | `app/modules/.../test_module_boundary.py`                      | Boundary test denies only 2 import substrings                                                                          | Deny all `app.*` except the contract/deps/errors/audit                   |
| Low  | `frontend/.../ConfirmDialog.tsx:51`                            | `autoFocus` on Confirm even when `destructive` (Cancel should be safe default)                                         | Move `autoFocus` to Cancel when destructive                              |

## Performance

| Location                                    | Finding                                                                                                                                      | Recommendation                                |
|---------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| `app/db/alembic/versions/0001_initial.py`   | No index on `appointment.scheduled_at`, `consent_grant.appointment_id`, `clinical_entry.patient_id`, `attachment.patient_id` (authz lookups) | Add indexes (migration)                       |
| `app/identity/activation.py`                | Token validate/activate do a full `repo.list()` scan (O(n))                                                                                  | Indexed lookup by `activation_token_hash`     |
| `app/auth/session.py:97`                    | Concurrency-cap eviction is a non-atomic multi-op sequence                                                                                   | Lua/pipeline transaction                      |
| `app/groups/service.py:132`                 | `groups_of` issues N+1 `get()` per membership                                                                                                | Single `IN` query                             |
| `app/attachments/service.py`, dicom backend | Whole object buffered into memory                                                                                                            | Stream chunks for large DICOM (SR-026 budget) |
| `frontend/.../useIdleTimer.ts:66`           | `mousemove`/`scroll` reset timers on every event                                                                                             | Debounce                                      |

## Simplicity / hygiene

| Location                                              | Finding                                                                                                   |
|-------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| `app/db/repositories/appointment_repo.py:29`          | `list_for_actor` embeds role-based authz in the persistence layer (boundary leak) → move to service/authz |
| `app/identity/account_service.py`, `lifecycle.py`     | Bypass `AuthorizationService` with direct role compares (violates single-decision-point, ADR-0006)        |
| `modules/dicom_viewer/.../dicom.py:9`                 | `SUPPORTED_MODALITIES` is dead code (never read)                                                          |
| `app/export_openapi.py` + `scripts/export_openapi.py` | Two export scripts; consolidate to the one CLAUDE.md references                                           |
| `app/core/logging.py`                                 | JSON formatter drops the promised `request-id` field                                                      |
| `.pre-commit-config.yaml`                             | Both `ruff-format` and `black` run on backend (double-format churn)                                       |
| `frontend/.../LoginPage.tsx:56`                       | Dead inline `evictedSession` Alert (unreachable after navigate)                                           |
| `frontend/.../ForcedPasswordGate.tsx:14`              | Casts `me` to `Record<string,unknown>` to read a non-existent field — the type-smell that hid the bug     |
| `app/modules/registry_service.py:23`                  | `sync_installed(..., db)` takes an unused `db` param                                                      |

## Cross-cutting test-quality gap (the audit's central lesson)

Multiple "Completed" tasks shipped real runtime defects while their unit tests stayed green, because
the tests mock the *assumed* contract instead of the *actual* one: lowercase `UserType` enums, the
`csrftoken` cookie name, the `accountType` login field, a `mustChangePassword` field on `/me`, a 404
for invalid activation tokens, and CSRF tokens that the route silently ignores. **Recommendation:** add
a CI contract-conformance check that validates MSW mock shapes against the generated `openapi.ts`, and
prefer integration tests over mock-shape assertions for security-relevant flows (CSRF, lockout,
consent, erasure). Tracked as a note on TASK-080 / TASK-111.
