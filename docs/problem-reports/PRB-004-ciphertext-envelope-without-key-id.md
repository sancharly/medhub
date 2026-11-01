---
id: "PRB-004"
type: problem-report
title: "Ciphertext envelope carries no key identifier, so key rotation cannot be performed safely"
status: open
version: "1.3"
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

Planned in CR-004: TASK-193 (key identifier in the envelope, decryption under any configured
key, unknown key refused), TASK-194 (data migration of existing values to the identified
format), TASK-195 (re-encryption command, documented rotation, rehearsal on a backup copy). The
design is [ADR-0018](../design/adr/0018-field-encryption-key-identifier-and-key-separation.md).
Not yet fixed.

**Interim note (2026-11-01, TASK-193 handed to QA, status stays `open`).** The envelope now names
its key (`mh1:<kid>:` with the prefix as AES-GCM associated data), values under any configured key
decrypt, an unknown key id is refused, and the key id and retired keys are validated at start-up
(`backend/app/db/crypto.py`, `backend/app/core/config.py`, `backend/app/core/secret_settings.py`).
Still open: existing unprefixed values are unreadable through the ORM until TASK-194 converts
them (the window is accepted in CR-004 D-5: the branch is not merged, tagged or deployed to a
database holding field-encrypted values until TASK-194 lands), and the re-encryption command, documented rotation
and rehearsal (TASK-195) do not exist.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Medium.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.2 (2026-11-01) — Interim note on TASK-193 under "Resolution". Status unchanged.
- 1.3 (2026-11-01) — Interim note cites CR-004 D-5 instead of "ship together". Status unchanged.
