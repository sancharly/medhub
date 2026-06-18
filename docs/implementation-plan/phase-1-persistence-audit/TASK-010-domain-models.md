# TASK-010 — SQLAlchemy domain models (FHIR-aligned)

- **Phase:** 1 — Persistence & audit
- **Software item / unit:** SI-PERSIST / U-PER-Models
- **Implements:** SR-021, SR-003, SR-004
- **Depends on:** TASK-002 (must be merged first)
- **Branch:** `feature/persist-domain-models`
- **Status:** Not started

## Objective

Define the SQLAlchemy 2.x ORM models for MedHub's core domain, aligned field-by-field with FHIR R4 per [fhir-mapping.md](../../specifications/fhir-mapping.md) and the domain-model diagram ([diagram-domain-model.puml](../../specifications/diagram-domain-model.puml)), so the relational schema (PostgreSQL 16) supports unique-email accounts (SR-003), single-valued user types (SR-004), and a future FHIR export/import adapter without redesign (SR-021). This task defines models only; migrations (TASK-011), repositories (TASK-012), and crypto (TASK-013) build on it.

## Interfaces to honor

- Produces the ORM model layer that `SI-PERSIST` repositories (TASK-012) expose to all data items. Per interface rule 12.3.3, **only SI-PERSIST talks to PostgreSQL**; models are not imported by modules directly.
- Field names and types must match the FHIR mapping table (camelCase DTOs are an API-layer concern; ORM columns use snake_case Python attributes that map cleanly to the documented FHIR paths).
- Must **not** add repository query logic, Alembic migrations, business rules, or authorization here — those are later units. Enumerations are constrained at the model layer; DB-level CHECK/UNIQUE/FK constraints are emitted by the migration (TASK-011) and must be consistent with these models.

## Implementation detail

- Files to create under `backend/app/db/models/`:
  - `base.py` — declarative `Base` (SQLAlchemy 2.x `DeclarativeBase`), shared mixins: `UUID` primary keys (server/`uuid4` default), `created_at` timestamp. JSONB helper for FHIR extension columns.
  - `account.py` — **Account**: `id`, `email` (unique across all states), `password_hash` (Argon2id; populated by auth/identity tasks), `user_type` (Enum `DOCTOR|PATIENT|ADMIN|SYSADMIN`, **NOT NULL** — SR-004), `status` (Enum `INACTIVE|ACTIVE|DEACTIVATED|DELETED`), `first_name`, `surname`, `date_of_birth`, `password_changed_at`, `created_at`, `fhir_extensions` (JSONB). FHIR: Patient/Practitioner per mapping.
  - `group.py` — **Group** (`id`, `name`, `auto_user_type` nullable enum) and **GroupMembership** (`group_id`, `account_id`, `source` Enum `AUTO|MANUAL`).
  - `module.py` — **ModuleRegistry** (`id`, `module_key`, `name`, `version`) and **GroupModuleEnablement** (`group_id`, `module_id`, `enabled`).
  - `appointment.py` — **Appointment**: `id`, `doctor_id` (FK Account), `patient_id` (FK Account), `scheduled_at`, `state` (Enum `PENDING|CONFIRMED|DECLINED`), `created_at`. FHIR Appointment.
  - `clinical.py` — **ClinicalEntry**: `id`, `patient_id`, `author_doctor_id`, `occurred_at`, `description` (text), `created_at`. FHIR Composition/DocumentReference.
  - `attachment.py` — **Attachment**: `id`, `clinical_entry_id` (FK), `patient_id` (FK), `filename`, `content_type`, `size`, `storage_key` (object-store ref), `checksum`. FHIR DocumentReference/Binary.
  - `consent.py` — **ConsentGrant**: `id`, `patient_id`, `doctor_id`, `source` (`MANUAL` or `APPOINTMENT:{appointment_id}` — model as `source_type` enum + nullable `appointment_id`), `active`, `created_at`, `revoked_at`. FHIR Consent.
  - `audit.py` — **AuditLog**: `id`, `actor_id` (nullable), `action`, `target_type`, `target_id`, `outcome` (Enum `SUCCESS|FAILURE`), `ip`, `timestamp`. Append-only semantics enforced by the writer (TASK-014) and migration constraints (TASK-011); model exposes no update path.
  - `anonymized_dataset.py` — **AnonymizedDataset**: `id`, `code_hash` (salted Argon2id KDF hash of the user-held anonymization code — code itself never stored, ADR-0013), `payload` (JSONB anonymized record data), `created_at`, `retention_deadline` (created_at + 5y). Supports SR-024 retrieval/erasure flows (built later).
  - `__init__.py` — export all models and `Base` for Alembic autogenerate (TASK-011).
- Libraries (exact stack): SQLAlchemy 2.x, PostgreSQL 16 (`JSONB`, `UUID`), `fhir.resources` referenced only for mapping verification (no runtime dependency here).
- Data model: relational with JSONB extension columns for FHIR fields not promoted to first-class columns (§8.1).
- Error cases: none at model layer (constraint violations surface in TASK-011/012).

## Tests (write first — TDD, CLAUDE.md §4)

- `backend/tests/db/test_models.py` (against an ephemeral PostgreSQL, e.g. testcontainers or CI `postgres:16`):
  - Every model maps and a row can be inserted/selected for each entity (mapping smoke).
  - **SR-004.1/2**: an Account cannot be created without `user_type`; `user_type` accepts only the four enum values.
  - **SR-003.1**: two Accounts with the same `email` cannot coexist (relies on the unique constraint; full enforcement asserted in TASK-011, referenced here).
  - Enum columns reject out-of-set values (`status`, `state`, `outcome`, membership `source`).
  - AnonymizedDataset stores only `code_hash` (no plaintext code field exists — ADR-0013).
- `backend/tests/db/test_fhir_mapping.py`: assert each model field listed in fhir-mapping.md exists on the model (guards SR-021.2 documented mapping ↔ schema sync).

## Acceptance criteria

Distilled from SR-021, SR-003, SR-004:

- [ ] Account, Practitioner/Patient distinction (via `user_type`), Appointment, ClinicalEntry, Attachment, ConsentGrant map to their FHIR R4 resources per fhir-mapping.md (SR-021.1).
- [ ] Every model field in the FHIR mapping table is present on the ORM model; mapping doc and schema are in sync (SR-021.2).
- [ ] Each Account has exactly one `user_type` from {DOCTOR, PATIENT, ADMIN, SYSADMIN}; `user_type` is NOT NULL (SR-004.1/2).
- [ ] `user_type` is exposed for access-control reads (available on the model for SR-004.4 consumers).
- [ ] `email` is modeled unique across all account states (SR-003.1; DB constraint in TASK-011).
- [ ] AuditLog has no update path; AnonymizedDataset stores only a salted code hash (ADR-0013).
- [ ] FHIR extension data uses JSONB columns (§8.1).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (N/A — no API surface)
- [ ] Audit events emitted for security-relevant actions (N/A — model layer)
- [ ] Traceability matrix row updated (SR-021, SR-003, SR-004 → TASK-010 → model/fhir tests)
- [ ] FHIR mapping reviewed against R4 definitions and review recorded (SR-021.3)
- [ ] Security review completed (N/A — no auth/session code)
