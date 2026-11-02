---
id: "TASK-196"
type: task
title: "Separate the object-store SSE key from the field key and migrate stored attachments"
status: approved
version: "1.7"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-02"
links:
  - target: "SR-041"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "RISK-011"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "PRB-007"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-025"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
tags: ["security", "encryption", "object-store", "data-migration", "cr:CR-004", "control:design", "ask-first"]
---

# TASK-196 — Separate the object-store SSE key from the field key and migrate stored attachments

- **Software item / unit:** SI-OBJSTORE `U-OBJ-Server`, `U-OBJ-Preflight` (ADD-025); SI-DEPLOY (ADD-026).
- **PRB:** PRB-007 (key reuse, carried over by CR-002 D-6; last PRB-007 task). **CR:** CR-004.
  **Decision:** CR-004 Q-3 (2026-10-31): in this CR, with a migration rehearsed on a backup.
- **Depends on:** TASK-197 (shared secret rule), TASK-203 (Compose and template edited first).
  Independent of TASK-193..195; its own commit, nothing else in it.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`infra/docker-compose.yml`, `infra/.env.example`, `infra/DEPLOY.md`,
  `backend/app/core/object_store_credentials.py`; tests; TS-014, TS-015)
- **Needs:** a Docker host; the reference workstation's populated `object_store_data` volume,
  copied, for the rehearsal.
- **Boundary (CR-004 "Ask first"):** can make attachments unreadable. Run only on copies until the
  human approves the rehearsal result.
- **Design:** [ADR-0018](../../design/adr/0018-field-encryption-key-identifier-and-key-separation.md)

## Carried from the TASK-193 QA review (2026-11-01)

- LOW: `infra/tests/test_compose_settings_coverage.py` `settings_fields()` has three silent gaps,
  found with a probe on synthetic lines:
  - It skips a field whose annotation contains `=` (`Annotated[str, Field(alias=…)]`).
  - It counts `Field(...)` as a default.
  - It ignores `alias`/`validation_alias`.

  None of these occurs in `config.py` today. When this task removes `OBJECT_STORE_SSE_KEY` from
  `EXCEPTIONS`:
  - Assert that every `^    name:` line in the `Settings` body was parsed.
  - Fail on `alias`/`Field(...)` until those forms are handled.

## Carried from the TASK-195 QA review (2026-11-01)

Field-key rotation (`infra/DEPLOY.md`, "Field-encryption key rotation") is forbidden until this
task lands, because `WEED_S3_SSE_KEY` is `${AT_REST_ENCRYPTION_KEY}`: step 4 of the rotation
recreates `object-store` with the new key and every attachment returns 500 (TASK-195 rehearsal: 6/6).

- **Make the coupling impossible, not only documented.** A refusal inside `app.db.reencrypt` would
  be too late, because the damage happens at the restart, before the command runs. Instead:
  - Add an infra rendered-compose test: `WEED_S3_SSE_KEY` is not interpolated from
    `AT_REST_ENCRYPTION_KEY` (nor from a retired key).
  - Add a start-up refusal, in `object-store-preflight` or the secret rule, when
    `OBJECT_STORE_SSE_KEY` equals `AT_REST_ENCRYPTION_KEY` or a key in
    `AT_REST_ENCRYPTION_RETIRED_KEYS`. The error names the settings and never the value.
- **Update the rotation text once the keys are separate.**
  - Replace the "Do not start while ..." paragraph and its `grep` check (DEPLOY.md, top of
    "Field-encryption key rotation") with the new state.
  - Drop "(object-store SSE key)" from the `AT_REST_ENCRYPTION_KEY` row of the secrets table.
  - Update the matching notes in TS-008 (paragraph after the TC table, "not usable ... until TASK-196")
    and in PRB-004.
- **Rehearse a field-key rotation on the shipped Compose file.** TASK-195 rehearsed only with the
  SSE line edited in a scratch copy. Rotate k1 to k2 with attachments present and record every
  attachment byte-identical after step 7.
- **Allow-lists and guards** (from the TASK-191, 193 and 194 reviews):
  - `OBJECT_STORE_SSE_KEY` goes only to the services that need it; check by *value* in
    `docker inspect`, not by name.
  - Every new `:?` guard is listed in the smoke-test awk and in the infra tests that name the
    first-reported guard (Compose picks one at random).

## Objective

SR-041 AC 5: the field key and the SSE key are separate settings; start-up is refused when they
are equal; attachments stored before the separation stay readable after it.

## Implementation detail

1. New secret setting `OBJECT_STORE_SSE_KEY` (base64 of 32 bytes). `infra/docker-compose.yml:147`:
   `WEED_S3_SSE_KEY: ${OBJECT_STORE_SSE_KEY:?…}`; the preflight receives both keys.
2. `object_store_credentials.py` (via the shared secret rule): refuse unset, placeholder, not 32
   bytes, or equal (decoded bytes) to `AT_REST_ENCRYPTION_KEY`.
3. Migration procedure in `infra/DEPLOY.md` "Separating the object-store SSE key", using
   `backend/scripts/migrate_object_store.py` (CR-002, TASK-178) unchanged apart from its docstring:
   stop the stack; copy `object_store_data`; start a source store on the copy with
   `WEED_S3_SSE_KEY=<old AT_REST_ENCRYPTION_KEY>` and a target store on a new volume with the new
   key; run the script (per-object SHA-256 against `attachment.checksum`, before and after; source
   read only); switch the Compose volume to the new one; start; download every attachment through
   the API; keep the old volume until the human releases it.
4. `.env.example`: `OBJECT_STORE_SSE_KEY=` with its generation command.

## Tests (write first)

- `backend/tests/core/test_object_store_credentials.py`: SSE key unset, placeholder, 31 bytes,
  equal to the field key → refused, naming the setting; distinct 32-byte keys → accepted.
- `infra/tests/test_compose_object_store.py`: `WEED_S3_SSE_KEY` comes from `OBJECT_STORE_SSE_KEY`
  with a `:?` guard and nowhere from `AT_REST_ENCRYPTION_KEY`.
- Rehearsal (recorded): object count, per-object checksum match, API downloads of every attachment
  equal to the stored checksum, the new volume's raw files contain no plaintext marker, the source
  tree hash unchanged.

