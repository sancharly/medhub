---
id: "TASK-194"
type: task
title: "Migrate existing encrypted field values to the identified envelope"
status: approved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-01"
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

- [x] SR-022 AC 7: a database in the earlier format is fully readable after the migration
      (`backend/tests/db/test_migration_0010_key_id.py`).
- [x] A value that cannot be decrypted stops the migration with no partial conversion (same file).
- [x] Rehearsal on a populated copy: row count and plaintext checksum per row identical before
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

- [x] Tests pass; rehearsal recorded and presented to the human before any other database runs 0010.
      **Ask-first approval:** the human approved the 0010 rehearsal result on 2026-11-01 (chat; CR-004 D-7),
      citing QA's rehearsal: 315 rows, identical per-row hashes, refusal on a wrong key or a damaged row, and
      survival of a SIGKILL. The tick of this item is QA's.
- [x] `traceability-check` shows no error for TASK-194, TS-008, SR-022.

## Implementation notes (2026-11-01, software developer)

Status `draft` -> `in_review`. Nothing is ticked: QA ticks.

### Files

- `backend/app/db/alembic/versions/0010_field_encryption_key_id.py` (new)
- `backend/tests/db/test_migration_0010_key_id.py` (new, 12 tests)
- `infra/DEPLOY.md` (new section "Converting existing field values (migration 0010)"; the sentence about the
  TASK-194 window rewritten)
- `docs/design-outputs/tests-specifications/TS-008-*.md` (TC-008.10, `in_review`, 1.7)
- `docs/problem-reports/PRB-004-*.md` (interim note, 1.4, still `open`); `docs/problem-reports/PRB-062-*.md` (new)
- This record.

No change to `crypto.py`, `docker-compose.yml` or `.env.example`: `db-migrate` already passes
`AT_REST_ENCRYPTION_KEY`, `_KEY_ID` and `_RETIRED_KEYS` (TASK-193), and the rehearsal confirmed that the
migration reads them there.

### Field inventory

`EncryptedString` is used by exactly one column: `clinical_entry.description` (`backend/app/db/models/clinical.py:23`).
Searched every `*.py` outside `.venv`/`node_modules`, including `backend/modules/dicom_viewer` (no hit), the other
models, migrations and scripts. PRB-004 and QA are right.

### Migration 0010

