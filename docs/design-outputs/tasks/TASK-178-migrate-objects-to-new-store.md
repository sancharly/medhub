---
id: "TASK-178"
type: task
title: "Migrate existing objects and key material to the new store, rehearsed against a backup"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-022"
    relation: implements
  - target: "SR-013"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "RISK-011"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "CR-002"
    relation: relates_to
  - target: "TASK-176"
    relation: relates_to
tags: ["migration", "encryption", "cr:CR-002", "issue:sancharly/medhub#33", "control:protective"]
---

# TASK-178 — Migrate existing objects and key material to the new store, rehearsed against a backup

- **Software item / unit:** SI-OBJSTORE (ADD-025). Developer and operator tooling under
  `backend/scripts/`, which ships in no image.
- **Depends on:** TASK-176 (`relates_to`). TASK-173 helps: its check proves the result through
  the API.
- **Branch:** `bug/minio-object-store`
- **Size:** M (1 script and its tests, 1 Compose file for the legacy store, a DEPLOY.md section)
- **Needs:** the reference workstation, which holds the cached MinIO image and a populated
  `minio_data` volume
- **Under another Q-1 answer:** (a) AIStor: rehearse an in-place upgrade of the same volume
  instead of a copy, with the same before-and-after checks. (c) Interim: dropped. ADR-0015 states
  that no migration is needed (AC-11).

## Objective

CR-002 AC-11 and RISK-012 "risks introduced by controls": move every stored object from MinIO to
the new store without loss, without plaintext at rest and without orphaning, and retire the MinIO
SSE key material only afterwards. Q-5, as the human decided on 2026-10-30, means no volume holds
real data. The procedure is still rehearsed against a backup, so it is proven before any
deployment that has data.

## Interfaces to honor

- Source of truth: the `attachment` rows (`storage_key`, `checksum`).
- Source store: the old MinIO, started read-only from the cached image, on an isolated network
  with only the migration container.
- Target: the new `object-store` through `ObjectStorageClient`'s settings, with bucket default
  encryption from TASK-175.
- Never delete or modify the source volume or any backup (prohibited without the human's
  explicit agreement). The rehearsal works on restored copies.
- Credentials for the legacy store come from the existing local `infra/.env` and are never
  printed.

## Implementation detail

1. Write `backend/scripts/migrate_object_store.py`. For each attachment row:
   - read the object from the source (MinIO decrypts it);
   - compare its SHA-256 with `checksum`;
   - write it to the target with `ServerSideEncryption="AES256"`;
   - read it back and compare again.

   It reports four counts: copied, already-present-and-matching, missing-in-source and
   checksum-mismatch. It also lists source objects with no row (orphans) and reports them only.
   It exits non-zero on any missing or mismatched object. It can be re-run.
2. Write `infra/migration/compose.minio-legacy.yml`. It starts the old MinIO from the pinned,
   cached reference against a named volume given as a variable, on an `internal` network. The
   pin check covers it.
3. Rehearsal, recorded step by step:
   1. Back up `minio_data` and the database: a tar of the volume through a pinned helper image,
      and `pg_dump`.
   2. Restore both into scratch volumes under their own Compose project name.
   3. Run the migration against the scratch copies.
   4. Every row matches. A file uploaded before the change downloads through the API on the new
      store with the same bytes and passes TASK-173's check.
   5. On the target volume, a search for a plaintext marker finds nothing.
   6. Re-run the migration: everything is reported as already present.
4. **Key material:**
   - After a successful comparison the new store does not need `MINIO_KMS_SECRET_KEY`. TASK-176
     already removed it from Compose.
   - `AT_REST_ENCRYPTION_KEY` stays, and is now the new store's SSE key source.
   - Record that the old volume and its backup are kept on the host until the human decides to
     delete them.
   - Remove the `minio_data` declaration from `infra/docker-compose.yml`. The legacy Compose file
     names the volume as external.
5. Add an `infra/DEPLOY.md` section "Migrating from MinIO" with the backup, migration,
   verification and rollback steps. Rollback means starting the legacy file again: the source is
   untouched.

## Tests (write first)

Unit tests with two stubbed clients and a list of rows:

- all copied;
- an object already present;
- missing in the source;
- a checksum mismatch at the source;
- a mismatch after the write;
- an orphan reported;
- exit codes.

## Acceptance criteria

- [ ] CR-002 **AC-11**: the procedure is rehearsed against a backup. After it every attachment
      downloads with a matching checksum (AC-5), and an object written before the change
      decrypts.
- [ ] No source data or backup is deleted. The rollback step is documented.

## Verification

```sh
cd backend && uv run pytest tests/scripts/test_migrate_object_store.py -v
python3 infra/check_image_pins.py
```

Plus the rehearsal record (counts, checksums and API downloads) in this task's evidence.

## Definition of Done

- [ ] Tests, pin check and backend suite pass.
- [ ] The rehearsal is recorded, and the DEPLOY.md section exists.
- [ ] `traceability-check` shows no error for this task.
