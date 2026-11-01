---
id: "TASK-195"
type: task
title: "Key rotation: re-encryption command, documented procedure, rehearsal on a backup copy"
status: approved
version: "1.4"
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
  - target: "TASK-194"
    relation: relates_to
  - target: "ADD-016"
    relation: relates_to
tags: ["security", "encryption", "cr:CR-004", "control:protective", "control:information", "ask-first"]
---

# TASK-195 — Key rotation: re-encryption command, documented procedure, rehearsal on a backup copy

- **Software item / unit:** SI-PERSIST `U-PER-Crypto` (ADD-016); `infra/DEPLOY.md`.
- **PRB:** PRB-004 (last task). **CR:** CR-004.
- **Depends on:** TASK-194.
- **Branch:** `fix/review-2026-07-security`. Its own commit.
- **Size:** M (new `backend/app/db/reencrypt.py`; `infra/DEPLOY.md`; 1 test file; TS-008)
- **Needs:** a Docker host; a restored backup copy of a populated development database.
- **Boundary (CR-004 "Ask first"):** a rotation changes stored values. The rehearsal runs on a
  copy only.

## Objective

SR-022 AC 8: the deployment guide describes a rotation (add a new current key, re-encrypt or keep
reading old values, retire the old key), rehearsed against a backup copy of a populated database,
result recorded in a test report.

## Implementation detail

1. `python -m app.db.reencrypt --check`: counts encrypted values per key id across every
   `EncryptedString` column (discovered from the models, so a future column is covered); exit 1
   if any value names a key that is not configured or is unprefixed.
2. `--apply [--batch-size N]`: for each value whose key id is not current, decrypt, encrypt under
   the current key, write, re-read and compare before commit; commit per batch; idempotent and
   resumable. Output names counts and key ids only.
3. `infra/DEPLOY.md` "Field-encryption key rotation": back up the database (and note PRB-057); add
   the new key as current with a new id and move the old one to
   `AT_REST_ENCRYPTION_RETIRED_KEYS`; restart; `--apply` (from `db-migrate`'s image, owner or
   runtime role); `--check` shows only the current id; remove the retired key; restart. Includes
   what to do if `--check` fails (keep the retired key; nothing is lost).

## Tests (write first)

`backend/tests/db/test_reencrypt.py` (real database):

- rows under key A; rotate to B with A retired; `--check` shows A; `--apply`; all rows under B and
  readable; `--check` exit 0;
- remove A before `--apply` → reads of those rows raise `UnknownKeyError`, `--check` exit 1, and
  adding A back restores them (nothing was modified);
- interrupted `--apply` (fault injected after the first batch) → rerun completes; no row lost.

## Acceptance criteria

- [x] SR-022 AC 8: the procedure is in `infra/DEPLOY.md` and its command is tested
      (`backend/tests/db/test_reencrypt.py`).
- [x] SR-022 AC 8: the rotation is rehearsed on a restored backup copy of a populated database:
      per-row plaintext checksums equal before and after, `--check` clean, the old key retired,
      API reads of clinical entries succeed (rehearsal record for the next TR).

## Verification

```sh
cd backend && uv run pytest tests/db/test_reencrypt.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

## Records

- **TS-008**: TC-008.11 (command, procedure, rehearsal), `verifies` SR-022.
- Rehearsal record for the next TR (CR-004 Verification approach).
- **PRB-004**: `## Resolution` (TASK-193..195), `resolved`.

## Definition of Done

- [x] Tests pass; rehearsal recorded and presented to the human.
- [x] TS-008 `in_review` (approved by QA); PRB-004 `resolved`.
- [x] `traceability-check` shows no error for TASK-195, TS-008, SR-022, PRB-004.

## Implementation notes (2026-11-01, software developer)

Handed to QA as `in_review`. No checkbox is ticked.

### Files

- New: `backend/app/db/reencrypt.py`, `backend/tests/db/test_reencrypt.py`.
- Changed: `infra/docker-compose.yml` (last step of `db-migrate`), `infra/tests/test_compose_db_roles.py`
  (order of the four steps), `infra/DEPLOY.md` (new "Field-encryption key rotation", two table cells,
  pointers in the 0010 and damaged-row sections, rehearsal record).
