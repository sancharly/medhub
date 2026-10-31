---
id: "TASK-178"
type: task
title: "Migrate existing objects and key material to the new store, rehearsed against a backup"
status: approved
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

- [x] CR-002 **AC-11**: the procedure is rehearsed against a backup. After it every attachment
      downloads with a matching checksum (AC-5), and an object written before the change
      decrypts.
- [x] No source data or backup is deleted. The rollback step is documented.

## Verification

```sh
cd backend && uv run pytest tests/scripts/test_migrate_object_store.py -v
python3 infra/check_image_pins.py
```

Plus the rehearsal record (counts, checksums and API downloads) in this task's evidence.

## Definition of Done

- [x] Tests, pin check and backend suite pass.
- [x] The rehearsal is recorded, and the DEPLOY.md section exists.
- [x] `traceability-check` shows no error for this task.

## Verification results (software developer, 2026-10-30)

Environment: `DOCKER_CONTEXT=desktop-linux`, arm64 host, branch `bug/minio-object-store`.

Changes: `backend/scripts/migrate_object_store.py`, `backend/tests/scripts/` (14 tests),
`infra/migration/compose.minio-legacy.yml`, `infra/docker-compose.yml` (the `minio_data`
declaration removed), `infra/tests/test_compose_minio_legacy.py` (6 tests),
`infra/tests/test_compose_object_store.py` (one assertion inverted), `infra/DEPLOY.md` ("Migrating
from MinIO"), TS-008 1.3 (TC-008.7, `in_review`, approval cleared).

Design notes. The script takes the rows from the `attachment` table (`storage_key`, `checksum`,
`content_type`) and talks to both stores through a three-call `Store` (get, put, keys), so the unit
tests use two dict-backed stubs. A row is "already present" only when the target holds the bytes
with the recorded SHA-256; a target object with other bytes is overwritten from the source. The
legacy file also holds the `migrate` one-shot (profile `migrate`, backend image, entrypoint
`scripts/migrate_object_store.py`), attached to the internal `legacy` network, the new store's
network and the database network, all named by variables. `MINIO_KMS_SECRET_KEY` appears only
there. `backend/scripts/` is copied into the runtime image (PRB-054); the script is there as the
task says.

### Automated checks

- `cd backend && uv run pytest tests/scripts/test_migrate_object_store.py -v` -> 14 passed.
- Mutations on the script (restored after each, `diff` clean): source comparison removed -> 1
  failed; read-back comparison removed -> 1 failed; "present" without the checksum -> 1 failed; exit
  code always 0 -> 2 failed.
- `cd backend && uv run pytest --cov=app --cov-fail-under=85` -> 568 passed, total coverage
  91.31 %.
- `uv run ruff check .` clean; `uv run black --check .` clean; `uv run mypy app` no issues in 126
  files.
- `python3 -m unittest discover -s infra/tests` -> 31 tests OK (25 before; 6 new).
- `python3 infra/check_image_pins.py` -> exit 0; `python3 infra/check_image_pins.py
  infra/migration/compose.minio-legacy.yml` -> exit 0 (the default run reads tracked files, so it
  includes the legacy file once committed; the file name matches `compose*.yml`, asserted by a test).

### Rehearsal record (CR-002 AC-11, Q-5)

Backup directory `BK` (outside the repository):
`/private/tmp/claude-501/-Users-carlos-santiago-Dev-prototypes-medhub-01/332f5855-c49e-4d4e-a2c1-f7835ae95272/scratchpad/task178-backup`.
Helper image `alpine@sha256:ee16d92f...2b5bd` (the digest cached on the host). Rehearsal project
`t178rh` (new stack) and `t178rh-legacy` (legacy file); scratch volumes `t178rh_legacy_minio`,
`t178rh_postgres_data`, `t178rh_object_store_data`, `t178rh_redis_data`. The dev `infra/.env` was only
read (its values, including the legacy credentials, were never printed or written back); the new
stack ran on a generated throwaway env file with the dev `AT_REST_ENCRYPTION_KEY` (the file was
deleted afterwards). The default `infra` project was not started.

1. **Source state.** `infra_minio_data`: 31 files, 292 KB, only MinIO system files (`.minio.sys`),
   bucket `medhub` empty. `infra_postgres_data`: 1327 files, 47 MB, `attachment` table with 0 rows
   (6 accounts). Per Q-5 no volume holds real data and nothing referenced an object, so the
   rehearsal added attachments in the scratch copy before the migration (step 4).
2. **Backup**, volumes mounted `:ro` into the helper, network none.
   `infra_minio_data.tar` 80,896 bytes, sha256 `6f4e4cb2...b8fb`; `infra_postgres_data.tar`
   49,760,768 bytes, sha256 `18da1e98...e05c`; both listed in `SHA256SUMS`. Tree hash of each
   source volume (sha256 of the sorted per-file sha256 list) taken before: minio `2d2c01ff...f8e`
   (31 files), postgres `7ced1bf9...c44` (1327 files). The tars were made read-only (`chmod a-w`).
3. **Restore** into scratch volumes under project `t178rh` (`tar -xpf`): both tree hashes equal the
   sources. A PostgreSQL 16.15 container (the pinned image of the Compose file) on the restored
   volume gave `pg_dump -Fc` -> `medhub-db.dump` (36,373 bytes, 14 table-data entries per
   `pg_restore -l`), kept in `BK` with its checksum. The new stack (`object-store-preflight`,
   `object-store`, `object-store-init`, `backend`) started on the scratch volumes; the dev
   `AT_REST_ENCRYPTION_KEY` was accepted as the SeaweedFS SSE key; the initialiser exited 0.
4. **Objects written before the change, through the legacy path.** The legacy MinIO started from the
   cached pinned image (`pull_policy: never`) on `t178rh-legacy_legacy` (internal, the only member
   besides the migration container; no published port) against `t178rh_legacy_minio`. A seeding
   container in the backend image wrote, with `ServerSideEncryption=AES256` (the MinIO KMS key from
   `AT_REST_ENCRYPTION_KEY`; `head_object` returned `AES256` for each), three objects and their
   `attachment` and `clinical_entry` rows in the scratch database: `note.txt` (2,400 bytes,
   sha256 `a9ce2436...`), `scan.bin` (1,048,576 bytes of random data, `6361a0ab...`), `report.pdf`
   (4,140 bytes, `115907df...`), plus one object with no row (`attachments/orphan/stray.txt`). The
   note and the PDF contain a marker `PLAINTEXT-MARKER-T178-<12 hex>`. This used `ObjectStorageClient`'s
   `put_object` call shape and an SQL insert, not the upload API (the API cannot target the legacy
   store). Search of the legacy volume for the marker: 0 files (MinIO encrypted them).
5. **Migration** (`run --rm migrate`): copied 3, already-present-and-matching 0, missing-in-source 0,
   checksum-mismatch 0, orphans-in-source 1 (listed, not copied); exit 0.
6. **Every row matches, through the API.** Logged in as the patient owning the entry (a password set
   on the scratch copy only), `GET /api/v1/attachments/{id}` on the backend using the new store:
   `note.txt` 200, 2,400 of 2,400 bytes, sha256 equal to the row; `report.pdf` 200, 4,140 of 4,140,
   equal; `scan.bin` 200, 1,048,576 of 1,048,576, equal. The route is `AttachmentService.open`, so
   TASK-173's check ran (a mismatch would have been 502). Repeated after `stop minio-legacy`: the
   same three results, so the downloads do not depend on the legacy store.
7. **Plaintext search on the target volume** (`t178rh_object_store_data`, read-only; 88 files, 1.3 MB):
   marker hits 0; `%PDF-1.4` header hits 0; control (bucket name `medhub`) 1 hit, so the search does
   read the files.
8. **Idempotence.** Re-run: copied 0, already-present-and-matching 3, missing 0, mismatch 0,
   orphans 1; exit 0. Negative run with a row for an absent object added to the scratch database:
   missing-in-source 1, 3 already present, exit 1; the row was deleted again and a final run gave
   exit 0 with the same counts as above.
9. **(Corrected in round 2.)** The first version of this record said the rollback was exercised
   and the source "read-only in effect". That was wrong: in step 5 MinIO ran on the scratch copy
   `t178rh_legacy_minio`, which is writable, and MinIO deletes housekeeping files on start and stop
   (QA measured 31 to 12 files on a restored copy; no object data). The source volumes stayed
   identical only because MinIO never ran on them. See "Round 2" below for the corrected procedure
   and the rollback rehearsal.
10. **Source untouched** (because MinIO never ran on it). After the rehearsal the tree hashes of `infra_minio_data` (31 files) and
    `infra_postgres_data` (1327 files) equal the "before" values (`diff` clean; files
    `source-*.treehash.{before,after}` in `BK`). `infra_minio_data` still exists after the
    `minio_data` declaration was removed from `infra/docker-compose.yml`. No image, volume or
    backup was deleted; the rehearsal's containers and networks were removed with `down` (no `-v`).

Left on the host for the human to keep or delete: backups in `BK`; scratch volumes `t178rh_legacy_minio`,
`t178rh_postgres_data`, `t178rh_object_store_data`, `t178rh_redis_data`; images built for the
rehearsal (`t178rh-backend`, `t178rh-object-store-init`, `t178rh-object-store-preflight`,
`t178rh-legacy-migrate`). The cached MinIO image and the dev volumes are as found.

Key material (step 4 of the implementation detail): the new store does not need
`MINIO_KMS_SECRET_KEY` (absent from `infra/docker-compose.yml` since TASK-176);
`AT_REST_ENCRYPTION_KEY` stays as the new store's SSE key (accepted in step 3); the old volume and
its backup are kept until the human decides otherwise.

Observations for the orchestrator (not fixed here): `infra/DEPLOY.md` step 5 ("Create the MinIO
bucket") and the Data Residency note still describe MinIO (`mc`, `minio_data`), which TASK-176
left behind (candidate PRB).

## QA review (2026-10-30): CHANGES REQUESTED

QA's own rerun matched the developer's numbers. Pytest gave 14 passed and the backend suite gave 568
passed at 91.31 %. ruff, black and `mypy app` were clean, and so was mypy on the script. The infra
tests gave 31 OK. The pin check exited 0 on the default run and on the legacy file. `grep -c
minio_data infra/docker-compose.yml` returned 0, and `infra_minio_data` still exists. All three
`SHA256SUMS` entries match the files. A restore of `infra_minio_data.tar` reproduces the source
tree hash `2d2c01ff…baf8e` (31 files).

QA also ran its own rehearsal under projects `qa178` and `qa178-legacy`. It used copies of
`t178rh_legacy_minio` and `t178rh_postgres_data` and an empty new store:

| Run | Copied | Already present | Missing | Mismatch | Orphans | Exit |
|---|---|---|---|---|---|---|
| 1 | 3 | 0 | 0 | 0 | 1 | 0 |
| 2 | 0 | 3 | 0 | 0 | 1 | 0 |

- **API downloads, legacy store stopped:** 3 of 3 returned 200 with matching sizes and SHA-256.
- **Tampered target object:** QA wrote other bytes over `report.pdf` on the new store. The download
  returned 502. A re-run then copied 1 (2 already present), and the download returned 200 with a
  matching hash.
- **Plaintext search on the new store's volume:** 0 marker hits and 0 `%PDF-1.4` hits. The control
  string had 3 hits.
- **Credentials:** none of the env values appear in any captured output.
- **Untouched volumes:** `infra_minio_data`, `infra_postgres_data` and the developer's scratch
  volumes have the same tree hashes before and after the QA run.
- **`traceability-check` (fallback parser, whole project):** 0 errors. TASK-178 and TS-008 have
  no findings. There is one expected new W5: TP-001 (approved) links to TS-008 (`in_review`).

**AC-11 evidence.** QA accepts the seeded data under Q-5. The legacy MinIO from the pinned cached
image wrote the objects with SSE `AES256` and the old key derivation. After migration the same
bytes download through the API on the new store. That shows an object encrypted by the old store
can be decrypted and moved. The human should still record this reading when CR-002 closes,
because the CR says "a backup of a populated volume" and the backed-up volume was empty.

### Findings

- **[HIGH] The procedure modifies the source volume.**
  - **Where:** `infra/DEPLOY.md`, "Migrating from MinIO" step 2 (`LEGACY_MINIO_VOLUME="$OLD_VOL"`)
    and "Rollback"; the header comment of `infra/migration/compose.minio-legacy.yml`; rehearsal
    record step 9.
  - **Problem:** The page says the procedure "never deletes or modifies the old volume" and that
    "the source was only read". Neither holds when MinIO runs on the volume. QA restored
    `infra_minio_data.tar` into `qa178_fresh_minio` and ran `up --wait minio-legacy`, then
    `down`. That alone deleted 19 files (31 → 12): the `.minio.sys/tmp/.trash/*/xl.meta.bkp`
    files and a tmp file. The developer's `t178rh_legacy_minio` shows the same pattern. The
    rehearsal's "source untouched" result holds only because MinIO never ran on the source.
  - **Fix:** In step 2, always restore `OLD_VOL` from the step 1 tar into a new volume and set
    `LEGACY_MINIO_VOLUME` to that copy, for live data as well as rehearsals. Never point it at the
    original. Then correct the "never modifies" and "only read" sentences, the compose header and
    step 9's "read-only in effect".
  - **Option:** A `:ro` mount is possible. In QA's probe MinIO reached ready on a `:ro` mount,
    logging rename errors. GETs on a read-only mount were not tested, so it needs its own
    rehearsal before the page relies on it.
- **[HIGH] The rollback cannot work as written.**
  - **Where:** `infra/DEPLOY.md`, "Rollback".
  - **Problem:** The page says to run the legacy file again and point the application at it with
    the previous `OBJECT_STORE_ENDPOINT`. Two things prevent that. `minio-legacy` is only on the
    internal `legacy` network, so the backend cannot reach it. The current
    `infra/docker-compose.yml` has no MinIO service and no `minio_data` volume. The page also
    does not say that attachments uploaded after the cutover exist only on the new store. The
    rehearsal's "rollback exercised" (step 9) showed only that the legacy store serves the
    migrate container, not that the application can go back.
  - **Fix:** Write the rollback as these steps:
    1. Stop the new stack.
    2. Check out the last release before CR-002.
    3. Restore `minio_data` from the tar into `<project>_minio_data`, or reuse the untouched
       original once finding 1 is fixed.
    4. Start that release's Compose file.
  - Then state what happens to uploads made after the cutover: either block uploads until step 4
    verification passes, or document a reverse copy. Rehearse it once, or label it as not
    rehearsed.
- **[MEDIUM] The page cannot be followed as written on a stack started by this guide.**
  - **Where:** `infra/DEPLOY.md`, "Migrating from MinIO" steps 2–5.
  - (a) **Project name.** Bring-up step 3 starts the default project `infra`. The migration uses
    `-p medhub` and `medhub_*` network names, which creates an empty `medhub_postgres_data` and
    `medhub_object_store_data`. The migration then reads a database that is not the live one.
    **Fix:** Use one variable, for example `P=infra`, in every command: `-p "$P"`,
    `OBJECT_STORE_NETWORK=${P}_object-store` and `DATABASE_NETWORK=${P}_medhub`. Use the same
    project for the step 4 backend start.
  - (b) **Env file.** The legacy file lives in `infra/migration/`, so Compose does not read
    `infra/.env`. QA ran the documented command without exports and got "required variable
    OBJECT_STORE_SECRET_KEY is missing a value". **Fix:** Add `--env-file infra/.env` to every
    legacy-file command.
  - (c) **Endpoint.** An existing host has `OBJECT_STORE_ENDPOINT` pointing at `minio` in
    `infra/.env`; the dev file does. `backend`, `object-store-init` and `migrate` interpolate
    that value. **Fix:** Step 2 must say to set `OBJECT_STORE_ENDPOINT=http://object-store:8333`,
    or to remove the line.
- **[LOW] No test covers the `S3Store` adapter.**
  - **Where:** `backend/scripts/migrate_object_store.py:108-146`;
    `backend/tests/scripts/test_migrate_object_store.py`.
  - **Problem:** When QA deleted `ServerSideEncryption="AES256"` from `S3Store.put`, all 14 tests
    still passed. TC-008.7 claims that request. Bucket default encryption from TASK-175 still
    encrypts the object at rest. The `NoSuchKey`/`404` → `None` mapping is not tested either.
  - **Fix:** Add tests with `botocore.stub.Stubber` that assert the `put_object` parameters include
    `ServerSideEncryption: AES256` and that a `NoSuchKey` error from `get_object` returns `None`.
- **[LOW] A run against the wrong database looks successful.**
  - **Where:** `backend/scripts/migrate_object_store.py:89-90` (`exit_code`).
  - **Problem:** With 0 rows and N source objects, the run exits 0 and lists every object as an
    orphan. The wrong-project case in finding 3a produces exactly this.
  - **Fix:** Exit 1, or print a warning that names the condition, when the database has no rows
    but the source has objects. Cover it with a unit test.
- **[LOW] The page cites an alpine pin that does not exist.**
  - **Where:** `infra/DEPLOY.md`, "Migrating from MinIO" step 1.
  - **Problem:** The page says "the digest of the `alpine` image already pinned in this
    repository's Dockerfiles". No tracked Dockerfile pins `alpine` by digest.
  - **Fix:** Give the digest used in the rehearsal (`alpine@sha256:ee16d92f…`, in full), or tell the
    operator how to get one (`docker buildx imagetools inspect alpine:3.21`).

Observations (not blocking):
- The script prints storage keys for missing, mismatched and orphan objects. Each key contains the
  patient ID and the original file name, which can be PHI. This is acceptable for operator tooling,
  but the page should say not to paste that output into tickets.
- The legacy store still starts its console (`--console-address ":9001"`). Only the migrate
  container can reach it, on the internal network. Dropping the flag would remove it.

Pre-existing (not blocking): `infra/DEPLOY.md` step 5 "Create the MinIO bucket" and the Data Residency
note still describe MinIO. TASK-176 left them, and the developer already flagged them as a candidate
PRB. The fallback check also reports `soup_without_risk` on SOUP-036.

## Round 2 (software developer, 2026-10-30): changes after QA

Findings 1 to 6 and the PHI observation of the QA review are addressed as follows.

- **1 [HIGH] The old volume is never given to MinIO.** `infra/DEPLOY.md` "Migrating from MinIO" now
  backs the old volume up through a `:ro` mount (step 1), restores the tar into a fresh copy volume
  (step 2) and runs the legacy MinIO only on that copy (step 4). The "never modifies" and "only read"
  claims now state what holds: the old volume, tars and dump are never deleted, and MinIO is never
  run on the old volume. `infra/migration/compose.minio-legacy.yml` mounts the volume `:ro`
  (a test asserts `read_only`) and its header says the volume must be a copy and why. Read-only
  check: a MinIO container (the pinned image, with the KMS key) on a `:ro` mount of a copy holding
  the 3 rehearsal objects started, listed 4 objects, returned and decrypted `note.txt` (2,400
  bytes), and the volume's tree hash (18 files) was identical before and after. MinIO logs rename
  errors for its housekeeping files; they are harmless for this use.
- **2 [HIGH] Rollback.** Rewritten: stop the new stack, check out the last release before CR-002
  (`b1d0b78` here) in a second tree, restore `.env` from the step-1 copy, use the untouched old
  volume (or restore it from the tar), start that release's Compose file. Uploads made after the
  cutover exist only on the new store and there is no reverse copy, so the page says to roll back
  only before uploads are opened (the new stack is started without the reverse proxy until the
  verification passes) and that rolling back afterwards is not supported and not rehearsed.
  **Rehearsal of the rollback** (project `t178r2`, scratch copies): after the migration below, the
  new stack was stopped with `down` (no `-v`), `git archive b1d0b78 infra backend frontend` was
  extracted to a scratch tree with the old `.env`, and its Compose file started MinIO, the backend
  and the proxy on `t178r2_minio_data` and `t178r2_postgres_data` (`OBJECT_STORE_ENDPOINT` =
  `http://minio:9000` in the backend). Through that backend's API the 3 attachments downloaded 200
  with 2,400, 4,140 and 1,048,576 bytes and matching SHA-256. This was done with no post-cutover
  upload, so it covers the supported case only. The scratch tree and its `.env` copy were deleted.
- **3 [MEDIUM] Followable page.** One variable `P` for the project in every command; the legacy
  commands carry `--env-file infra/.env` and `${P}_...` network names; step 3 tells the operator to
  set `OBJECT_STORE_ENDPOINT=http://object-store:8333` (or remove the line), to keep the old pair as
  `LEGACY_ACCESS_KEY`/`LEGACY_SECRET_KEY`, and starts only `postgres redis object-store-init backend`
  until the verification passes.
- **4 [LOW] `S3Store` tests.** Eight botocore `Stubber` tests: `put_object` parameters including
  `ServerSideEncryption: AES256` and `ContentType`, `NoSuchKey`/`404`/`NotFound` -> `None`, other
  errors re-raised, `get` returns bytes, `keys` follows pagination. Mutation: deleting
  `ServerSideEncryption="AES256"` from `S3Store.put` now fails `test_s3store_put_requests_aes256_and_content_type`
  (1 failed, 23 passed); restored.
- **5 [LOW] Wrong database.** `Report.wrong_database` (no rows while the source holds objects) makes
  `ok` false: exit 1 and an `error:` line naming the condition. Two tests (fails with objects, fine
  with an empty source).
- **6 [LOW] Helper pin.** The page gives the full `alpine@sha256:ee16d92f...2b5bd` (the digest used
  in the rehearsal, the alpine:3.21 repo digest of the arm64 host) and how to get one elsewhere.
- **PHI observation.** The script now prints the attachment id for missing and mismatched rows and a
  12-hex-character SHA-256 prefix of the key for orphans; storage keys are never printed (test
  asserts no patient id or file name appears). The page still says to keep the output out of
  tickets.

**Rehearsal following the corrected page** (project `t178r2`; `infra/.env` replaced by a throwaway
env file that holds the dev legacy credentials and `AT_REST_ENCRYPTION_KEY`, the only deviation; the
"old host" was built from copies: `t178r2_minio_data` from the 3-object copy, `t178r2_postgres_data`
from the scratch database with its 3 rows):

1. Step 1: no container running for the project; `minio_data.tar` and `postgres_data.tar` made from
   `:ro` mounts, `SHA256SUMS` written, tars made read-only. Old volume tree hash `0a4bb61d...0d17`
   (18 files).
2. Step 2: the copy volume `t178r2_minio_data_copy` has the same tree hash and file count.
3. Step 3: `OBJECT_STORE_ENDPOINT` was `http://minio:9000` in the env file and was changed as the page
   says; `up -d --build postgres redis object-store-init backend`: store healthy, initialiser exit 0.
4. Step 4: legacy MinIO on the copy (`:ro`), migrate: copied 3, already-present 0, missing 0,
   mismatch 0, orphans 1, exit 0, output `ORPHAN 1573c14fdb83` (no key). Second run: copied 0,
   already-present 3, exit 0.
5. Step 5: legacy store stopped; API downloads of the 3 attachments: 200, 2,400/4,140/1,048,576
   bytes, SHA-256 equal to the rows. Plaintext marker on `t178r2_object_store_data` (67 files): 0
   hits, 0 `%PDF-1.4` hits; control: `AES256` 3 hits and `text/plain` 2 hits (metadata is readable,
   content is not).
6. Step 6: `up -d` of the whole stack (proxy, frontend, worker started), `--profile migrate down` of
   the legacy project. After the run the tree hash of the copy (the volume MinIO ran on, read-only)
   and of `t178r2_minio_data` (the old volume) were both still `0a4bb61d...0d17`, 18 files. Then the
   rollback above ran an old release's MinIO on `t178r2_minio_data` (scratch, so writable there).
7. Still unchanged at the end: `infra_minio_data` (31 files, `2d2c01ff...f8e`) and
   `infra_postgres_data` (1327 files, `7ced1bf9...c44`). The default `infra` project was never
   started.

Verification rerun after the changes: `uv run pytest tests/scripts/test_migrate_object_store.py -v`
24 passed; `uv run pytest --cov=app --cov-fail-under=85` 578 passed, 91.31 %; ruff, black and
`mypy app` clean; infra tests 31 OK (read-only mount asserted); `python3 infra/check_image_pins.py`
exit 0, and on the legacy file exit 0.

Left on the host in addition to the earlier list (nothing deleted): volumes `t178r2_minio_data`,
`t178r2_minio_data_copy`, `t178r2_postgres_data`, `t178r2_object_store_data`, `t178r2_redis_data`,
`t178r2_probe_ro`; backups `task178-r2-backup/` and, in `task178-backup/`,
`t178rh_legacy_minio_with_objects.tar` and `t178rh_postgres_with_rows.tar` (both under the same
scratchpad); images built for the rehearsal under `t178r2*` names and for the rollback
(pre-CR-002 backend and frontend).

## QA review, round 2 (2026-10-30): APPROVED

All six round-1 findings and the PHI observation are closed. QA checked each one itself.

- **1 (source volume).**
  - **Restore copy:** DEPLOY steps 1–2 back up the old volume through a `:ro` mount and restore
    it into `$COPY_VOL`. The legacy MinIO runs only on that copy.
  - **Read-only mount:** `infra/migration/compose.minio-legacy.yml` mounts `minio_data:/data:ro`, and
    `test_store_is_isolated_and_volume_is_external` asserts `read_only`.
  - **QA run:** a copy of `t178rh_legacy_minio` in `qa178r2_ro` (18 files, tree hash `0a4bb61d…0d17`)
    was used through the page's commands under project `qa178r2`, with `--env-file` and an empty
    new store. Docker reports the mount as `RW=false`.
  - **Result:** migrate copied 3 (1 orphan, printed as `ORPHAN 1573c14fdb83`), exit 0. The re-run
    found 3 already present, exit 0. Tree hash and file count were identical after the run.
  - **API check:** 3 of 3 downloads through the new store returned 200 with matching size and
    SHA-256.
- **2 (rollback).**
  - **Steps:** the page now says to stop the new stack, check out `b1d0b78` in a worktree, restore
    `env.before`, use the never-run `$OLD_VOL`, and start the old Compose file.
  - **Release:** `b1d0b78` is the parent of the first CR-002 commit (`68fc68b`). There is no schema
    migration between it and HEAD, so the old backend runs on the same database.
  - **Old Compose file:** it mounts `${P}_minio_data`, which equals `$OLD_VOL`.
  - **Uploads:** the page keeps uploads blocked (no proxy) until verification passes and says plainly
    that rollback after step 6 is not supported.
  - **Rehearsal:** QA did not rerun the rollback. The developer's record covers the supported case,
    and the page's limits are stated honestly.
- **3 (followability).** `P` is used everywhere. `--env-file infra/.env` is on the legacy commands,
  the `${P}_object-store` and `${P}_medhub` networks are named, and step 3 changes the endpoint.
  QA followed steps 3–5 with these commands.
- **4 (S3 adapter tests).** 24 tests pass. QA's mutations each fail at least one test:

  | Mutation | Failing tests |
  |---|---|
  | SSE argument removed | 1 |
  | Source comparison removed | 1 |
  | Read-back comparison removed | 1 |
  | Exit code forced to 0 | 3 |
  | Wrong-database check removed | 1 |
  | Storage key printed | 1 |
  | Missing → `None` mapping removed | 3 |
- **5 (wrong database).** The wrong-database case now exits 1, and tests cover it.
- **6 (alpine pin).** The page gives the full digest.
- **PHI observation.** `test_printed_lines_carry_attachment_id_or_hash_not_the_storage_key` checks
  that no patient id or file name is printed.

Reruns:

| Check | Result |
|---|---|
| Backend suite | 578 passed, 91.31 % |
| ruff, black, `mypy app` and mypy on the script | clean |
| Infra tests | 31 OK |
| Pin check | 0, and 0 on the legacy file |
| `grep -c minio_data infra/docker-compose.yml` | 0 |
| `infra_minio_data` | exists |
| Backup `SHA256SUMS` | 3/3 OK |

`traceability-check` (fallback parser, whole project) reports 0 errors. Approving adds one
expected W5: TASK-178 is approved and links to RISK-012, which is `in_review` until TASK-181.

Remaining findings (not blocking):
- **[MEDIUM] TC-008.7 is double-booked.**
  - **Where:** TS-008 and this task use TC-008.7 for the migration. TASK-179 (`:83`, `:95`),
    TASK-180 (`:67`), TASK-181 (`:78`) and CR-002's §7.4 row for TASK-179 (`:288`) plan TC-008.7
    for the CI SSE check.
  - **Fix:** Before TASK-179 starts, renumber the CI case to TC-008.8 in TASK-179, TASK-180 and
    TASK-181, and in the CR-002 row once the PRB-052 workstream's CR edits are committed. TS-008
    keeps TC-008.7 for the migration.
- **[LOW] Two commands break as written.**
  - **Where:** `infra/DEPLOY.md`, "Migrating from MinIO".
  - **Problem:** `L="docker compose …"; $L up …` relies on word splitting, so it fails in zsh, the
    default macOS shell. `docker stop $(docker ps -q …)` errors when no container is running.
  - **Fix:** Use a shell function (`L() { docker compose -p "${P}-legacy" … "$@"; }`), or say the
    blocks need bash. Use `docker ps -q … | xargs -r docker stop`.
