# ADR-0004: PostgreSQL as the primary relational database

## Status

Accepted

## Context

The domain is highly relational and consistency-critical: accounts, user types, groups, group-module enablement, appointments and their confirmation states, clinical entries, attachments metadata, and — crucially — **consent grants tracked per source** (SR-036 requires grants keyed by appointment ID or "manual", evaluated as a union; these grants are the sole basis of doctor access, with no separate care-relationship entity per ADR-0006). Authorization decisions (SR-005) and immediate revocation (SR-008) demand strong transactional consistency. An append-only audit log (SR-023) and erasure/anonymization (SR-024, SR-034) must be supported. Data at rest must be encrypted (SR-022).

## Decision

Use **PostgreSQL 16** as the single primary database for all structured domain data, including the audit log. Use foreign keys, unique constraints (e.g., unique email across active/inactive/deleted accounts, SR-032 AC-3), CHECK constraints (user type enum, SR-004), and transactions for multi-entity consent operations (SR-036). Enable encryption at rest at the volume/storage layer and use `pgcrypto` only where field-level encryption is warranted. Use Alembic migrations under version control (NFR-006).

Large binary files (DICOM, reports) are **not** stored in PostgreSQL; only their metadata and storage references are (see ADR-0009).

## Consequences

### Positive

- ACID transactions make immediate, atomic consent changes correct (SR-008, SR-036) — a per-source grant table with a transactional union query directly implements SR-036's "track grants by source" control.
- Declarative integrity (FK, UNIQUE, CHECK) enforces invariants the requirements demand: one user type per account (SR-004), unique email (SR-003/SR-032), valid appointment references (SR-010).
- Parameterized access via SQLAlchemy ORM satisfies the SQL-injection control (SR-031 AC-1).
- Mature, auditable, open-source; strong backup/PITR story for medical-record durability (UN-008).
- JSONB columns allow storing FHIR-aligned extension fields without schema churn (SR-021).

### Negative

- Vertical-scaling ceiling; mitigated for the MVP by read patterns being modest and by deferring heavy assets to object storage. Read replicas can be added later.
- Requires migration discipline (Alembic) and DBA care for indexing to meet performance budgets (SR-026).

### Neutral

- One database engine to operate and secure — consistent with the single-audit-trail philosophy of ADR-0001.

## Alternatives Considered

**MySQL/MariaDB.** Comparable ACID story. Rejected: weaker JSONB and constraint ergonomics, and PostgreSQL's `pgcrypto`/partial-index/exclusion-constraint features fit the consent and audit modeling better.

**MongoDB (document).** Rejected: the consent-union and relational-integrity requirements (SR-036, SR-004, SR-010) want relational constraints and multi-document transactions that a document store handles less naturally; weaker fit for auditable, constraint-enforced medical data.

**A dedicated FHIR server datastore (e.g., HAPI's).** Rejected for the MVP; see ADR-0007 — we align the model with FHIR but do not adopt a full FHIR server.

## References

- Requirements: SR-003, SR-004, SR-008, SR-010, SR-021, SR-022, SR-023, SR-024, SR-031, SR-032, SR-034, SR-036; NFR-006, NFR-008
- Related: ADR-0009 (object storage), ADR-0007 (FHIR)
