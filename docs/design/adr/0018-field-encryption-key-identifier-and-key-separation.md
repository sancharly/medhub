# ADR-0018: Field-encryption envelope with a key identifier, key rotation, and a separate object-store SSE key

## Status

Accepted (2026-10-31, CR-004 plan gate: the human approved the plan). Proposed earlier the
same day by the Software Architect role. It refines
[ADR-0011](0011-security-compliance-approach.md) (encryption at rest) and
[ADR-0015](0015-object-store-component-after-minio.md) D2 (the store's SSE key).

## Context

- SR-022 AC 6 to AC 8 (1.5): every field-level ciphertext names its key; values under any
  configured key decrypt, an unknown key is refused; no existing value becomes unreadable; a
  documented rotation rehearsed on a backup copy.
- SR-041 AC 5: the field-encryption key and the object-store SSE key are separate settings,
  refused when equal; attachments stored before the separation stay readable. CR-004 Q-3
  (2026-10-31): in this CR, with a rehearsed migration.
- Today the envelope is `base64url(nonce || ciphertext)` with no identifier
  (`backend/app/db/crypto.py:45-60`), one column uses it (`clinical_entry.description`), and the
  object store takes `AT_REST_ENCRYPTION_KEY` as its only SSE key (`infra/docker-compose.yml:147`).
  A different SSE key on the same volume makes every object unreadable (SOUP-036 F-4).

## Options

**Envelope.**

1. A prefix `mh1:<key-id>:<base64url(nonce || ciphertext)>`, with `mh1:<key-id>` as AES-GCM
   associated data.
2. A binary header inside the base64 payload (version byte, key-id byte).
3. A separate `key_id` column per encrypted column.

**Existing values.**

- (a) Re-encrypt every existing value in a data migration.
- (b) Keep reading unprefixed values forever as "legacy, current key".

**SSE key separation.**

- (i) Copy every object from a store started on the old volume with the old key to a store on a
  new volume with the new key.
- (ii) Change the key in place.

## Decision

- **Envelope: option 1.** `:` is not in the base64url alphabet, so a prefixed value can never be
  mistaken for an unprefixed one. Binding the prefix as associated data means an edited key id
  fails authentication instead of selecting a different key. A string format keeps the column
  type and needs no schema change (option 3 would, per column).
- **Keys as settings.** `AT_REST_ENCRYPTION_KEY` stays the current key (SR-041 AC 3 names it). New:
  `AT_REST_ENCRYPTION_KEY_ID`, the current key's identifier (`[a-z0-9-]{1,32}`, required), and
  `AT_REST_ENCRYPTION_RETIRED_KEYS`, an optional comma-separated `id:base64key` list, used for
  decryption only. Start-up refuses duplicate ids, a key that does not decode to 32 bytes, and a
  retired key equal to the current one.
- **Decrypt rule.** Parse the prefix, find the key by id among current and retired keys, and
  decrypt with that key only. No prefix, an unknown id or a failed tag raises an error that names
  the key id and never the value. Nothing falls back to another key or returns ciphertext.
- **Existing values: option (a).** Migration 0010 (run by `db-migrate`, ADR-0017) re-encrypts every
  unprefixed `clinical_entry.description` under the current key in one transaction. If any value
  does not decrypt with the current key, the migration fails and rolls back, so the database is
  never half-converted. Option (b) was rejected because it keeps an unidentified format alive
  indefinitely, contrary to AC 6.
- **Rotation.** A command `python -m app.db.reencrypt` with `--check` (counts values per key id,
  exit 1 if any value names a key that is not configured) and `--apply` (re-encrypts, in batches,
  every value whose key id is not current, reading each value back before commit). The procedure in
  `infra/DEPLOY.md`: back up; add the new key as current and the old one as retired; restart;
  `--apply`; `--check` shows only the current id; remove the retired key. It is rehearsed against a
  restored backup copy of a populated database and the result goes into the next test report.
- **SSE key: option (i).** New secret setting `OBJECT_STORE_SSE_KEY` (base64 of 32 random bytes)
  feeds `WEED_S3_SSE_KEY`. The preflight refuses it when it equals `AT_REST_ENCRYPTION_KEY`
  (compared as decoded bytes). Existing attachments are moved with the CR-002 tool
  `backend/scripts/migrate_object_store.py`: the source is a store started on a copy of the old
  volume with the old key, the target a store on a new volume with the new key; every object's
  SHA-256 is compared with the `attachment.checksum` row before and after the write, and the
  source is only read. Option (ii) does not exist: SeaweedFS has no in-place SSE re-key (F-4). A
  later SSE rotation follows the same copy procedure.

## Consequences

### Positive

- A compromised or ageing field key can be replaced without orphaning a row (RISK-011, RISK-007).
- A compromise or loss of one key no longer reaches both stores (RR-003, SR-041 AC 5).
- Every failure mode fails loudly and before data is changed: refused start-up, failed migration
  with rollback, `--check` exit 1.

### Negative

- Two data migrations touch production data: migration 0010 (fields) and the object copy
  (attachments). Each is a CR-004 "ask first" step and is rehearsed on a backup copy first.
- The operator now holds two keys plus, during a rotation, a retired key. DEPLOY.md documents
  generation and custody. No backup procedure exists yet (PRB-057), so losing a key still loses
  the data it protects.
- Each ciphertext grows by the prefix (about 10 bytes).

### Neutral

- Which further columns are encrypted is out of scope (CR-004 Q-2); new columns use the same
  envelope.

## Alternatives considered

Envelope options 2 and 3, existing-values option (b) and SSE option (ii), above. A key-management
service (KMS, Vault) was not considered further: it is a new runtime component that ADR-0010's
single-host deployment does not carry.

## References

- Requirements: SR-022 AC 3, AC 6 to AC 8; SR-041 AC 3, AC 5; RR-003; NFR-007
- Problem reports: PRB-004, PRB-007, PRB-057
- Risks: RISK-011, RISK-007
- SOUP: SOUP-011 (cryptography), SOUP-036 (SeaweedFS)
- Related: ADR-0011, ADR-0015, ADR-0017; ADD-016, ADD-025, ADD-026