- Records: TS-008 1.10 (`in_review`, TC-008.11), PRB-004 1.5 (interim note, still `open`), this task.

### The command

`python -m app.db.reencrypt`, run in the `db-migrate` image as the owner (`DATABASE_OWNER_URL`):

| Mode | Behaviour | Exit |
|---|---|---|
| `--check` | read only; decrypts every value; counts per key id | 0 all under the current key; 3 readable, some under a retired key; 1 unconfigured key id or does not decrypt (row ids listed) |
| `--apply [--batch-size N]` | refuses before any write if `--check` would exit 1; then per batch one transaction: `LOCK TABLE ... SHARE ROW EXCLUSIVE` (0010's lock) with a 10 s `lock_timeout`, decrypt, encrypt with the current key, decrypt the new value and compare, update, read the batch back from the database and compare, commit; counts per key before and after | 0 / 1 |
| `--verify-key-ids` | read only, no decryption; refuses a stored key id that is not configured | 0 / 1 |

- Columns come from `Base.metadata` (every `EncryptedString` column, single-column key); the SQL uses a
  plain `String` table so the ORM type does not encrypt or decrypt on its own.
- Output: counts, key ids, table and column names, row ids (first 100). A database error is reduced to its
  class name and the engine hides statement parameters, so no value, ciphertext or key reaches output.
- Resumable: each batch commits alone; a crash leaves every row readable (current or retired key); a re-run
  continues; with nothing to convert it takes no lock and writes nothing.
- Needs no application stop: the lock is per batch and the backend writes under the current key after the
  restart of step 4. DEPLOY.md says to restart first and to run `--check` after (a straggler shows as exit 3).

### Decisions for the human

1. **Guard in `db-migrate` (kept, small, easy to veto).** `python -m app.db.reencrypt --verify-key-ids` is
   the last step of the `db-migrate` command. A retired key removed while values still name it now stops the
   start-up with the count and row ids instead of leaving 500s on clinical reads. Cost: the refusal takes the
   application down (Compose stops `backend`, the workers and the proxy before re-running `db-migrate`)
   until the entry is put back (rehearsed: 19 s to recover, data unchanged). It checks key ids only (no
   decryption, so it is cheap at every start) and ignores damaged or non-envelope values, which 0010 and
   `--check` own. To drop it, remove the one line in the compose command and the one entry in the infra test.
2. **Exit code 3 for "readable, rotation pending"** goes beyond the task text (which defines 0 and 1), so the
   step "verify nothing is under the old key" is a command's exit code and not a reading of the output.
3. **PRB-004 is left `open`.** The task text says `resolved`; CR-004 (Scope, Out of scope) says only the
   human changes a PRB to `resolved` or `closed`. The two conflict; the CR is the approved record.
4. **Blocking dependency on TASK-196.** `WEED_S3_SSE_KEY` is `${AT_REST_ENCRYPTION_KEY}` in the shipped
   Compose file. Replacing the field key therefore replaces the object store's SSE key and every
   attachment answers 500 (observed in the rehearsal, undone by putting the key back). DEPLOY.md forbids
   the procedure until the keys are separate and gives the check. The rehearsal used a scratch copy of the
   Compose file with `WEED_S3_SSE_KEY: ${OBJECT_STORE_SSE_KEY}`, which is what TASK-196 will ship. Either
   TASK-196 lands before this task's procedure is used, or the human accepts the warning as it stands.

### Records the human must change (approved, not edited here)

- ADR-0018 (Rotation): `--check` also exits 3 for a pending rotation; there is a third mode `--verify-key-ids`
  and `db-migrate` runs it; the batch lock and `lock_timeout`; `--apply` is run with `run --build`, and a
  premature removal stops the application.
- ADD-016 (U-PER-Crypto) and ADD-026 (SI-DEPLOY, `db-migrate` steps): the new unit `app.db.reencrypt` and the
  fourth `db-migrate` step; arc42 via TASK-201.
- RISK-011 / RISK-007: control description may cite the command, the guard and the rehearsal; scores unchanged
  (RISK-011 stays 3 x 2 until PRB-057).
- SR-022 AC 8 is met by the procedure, tests and rehearsal below; no change to the SR text is needed.

### Acceptance criteria to evidence

| AC | Evidence |
|---|---|
| SR-022 AC 8: the procedure is in `infra/DEPLOY.md` and its command is tested | DEPLOY.md "Field-encryption key rotation"; `backend/tests/db/test_reencrypt.py` (25 tests); `infra/tests/test_compose_db_roles.py` |
| SR-022 AC 8: rehearsed on a restored backup copy; per-row checksums equal; `--check` clean; old key retired; API reads succeed | Rehearsal record below; DEPLOY.md rehearsal paragraph |

### Verification results

- `cd backend && uv run pytest tests/db/test_reencrypt.py -v`: 21 passed.
- `cd backend && uv run pytest --cov=app --cov-fail-under=85`: 1207 passed, 4 skipped; coverage 94.13%.
- `cd backend && uv run pytest modules/dicom_viewer/tests`: 25 passed.
- `cd backend && uv run ruff check . && uv run black --check . && uv run mypy app`: clean (253 files; 132 source files).
- `cd infra && python3 -m unittest discover -s tests`: 85 tests OK.
- Negative controls (each on `backend/app/db/reencrypt.py`, reverted): a row skipped in every batch, 4 failures
  (rotation, counts, large batch, mid-batch); in-memory read-back compare dropped, 1 failure; database read-back
  compare dropped, 1 failure; both dropped, 2; pre-write refusal dropped, 3 failures (old key removed, unknown
  key in a late row leaves no write, wrong-key or damaged rows). `--verify-key-ids` removed from the compose
  command: the infra order test fails.

### Rehearsal record

Scratch Compose projects `task195` and `task195r`, env files in the session scratchpad, `infra/.env` SHA-1
`714c7630962b01799b6b8ac467859d06095b0b64` before and after. See the "Rehearsal result (TASK-195, ...)"
paragraph in `infra/DEPLOY.md` for steps and counts; the per-row hash script ran in a backend container with
`AESGCM` and the environment keys only, and printed counts and no plaintext. Teardown: `down -v
--remove-orphans` on both projects, the project images and the untagged images created during the builds
removed; volume, container and network lists equal to the start (`peaceful_pike` untouched).

## QA review — round 1 (2026-11-01): CHANGES REQUESTED

Status returned to `draft`. No data defect was found: the command is correct, and QA's probes and
rehearsal confirm it. Round 1 asks for a missing regression test of the concurrency property and for
corrections to the operator text. The human decisions taken during this review are CR-004 D-8: the
`--verify-key-ids` guard stays in `db-migrate`, and QA approval may set PRB-004 to `resolved`.
Decision 3 above is therefore settled: on approval, PRB-004 goes to `resolved`, with a Resolution
covering TASK-193, 194 and 195.

### Findings

1. **MEDIUM. No test proves that a batch reads its rows under the lock.**
   - Where: `backend/tests/db/test_reencrypt.py:453` (lock test) and `backend/app/db/reencrypt.py:255-257`.
   - The problem: QA swapped the `LOCK TABLE` and the batch `SELECT` in `_convert_batch` (select first,
     then lock). All 21 tests still pass. With that order, a write committed between the select and the
     lock is overwritten with the converted *old* plaintext. QA's probe shows it: an uncommitted
     `UPDATE` holds the row while `--apply` starts, and after the commit the row reads `old 7` instead of
     the writer's `NEW CLINICAL CONTENT`. The existing lock test checks that writers wait *during* a
     batch, which is necessary but not sufficient.
   - Exposure today: none. The current code locks first, and the application has no update path for
     `clinical_entry.description` (it only inserts, under the current key). But DEPLOY.md's "the
     application does not need to be stopped" depends on this property, and a refactor could silently
     break it.
   - Fix: add a test in which a second connection runs, without committing,
     `UPDATE clinical_entry SET description = <new value under the retired key> WHERE id = X`. Start
     `apply` in a thread with a `batch_size` that covers every row, so that X is in the first batch.
     Wait until the thread is blocked on the lock (for example `pg_locks` with `granted = false`), commit
     the writer, join the thread, and assert that X decrypts to the writer's plaintext.
     - Add a second case that commits the write from a wrapper around `_convert_batch`, before the real
       call, so it lands between the pre-scan and the batch.
     - Record in TC-008.11 that the select-before-lock mutation makes the test fail.
     - QA's probe file can be copied:
       `/private/tmp/claude-501/-Users-carlos-santiago-Dev-prototypes-medhub-01/5c7e8dc5-718b-47ba-8cc3-56d00d5b341a/scratchpad/qa195/probe/test_qa195_probe.py`
       (`test_concurrent_writer_committing_after_prescan_is_not_overwritten`,
       `test_writer_commit_between_prescan_and_batch`).
2. **LOW. The exit-1 text says "changed nothing", which is false for `--apply` after its first batch.**
   - Where: `infra/DEPLOY.md:451` (table cell "1 refused or failed, the failing batch was rolled back")
     and `infra/DEPLOY.md:510` ("It names the key id or the row ids and has changed nothing").
   - The problem: when `--apply` fails after the pre-check, the batches before the failure stay
     committed. QA saw this on the stack: the connection was terminated after 104 rows, and the result
     was `k1=105, k2=215`. Two failures are also not listed among the messages the text explains:
     - `reencrypt failed: <ErrorClass>` (lock timeout, lost connection);
     - `values remain under another key after apply`, which comes from `reencrypt.py:324-325`, when a
       process still on the old key wrote during the run.
   - Fix: say that a refusal changes nothing, and that a failure during conversion leaves the earlier
     batches converted, with every row readable. Add the two messages and what to do for each:
     run the command again; for the second message, first confirm step 4 (`printenv` on every service).
3. **LOW. The rotate-back rollback contradicts the id rule and stops early.**
   - Where: `infra/DEPLOY.md:442` and `:520`.
   - The problem: line 442 says "never reuse the id of a key you retired", but rotate-back makes the
     retired id current again (with the same key, which is safe). The rollback text also ends at
     `--apply`, with no `--check` exit 0 and no step-6 removal of the new id.
   - Fix: change the rule to "an id always names the same key: never give a used id to a different
     key". End the rollback with "then `--check` (exit 0) and step 6, removing `<new id>`". The rollback
     itself works: QA rehearsed it, with the results below.
4. **LOW. Step 1 contradicts itself.**
   - Where: `infra/DEPLOY.md:470`.
   - The problem: it says "Stop nothing", then asks for a copy of the `postgres_data` volume, which
     "needs the stack stopped".
   - Fix: make the live `pg_dump -Fc` the required backup and the volume copy optional, with the
     stack stopped.
5. **LOW. Each batch scans from the start of the table while it holds the lock.**
   - Where: `backend/app/db/reencrypt.py:257`.
   - The problem: `_convert_batch` calls `_batches(...)` afresh, without the last id, so batch *k*
     walks past every row already converted. The scan time, and so the time writers wait, grows with
     the table: O(n²/batch) in total. This is negligible at the expected size (QA: 300 single-row
     batches with the application up, no write failed). It will matter for a large table.
   - Fix: pass the last converted id from one batch to the next. Stragglers are already caught by
     the final scan (exit 1) and by a re-run.
   - Optional: say in DEPLOY.md how long the lock is held per batch.

Observations (no change needed):
- The guard (`--verify-key-ids`) ignores NULL, `''`, non-envelope values and also
  `mh1:<unknown id>:<malformed payload>` (counted as `unreadable`, which its success line prints).
  Those are owned by 0010 and `--check`; consistent with the module docstring. Verified by probe.
- The recovery after a premature removal took 38 s with `up -d --build --wait` (DEPLOY says "about 20
  seconds"). Same outcome as documented: `backend`, both celery services and `reverse-proxy` stopped,
  `up` exit 1 naming `db-migrate`, database unchanged (320 values still `k1`).
- The developer's rehearsal tree carried a `reencrypt.py` that differs from the committed one in one
  message string only (`reencrypt.py:289`); no behavioural difference.
- SSE coupling: the DEPLOY precondition (`infra/DEPLOY.md:432`) is bold, first in the section, gives a
  checkable `grep` and is mirrored in the secrets table. A refusal inside the command would come too
  late: attachments break at step 4 (`up -d --build` recreates `object-store` with the new key), before
  the command runs. The structural guard therefore belongs in TASK-196 (carried there).

### QA verification (round 1)

- Re-runs: `tests/db/test_reencrypt.py` 21 passed; full suite 1207 passed, 4 skipped, coverage
  94.13 % (`reencrypt.py` 95 %); dicom 25 passed; ruff, black, mypy clean; infra 85 OK; traceability
  (TASK-195, TS-008, PRB-004, CR-004, SR-022, TASK-196) 0 errors.
- Unit probes (scratch, real DB, all pass on the committed code):
  - A writer holding an uncommitted `UPDATE` when `--apply` starts keeps its content, under the retired
    key and under the current key.
  - A commit between the pre-scan and the first batch keeps its content.
  - SIGKILL of a separate process at the 275th `encrypt` (25 rows of batch 6 updated, not committed)
    gives:
    - `k1=750, k2=250`, with no lock left;
    - every row decrypts with k2 plus retired k1;
    - with k1 removed, `--verify-key-ids` and `--check` exit 1; with k1 back, exit 0 and 3;
    - the re-run converts 750, and every plaintext is identical.
  - Rotate-back k1→k2→k1.
  - Guard edge values.
- Stack rehearsal (project `qa195`, scratch tree with the TASK-196 SSE layout simulated):
  - 300 entries and 2 attachments under k1.
  - k1→k2 with 20 API writes during `--apply --batch-size 1`: all 201, all ended under k2, `--check` 0.
  - **Rotate-back** (k1 current, k2 retired, restart, `--check` 3):
    - `--apply --batch-size 1` was interrupted by `pg_terminate_backend` after 104 rows: exit 1,
      `reencrypt failed: OperationalError`, state `k1=105, k2=215`;
    - re-run: exit 0, 215 converted;
    - `--check` 0, then k2 removed and `db-migrate` verified `k1=320`.
  - Premature removal is refused with the application down, and recovers.
  - Per-row plaintext SHA-256 (DB, AESGCM-only script) and API hashes are identical for all 300 entries
    at every stage; the 20 concurrent writes match; both attachments are byte-identical.
  - Smoke from the scratch tree: 65 passed, 0 failed.
  - Teardown: `down -v --remove-orphans` and the `qa195-*` images removed. The image, volume and
    network sets equal the start, and `peaceful_pike` was untouched. `infra/.env` SHA-1
    `714c7630962b01799b6b8ac467859d06095b0b64` before and after.

## Round 2 (software developer, 2026-11-01): QA round-1 findings addressed

Back to `in_review`. No stack rehearsal was repeated: the only behavioural change is the cursor of item 5, covered by real-database tests (a 1300-row run among them); the rest is tests and DEPLOY.md text.

1. **MEDIUM, batch rows read under the lock.** `test_a_write_committed_while_apply_waits_for_the_lock_is_not_overwritten` (k1 and k2 writer) holds an uncommitted `UPDATE` on a row of the first batch (batch size covers all 20 rows), lets `apply` pre-scan and block on `LOCK TABLE`, commits, and requires the writer's plaintext to survive and the others to be unchanged. `test_a_value_written_between_the_pre_scan_and_a_batch_is_converted_as_written` is QA's wrapper probe (a commit before the batch). Mutation: select moved before `LOCK TABLE` on a scratch copy: 2 failures (both parametrisations of the first test); the wrapper test does not discriminate on its own (the batch select runs after the commit in both orders).
2. **LOW, exit 1 text.** Refusal changes nothing; a failure after batches committed leaves a readable mix and a re-run continues; `reencrypt failed: <Class>` and `values remain under another key after apply` each have an explicit instruction.
3. **LOW, ids and rollback.** "Never give a used id to a different key"; the rollback ends with `--check` exit 0 and steps 6 and 7.
4. **LOW, step 1.** Live `pg_dump -Fc` mandatory (command given); the volume copy is optional and needs the stack stopped; recovery time "about 40 seconds with `--wait`".
5. **LOW, cursor.** `_convert_batch` takes `after`; `apply` carries the id of the last converted row and each batch selects `id > after` under the lock. When a cursor pass finds nothing, one sweep from the start follows (a row an old process wrote behind the cursor); an empty sweep ends the run. New test `test_batches_continue_after_the_last_converted_id_and_a_final_sweep_finds_late_rows`. Mutations: cursor ignored: 1 failure; final sweep removed: 1 failure.

Also: the in-memory read-back test now matches `read-back check; batch rolled back`, so it no longer passes through the database check (dropping the in-memory compare alone: 1 failure again).

Verification: `tests/db/test_reencrypt.py` 25 passed; full suite 1211 passed, 4 skipped, coverage 94.13%; DICOM 25 passed; ruff, black, mypy clean; infra 85 OK. Earlier controls re-run: row skipped 4 failures; DB read-back dropped 1; in-memory read-back dropped 1; pre-write check dropped 3.

## QA review — round 2 (2026-11-01): APPROVED

TASK-195 and TS-008 are `approved`. PRB-004 is `resolved` (1.6), with a Resolution covering TASK-193,
194 and 195 (CR-004 D-8).

Round-1 findings:
1. MEDIUM, closed. `test_a_write_committed_while_apply_waits_for_the_lock_is_not_overwritten` (k1, k2).
   QA re-ran its select-before-lock mutation: both parametrisations fail, and so does QA's own probe.
2. LOW, closed. The exit-1 section now separates a refusal from a failure after commits, and covers
   `reencrypt failed: <Class>` and `values remain ...`.
   - One leftover: `infra/DEPLOY.md:461` says a lock timeout "stops, unchanged". After the first batch,
     the earlier batches stay committed (every row stays readable, and the action, run again, is the
     same). This is a non-blocking LOW, for the CR-004 documentation pass (TASK-201).
3. LOW, closed. The id rule now reads "never give a used id to a different key". The rollback ends
   with `--check` exit 0 and steps 6 and 7.
4. LOW, closed. The live `pg_dump` is mandatory and the volume copy is optional, with the stack stopped.
5. LOW, closed. The batch cursor and the final sweep: QA's mutations each fail one test (cursor
   ignored; sweep replaced by `break`).

Termination and coverage of the cursor:
- Every batch still selects under the lock.
- A row behind the cursor is either under the current key (excluded by the filter) or under a retired
  key, which the sweep catches. A row the sweep misses is caught by the final scan (exit 1, then run again).
- Each loop iteration either converts at least one row or ends the pass, so the run only lasts while
  retired-key rows keep appearing.
- QA probe: an "old process" inserted retired-key rows for 3 s during `--apply --batch-size 3`, with a
  slowed `encrypt`. The run took 3.28 s, converted every row (89 under k2), and exited 0.

QA verification (round 2):
- Suites: `tests/db/test_reencrypt.py` 25 passed, plus QA's 7 probes; full suite 1211 passed,
  4 skipped, 94.13 %; dicom 25; ruff, black and mypy clean; infra 85 OK.
- Traceability (TASK-195, TS-008, PRB-004, CR-004, SR-022): 0 errors.
- Stack re-run with the cursor code (project `qa195`, scratch tree, TASK-196 SSE layout simulated):
  - 200 entries and 1 attachment.
  - k1→k2: `--apply --batch-size 7` (29 batches) while 10 API writes ran; all writes returned 201;
    `--check` 0.
  - Rotate-back k2→k1: `--check` 3. `--apply --batch-size 1` was terminated by
    `pg_terminate_backend` at 94 converted rows (exit 1, `reencrypt failed: OperationalError`,
    `k1=95, k2=115`). The re-run converted 115 and exited 0. `--check` 0. With k2 removed,
    `db-migrate` verified `k1=210`.
  - The per-row database and API hashes matched for 200/200 entries at every stage, and for 10/10
    writes. The attachment was byte-identical.
  - Smoke test: 65 passed, 0 failed.
- Teardown: `down -v --remove-orphans`, then the `qa195-*` images removed. The image, volume and
  network sets equal the start, and `peaceful_pike` was untouched. `infra/.env` SHA-1
  `714c7630962b01799b6b8ac467859d06095b0b64` before and after.
