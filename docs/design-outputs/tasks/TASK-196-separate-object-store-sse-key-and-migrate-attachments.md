---
id: "TASK-196"
type: task
title: "Separate the object-store SSE key from the field key and migrate stored attachments"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-01"
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