- Reads the keys through `app.db.crypto.get_keyring()` (the application's settings). Uses a table construct,
  not the ORM type, so it does not depend on the application's read path (which refuses unprefixed values).
  Retired keys are not tried: the earlier format had one key, the current one.
- `upgrade`: `LOCK TABLE ... SHARE ROW EXCLUSIVE` (readers continue, writers wait). Pass 1, read only: every
  non-NULL value that does not start with `mh1:` must pass `decrypt_legacy` with the current key; if any fails,
  nothing is written and `FieldMigrationError` names the count and the row ids (first 100) and no value.
  Pass 2: batches of 500 by primary key; each value is re-encrypted with `encrypt`, read back with `decrypt`
  and compared, then updated. One count line is logged (`alembic.runtime.migration`). An error in pass 2 rolls
  back the whole Alembic transaction (tested by a failure injected after three rows).
- NULL is left alone (the column is `NOT NULL` today). An empty plaintext converts. A raw empty string cannot
  be produced by the application and cannot be read, so it is refused and named.
- Idempotent: values starting `mh1:` are never selected, so a second run converts nothing. An empty or
  fully converted table returns before reading the key settings.
- `downgrade`: re-encrypts `mh1:` values that name the current key to the unprefixed format with the current key,
  verified by read-back. If any value names another key id or does not decrypt, it refuses with count and row
  ids and changes nothing.

### Acceptance criteria -> tests

| Criterion | Evidence |
|---|---|
| SR-022 AC 7: a database in the earlier format is fully readable after the migration | `test_legacy_rows_become_identified_and_read_back`, `test_large_batch_spans_several_batches`, `test_null_empty_plaintext_and_raw_empty_value` (rows built with `AESGCM`, no prefix, no AAD); rehearsal 1100 of 1100 |
| An undecryptable value stops the migration with no partial conversion | `test_value_under_another_key_stops_the_migration_with_no_partial_conversion`, `test_every_undecryptable_row_is_named`, `test_large_batch_with_a_bad_row_in_the_last_batch_converts_nothing`, `test_failure_during_conversion_rolls_back_every_row`; rehearsal wrong-key run |
| Rehearsal on a populated copy: row count and plaintext checksum per row identical | Rehearsal record below |
| Re-run is a no-op; `mh1:` values untouched | `test_rerun_converts_nothing_and_changes_no_value`, `test_identified_rows_are_untouched`, `test_empty_table_is_a_no_op_and_needs_no_key_settings` |
| Downgrade | `test_downgrade_returns_to_the_unprefixed_format_with_the_same_plaintext`, `test_downgrade_refuses_a_value_under_a_retired_key_and_changes_nothing` |

### Verification results

| Command | Result |
|---|---|
| `uv run pytest tests/db/test_migration_0010_key_id.py tests/db/test_migration.py -q` | 14 passed |
| `uv run pytest --cov=app --cov-fail-under=85` | 1184 passed, 4 skipped (as before), coverage 94.06% |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `ruff check .`, `black --check .`, `mypy app` | clean (251 files, 131 source files) |
| `cd infra && python3 -m unittest discover -s tests` | 78 passed |

Negative controls (scratch edits to the migration, restored after): skipping the first row of every batch in
pass 2 -> 5 tests fail; selecting every row and re-encrypting `mh1:` values too (idempotence broken) -> 4 tests fail.

### Rehearsal record (projects `task194` and `task194r`, scratch, removed)

1. `git archive 284e7e6` (migrations through 0009, no key id) into a scratch tree; a scratch tree of the working
   tree for the new layout; each with its own `infra/.env` and certificates. Old stack started with
   `up -d --build`; a doctor, a patient and a consent created; **1100 clinical entries written through the API**
   (unicode, 25 to about 500 characters). Stored form before: 1100 legacy, 0 `mh1:`; `alembic_version` 0009; 2212 `audit_log` rows.
2. `pg_dump -Fc` backup (492 KB), old stack down, `AT_REST_ENCRYPTION_KEY_ID=k1` and an empty
   `AT_REST_ENCRYPTION_RETIRED_KEYS` added, `up --build db-migrate`, `up -d --build`.
3. After: `alembic_version` 0010; 1100 `mh1:k1:`, 0 legacy; row count 1100 and `audit_log` 2212 unchanged.
   Per-row SHA-256 of the decrypted plaintext, computed by a separate script with `AESGCM` only: identical for
   all 1100 ids before and after; the API returned identical hashes before and after; the set of hashes equals
   the seeded set after the API's `strip()`, which trims both ends. A new entry written through the API was stored as
   `mh1:k1:` (1101 `mh1:k1:`). A second `up --build db-migrate` left the column byte-identical (MD5 over id and
   stored value equal) and printed no conversion. Smoke test (`COMPOSE_PROJECT_NAME=task194`, scratch tree):
   64 passed, 0 failed.
4. Restored copy (`task194r`): `pg_restore` of the backup (the 15 `GRANT ... TO medhub_app` errors are the role not existing yet
   and are expected), migration with a random wrong key: exit 1, message with 1100 rows named (first 100 listed), no description text in the log,
   column MD5 and `alembic_version` (0009) unchanged. Then the right key: `migration 0010 upgrade: 1100
   clinical_entry.description value(s) converted`, exit 0, 1100 `mh1:k1:`, per-row plaintext hashes identical to the "before" file.
5. Duration: `db-migrate` about 8 seconds wall time including the roles step on 1100 rows.
6. `infra/.env` SHA-256 a4933b8c82d6f81e35acd40b3188c21bf1b40419ac73e3dff2e3636823c696da before and after.
   `down -v --remove-orphans` of both projects and removal of the `task194*` images: no `task194*`
   container, volume, network or image remains; the lists of volumes, containers and networks are identical to
   those before the run (the container `peaceful_pike` was not touched).

The window of CR-004 D-5 closes with this task: on a stack upgraded as above, existing descriptions are readable again.

### Deviations and notes for QA

- The task says "in one transaction, batches of 500". Implemented as that, plus a read-only validation pass first
  and a table lock, so that a failure leaves nothing written even apart from the rollback (the order was
  strengthened, not relaxed).
- Finding (PRB-062, out of scope): DEPLOY.md runs `up db-migrate` without `--build`; on an upgrade that runs the
  previous image and skips 0010 with exit 0. The new section says `--build`; the two older places are not changed.
- The lock waits for in-flight writers; the TS-008 resource criterion "migrations do not lock tables longer than the
  deploy window" holds (the stack is stopped for the upgrade; the whole `db-migrate` run took about 8 seconds on 1100 rows, the lock time was not measured separately).
- Records that need a human-approved change, none made here: ADR-0018 "Existing values" could mention the
  validation pass, the table lock and `--build` (optional); CR-004 D-5 can be marked closed by this task.
- Not done on purpose: no retired-key fallback (TASK-195), no SSE key work (TASK-196).

## QA review round 1 (QA engineer, 2026-11-01): CHANGES REQUESTED

Status `in_review` → `draft`. TS-008 1.7 stays `in_review`. PRB-004 1.4 and PRB-062 1.0 are unchanged.

The migration is correct. My probes, my rehearsal and my negative controls found no data-integrity
defect:
- Plaintext is preserved byte for byte, including whitespace, newlines, NUL, NFD, RTL, emoji and
  1 MB values.
- A SIGKILL mid-conversion rolls back.
- The lock blocks writers and not readers.
- A wrong key or one damaged row changes nothing.
- Retired-key envelopes and literal `mh1:` text are left alone.

The changes requested concern the evidence, which is the record of SR-022 AC 7, and the operator text.

### Findings

1. **MEDIUM: the committed tests do not show that the plaintext is preserved byte for byte.**
   Location: `backend/tests/db/test_migration_0010_key_id.py:123`, `:244`, `:274`.
   - **Gap.** The plaintexts are `entry {n} é中 xxx`, `row {n}`, `one`, `""` and `tres é`. None has
     leading or trailing whitespace, a newline, CR/LF, NUL, a decomposed (NFD) character or a large
     value.
   - **Evidence.** In a scratch copy, I changed `_run` to encode `plaintext.strip()`. In a second
     copy, I changed it to encode `unicodedata.normalize("NFC", plaintext)`. Both mutations pass all
     12 tests. The rehearsal doesn't cover it either: its 1100 entries went through the API, and
     `ClinicalService.create_entry` strips the text before storing it. My probe catches both mutations.
   - **Why it matters.** AC 7 and TC-008.10 rest on "decrypts to the original plaintext", and these
     are clinical descriptions.
   - **Fix.** Add one test, upgrade and then downgrade plus upgrade, over plaintexts like:
     `"trailing   "`, `"   leading"`, `"\ttab\t"`, `"a\nb\n"`, `"a\r\nb\r\n"`, `"\n"`, `" "`,
     `"nul\x00in"`, `"é"` (NFD), `"‮RTL‬"`, emoji/CJK/Arabic, `"​﻿"`,
     `"x" * 1_000_000`, `"mh1:k2:literal"`, `"%_\\"`.
     - Compare with `decrypt(v).encode() == plaintext.encode()`.
     - Rerun the strip and NFC mutations and record that they fail.
     - The probe is `scratchpad/qa194/probe/test_qa194_probe.py::test_plaintext_byte_identical`.
2. **LOW: nothing tests the table lock.** Location: `0010_field_encryption_key_id.py:127-128`, `:142`.
   - **Evidence.** Removing `_lock(bind)` passes all 12 tests. My probe ran the migration in a thread
     and held it inside batch 2.
     - `pg_locks` showed `ShareRowExclusiveLock` granted.
     - A concurrent `SELECT` returned all 700 values, still in the legacy format.
     - An `INSERT` with `lock_timeout = 1s` failed with a lock timeout.
     - Without the lock, the probe fails.
   - **Fix.** Add that probe as a test, or record in TS-008 that the lock is verified by review only.
3. **LOW: the exit codes in DEPLOY.md do not match what Compose returns.** Location:
   `infra/DEPLOY.md:322` ("exit code 0") and `:328` ("stops with exit code 1"); also `:286`
   (TASK-191 text).
   - **Evidence.** `docker compose up --build db-migrate` returned **0** even though the container
     exited 1 with the refusal (Compose v2.20.2).
   - **Effect.** An operator who checks `$?`, or a script written as `up --build db-migrate && up -d`,
     gets false assurance. The backend still won't start, because its `depends_on` requires
     `service_completed_successfully`, so this fails safe.
   - **Fix.** Write `docker compose -f infra/docker-compose.yml up --build --exit-code-from db-migrate db-migrate`.
     I verified it returns 1 on refusal and 0 on success. Or tell the operator to look for
     `db-migrate-1 exited with code 0`.
4. **LOW: PRB-062 overstates its impact, and its safety evaluation names a check that doesn't exist.**
   Location: `docs/problem-reports/PRB-062-…md:23-24`, `:40`.
   - **The mechanism is right.** I reproduced it: `up db-migrate` without `--build` reused the old
     image, printed `database roles applied` and exited 0, and the schema stayed at `0009`.
   - **The impact claim is wrong for the documented procedure.** "The operator then starts the new
     backend against the old schema" does not happen there. Step 4, `up -d --build`, rebuilt
     `db-migrate` and ran 0009→0010 (315 converted) before the backend started. What actually fails:
     - step 3's checkpoint is falsely green;
     - section 6, used alone after a `git pull`, really does skip the migration.
   - **The smoke test does not catch it.** `infra/smoke-test.sh` has no clinical read and no
     `alembic_version` check. Section 9 accepts a 401 on login, and that passes at 0009. Only the
     first clinical read shows the problem: I reproduced the D-5 window and got HTTP 500 on the list
     and attachment endpoints.
   - **Fix.** Correct Observed and Impact. Replace "caught by the smoke test" with "caught by the
     first clinical read (HTTP 500)". Criticality `minor` still holds.
5. **LOW, record accuracy: the trimming happens at both ends, and before CR-004.** Location: this
   record, rehearsal step 3 ("the API's whitespace trimming").
   - `ClinicalService.create_entry` calls `description.strip()` (`backend/app/clinical/service.py:49`),
     which removes leading *and* trailing whitespace.
   - It has been there since commit `28b7dcd` (2026-06-22, TASK-040–051). It is not a CR-004 change.
   - **Fix.** Correct the wording. See the determination below.

### PRB-062: scope recommendation (human decision)

- PRB-062 is a defect in CR-004's own output, TASK-191's DEPLOY.md text. Its only effect is on the
  upgrade that 0010 needs.
- **Recommendation: fix it inside CR-004, in TASK-194.** This task already edits that file and
  states the `--build` rule. Two changes would do it:
  - add `--build` to `:250` and `:284`, together with finding 3's `--exit-code-from`;
  - add `PRB-062` as a `resolves` link on CR-004.
- TASK-201 is the alternative. It is docs-only, but it comes last, and it would leave the guide
  inconsistent in the meantime.
- Right now DEPLOY.md is inconsistent:
  - lines 250 and 284 say `up db-migrate`;
  - line 319 says `up --build db-migrate`;
  - line 135 (initial start) says `up -d`, which is fine on a first install.

### Whitespace-trimming determination: (a), pre-existing

- `git blame backend/app/clinical/service.py:49-62` shows `trimmed = description.strip()` and
  `description=trimmed`.
- Both lines come from `28b7dcd` (2026-06-22, "ENH: Add phase-3 domain services … (TASK-040–051)").
- `git log -S'description.strip()'` shows no other commit, and CR-004's commits (TASK-185 onward)
  don't touch the file.
- SR-012 says nothing about normalising whitespace. Whether storing a stripped description is
  acceptable is a separate, pre-CR-004 question for the human; if not, a PRB against SR-012.
- The migration itself never trims. I inserted legacy rows directly, through the old ORM type, with
  leading and trailing whitespace, `\n`, `\r\n`, NUL, NFD, RTL, zero-width characters, a 200 kB value
  and literal `mh1:` text. They came back byte-identical through the API after 0010.

### Assessment of the brief's other points

- **Lock mode.** `SHARE ROW EXCLUSIVE` does not conflict with `ACCESS SHARE`, so readers continue,
  as measured. It is the weakest mode that blocks writers *and* conflicts with itself:
  - `SHARE` would also block writers, but two concurrent migrators could each hold it and then
    deadlock on `UPDATE`.
  - So the choice is right.
- **One transaction, bloat and lock time.** Measured at 976 rows/s (20,000 rows in 20.5 s), because
  there is one `UPDATE` round trip per row.
  - At that rate, 100,000 rows take about 2 minutes and 1,000,000 about 17 minutes, holding the lock
    and doubling the table's dead tuples until autovacuum.
  - The stack is stopped for the upgrade, so readers aren't affected.
  - That is acceptable for a single-site clinical database. Optionally, DEPLOY.md could give the
    rate for planning.
- **Crash mid-batch.** In a separate process, killed with SIGKILL after 749 encryptions (batch 1
  already updated):
  - every row was byte-identical and `alembic_version` was `0009`;
  - no lock was left behind;
  - a re-run converted all rows.
- **`enforce()` before `get_keyring()`.** In the deployed path it runs twice: first in the
  `db-migrate` entrypoint (`docker-compose.yml:154`), then in `env.py` `check_secrets()`, because
  `sqlalchemy.url` is unset. Only callers that supply their own URL (the tests) skip it.
- **Literal `mh1:` prefix.** Legacy values are `base64.urlsafe_b64encode` output, as in
  `crypto.py` at `284e7e6`, and contain no `:`. Over 3000 legacy encodings, none had a `:`.
  - A row holding literal `mh1:zz:…` text is excluded from the upgrade and left byte-identical.
  - The downgrade refuses it.
- **Mixed rows (after a partial run).** Legacy, `mh1:k2` current and `mh1:k1` retired rows:
  - only the legacy rows converted;
  - both envelopes stayed byte-identical.
- **Downgrade refusals.**
  - Retired kid: refused (developer test).
  - Unknown kid `k9` and a malformed envelope: refused, naming 2 and not the good row, with nothing
    changed (my probe).
- **Refusing raw `''`.** It cannot block a real installation.
  - `EncryptedString` has encrypted on write since `6fc5277` (phase 1).
  - 0005 only changed the column type.
  - The service rejects blank text.
  - So the application never stored `''` (the column has always been `NOT NULL`).
- **Retired keys not tried.** This is safe under ADR-0018, which says "re-encrypts every unprefixed
  value under the current key". Before 0010 there was one key.
  - If an operator rotates during this upgrade, 0010 refuses all legacy rows and changes nothing:
    it fails closed.
  - DEPLOY.md step 2 says the key must be the one that wrote the values.
  - My probe: a legacy row under a key that is configured only as retired was refused, by id, with
    nothing changed.
- **A damaged row blocks the whole upgrade.** That is deliberate, but DEPLOY.md says "fix … the
  rows" without saying how. The operator can only roll back or ask for help. This needs a human
  decision: accept it, or document a procedure such as quarantining the row.
- **D-5 window closed.** On my stack:
  - the new backend at schema 0009 returned **500** for the list as both patient and doctor, and for
    `/clinical-entries/{id}/attachments`;
  - after `db-migrate` it returned **200**, and the API hashes for 315 of 315 entries were identical
    before and after.

### Verification run (QA, 2026-11-01)

| Command | Result |
|---|---|
| `uv run pytest tests/db/test_migration_0010_key_id.py tests/db/test_migration.py -v` | 14 passed |
| `uv run pytest --cov=app --cov-fail-under=85` | 1184 passed, 4 skipped, 94.06 % |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `ruff check .`, `black --check .`, `mypy app` | clean (251 files; 131 source files) |
| `cd infra && python3 -m unittest discover -s tests` | 78 passed |
| QA probe, 7 tests: bytes, colon, mixed, downgrade refusals, lock, SIGKILL, throughput | 7 passed |
| Mutations: `strip()` / NFC / no lock, against the developer's tests | 12 passed each (not detected); probe fails each |
| Traceability on TASK-194, TS-008, PRB-004, PRB-062, SR-022 (`trace.py`) | 0 errors, 19 warnings (W5/W6 on records outside this task) |

Rehearsal, scratch projects `qa194` and `qa194r`:
1. **Old layout.** `git archive 284e7e6`, with a new random scratch env.
   - Seeded 300 entries through the API and 15 tricky legacy rows through the old ORM type, 315 in all.
   - Before: 315 legacy, `0009`, and a per-row SHA-256 record.
   - Then `pg_dump -Fc` and `stop`.
2. **New tree under the same project.**
   - `up db-migrate` without `--build`: exit 0, still `0009` (PRB-062).
   - New backend started: list and attachments returned 500 (D-5).
   - `up -d --build`: 315 converted, `0010`.
   - The per-row SHA-256 matched for 315 of 315, the API before and after matched for 315 of 315,
     and the tricky rows were byte-identical through the API.
   - `up --build db-migrate` again: no conversion, column MD5 unchanged (`54e18e9b…`).
   - A new write was stored as `mh1:k1:`.
   - Smoke from the scratch tree: **64 passed, 0 failed**.
   - No description text in any service log.
3. **Restored copy, `qa194r`.**
   - Wrong key: container exit 1 (Compose exit 0, see finding 3); 315 named; no description text in
     the log; column MD5 and `0009` unchanged.
   - One damaged row with the right key: exit 1, naming only that id, nothing changed.
   - Row restored, then the right key: 315 converted, and the per-row SHA-256 digest equals the one
     from before the upgrade.
4. **Teardown.**
   - `down -v --remove-orphans` for both projects, and the `qa194*` images removed.
   - Volume list identical to the one before the run; no `qa194*` containers or networks left.
   - `peaceful_pike` was not touched.
   - `infra/.env` SHA-256 `a4933b8c…696da` before and after.

### For round 2

- Findings 1 to 5.
- If the human agrees, the PRB-062 fix and the `resolves` link on CR-004.
- Not blocking: a human decision on how to handle a damaged row, and, separately, on SR-012
  trimming.

## Round 2 (software developer, 2026-11-01): QA round-1 findings 1 to 5 addressed

Status `draft` -> `in_review`, version 1.2. No code change to the migration. Human decisions are in CR-004 D-7
(1.5); the migration was not touched, the changes are tests, DEPLOY.md, the smoke test and records.

| Finding | Change |
|---|---|
| 1 MEDIUM byte preservation | `test_plaintext_is_preserved_byte_for_byte_through_upgrade_downgrade_upgrade` in `backend/tests/db/test_migration_0010_key_id.py`: 15 plaintexts (QA's list, 200 kB instead of 1 MB), inserted directly in the earlier format, upgrade -> downgrade -> upgrade, compared as `.encode()` bytes at each step (downgrade read with an independent legacy decrypt) |
| 2 LOW table lock | `test_migration_holds_a_table_lock_that_blocks_writers_but_not_readers`: the migration is held inside its second batch; a reader gets all 700 rows, an INSERT under `lock_timeout = 1s` fails with a lock timeout |
| 3 LOW exit codes | `infra/DEPLOY.md`: all four `db-migrate`-alone commands (section 6, owner-upgrade step 3, migration 0010 step 3, and the explanation) use `up --build --exit-code-from db-migrate db-migrate`; new `infra/tests/test_deploy_db_migrate_commands.py` fails if a line lacks either flag |
| 4 LOW PRB-062 | Impact corrected (falsely green step 3; section 6 alone), "caught by the smoke test" replaced, Resolution written, status `resolved` (1.1); `infra/smoke-test.sh` checks `alembic_version` equals the tree's head revision |
| 5 LOW wording | Rehearsal step 3 now says `strip()` on both ends, older than CR-004, accepted |
| D-7 damaged rows | `infra/DEPLOY.md` "A row that does not decrypt (migration 0010 refused)": back up, take the ids from the error, check the key first, then restore from a backup or quarantine (copy to a table, record clinically, only then delete), re-run. No tooling added |

Mutations, on a scratch edit of `_run` restored afterwards (the working file was diffed against the saved copy):

| Mutation | Result |
|---|---|
| `encode(plaintext.strip())` | the byte-preservation test fails (1 failed, 13 passed); the migration's own read-back check also refuses the row |
| `encode(unicodedata.normalize("NFC", plaintext))` | the byte-preservation test fails (1 failed, 13 passed) |
| `_lock(bind)` removed | the lock test fails (1 failed, 13 passed) |
| `--exit-code-from db-migrate` removed from one DEPLOY.md line | the infra test fails |

Smoke check verified on a scratch stack (`task194s`, empty database, removed afterwards; volumes, containers, networks
and images as before; `infra/.env` SHA-256 unchanged, a4933b8c...c696da): at 0010, 65 passed, 0 failed; with
`alembic_version` set to 0009, the new check failed (64 passed, 1 failed).

Verification, round 2:

| Command | Result |
|---|---|
| `uv run pytest tests/db/test_migration_0010_key_id.py tests/db/test_migration.py -q` | 16 passed |
| `uv run pytest --cov=app --cov-fail-under=85` | 1186 passed, 4 skipped, 94.06% |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `ruff check .`, `black --check .`, `mypy app` | clean |
| `cd infra && python3 -m unittest discover -s tests` | 80 passed |

DEPLOY.md consistency: `grep -n "up .*db-migrate" infra/DEPLOY.md` shows three command lines (250, 291, 326), all with
both flags; the prose that mentions exit codes (step 3 of the owner upgrade, "exit code 0"; the migration 0010 text,
"exit code 1 (with `--exit-code-from`)") matches what Compose returns with the flag.

## QA review round 2 (QA engineer, 2026-11-01): CHANGES REQUESTED

Status `in_review` → `draft`. TS-008 1.8 stays `in_review`.

All five round-1 findings are closed, and the code, the tests, the smoke check and PRB-062 are
fine. One finding is open: the new damaged-row procedure tells the operator to hard-delete a
clinical entry, and its "record the loss through the application" step can't be carried out at the
point where it appears.

### Round-1 findings, re-checked

1. **Closed.** `test_plaintext_is_preserved_byte_for_byte_through_upgrade_downgrade_upgrade` fails
   under my `strip()` and NFC mutations. My probe also passes against the current code (7 of 7).
2. **Closed.** `test_migration_holds_a_table_lock_that_blocks_writers_but_not_readers` fails when
   `_lock` is removed. It also fails when the mode is changed to `ACCESS EXCLUSIVE`, but only after
   about 30 s (see R2-3).
3. **Closed.** Every command that runs `db-migrate` alone is
   `up --build --exit-code-from db-migrate db-migrate` (lines 250, 291, 326), and the prose matches
   what Compose actually does. I checked on scratch project `qa194c` (Compose v2.20.2):
   - With a damaged row it exits **1**.
   - It exits **0** on a running stack. All 8 running containers kept running: the "Aborting on
     container exit" message stopped only `db-migrate`, so "re-run at any time" holds.
   - `infra/tests/test_deploy_db_migrate_commands.py` passes, and its regex doesn't match the
     `up -d --build` or `logs` lines.
4. **Closed.** PRB-062 1.1 is accurate: the impact is corrected, the smoke claim is gone, and it is
   `resolved` with the `resolves` link on CR-004 1.5. The smoke check works:
   - 65 passed at 0010;
   - with `alembic_version` forced to 0009: `[FAIL] the database is at the head migration: database
     at '0009', this tree's head is '0010'`, 64/1.
5. **Closed.** The wording now says "`strip()`, which trims both ends".

### Round-2 findings

1. **MEDIUM: the damaged-row procedure hard-deletes a clinical record with no audit trail, and one
   of its steps can't be performed.** Location: `infra/DEPLOY.md:362-372` ("Quarantine").
   - **No audit record.** The `DELETE FROM clinical_entry` runs as the owner in `psql`. The audit
     trail is written by the application only, and `clinical_entry` has no trigger, so `audit_log`
     never records the deletion.
   - **Against the requirements.** The application itself has no delete path for clinical entries.
     Erasure re-keys clinical data and keeps it. SR-024 AC 4 says retained clinical records are
     "not silently deleted", and SR-012 AC 4 says a saved entry stays retrievable in the patient's
     history.
   - **The "record the loss" step is impossible at that point.** While 0010 refuses, the
     application can't run. On `qa194c`, after a refusal, `up -d --build` exited 1 with
     `service "db-migrate" didn't complete successfully` and the backend never started, because of
     `depends_on: service_completed_successfully`. The only route would be to roll back to the
     previous release. Recording the loss also needs a doctor with consent for that patient (a new
     entry); an operator can't do it.
   - **Attachments.** `fk_attachment_clinical_entry_id` is `NO ACTION` (`confdeltype a`), so the
     `DELETE` fails for an entry with attachments. The procedure then leaves the outcome to "the
     responsible person". Without a delete there would be no orphan objects to manage.
   - **The quarantine table.** If it is created in `public`, the next `db-migrate` grants the
     runtime role `SELECT, INSERT, UPDATE, DELETE ON ALL TABLES` on it (`app/db/roles.py:82`), and
     erasure (SR-024) doesn't know it exists.
   - **The restore step.** Its `UPDATE` is also outside the audit trail. That is acceptable, because
     it puts the original value back, but it should be recorded.
   - **Fix: wording only, consistent with D-7 (no code change).**
     - Never `DELETE` a `clinical_entry`.
     - Open a problem report for every damaged row (§9), and record there every manual `UPDATE`
       (the restore or the placeholder), since the audit log doesn't see them.
     - Options, in order:
       - (a) restore the value from a pre-damage backup, as written now;
       - (b) if there is no good copy, stay on, or roll back to, the previous release until the
         responsible person decides;
       - (c) if they decide to go on without the text: keep the damaged value outside the
         application schema (a `pg_dump -t` of the row, or a schema the runtime role is not
         granted), then replace the value with a placeholder encrypted under the current key. The
         placeholder can come from the existing code, for example
         `docker compose -f infra/docker-compose.yml run --rm --no-deps --entrypoint python db-migrate -c "from app.db.crypto import encrypt; print(encrypt('[Original text unreadable since <date>; see <PRB id>]'))"`
         (rehearse this on a copy first). Then `UPDATE … SET description = '<that value>'`.
         0010 skips the `mh1:` value. The row, its attachments and its place in the history are
         kept, and clinicians see that the text was lost.
     - Once the stack is up, a doctor adds a clinical note if one is clinically needed.
2. **LOW: the smoke check derives the head from the files with an `awk` that only understands
   `revision = "…"`.** Location: `infra/smoke-test.sh:320-324`. I ran the same awk over synthetic
   files:
   - **Merge** (`down_revision = ("a", "b")`): it prints two heads, so the check fails although the
     database is correct. This fails closed.
   - **Alembic's typed template** (`revision: str = '0011'`): the file isn't seen at all, so a
     skipped 0011 would **pass**.
   - Every file today uses `revision = "…"` and the repo has no `script.py.mako`, so this is LOW.
   - Fix: count `versions/[0-9]*.py` and fail when the number of revisions found differs, or when
     there is more than one head. Or take the head from `alembic heads` in the `db-migrate` image.
     Can be carried to TASK-201.
3. **LOW: the lock test's reader has no timeout.** Location: the `SELECT` in
   `test_migration_holds_a_table_lock_that_blocks_writers_but_not_readers`. If the lock blocked
   readers, the `SELECT` would wait for the 30 s gate before the test failed. Fix: run
   `SET statement_timeout = '3s'` before the `SELECT`. Can be carried.

### Verification run (QA, round 2)

| Command | Result |
|---|---|
| `uv run pytest tests/db/test_migration_0010_key_id.py tests/db/test_migration.py -v` | 16 passed |
| `uv run pytest --cov=app --cov-fail-under=85` | 1186 passed, 4 skipped, 94.06 % |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `ruff check .`, `black --check .`, `mypy app` | clean (251 files; 131 source files) |
| `cd infra && python3 -m unittest discover -s tests` | 80 passed |
| QA probe (bytes, colon, mixed, downgrade refusals, lock, SIGKILL, throughput) | 7 passed |
| Mutations: `strip()` / NFC / no lock / `ACCESS EXCLUSIVE` | each makes 1 test fail (byte, byte, lock, lock) |
| Traceability: TASK-194, TS-008, PRB-004, PRB-062, CR-004, SR-022 | 0 errors, 30 warnings (W1 SR-043, W5/W6 outside this task) |

Scratch stack `qa194c` (current tree, round-1 `pg_dump` with 315 legacy rows):
1. Damaged row:
   - the `db-migrate` command exited 1;
   - `up -d --build` exited 1 and the backend did not start.
2. Row repaired: `up -d --build` exited 0 and the database reached 0010.
3. Re-run on the running stack: exited 0, and the same 8 containers were still running.
4. Smoke: 65/0 at the head, 64/1 at a forced 0009.
5. Teardown: `down -v --remove-orphans` and the `qa194*` images removed. The volume list is the same
   as before; `peaceful_pike` was not touched; `infra/.env` SHA-256 `a4933b8c…696da` before and
   after.

### For round 3

- R2-1 (DEPLOY.md text only).
- R2-2 and R2-3 may be fixed now or carried.
- The code, the tests and the other records need no change. The AC and DoD items stay unticked
  until approval.

## Round 3 (software developer, 2026-11-01): QA round-2 findings addressed

Status `draft` -> `in_review`, version 1.3. No change to the migration.

| Finding | Change |
|---|---|
| 1 MEDIUM damaged-row procedure | `infra/DEPLOY.md` "A row that does not decrypt" rewritten: never `DELETE` a `clinical_entry`; a PRB for every damaged row recording every manual change (direct SQL is not in `audit_log`); options (a) restore from a pre-damage backup, (b) stay on or roll back to the previous release, (c) only on the responsible person's written decision: keep the damaged value in a file outside the schema (no table in `public`), replace it with a placeholder encrypted under the current key, `db-migrate` skips `mh1:` values; a doctor adds a note afterwards. Documentation only (CR-004 D-7) |
| 2 LOW smoke head detection | New `infra/alembic-head.sh` (used by `smoke-test.sh`): accepts `revision = "x"`, `revision: str = 'x'` and a tuple `down_revision`; fails if there is not exactly one head or if the revisions found differ in number from the migration files. New `infra/tests/test_alembic_head.py` with synthetic directories: plain, typed and single-quoted, a merge (one head), two heads (fails), an unreadable revision (fails), and the real directory |
| 3 LOW lock test | `SET statement_timeout = '3s'` before the reader's SELECT |

The head is read from the source files, not from `alembic heads` in the `db-migrate` image: a stale image would report the old
head and the check would go green exactly when it must fail (PRB-062).

### Option (c) rehearsal (scratch project `task194c`, removed afterwards)

1. Stack up at 0010 (empty), a doctor, a patient and consent, entry E1 with an attachment (`flow191.py`) and a second entry through the API.
2. E1's `description` set to a non-envelope value and `alembic_version` set to 0009.
3. `up --build --exit-code-from db-migrate db-migrate`: **exit 1**, `1 clinical_entry.description value(s) ... row ids: <E1>`, the damaged text appears nowhere in the output.
4. Damaged value written to a file (outside the schema); the placeholder command of the procedure printed one `mh1:k1:` line; `UPDATE` of E1.
5. `up --build --exit-code-from db-migrate db-migrate`: **exit 0**, `alembic_version` 0010, 2 of 2 rows `mh1:k1:`, E1 still has its 1 attachment row.
6. `up -d --build`, then through the API as the doctor: both entries listed, E1 returns the placeholder text, the attachment downloads byte-identical, the other entry is unchanged; smoke test 65 passed, 0 failed (including the head check, 0010).
7. `down -v --remove-orphans`, `task194*` images removed: volumes, containers and networks identical to the start; `infra/.env` SHA-256 a4933b8c...c696da unchanged; `peaceful_pike` untouched.

### Verification, round 3

| Command | Result |
|---|---|
| migration tests (`test_migration_0010_key_id.py`, `test_migration.py`) | 16 passed |
| `uv run pytest --cov=app --cov-fail-under=85` | 1186 passed, 4 skipped, 94.06% |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `ruff check .`, `black --check .`, `mypy app` | clean |
| `cd infra && python3 -m unittest discover -s tests` | 85 passed |

### The procedure as it now stands in DEPLOY.md

### A row that does not decrypt (migration 0010 refused)

`db-migrate` printed `migration 0010 upgrade refused: N clinical_entry.description value(s) do not
decrypt with the current key` and row ids, and exited 1. Nothing was changed. While it refuses, `backend`,
`celery-worker` and `celery-beat` do not start (they wait for `db-migrate` to complete), so the
application cannot be used to repair or annotate anything. This is a manual procedure: the repository
has no tool for it, and the SQL below is run with `psql` as the owner. **Direct SQL is not written to
`audit_log`**, which only the application writes.

**Never `DELETE` a `clinical_entry`.** The application has no path that deletes one (SR-012 AC 4,
SR-024 AC 4), a delete is not audited, and it fails for an entry that has attachments.

1. Back up first (volume copy and `pg_dump -Fc`) and keep the `db-migrate` output. It lists the first
   100 ids; if N is larger, fix those and run again to get the next ones.
2. **Check the key settings before suspecting the rows.** A wrong or swapped `AT_REST_ENCRYPTION_KEY`
   makes every unconverted row fail, so N equal to the number of unconverted rows points at the key.
   Compare with the key that was in `infra/.env` when the rows were written (an old copy of `.env`, a
   secret store). With the right key, run the `db-migrate` command again.
3. If only some rows are named, the stored value was damaged after it was written (a partial restore, a
   manual edit, a disk fault). **Open a problem report (PRB, IEC 62304 §9) for every damaged row.** Record
   in it the row id, the `db-migrate` output, the cause if known, the decision taken, and **every manual
   change** you make (each `UPDATE`, with the date, who ran it and the old and new value's SHA-256),
   because `audit_log` does not see them.
4. Then, in this order:
   - **(a) Restore the value from a backup taken before the damage.** Restore that backup to a scratch
     database, copy that one value into the live row (`UPDATE clinical_entry SET description = '<value>'
     WHERE id = '<id>'`), note it in the PRB, and run `db-migrate` again. The value may be in either
     format (the migration converts the earlier one; a value in `mh1:` form must name a configured key),
     and it must decrypt with the key of step 2.
   - **(b) No good copy exists: stay on, or roll back to, the previous release** (restore the step-1
     volume copy if the new release has already changed data) until the responsible person decides what
     to do. Do not continue the upgrade meanwhile.
   - **(c) Only if the responsible person decides in writing to go on without the text** (record the
     decision in the PRB):
     1. Keep the damaged stored value outside the application schema. For example, write it to a file in
        the backup set: `docker compose -f infra/docker-compose.yml exec -T postgres sh -c 'psql -U
        "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT id, description FROM clinical_entry"' | grep
        '^<id>|' > damaged-<id>.txt`. Do **not** create a table for it in `public`: the next
        `db-migrate` grants the runtime role access to every table there, and erasure (SR-024) does not
        know the table.
     2. Produce a placeholder encrypted under the current key (it prints one `mh1:<id>:...` line):
        `docker compose -f infra/docker-compose.yml run --rm --no-deps -T --entrypoint python db-migrate
        -c "from app.db.crypto import encrypt; print(encrypt('[Original text unreadable since <date>;
        see <PRB id>]'))"`.
     3. `UPDATE clinical_entry SET description = '<that line>' WHERE id = '<id>'`, and note it in the PRB.
     4. Run the `db-migrate` command again. It skips values that start with `mh1:`, so the row, its
        attachments and its place in the patient's history are kept, and the application shows the
        placeholder text.
5. Once the stack is up, a doctor with consent for that patient can add a clinical note about the lost
   text if it is needed. An operator cannot do that.

## QA review round 3 (QA engineer, 2026-11-01): APPROVED

Status `in_review` → `approved`; TS-008 1.9 `in_review` → `approved`. The acceptance criteria and
both DoD items are ticked. The ask-first item rests on the human's approval of the 0010 rehearsal,
recorded in CR-004 D-7. Two LOW items are carried below; neither blocks approval.

### Round-2 findings, re-checked

1. **R2-1 closed.** The damaged-row procedure now protects the clinical record.
   - **No `DELETE`, and the warnings are in place.** The procedure forbids it, warns that direct SQL
     is not audited and that the application is down while 0010 refuses, opens a PRB per row, and
     records every manual change with its SHA-256. Option (c) needs a written decision.
   - **No delete path in the application.** I checked this myself:
     - No caller deletes a `ClinicalEntry`. The only `session.delete` calls are group memberships
       (`group_repo.py:45`) and anonymised datasets (`retention_tasks.py:58`).
     - The `DELETE` routes are group members, consents and accounts.
     - Account deletion is a soft change to `status` and `email` (`erasure.py`).
     - No `ondelete` or cascade in `app/db`, and no clinical deletes in `scripts/` or `modules/`.
   - **SQL safety.** Option (a)'s pasted value is the stored ciphertext, which is base64url with no
     `'` (checked: 0 characters outside the alphabet). Option (c)'s pasted value is an `mh1:` line.
     The placeholder text sits inside a Python literal; an apostrophe in it breaks the Python command,
     not the SQL.
   - **The 100-id loop ends.** Each run lists the first 100 failing ids in id order. Every fixed row
     either decrypts or is `mh1:`, so it leaves the set. A row that isn't fixed reappears, so a lack
     of progress is visible.
2. **R2-2 closed.** I ran `infra/alembic-head.sh` on the repo and on synthetic files:
   - repo: `0010`;
   - the earlier false green, a typed single-quoted `0011`: now `0011`;
   - two heads: rc 1;
   - a tuple merge: one head;
   - a single-quoted 1-tuple: correct;
   - an unparsable `revision = REVISION_ID`: rc 1 ("found 15 revisions in 16 files");
   - a quoted comment: correct;
   - an empty or missing directory: rc 1.

   It also works under mawk 1.3.4 (Debian, in a throwaway `postgres:16` container), as well as under
   macOS awk. The 5 tests in `infra/tests/test_alembic_head.py` pass.
3. **R2-3 closed.** The reader has `statement_timeout = '3s'`. The `ACCESS EXCLUSIVE` mutation now
   fails the lock test in 6 s, not 36 s. Removing `_lock` still fails it.

### Carried (LOW, not blocking; for TASK-201 or the next DEPLOY.md edit)

- **C-1. The export file in option (c)1.** The command writes `damaged-<id>.txt` to the current
  directory, normally the repository checkout, which `.gitignore` doesn't cover. With umask 022 the
  file is `-rw-r--r--` (seen in my run). The text doesn't say that the file holds the stored
  *ciphertext* only, not plaintext. That ciphertext should still be treated as PHI, because it may
  become readable if the right key turns up. Fix:
  - say that it holds the ciphertext;
  - write it into the backup location with `umask 077`;
  - record its SHA-256 in the PRB.
- **C-2. Option (a) with a value in `mh1:` form.** The procedure says to run `db-migrate` again to
  check that the restored value decrypts. 0010 doesn't check `mh1:` values (it skips them), so such
  a value that fails its tag would pass `db-migrate` and then fail on read. A backup taken before
  0010 is always in the earlier format, so this only arises with a later backup. Fix: check by
  reading the entry through the API once the stack is up.

### Verification run (QA, round 3)

| Command | Result |
|---|---|
| Migration tests | 16 passed |
| Full suite with coverage | 1186 passed, 4 skipped, 94.06 % |
| DICOM | 25 passed |
| ruff, black, mypy | clean |
| infra | 85 passed |
| Mutations: `ACCESS EXCLUSIVE` / no lock, with the current test file | lock test fails (6 s / 3 s) |
| Traceability: TASK-194, TS-008, PRB-004, PRB-062, CR-004, SR-022 | 0 errors, 30 warnings (outside this task) |

Rehearsal of the procedure, scratch project `qa194d` on the current tree. I started from the
round-1 dump: 315 rows in the earlier format, at 0009.

1. **Refusal.** I damaged rows A and B. The `db-migrate` command exited 1, named both ids, and
   changed nothing.
2. **Option (a) on A, as documented.**
   - `createdb restore_scratch` and a `pg_restore` of the pre-damage dump into it.
   - I copied the one value and ran `UPDATE` with it pasted (SHA-256 of the stored value
     `65142a27…` → `9270c9d4…`), then `dropdb`.
3. **Option (c) on B, with the documented commands verbatim.**
   - The export wrote one line (mode 0644, see C-1).
   - The placeholder command printed exactly one `mh1:k1:` line and nothing on stderr.
   - Then the `UPDATE`.
4. **Result.** `db-migrate` exited 0 (314 converted, version 0010). Through the API, A came back
   identical to before the damage, B returned the placeholder, and the other 313 entries were
   identical.
5. **Option (c) with an attachment on entry C.**
   - I uploaded a 102,400-byte attachment (SHA-256 `27783e87…`), stopped the application services,
     damaged C and forced version 0009.
   - `db-migrate` refused, naming C only. Then export, placeholder and `UPDATE`.
   - `db-migrate` exited 0 at 0010, with 315 entries and the attachment row kept.
   - After `up -d --build`, the attachment downloaded with the same SHA-256 and C showed the
     placeholder.
   - Smoke: **65 passed, 0 failed**, including "the database is at the head migration (0010)".
6. **Teardown.** `down -v --remove-orphans` and the `qa194*` images removed. The volume list is the
   same as before, and no `qa194*` container or network is left. `peaceful_pike` was not touched.
   `infra/.env` SHA-256 `a4933b8c…696da` before and after.
