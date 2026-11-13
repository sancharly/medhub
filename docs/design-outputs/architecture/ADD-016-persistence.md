---
id: ADD-016
type: architecture-doc
title: Persistence (SI-PERSIST)
status: in_review
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-13"
links:
  - target: SR-026
    relation: implements
  - target: SR-003
    relation: implements
  - target: SR-004
    relation: implements
  - target: SR-021
    relation: implements
  - target: SR-022
    relation: implements
  - target: SR-031
    relation: implements
  - target: RISK-002
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: RISK-011
    relation: relates_to
  - target: SOUP-006
    relation: relates_to
  - target: SOUP-008
    relation: relates_to
  - target: SOUP-009
    relation: relates_to
  - target: SOUP-010
    relation: relates_to
  - target: SOUP-011
    relation: relates_to
  - target: SOUP-020
    relation: relates_to
  - target: SR-023
    relation: implements
  - target: RISK-006
    relation: relates_to
tags:
  - software-item:SI-PERSIST
  - class:B
  - layer:backend
---

# ADD-016 — Persistence (SI-PERSIST)

## Responsibility

SQLAlchemy models, repositories, Alembic migrations, encryption-at-rest config

## Software units (IEC 62304 §5.4.1)

- `U-PER-Models` — SQLAlchemy ORM models (FHIR-aligned, SR-021).
- `U-PER-Repos` — repositories with parameterized queries (SR-031.1).
  **CR-006 (TASK-227, ADR-0023):** the request transaction ends before the response is sent. `get_db`
  keeps its body (commit on return, rollback on exception, close) and is declared only through the
  alias `DbSession = Annotated[Session, Depends(get_db, scope="function")]`, so FastAPI tears it down
  when the endpoint has returned and the response is serialised, before it is sent. A commit failure is
  a 5xx problem response, never the prepared success status (SR-012 AC 5, SR-023 AC 10). A test walks
  the dependants of every route and fails on any `get_db` with another scope or on a route that
  resolves two `get_db` cache keys (two sessions). `AuditRepository.add_independent` binds its own
  session to the bind of the request session, which is available after the close (ADR-0016).
- `U-PER-Crypto` — field encryption (`EncryptedString`): AES-256-GCM envelope
  `mh1:<key-id>:<base64url(nonce || ciphertext)>` with the prefix as associated data. A keyring
  holds the current key (`AT_REST_ENCRYPTION_KEY`, id `AT_REST_ENCRYPTION_KEY_ID`) and optional
  retired keys (`AT_REST_ENCRYPTION_RETIRED_KEYS`, decryption only). `decrypt` uses the key named
  in the prefix only; no prefix, an unknown id or a failed tag raises, with no fallback.
  `decrypt_legacy` reads the pre-0010 unprefixed format with a given key and exists for
  migration 0010. The re-encryption command `app.db.reencrypt` (`--check`, `--apply`,
  `--verify-key-ids`) covers every `EncryptedString` column and runs as the owner from the
  `db-migrate` image (SR-022 AC 6 to AC 8,
  [ADR-0018](../../design/adr/0018-field-encryption-key-identifier-and-key-separation.md)).
- `U-PER-Migrations` — Alembic migrations (NFR-006). Migration 0009 drops the `audit_log` rules of
  0006; migration 0010 converts existing encrypted values to the identified envelope in one
  transaction (SR-022 AC 7). Migrations run only in the `db-migrate` service, as the owner role.
- `U-PER-Roles` — `app.db.roles`: creates the runtime role and applies its grants after every
  migration run, revoking `UPDATE`, `DELETE`, `TRUNCATE` on `audit_log` (SR-023 AC 8,
  [ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md)); refuses an
  existing runtime role that is a superuser, a member of another role or an owner of objects.
- **CR-006 (planned).** `U-PER-Migrations` (TASK-219): migration 0011 adds indexes on
  `appointment.scheduled_at`, `consent_grant.appointment_id`, `clinical_entry.patient_id` and
  `attachment.patient_id`, so the authorization lookups do not scan (SR-026 AC 6); it locks writes on
  the four tables while building. `U-PER-Repos` (TASK-220): `groups_for_account` returns a user's
  groups in one joined query. Engine (TASK-136, ADR-0022): `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`,
  `DB_POOL_TIMEOUT` settings, sized with the API thread pool (SR-026 AC 5; values approved by the
  human, D-14).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-003, SR-004, SR-021, SR-022, SR-031; CR-004 adds SR-023 (AC 8); CR-006 adds SR-026 (AC 5, AC 6).
Non-functional requirements constraining this item: —.

## Interfaces

Provided and consumed interfaces are specified in
[12-interfaces.md](../../design/12-interfaces.md); the runtime interactions this item takes part in
are in [06-runtime-views.md](../../design/06-runtime-views.md) and the sequence diagrams under
[`../../specifications/`](../../specifications/).

## Architecture narrative

This record is a summary and traceability anchor, not the narrative. The design itself is in the
arc42 sections — [05 building blocks](../../design/05-building-blocks.md) for the decomposition,
[04 solution strategy](../../design/04-solution-strategy.md),
[08 cross-cutting concepts](../../design/08-cross-cutting-concepts.md) and, for deployment,
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0004](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0007](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0010](../../design/adr/), [ADR-0011](../../design/adr/), [ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md), [ADR-0018](../../design/adr/0018-field-encryption-key-identifier-and-key-separation.md).

## Risk relevance

Participates in RISK-002, RISK-007, RISK-011 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): unit changes for the planned design added (marked "CR-004"), links added. Content change, so the approval record is cleared and the record returns to review. The implementing tasks confirm the unit text when they land.
- 1.2 (2026-11-08) — TASK-201 (CR-004): unit text replaced with the unit as built; `U-PER-Crypto` names the keyring, `decrypt_legacy` and `app.db.reencrypt`; `U-PER-Roles` notes the unsafe-role refusal. Arc42 sections 05, 06 and 08 hold the narrative. Content change, so the 1.1 approval record is cleared and the record returns to review.
- 1.3 (2026-11-13) — CR-006 Plan stage (Software Architect role): migration 0011 indexes, the joined group lookup and the pool settings (ADR-0022) marked "CR-006 (planned)"; `implements` SR-026 added. Content change, so the 1.2 approval record is cleared and the record returns to review.
- 1.4 (2026-11-13) — TASK-227 (CR-006, ADR-0023): `U-PER-Repos` states that the request transaction ends before the response (`DbSession`, scope `function`). Content change, so the 1.3 approval record is cleared and the record returns to review.
