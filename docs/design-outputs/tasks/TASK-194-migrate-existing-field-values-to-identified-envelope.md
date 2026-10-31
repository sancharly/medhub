---
id: "TASK-194"
type: task
title: "Migrate existing encrypted field values to the identified envelope"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-022"
    relation: implements
  - target: "RISK-011"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "PRB-004"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-193"
    relation: relates_to
  - target: "TASK-191"
    relation: relates_to
  - target: "ADD-016"
    relation: relates_to
tags: ["security", "encryption", "data-migration", "cr:CR-004", "control:protective", "ask-first"]
---

# TASK-194 — Migrate existing encrypted field values to the identified envelope

- **Software item / unit:** SI-PERSIST `U-PER-Migrations` (ADD-016).
- **PRB:** PRB-004. **CR:** CR-004.
- **Depends on:** TASK-193 (envelope), TASK-191 (`db-migrate` runs migrations with the key
  settings), TASK-190 (migration 0009 precedes 0010).
- **Branch:** `fix/review-2026-07-security`. **Its own commit, nothing else in it** (isolated
  risky change).
- **Size:** S (migration `0010_field_encryption_key_id.py`; 1 test file; TS-008)
- **Needs:** a Docker daemon (testcontainers PostgreSQL); a copy of a populated development
  database for the rehearsal.
- **Boundary (CR-004 "Ask first"):** this can make stored values unreadable. It runs only against
  test databases and the rehearsal copy until the human approves the rehearsal result.

## Objective

SR-022 AC 7: introducing the key identifier leaves no existing value unreadable; a test against a
database populated in the earlier format shows it.

## Implementation detail

- Migration 0010 (`upgrade`): in one transaction, select `id, description` from `clinical_entry`
  where `description` does not start with `mh1:`; decrypt each with the current key through
  `decrypt_legacy`; re-encrypt with `encrypt`; update by id; log only the count. Any decryption
  failure raises and the whole migration rolls back, naming the row id (not the content).
  Batches of 500 within the same transaction.
- `downgrade`: re-encrypt `mh1:` values that name the current key back to the legacy format
  (so a rollback of the release is possible); refuse if any value names a retired key.
- The migration reads keys through the same settings as the application.

## Tests (write first)

`backend/tests/db/test_migration_0010_key_id.py` (real database, Alembic to 0009, rows written
with the **legacy** encryption code path, i.e. the pre-TASK-193 format, using a fixed key):

- upgrade to 0010 → every row reads back through `EncryptedString` with the original plaintext,
  every stored value starts with `mh1:<current id>:`;
- one row encrypted under a different key → upgrade fails, and every row is still in the legacy
  format (rollback);
- upgrade on an empty table and a second upgrade run are no-ops;
- downgrade → legacy format, plaintext unchanged.

## Acceptance criteria

- [ ] SR-022 AC 7: a database in the earlier format is fully readable after the migration
      (`backend/tests/db/test_migration_0010_key_id.py`).
- [ ] A value that cannot be decrypted stops the migration with no partial conversion (same file).
- [ ] Rehearsal on a populated copy: row count and plaintext checksum per row identical before
      and after (rehearsal record).

## Verification

```sh
cd backend && uv run pytest tests/db/test_migration_0010_key_id.py tests/db/test_migration.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85
```

## Records

- **TS-008**: TC-008.10 (old-format database migrated; failure rolls back; rehearsal), `verifies` SR-022.
- Rehearsal record (counts, checksums, duration) for the next TR.

## Definition of Done

- [ ] Tests pass; rehearsal recorded and presented to the human before any other database runs 0010.
- [ ] `traceability-check` shows no error for TASK-194, TS-008, SR-022.
