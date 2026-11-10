---
id: "PRB-004"
type: problem-report
title: "Ciphertext envelope carries no key identifier, so key rotation cannot be performed safely"
status: resolved
version: "1.7"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-01"
criticality: major
links: []
tags: ["security", "hazard:availability"]
---

# PRB-004 — Ciphertext envelope carries no key identifier, so key rotation cannot be performed safely

## Observed

`app/db/crypto.py` writes the AES-GCM envelope with no key id or version prefix, so no row records which key encrypted it. A rotation therefore cannot decrypt pre-rotation rows. Separately, no PHI column currently uses `EncryptedString`, so the field-level encryption scope is undefined.

## Impact

SR-022 (encryption in transit and at rest) is only partly realized: either rotation is avoided — leaving a possibly compromised key in use — or it silently orphans existing rows.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **The key-identifier defect is
present. The field-scope sentence of "Observed" is stale.**

- `backend/app/db/crypto.py:45-51` writes `base64url(nonce || ciphertext)` with no key
  identifier, version or associated data; `crypto.py:54-60` decrypts every value with the one
  key that `_get_key()` (`crypto.py:27-42`) reads from `AT_REST_ENCRYPTION_KEY`. With a second
  key there is no way to tell which key a stored value needs, so a rotation either keeps the old
  key in use or orphans every existing value (`InvalidTag`).
- The key is validated lazily, at the first encrypt or decrypt, not at start-up, although the
  docstring of `_get_key` (`crypto.py:31`) says "fails fast on startup". A wrong key is found by
  the first clinical read, not by the deployment.
- **Stale:** "no PHI column currently uses `EncryptedString`". `clinical_entry.description` uses
  it (`backend/app/db/models/clinical.py:23`, migration `0005_clinical_entry_description_encrypted.py`),
  and the scope decision is recorded in `crypto.py:6-14`. It is the only such column. Which other
  columns should be encrypted is outside CR-004 (CR-004 Q-2, decided 2026-10-31: no further
  columns in this CR).
- The object store derives its only SSE key from the same setting
  (`infra/docker-compose.yml:147`), so the same key protects both stores (PRB-007, SR-041 AC 5).

Not recommended for rejection: the key-identifier part stands.

## Safety evaluation

Contributes to RISK-011 (encryption or key-management failure) and RISK-007 (clinical information unavailable). No occurrence to date; no rotation has been attempted.

## Resolution

**Resolved (2026-11-01, QA approval of TASK-195, CR-004 D-8).** Fixed by CR-004 (which links this
PRB with `resolves`) in three tasks on branch `fix/review-2026-07-security`. The design is
[ADR-0018](../design/adr/0018-field-encryption-key-identifier-and-key-separation.md).

| Task | Commit | Change |
|---|---|---|
| TASK-193 | `3e9dee7` | Envelope `mh1:<kid>:<base64url(nonce‖ciphertext)>`, with `mh1:<kid>` as AES-GCM associated data. Decryption uses only the key the prefix names. An unknown id is refused. The key id and the retired keys are validated at start-up (`backend/app/db/crypto.py`, `backend/app/core/config.py`, `backend/app/core/secret_settings.py`) |
| TASK-194 | `7b665c2` | Migration 0010 (`backend/app/db/alembic/versions/0010_field_encryption_key_id.py`), run by `db-migrate`, converts every existing value to the envelope. It refuses, changing nothing, any value that does not decrypt |
| TASK-195 | the TASK-195 commit, the next one after `7b665c2` | Rotation command `python -m app.db.reencrypt` (`--check` exit 0/3/1, `--apply`, `--verify-key-ids`; `backend/app/db/reencrypt.py`). `db-migrate` runs `--verify-key-ids` as its last step, so a key that stored values still need cannot be removed. Procedure in `infra/DEPLOY.md`, "Field-encryption key rotation" |

To reproduce the verification, from `backend/`:

- `uv run pytest tests/db/test_crypto.py tests/db/test_crypto_known_answer.py tests/core/test_secret_settings.py tests/db/test_migration_0010_key_id.py tests/db/test_reencrypt.py -v`
  (TS-008 TC-008.9, TC-008.10, TC-008.11; Docker required);
- `cd ../infra && python3 -m unittest discover -s tests` (the `db-migrate` step order).

The rehearsals follow DEPLOY.md on scratch Compose projects. Steps and counts are in TASK-194 and
TASK-195 ("Rehearsal record", "QA verification"):
- k1→k2 with the application up;
- the same rotation on a restored backup copy;
- rotate-back k2→k1 after an interrupted `--apply`;
- premature removal of the old key, which `db-migrate` refused.

