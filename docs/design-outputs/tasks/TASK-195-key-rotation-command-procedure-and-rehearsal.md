---
id: "TASK-195"
type: task
title: "Key rotation: re-encryption command, documented procedure, rehearsal on a backup copy"
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

- [ ] SR-022 AC 8: the procedure is in `infra/DEPLOY.md` and its command is tested
      (`backend/tests/db/test_reencrypt.py`).
- [ ] SR-022 AC 8: the rotation is rehearsed on a restored backup copy of a populated database:
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

- [ ] Tests pass; rehearsal recorded and presented to the human.
- [ ] TS-008 `in_review`; PRB-004 `resolved`.
- [ ] `traceability-check` shows no error for TASK-195, TS-008, SR-022, PRB-004.