## Acceptance criteria

- [ ] SR-041 AC 5: separate settings; equal keys refused (`backend/tests/core/test_object_store_credentials.py`,
      `infra/tests/test_compose_object_store.py`).
- [ ] SR-041 AC 5, AC 6: attachments stored before the separation are readable after it, on a
      started stack (rehearsal record).

## Verification

```sh
cd backend && uv run pytest tests/core/test_object_store_credentials.py tests/scripts -v
cd infra && python3 -m pytest tests -v
docker compose -f infra/docker-compose.yml up -d && infra/smoke-test.sh
```

## Records

- **TS-014** → 1.6 (`in_review`): TC-014.7 (SSE key separation and migration), `verifies` SR-040
  and SR-041; **TS-015**: TC-015.3 extended (equal-key refusal).
- **SOUP-036** (SeaweedFS): F-4 handling recorded as relied-on behaviour (one SSE key per volume;
  re-keying by copy); `in_review`.
- **ADD-025** 1.3: confirm unit text. **PRB-007**: `## Resolution` (TASK-191, 196, 197, 198, 203,
  TASK-140), `resolved`.

## Definition of Done

- [ ] Tests and smoke pass; rehearsal recorded and presented to the human.
- [ ] TS-014, TS-015, SOUP-036 `in_review`; PRB-007 `resolved`.
- [ ] `traceability-check` shows no error for TASK-196, TS-014, TS-015, SR-041, PRB-007.

## Implementation notes (2026-11-01, software developer)

Handed to QA as `in_review`. No checkbox is ticked. Nothing is staged or committed.

### Files

- Backend: `backend/app/core/secret_settings.py` (`sse_key_problems`, `check`, `settings_env`),
  `backend/app/core/config.py` (`object_store_sse_key` field and validator),
  `backend/app/core/object_store_credentials.py` (the preflight checks the SSE key),
  `backend/app/core/object_store_init.py` (read-back of a stored object),
  `backend/scripts/migrate_object_store.py` (per-row error reporting, docstring).
- Infra: `infra/docker-compose.yml`, `infra/.env.example`, `infra/DEPLOY.md`, `infra/smoke-test.sh`,
  `.github/workflows/ci.yml` (object-store job), new `infra/migration/compose.sse-source.yml`.
- Tests: `backend/tests/core/test_object_store_credentials.py`, `test_secret_settings.py`,
  `test_object_store_init.py`, `backend/tests/scripts/test_migrate_object_store.py`,
  `backend/tests/test_env_example.py`, new `backend/tests/integration/test_object_store_rekey.py`;
  `infra/tests/test_compose_object_store.py`, `test_compose_secrets.py`,
  `test_compose_settings_coverage.py`, `test_ci_compose_env.py`, new `test_compose_sse_source.py`.
- Records: TS-014 1.6, TS-015 1.5, TS-008 1.11 (all `in_review`), SOUP-036 1.3 (`in_review`), PRB-004 1.7,
  PRB-007 1.8 (Resolution written, status left `open` for QA, CR-004 D-8), new PRB-063, this task.

### How each criterion is met

- **SR-041 AC 5, separate settings, equal keys refused.** `OBJECT_STORE_SSE_KEY` is required by Compose
  (`:?` guard) for `object-store` (`WEED_S3_SSE_KEY: ${OBJECT_STORE_SSE_KEY…}`) and the preflight, which
  also receives `AT_REST_ENCRYPTION_KEY` and `AT_REST_ENCRYPTION_RETIRED_KEYS` to compare. The rule
  (`sse_key_problems`) refuses unset, empty, placeholder, not base64, not 32 bytes, and equal (decoded
  bytes) to the field key or any retired key, naming settings only. Tests: `test_object_store_credentials.py`,
  `test_secret_settings.py`, `infra/tests/test_compose_object_store.py`.
- **SR-041 AC 5, AC 6, attachments readable after the separation.** Copy procedure
  (`infra/DEPLOY.md` "Separating the object-store SSE key") and its rehearsal on a started stack (below).
- **Make the TASK-195 coupling impossible.** Rendered-compose test: `WEED_S3_SSE_KEY` is exactly
  `${OBJECT_STORE_SSE_KEY:?…}`, takes the template value even when the shell changes the field key, and
  no service but `object-store` and the preflight holds the SSE value (by value, over every service).
  Start-up refusal in the preflight; DEPLOY.md rotation precondition, secrets table, "What refuses an
  unsafe value", TS-008 and PRB-004 notes rewritten.
- **Carried requirement C2 (TASK-197 QA).** `object_store_sse_key` is a `Settings` field read by
  `settings_env()`; 32 bytes of base64; refused when equal to the field key or a retired key (compared as
  decoded bytes); the preflight gets both keys. See deviation 1 for "required".
- **R2-3 parser gaps.** `infra/tests/test_compose_settings_coverage.py`: the `EXCEPTIONS` entry is gone
  (the empty dict is checked by the stale-exception test); the parser takes the first top-level ` = `
  (so `Annotated[..., Field(alias=…)]` is read), accounts for every `    name:` line, and raises on
  `alias` or `Field(...)` instead of guessing; probes on synthetic bodies are tests. The preflight is
  counted as a service that reads secrets (`SECRET_RULE_SERVICES`) because it does not build `Settings`.
- **Allow-lists and guards.** New `:?` guards: the smoke awk, `test_compose_secrets.py` (`BringUpRefusal`
  loops, `GUARDED` for the preflight), `test_compose_object_store.py` unset/empty loops,
  `test_ci_compose_env.py` and the CI step (which now writes two different `openssl rand -base64 32`
  values). `smoke-test.sh` section 12 checks by value that the SSE key differs from the field key, is in no
  container but the store, and that the store holds no field key.

### The copy and the key per object

- SeaweedFS cannot say which key an object was written under and cannot re-key in place (SOUP-036 F-4):
  the key of an object is the key of its volume. The mechanism is the CR-002 tool, per ADR-0018 option (i),
  plus a Compose file for the source store: `infra/migration/compose.sse-source.yml` runs the same pinned
  image on a **copy** of the old volume with `SOURCE_SSE_KEY` (the old field key) next to the `migrate`
  container; the stack's `object-store` runs on a **new volume** (`OBJECT_STORE_VOLUME`) under the new key.