Every per-row plaintext SHA-256 matched before and after, and the smoke test passed (65 / 0).

Limits that remain (not part of this defect):
- ~~Do not run a rotation while the object store takes `AT_REST_ENCRYPTION_KEY` as its SSE key.~~
  Lifted by TASK-196 (2026-11-01): the store has its own `OBJECT_STORE_SSE_KEY`, refused when equal to a
  field key, and a rotation k1 to k2 was rehearsed on the shipped Compose file with 15 attachments that
  stayed readable at every step (`infra/DEPLOY.md`).
- A key is only as safe as its backup (PRB-057, open).
- `closed` is a release-time human step (CR-004 D-8).

**Interim note (2026-11-01, TASK-193 handed to QA, status stays `open`).** The envelope now names
its key (`mh1:<kid>:` with the prefix as AES-GCM associated data), values under any configured key
decrypt, an unknown key id is refused, and the key id and retired keys are validated at start-up
(`backend/app/db/crypto.py`, `backend/app/core/config.py`, `backend/app/core/secret_settings.py`).
Still open: existing unprefixed values are unreadable through the ORM until TASK-194 converts
them (the window is accepted in CR-004 D-5: the branch is not merged, tagged or deployed to a
database holding field-encrypted values until TASK-194 lands), and the re-encryption command, documented rotation
and rehearsal (TASK-195) do not exist.

**Interim note (2026-11-01, TASK-194 handed to QA, status stays `open`).** Migration 0010
(`backend/app/db/alembic/versions/0010_field_encryption_key_id.py`), run by `db-migrate` before the
backend starts, converts every existing unprefixed `clinical_entry.description` (the only
field-encrypted column) to `mh1:<id>:` under the current key, so the CR-004 D-5 window closes:
existing installations are readable again once `db-migrate` has run. It refuses, changing nothing and
naming the count and the row ids, any value that does not decrypt with the current key. Rehearsed on a
populated scratch database (1100 rows, all identical before and after) and on a restored copy. Still
open: the re-encryption command, documented rotation and its rehearsal (TASK-195); the defect stays
`open` until they exist.

**Interim note (2026-11-01, TASK-195 handed to QA, status stays `open`).** The re-encryption
command `python -m app.db.reencrypt` (`--check`, `--apply`, `--verify-key-ids`;
`backend/app/db/reencrypt.py`), the step-by-step rotation procedure with backup, rollback and the
refusal to drop a key that stored values still need (`infra/DEPLOY.md`, "Field-encryption key
rotation"), and its rehearsal exist: 1100 entries and 6 attachments rotated k1 to k2 with the
application up, per-row plaintext hashes identical, k1 removed, smoke test 65 passed; the same
rotation on a restored backup copy; removing k1 too early was refused. All three planned tasks
(TASK-193, 194, 195) are therefore implemented. The defect is not set `resolved` here: CR-004
(Scope, Out of scope) reserves that change for the human. Two things bear on that decision: the
rotation must not be run on an installation whose object store still takes
`AT_REST_ENCRYPTION_KEY` as its SSE key (rotating it made every attachment unreadable in the
rehearsal) until TASK-196 separates the two (done: see the next note), and the new key is only as safe as its backup
(PRB-057, still open).

**Interim note (2026-11-01, TASK-196 handed to QA, status stays `resolved`).** The object store's SSE key
is now its own setting, `OBJECT_STORE_SSE_KEY`; the preflight refuses it when it equals
`AT_REST_ENCRYPTION_KEY` or a retired key; `infra/DEPLOY.md` "Separating the object-store SSE key" moves
existing attachments by copy, and a rotation on the shipped Compose file left all attachments readable
and byte-identical. The rotation limit of the previous note no longer applies.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Medium.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.2 (2026-11-01) — Interim note on TASK-193 under "Resolution". Status unchanged.
- 1.3 (2026-11-01) — Interim note cites CR-004 D-5 instead of "ship together". Status unchanged.
- 1.4 (2026-11-01) — Interim note on TASK-194 under "Resolution". Status unchanged.
- 1.5 (2026-11-01) — Interim note on TASK-195 under "Resolution". Status unchanged.
- 1.6 (2026-11-01) — QA approved TASK-195 (round 2). The Resolution now covers TASK-193, 194 and 195; status `open` → `resolved` (CR-004 D-8). Criticality unchanged.
- 1.7 (2026-11-01) — TASK-196: the SSE-key limit on rotation lifted (TASK-196 separates the keys and rehearses a rotation with attachments). Status `resolved` and criticality unchanged.