- Per row: read source, SHA-256 against `attachment.checksum`, write `AES256`, read back, compare again.
  Idempotent and resumable (target already right is skipped), source only read, no delete in the store
  protocol, counts (`copied`, `already-present-and-matching`, `missing-in-source`, `checksum-mismatch`,
  `read-or-write-error`, `orphans-in-source`), failures by attachment id (never storage key), exit 1.
  New in the script: a read or write error on a row no longer aborts the run with a traceback; it is
  listed as `ERROR <id>` and the run goes on.
- To tell that a store runs under the wrong key: `object-store-init` reads back the smallest object of the
  bucket's first page (new, see deviation 2); `docker compose up` of the new code on the old volume with a
  new key therefore stops with `... OBJECT_STORE_SSE_KEY is not the key this volume was written with` and
  the backend is not started.
- Rollback is documented (DEPLOY.md): last release before TASK-196 with `env.before-sse` on the untouched
  original volume; rehearsed.

### Verification run

| Command | Result |
|---|---|
| `cd backend && uv run pytest tests/core/test_object_store_credentials.py tests/scripts` | 85 passed |
| `cd backend && uv run pytest --cov=app --cov-fail-under=85` | 1246 passed, 6 skipped (the 6 object-store tests), coverage 94.11% |
| `cd backend && uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `uv run ruff check .`, `uv run black --check .`, `uv run mypy app` | clean (254 files, 132 source files) |
| `cd infra && python3 -m unittest discover -s tests` | 98 tests OK |
| `OBJECT_STORE_INTEGRATION=1 … uv run pytest -m object_store` against a scratch store (CI override port) | 6 passed (4 existing + 2 new) |
| `bash infra/smoke-test.sh` from a scratch copy, new layout | 74 passed, 0 failed (after the upgrade and again after the rotation) |

Negative controls (each reverted, suites green again afterwards): `WEED_S3_SSE_KEY` pointed back at
`${AT_REST_ENCRYPTION_KEY…}`: 4 infra tests fail; equality check removed from `sse_key_problems`: 7
backend tests fail; post-copy read-back comparison removed: `test_mismatch_after_write` and
`test_every_object_is_verified_after_the_copy` fail; source comparison removed:
`test_source_checksum_mismatch_is_not_written` fails; initialiser read-back removed: 7 tests fail.

### Rehearsal (scratch project `task196`; full text in `infra/DEPLOY.md`)

Old layout = tree of `f7d79fc`, shared key; 30 clinical entries, 15 attachments (0 B, 1 B, 17 B … 50,331,648 B;
89,223,277 bytes; one with a plaintext marker; one with a non-Latin-1 file name).

- Backup tar of the original volume (sha256 `b9abeb1a…408e`); restored copy and original: identical
  file-by-file hash (88 files) before and after the whole procedure.
- Refusals before the store starts: SSE key empty, equal to the field key, equal to a retired key,
  placeholder, 31 bytes, 48 bytes. A new key on a copy of the old volume: store up, `object-store-init`
  exit 1, backend not started.
- Copy: `copied: 15`, others 0, exit 0 (20 s with build); second run `already-present-and-matching: 15`;
  with the source under a wrong key: 15 `ERROR <id>`, nothing written, exit 1.
- After: 15 of 15 downloads with the same status and SHA-256 as before the upgrade (14 with status 200
  and the SHA-256 of the uploaded bytes; the non-Latin-1 name answers 500 before and after, PRB-063; its
  bytes were compared by the tool). Marker found in 0 files of the new volume (control: 1). Smoke 74/0 after step 7 (round 1 wrongly placed it at step 6, where it gives 64/5; corrected in round 2).
- Rotation k1 to k2 on the shipped file, steps 1 to 7 of DEPLOY.md: attachments identical after steps 4, 5
  and 6, a 2.5 MB attachment uploaded under k2 readable, 30 of 30 clinical descriptions identical,
  smoke 74/0 (TASK-195 had ended with 6 of 6 HTTP 500 on the earlier file).
- Rollback to the `f7d79fc` tree on the original volume with `env.before-sse` and the dump: 15 of 15
  identical. (The original volume's file hash differs after that run, because the old store ran on it again.)
- Teardown: `down -v --remove-orphans` of `task196` and `task196-rekey`, the project images and 8 dangling
  images removed; container, volume, network and image lists equal to the start; `infra/.env` checksum
  unchanged; `peaceful_pike` untouched. No `docker builder prune`, no `system prune`.

### Deviations and decisions for the human

1. **`OBJECT_STORE_SSE_KEY` is optional in `Settings`** (`SecretStr | None`), not required. Carried
   requirement C2 says "required wherever it is used": it is required where it is used, in Compose
   (`:?`) and in the preflight (`sse_key_problems` refuses unset). Making the `Settings` field required
   would hand the SSE key to the backend, the Celery services and `db-migrate`, which contradicts the
   by-value allow-list the same task requires. When a service does receive it, `Settings` refuses it if it
   equals a field key.
2. **Start-up read-back in `object-store-init`** is not in the task text. It is the only defined way to
   tell, at start-up, that a store runs under another key than its volume, and it keeps an upgrade
   without the procedure from writing anything. Easy to veto: one function and its call in
   `initialise()`. The rehearsal showed a first version (first listed object, range read) passing on a
   wrong key because the first object was empty; fixed and tested (`test_a_zero_byte_object_is_read_whole…`).
3. **`OBJECT_STORE_VOLUME`** (`name: ${OBJECT_STORE_VOLUME:-}` on the `object_store_data` volume) is the
   "switch the Compose volume" mechanism. Empty keeps the default name (tested on Compose 2.20.2; an
   older or newer Compose that treats an empty `name` differently would need a check).
4. **`migrate_object_store.py` changed beyond its docstring** (task text: "unchanged apart from its
   docstring"): per-row error handling and the `read-or-write-error` count, required by "stops with object
   ids" when a source answers 500. The copy logic is the same function split in two.
5. **`task196r` was not used.** The restore path was exercised by the rollback (dump restore plus the
   untouched volume) and by restoring the tar into the copy volume. The tar restore of the old volume into
   a project of its own was not run as a separate stack.
6. **PRB-007 stays `open`**; its Resolution is written (1.8) for QA to set `resolved` on approval (D-8).
7. New defect PRB-063 (downloads of attachments with non-Latin-1 file names answer 500), out of scope.
8. Objects that no row refers to (orphans) are reported and not copied, so they stay on the old volume
   only; none existed in the rehearsal.

### Changes the human-approved records need (not edited here)

- **ADD-025** (U-OBJ-Preflight, U-OBJ-Server, U-OBJ-Init): the preflight also checks `OBJECT_STORE_SSE_KEY`
  and receives the field keys; `object-store` takes its key from `OBJECT_STORE_SSE_KEY` and its volume name
  from `OBJECT_STORE_VOLUME`; the initialiser reads back a stored object; add the source-store file
  `infra/migration/compose.sse-source.yml`.
- **ADD-026** (U-DEP-SecretRule): `OBJECT_STORE_SSE_KEY` is a Settings field, optional, checked when
  present, and `sse_key_problems` is the rule; the template and smoke test gain the new setting.
- **ADR-0018**: add that the target store is the stack's own store on a new volume selected with
  `OBJECT_STORE_VOLUME` and that a start-up read-back detects a wrong key; the "preflight refuses it" sentence
  stays true.
- **CR-004**: nothing; PRB-007 is mapped to this task in its Scope table and D-8 allows `resolved` on QA approval.
- **SR-041 / RISK-011 / RISK-007**: no text change required; RISK-011 control (separate keys) can cite TC-014.7.

## QA review — round 1 (2026-11-02): CHANGES REQUESTED

No CRITICAL or HIGH finding. The code is correct, and the copy is data-safe:
- No path deletes the source or the old volume, or overwrites them.
- A target object is overwritten only by source bytes already verified against
  `attachment.checksum`, and the result is read back.
- An upgrade without the procedure is refused and leaves the volume readable under the old key.

The verdict is CHANGES REQUESTED because the procedure, which is the deliverable of SR-041 AC 5/6
under the CR-004 "Ask first" boundary, cannot be run verbatim on the installation it is written for.
The rehearsal record also says that steps 1 to 7 "were run as written" and that the smoke test passed
at step 6, and step 6.4 does not pass as written (finding 2). Every finding is a text or test change.

1. **MEDIUM — the upgrade order is not executable from the release before CR-004.** `infra/DEPLOY.md:447-448`
   says "Do the other upgrade sections above first". But Compose interpolates the whole file:
   - Without `OBJECT_STORE_SSE_KEY`, every command of this release fails, including "Upgrading an
     installation that connects as the owner" step 3 (`up --exit-code-from db-migrate db-migrate`).
     QA ran `config db-migrate` with the pre-TASK-196 `.env`: `required variable OBJECT_STORE_SSE_KEY
     is missing a value`, exit 15.
   - That section's step 4 (`up -d` + smoke) cannot succeed on a store that holds attachments until
     this section is done: the initialiser refuses, as designed.
   - The copy tool needs the runtime role (`medhub_app`), so the role upgrade has to come first.

   The developer's rehearsal started at `f7d79fc`, which skips this interaction. The reference
   workstation does not start there.
   → Fix: state the real order in the intro of "Separating the object-store SSE key":
   - Run the earlier sections only up to and including their `db-migrate` command.
   - Before that, set `OBJECT_STORE_SSE_KEY` (a new value) and `OBJECT_STORE_VOLUME` as in step 3 of
     this section.
   - Skip their `up -d`/smoke steps; this section's step 7 starts the stack.

   Also add one sentence to "Upgrading an installation that connects as the owner", step 2.
2. **MEDIUM — step 6.4 cannot pass where it is placed.** `infra/DEPLOY.md:556` runs
   `bash infra/smoke-test.sh` while the reverse proxy and the frontend are still stopped (step 6.2
   starts only the backend and Celery). QA ran it verbatim: `64 passed, 5 failed`. The failures are:
   - login through the proxy
   - the probe tool in `reverse-proxy`
   - the probe tool in `frontend`
   - `frontend` not running
   - the SPA through the proxy

   After step 7 the result was 74/0. DEPLOY gives no instruction for a failing verification step, and
   the rehearsal record at `infra/DEPLOY.md:612-618` (step 6 bullet) and this task's "Rehearsal" ("Smoke 74/0") do not
   match what step 6 produces.
   → Fix: move the smoke test after step 7's `up -d`, or list the five checks expected to fail at
   step 6.4 and the SSE checks that must pass ("the object-store SSE key differs from the field key",
   "holds the right encryption key"). Then correct the rehearsal record to say which step gave 74/0.
3. **MEDIUM — a wrong or empty volume is not detected, and `.env.example` invites clearing the setting.**
   - `object_store_init.py:119`: an empty bucket passes.
   - `infra/.env.example:88-90`: "Leave empty for the default".
   - QA started the store with a mistyped `OBJECT_STORE_VOLUME` and `--force-recreate`. Compose created
     the new empty volume, the initialiser printed `object-store init ok`, and the backend became
     healthy. 0 of 6 attachments downloaded (all 500), and new uploads would have gone to the wrong
     volume.
   - The same happens if `OBJECT_STORE_VOLUME` is cleared after the owner deletes `$OLD_VOL`: the
     default name is that deleted volume, so Compose creates it empty.
   - Changing only `OBJECT_STORE_VOLUME` does not recreate `object-store` under Compose 2.20.2 (QA:
     the container stayed on `_sse`). The switch takes effect at some later recreate, so the mistake
     surfaces at an unrelated restart. Step 4 works only because `WEED_S3_SSE_KEY` changes at the same
     time.

   This is RISK-007 (attachments unavailable) and a split store. Nothing is lost.
   → Fix:
   - (a) In `.env.example` and DEPLOY step 3/7: once set, `OBJECT_STORE_VOLUME` must never be cleared
     or changed, it is part of the `.env` backup, and an empty or wrong value starts an empty store
     with every attachment answering 500.
   - (b) Add `--force-recreate object-store` to step 4's command (or say why it is not needed).
   - (c) Recommended: a smoke-test check that the bucket holds at least as many objects as there are
     `attachment` rows. The initialiser has no database access, so the smoke test is the place.
4. **LOW — step 7 works only in the shell of step 5.** `infra/DEPLOY.md:561-565`.
   - `rekey --profile migrate down` needs `OBJECT_STORE_NETWORK`, `DATABASE_NETWORK` and
     `SOURCE_STORE_VOLUME`, which step 5 exported. In a new shell it fails with `required variable
     OBJECT_STORE_NETWORK is missing a value`, exit 15, and the source store (holding the old key)
     keeps running. Step 6 is manual and can take long, so a new shell is likely.
   - Step 4 does not say to check that `object-store-init` exited 0: `up -d` returned 0 while the
     initialiser was still running.

   → Fix: in step 7, repeat the `export` line and the `rekey` definition (or say "same shell as
   step 5"). In step 4, add `docker compose -p "$P" -f infra/docker-compose.yml ps -a object-store-init`
   (exit 0 expected).
5. **LOW — the zero-byte rule that the rehearsal found is not pinned by a test.** QA mutation: replacing
   `options = {"Range": "bytes=0-0"} if probe.get("Size", 0) > 0 else {}` with an unconditional range
   passes all 229 targeted tests (`object_store_init.py:122`).
   - On the real store (pinned 4.51, right key), a range read of a 0-byte object answers `InvalidRange`.
     So that regression would refuse start-up on every healthy store whose smallest object is empty.
   - `test_a_zero_byte_object_is_read_whole_because_a_wrong_key_fails_it_too` stubs `get_object`
     without `expected_params`, so it accepts a ranged call.
   - No automated test runs the read-back against a store with the wrong key. That evidence is the
     manual rehearsal only.

   → Fix: add a passing zero-byte case with `expected_params={"Bucket": BUCKET, "Key": ...}` (no
   `Range`), and set `expected_params` in the zero-byte refusal test. Optional: in the CI object-store
   job, recreate the store with a second key and assert that `object-store-init` exits 1.
6. **LOW — every probe error is reported as a wrong key.** `object_store_init.py:125-130` turns any
   `ClientError` from the probe `get_object` into "OBJECT_STORE_SSE_KEY is not the key this volume was
   written with". Examples are `NoSuchKey` (an object deleted between the listing and the read, for
   example when `up -d` re-runs the initialiser while the backend cleans up a failed upload),
   `AccessDenied` and `SlowDown`. The operator is then sent to the key procedure for a transient error.
   → Fix: give the wrong-key message only for `InternalError`/HTTP 500 (the code QA observed for a wrong
   key on every size); report the others with `_failed("get_object", exc)`. For `NoSuchKey`, re-list
   once.
7. **LOW — the retention warning does not cover the key stored next to the data.** `infra/DEPLOY.md:480-487`
   (step 1) and `:567-572` (retention).
   - Step 1 writes `env.before-sse` (which holds `AT_REST_ENCRYPTION_KEY`, the key that decrypts the
     tar's attachments) into the same `$BK` as `object_store_data.tar`.
   - `chmod a-w` leaves the tar world-readable (QA: `-r--r--r--`), and `$BK` is created with the
     default umask.
   - The retention paragraph names what to delete, but not that the tar together with
     `env.before-sse` is equivalent to plaintext. It also does not say that ORPHAN objects exist only
     on `$OLD_VOL`/the tar.

   → Fix: create `$BK` with `umask 077`, use `chmod 400` for the tar, keep `env.before-sse` in the
   secret store and not beside the tar, and say in the retention paragraph that deleting them also
   deletes any ORPHAN objects for good.

Observations (not findings):
- `test_the_parser_accounts_for_every_field_line` compares `_FIELD_LINE` with itself. An annotation
  split over several lines would be misread as having no default. No such field exists today.
- PRB-063: QA reproduced it with `report’s summary.pdf` (U+2019, a common apostrophe in macOS and
  Office file names): 500 before and after the upgrade, `UnicodeEncodeError ... '’'`. The exception
  is raised at `backend/app/api/routers/attachments.py:107` (`StreamingResponse`), from the header built
  at `:110`. A failed download writes no audit event (only `ATTACHMENT_UPLOAD|SUCCESS` for that id).
  Recommendation: keep `major`. Widen the Impact text: any character outside Latin-1, including
  `’`, `–` and `€`, not only CJK or Arabic.
- DICOM: `modules/dicom_viewer` reads only through `services.attachments.open`, and the only writer of
  objects is `AttachmentService.store`. Every object is an attachment row, and orphans can come only from
  a failed upload cleanup.

### QA verification (round 1)

All docker work ran in scratch projects `qa196` and `qa196-rekey`, from scratch trees. `old` is
`git archive f7d79fc`, and `new` is a copy of the working tree. The env files and the self-signed
certificate were scratch files.

| Check | Result |
|---|---|
| `uv run pytest --cov=app --cov-fail-under=85` | 1246 passed, 6 skipped, 94.11 % |
| targeted (`test_object_store_credentials`, `test_secret_settings`, `test_object_store_init`, `tests/scripts`, `test_env_example`) | 247 passed |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| ruff, black, mypy | clean (254 files, 132 source files) |
| `cd infra && python3 -m unittest discover -s tests` | 98 OK |
| `OBJECT_STORE_INTEGRATION=1 uv run pytest -m object_store` (scratch store with the CI override, port 18339) | 6 passed |
| Traceability (fallback parser, scope TASK-196, TS-008/014/015, SR-022/041, PRB-004/007/063, SOUP-036, CR-004, RISK-007/011, ADD-025/026) | 0 errors, 38 warnings (W5 for in_review ADD/SOUP, W6 obsolete, W1 SR-026/043; none new from this task) |

Mutations, run in a scratch copy of `backend/` against the targeted tests:

| Mutation | Result |
|---|---|
| max instead of min | 1 failed |
| unconditional Range | **0 failed** (finding 5) |
| probe removed | 7 failed |
| raw-string equality instead of decoded bytes | 1 failed |
| retired keys not compared | 3 failed |
| no read-back after the write | 2 failed |
| write before the source check | 3 failed |
| `errors` not counted in `ok` | 3 failed |
| preflight without the SSE check | 6 failed |
| probe error swallowed | 2 failed |

Rehearsal: 4 entries and 6 attachments (0 B, 1 B, 40 B with a plaintext marker, 300 B `résumé.txt`,
5000 B `report’s summary.pdf`, 3 MiB), plus one orphan object put directly.
- **Before the upgrade:** 5 of 6 downloads were 200 and matched the upload hash. The U+2019 file
  answered 500 (PRB-063).
- **Upgrade without the procedure, on a restored copy:** the preflight passed, and
  `object-store-init` exit 1 (`... (InternalError): OBJECT_STORE_SSE_KEY is not the key this volume
  was written with`). The backend stayed `Created`. The same copy, read afterwards under the old key
  through the source store: 6 of 6 matched `attachment.checksum`.
- **Wrong-key probe on the real store:** every size answers `InternalError`, whole or ranged, except
  a 0-byte object with a range, which answers `InvalidRange`. Right key: a 0-byte range also answers
  `InvalidRange`, and a 0-byte whole read is OK. This confirms SOUP-036 item 9.
- **Steps 1 to 7, run verbatim:**
  - Steps 1 and 2: the tar, and `$SRC_VOL` with a file-tree hash equal to `$OLD_VOL` (88 files).
  - Step 4: init `ok` on the new empty bucket.
  - Step 5, with the SIGKILL: `docker kill -s KILL` of `migrate` 1.6 s after start left 2 of 6
    objects on the target. The re-run gave `copied: 4`, `already-present-and-matching: 2`,
    `ORPHAN 01de1fc61fa6`, exit 0.
  - Step 6.1: `copied: 0`, `already-present-and-matching: 6`.
  - Wrong `SOURCE_SSE_KEY` with one target object replaced by 4 bytes of junk and one deleted: 2
    `ERROR <id>`, exit 1, target unchanged. Right key again: `copied: 2`, exit 0, junk replaced.
  - Step 6.2: 6 of 6 downloads identical to before (5 match the upload). Init `ok` on the non-empty
    new bucket, so a healthy store is not refused.
  - Step 6.3: the marker was found in 0 files of `$NEW_VOL` and of `$OLD_VOL` (control: found).
  - Step 6.4: 64/5 (finding 2).
  - By value: only `object-store` and `object-store-preflight` hold the SSE key, and the store holds
    no field key.
  - Step 7: fails in a new shell (finding 4); in the same shell, exit 0. Smoke 74/0. `$OLD_VOL` hash
    unchanged.
- **Rollback**, with the stack on `f7d79fc`, `env.before-sse` (byte-equal) and `$OLD_VOL`: 6 of 6
  identical.
- **Field rotation k1→k2 on the shipped Compose file:** `--check` k1=4. After step 4 all services
  were on `k2`, and attachments 6 of 6 identical. Step 5 `converted: 4`, `--check` k2=4, exit 0.
  Step 6 and step 7: smoke 74/0, attachments 6 of 6 identical, 4 of 4 descriptions identical. The
  store stayed on `qa196_object_store_data_sse`.

Teardown:
- `down -v --remove-orphans` of both projects.
- The four scratch volumes, the eight `qa196*` images, six dangling images from QA builds and the
  `qa196_ci-publish` network were removed.
- Images, volumes, networks and containers are equal to the lists taken at the start.
- `infra/.env` sha256 `a4933b8c…96da` before and after.
- `peaceful_pike` was not touched. No `builder prune` or `system prune` was run.

Records not changed by QA: TS-008, TS-014, TS-015 and SOUP-036 stay `in_review`, and PRB-007 stays
`open`. Set them at the approving round.

## Implementation notes, round 2 (2026-11-02, software developer)

Answer to "QA review — round 1". Handed to QA as `in_review`, version 1.4. No checkbox is ticked. Nothing staged
or committed. The human decided (2026-11-02): PRB-063 is folded into CR-004 (D-9, TASK-204 by the architect; I
did not create TASK-204 or fix PRB-063), and finding 3c is included.

### Findings and how each is closed

1. **Upgrade order (MEDIUM).** `infra/DEPLOY.md`, "Separating the object-store SSE key", now opens with "Order on an
   installation that comes from a release before this one": one `docker compose down` (no `-v`), the
   backups, the SSE `.env` edits first, the owner and 0010 sections up to and including their `db-migrate` command,
   then steps 4 to 7 here. The owner section (step 2 and step 4) and the 0010 section (step 4) carry the matching
   sentence. The rehearsal found two more things that a start at `f7d79fc` hides, both fixed in the text: an old
   `medhub` network without the fixed subnet makes the reverse proxy fail to start (hence `down`, not `stop`, in
   step 1), and `up -d` without `--build` leaves the old frontend image (hence `--build` in step 7).
2. **Step 6.4 smoke (MEDIUM).** The smoke test moved to step 7 (after `up -d --build`); step 6 says why (five
   checks fail there, measured: 64 passed, 5 failed). The rehearsal record names the step that gives the green run.
3. **Wrong or empty volume (MEDIUM).**
   - (a) `.env.example` and DEPLOY step 3: `OBJECT_STORE_VOLUME` must never be cleared or changed once set; part of the
     `.env` backup.
   - (b) Step 4 uses `up -d --build --force-recreate object-store-init`.
   - (c) New smoke check "the object store holds every attachment (SR-041 AC 6)": bucket objects >= `attachment` rows,
     counts only. Negative control on a started stack: a mistyped `OBJECT_STORE_VOLUME` with the store
     force-recreated gives `74 passed, 1 failed` (`the database has 16 attachment rows, the bucket 0 objects`);
     restored, 75 and 0. The optional refusal in `object-store-init` was not added: the initialiser has no database access
     and the smoke test is where the comparison belongs (as QA judged). Known limit: clearing the setting while
     `$OLD_VOL` still exists makes the store use the old volume under the new key; the object count is then right,
     and `object-store-init` (which Compose re-runs when it recreates the store) refuses it.
4. **Step 7 in a new shell, and step 4 exit code (LOW).** Step 7 says to define the variables again, repeats the
   `export` and the `rekey` function and gives the full command; step 4 runs `docker wait` on the initialiser (prints
   its exit code, 0 expected) and checks the store's mount.
5. **Zero-byte test (LOW).** `test_a_readable_zero_byte_object_is_read_without_a_range` and `expected_params` (no
   `Range`) on the refusal test. The optional CI job with a second key was not added.
6. **Error mapping (LOW).** Only `InternalError`/500 says "wrong key"; others are `get_object failed: <code>`;
   `NoSuchKey` re-lists once (a second one is a failed `get_object`). Tests: other errors (two codes), gone once, gone twice.
7. **Retention (LOW).** `$BKENV` (the copy of the old `.env`) is a different place from `$BK` (the tar); both are created
   with `umask 077`, the tar and its checksum with `chmod 400` inside the helper container; the text says that tar plus
   `.env` is the attachments in plain text and that deleting them also deletes the orphans for good.

### Verification (round 2)

| Command | Result |
|---|---|
| targeted (`test_object_store_credentials`, `test_object_store_init`, `tests/scripts`, `test_env_example`, `test_secret_settings`) | 252 passed |
| `cd backend && uv run pytest --cov=app --cov-fail-under=85` | 1251 passed, 6 skipped, coverage 94.13% |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `uv run ruff check .`, `black --check .`, `mypy app` | clean |
| `cd infra && python3 -m unittest discover -s tests` | 99 OK |
| `OBJECT_STORE_INTEGRATION=1 … pytest -m object_store` against a scratch store | 6 passed |

Mutations (reverted afterwards; 24 initialiser tests green again): unconditional `Range`: 1 failed
(`test_a_readable_zero_byte_object_is_read_without_a_range`); every probe error reported as a wrong key: 3 failed;
no re-list on `NoSuchKey`: 1 failed; wrong-volume smoke check: live control above. (The round-1 mutations were not
rerun; the code they cover is unchanged.)

### Rehearsal from the release before CR-004 (`4d57094`, project `task196`)

Full text in `infra/DEPLOY.md`, "Rehearsal result". The old layout: owner connection, `env_file`, no key id, store key =
field key, `SESSION_SIGNING_KEY` left over. (Its `.env.example` ships an empty `CORS_ORIGINS`, which that release cannot start
with, PRB-056; the scratch `.env` set a JSON list.) 30 clinical entries, 16 attachments (0 B to 50,331,648 B,
89,228,277 bytes; two names outside Latin-1; one marker).
- Order 1: `pg_dump` 39,147 bytes; `docker compose down`; tar sha256 `7b924c81…5ab2`, modes 400/600; original and copy
  volume hash equal (67 files, `d89719b7…3182`), original unchanged at the end.
- Order 2 and 3: one `db-migrate` run, exit 0, 10.7 s: `0008 -> 0009`, `0009 -> 0010`, 30 values converted, runtime role
  applied, `k1=30` verified.
- Steps 4 to 7: initialiser exit 0 on `$NEW_VOL`; `copied: 16`; second run `already-present-and-matching: 16`; 16 of 16
  downloads with the status and SHA-256 of the old release (14 at 200, the two non-Latin-1 names 500 before and
  after); marker in 0 files; step 7 in a new shell; smoke **75 passed, 0 failed**.
- Teardown: `down -v --remove-orphans`, volumes, network, the project images and dangling images removed; container,
  volume (76), network (3) and image (287) lists equal to the start; `infra/.env` sha256 unchanged; `peaceful_pike`
  untouched; no `builder prune` or `system prune`.
- Not repeated on this path: the field-key rotation and the rollback (both done in round 1 on `f7d79fc`; the rollback
  text changed only in the name of the `.env` copy).

### Deviations (round 2)

- Step 1 now uses `docker compose down` instead of `docker stop`, and step 7 `up -d --build`: both found by the
  rehearsal from `4d57094`, neither in QA's list.
- The wrong-volume check is in the smoke test only (3c); no refusal in the initialiser.
- Records: CR-004 1.7 (D-9, `resolves` PRB-063, Scope row to TASK-204), PRB-063 1.1 (Impact widened, still `open` and
  `major`), TS-014 1.7. No TASK-204.

## QA review — round 2 (2026-11-02): CHANGES REQUESTED

All seven round-1 findings are closed (evidence below). One new MEDIUM remains, found by re-running
the rollback on the reference path, which the developer did not re-run. It fails safe (Compose
refuses, nothing changes) and the fix is a few lines of DEPLOY text, but it is the recovery path of
the "Ask first" procedure on the installation it is written for. No CRITICAL or HIGH.

1. **MEDIUM — the "Rollback" of "Separating the object-store SSE key" is wrong for an installation
   that comes from a release before CR-004** (`infra/DEPLOY.md:637-645`). It says: check out
   `f7d79fc`, put `$BKENV/env.before-sse` back as its `.env`, and start it on `$OLD_VOL`. On the
   reference path, `env.before-sse` is the pre-CR-004 `.env` (owner as `DATABASE_URL`, no
   `DATABASE_OWNER_URL`, no `AT_REST_ENCRYPTION_KEY_ID`). QA ran it verbatim: `up -d --build` exit 15,
   `required variable DATABASE_OWNER_URL is missing a value`. The text also says nothing about the
   database, which `db-migrate` has already taken to 0010 (descriptions now `mh1:k1:`), so the release
   the installation came from cannot read it without a restore.
   What works, run by QA:
   - `down` (no `-v`)
   - restore the `postgres_data` copy of the owner section, step 1
   - start the release the installation came from (`4d57094`) with `env.before-sse`

   Result: backend healthy, store on `qa196_object_store_data`, 5 of 5 downloads with the status and
   SHA-256 of before the upgrade, 3 of 3 descriptions identical.
   → Fix: split the Rollback by starting point.
   - (a) From `f7d79fc` (the earlier changes already in place): the current text.
   - (b) From a release before CR-004: `down` without `-v`, restore the step-1 `postgres_data` copy
     (or the `pg_dump` into an empty volume), start the release you came from with
     `$BKENV/env.before-sse` on `$OLD_VOL`. Point to "Upgrading an installation that connects as the
     owner", step 5, for the role note.

   Record the QA result above in the rehearsal result, or rehearse it yourself.
2. **LOW — step 1 of the procedure, as a code block, needs the old release's files.**
   `infra/DEPLOY.md` step 1 `docker compose -p "$P" -f infra/docker-compose.yml down` run from this
   release's files with the pre-upgrade `.env` stops at interpolation (`OBJECT_STORE_SSE_KEY must be
   set`). This is harmless, and "Order" item 1 says "from the old release's directory", but the code
   block does not. The `pg_dump` that the owner section asks for needs a running `postgres`, so it has
   to be taken before that `down`.
   → Fix: a comment on the `down` line ("with the files of the release you are leaving"), and "take the
   `pg_dump` first" in Order item 1.

### Round-1 findings: status

| R1 | Status | Evidence (QA round 2) |
|---|---|---|
| 1 Upgrade order | closed | The order was followed verbatim from `4d57094`: one `db-migrate` (`--exit-code-from`, nothing else started), `0008 -> 0009 -> 0010`, 3 values converted, `database roles applied for runtime role medhub_app`, `k1=3`, exit 0 |
| 2 Smoke timing | closed | Before step 7: 64/5, the five checks named in step 6. After step 7: **75/0** |
| 3 Volume | closed | (a) template and step 3 text; (b) step 4 `--force-recreate`, mount printed `qa196_object_store_data_sse`; (c) mistyped volume plus recreate: smoke 74/1 `the database has 5 attachment rows, the bucket 0 objects`; restored: 75/0. An open multipart upload does not change the count (5, 5, 5), so it cannot mask an empty volume; orphans can only raise it |
| 4 Fresh shell | closed | Steps 5 and 7 each ran in their own bash process, step 7 under `env -i`: `rekey down` exit 0, `up -d --build` exit 0, no `qa196-rekey` container left; step 4 `docker wait` printed `0` |
| 5 Zero-byte test | closed | The unconditional-Range mutation fails 1 test |
| 6 Error mapping | closed | Every probe error a wrong key: 3 failed; no re-list: 1; re-list that swallows: 2 |
| 7 Retention | closed | `$BK` and `$BKENV` created `drwx------`; `env.before-sse` 600 in `$BKENV`, not beside the tar. Docker Desktop shows the tar as 600, not 400, through its file sharing; on Linux it is 400. Plaintext and ORPHAN warnings present |

### QA verification (round 2)

All docker work ran in scratch projects `qa196` and `qa196-rekey`, from scratch trees:
`git archive 4d57094` (old), `git archive f7d79fc` (rollback test) and a copy of the working tree.
The scratch `.env` set `CORS_ORIGINS=[]` (PRB-056) and `SESSION_COOKIE_SECURE=false`.

- Seed on `4d57094` (owner connection, shared key, leftover `SESSION_SIGNING_KEY`): 3 entries and 5
  attachments, plus one orphan object put directly. The attachments were 0 B; 1 B; 42 B with a marker;
  5000 B `患者 report’s.pdf`, which answers 500 (PRB-063); and 3 MiB.
- Order 1 (from the old tree): `pg_dump -Fc` while the stack was up, then `down` (no `-v`). Every
  volume survived. Tar, `env.before-sse`, a `postgres_data` copy, and `$SRC_VOL` with a file-tree
  hash equal to `$OLD_VOL` (88 files).
- Order 2 and 3: the `.env` edits in the stated order, then the single `db-migrate` run above.
- Step 4: init exit 0. Step 5: `copied: 5`, `ORPHAN 01de1fc61fa6`, exit 0. Step 6.1: `copied: 0`,
  `already-present-and-matching: 5`.
- Step 6.2/6.3: 5 of 5 downloads with the status and SHA-256 they had before the upgrade (4 equal
  the upload). Marker found in 0 files of `$NEW_VOL`.
- Step 7, fresh shell: smoke 75/0, including "the object store holds every attachment". 5 of 5
  downloads identical, 3 of 3 descriptions identical. Only `object-store` and
  `object-store-preflight` hold the SSE value. `$OLD_VOL` hash unchanged.
- Rollback: as written, refused (finding 1). The owner-section way back: 5/5 and 3/3.
- Not re-run on this path: the k1→k2 rotation. Round 1 rehearsed it on the shipped Compose file, and
  nothing in it depends on the starting release.

| Check | Result |
|---|---|
| `uv run pytest --cov=app --cov-fail-under=85` | 1251 passed, 6 skipped, 94.13 % |
| `modules/dicom_viewer/tests` | 25 passed |
| ruff, black, mypy | clean |
| infra unittest | 99 OK |
| `-m object_store` against a scratch store | 6 passed |
| Mutations (12) | all caught (1 to 12 failures each), including the three new ones above |
| Traceability (TASK-196, TS-008/014/015, PRB-004/007/063, CR-004, SOUP-036, SR-041) | 0 errors, 34 warnings |

Teardown:
- `down -v --remove-orphans` of both projects.
- Scratch volumes and all `qa196*` and dangling QA images removed.
- Image, volume, network and container lists equal to the start.
- `infra/.env` sha256 `a4933b8c…96da` unchanged.
- `peaceful_pike` untouched. No prune.

TS-008/014/015 and SOUP-036 stay `in_review`. PRB-007 stays `open`.

## Implementation notes, round 3 (2026-11-02, software developer)

Text-only fix per human decision 2026-11-02, no QA re-review. No code, no tests, no stack runs; nothing staged or
committed. Only `infra/DEPLOY.md` changed, in "Separating the object-store SSE key":
- **Round 2 finding 1 (MEDIUM).** "Rollback" is split: (a) from `f7d79fc` (the previous text), (b) from a release before
  CR-004 (`4d57094`): `down` without `-v` with this release's files, restore the `postgres_data` copy of the owner section
  step 1, check out `4d57094` with `$BKENV/env.before-sse` as its `.env`, start it on `$OLD_VOL`, verify. QA's result is
  recorded (backend healthy, 5/5 downloads with matching status and SHA-256, 3/3 descriptions identical), with the
  warning that uploads accepted on the new volume are lost by a rollback, and a pointer to the role note.
- **Round 2 finding 2 (LOW).** The `down` line of step 1 carries a comment (files and `.env` of the release you are leaving);
  "Order" item 1 says the `pg_dump` is taken first because it needs a running `postgres`.
- The rollback (b) text is QA's verified sequence; I did not run it myself.

## Approval (2026-11-02)

Status set to `approved` by the orchestrator: approved by the human's decision of 2026-11-02 (CR-004 D-10: TASK-196 accepted with the QA round-2 text fix, no QA re-review).
