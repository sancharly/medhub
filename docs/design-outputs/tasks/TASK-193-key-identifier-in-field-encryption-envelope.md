---
id: "TASK-193"
type: task
title: "Key identifier in the field-encryption envelope; decrypt under any configured key"
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
  - target: "TASK-197"
    relation: relates_to
  - target: "ADD-016"
    relation: relates_to
tags: ["security", "encryption", "cr:CR-004", "control:design"]
---

# TASK-193 — Key identifier in the field-encryption envelope; decrypt under any configured key

- **Software item / unit:** SI-PERSIST `U-PER-Crypto` (ADD-016).
- **PRB:** PRB-004. **CR:** CR-004.
- **Depends on:** TASK-197 (key settings validated at start-up; both edit `config.py` and the
  secret rule). After Checkpoint C. **Gate** for TASK-194.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`backend/app/db/crypto.py`, `config.py`, `core/secret_settings.py`; 2 test files; TS-008)
- **Design:** [ADR-0018](../../design/adr/0018-field-encryption-key-identifier-and-key-separation.md)

## Objective

SR-022 AC 6: every field-level ciphertext names its key; new values use the current key; values
under any configured key decrypt; a value whose key id matches no configured key is refused and
never decrypted with another key or returned as ciphertext.

## Implementation detail

1. Settings: `at_rest_encryption_key_id: str` (required, `^[a-z0-9-]{1,32}$`),
   `at_rest_encryption_retired_keys: SecretStr | None` (`id:base64key,…`). The secret rule
   (TASK-197) refuses duplicate ids, wrong-length keys and a retired key equal to the current one.
2. `crypto.py`: a `Keyring` (current id and key, retired keys by id) built once from settings.
   `encrypt(value)` → `f"mh1:{kid}:" + base64url(nonce || AESGCM(key).encrypt(nonce, value, aad))`
   with `aad = f"mh1:{kid}".encode()`. `decrypt(value)`: parse `mh1:<kid>:<payload>`; missing
   prefix → `CiphertextFormatError`; unknown kid → `UnknownKeyError(kid)`; tag failure →
   `InvalidTag`. Messages name the key id, never the value. No fallback.
3. A private `decrypt_legacy(value, key)` (unprefixed, no AAD) exists **only** for TASK-194's
   migration and TASK-195's command; `EncryptedString` never calls it.
4. `EncryptedString` (`backend/app/db/types.py`) is unchanged in shape; it calls the new functions.

## Tests (write first)

- `backend/tests/db/test_crypto.py`: round trip under the current key; a value written under a
  retired key decrypts after the current key changes; unknown kid → `UnknownKeyError`, and the
  ciphertext is not returned; edited kid in the prefix (valid other key) → `InvalidTag` (AAD
  binding); unprefixed value → `CiphertextFormatError`; the error text contains no plaintext.
- `backend/tests/db/test_crypto_known_answer.py`: a fixed key, nonce and kid give a fixed envelope.
- `backend/tests/core/test_secret_settings.py`: the key-id and retired-key rules.

## Acceptance criteria

- [ ] SR-022 AC 6: identifier in every new value; any configured key decrypts; unknown key
      refused with an error, never decrypted with another key or returned as ciphertext
      (`backend/tests/db/test_crypto.py`).
- [ ] SR-022 AC 3: key settings validated at start-up (`backend/tests/core/test_secret_settings.py`).

## Verification

```sh
cd backend && uv run pytest tests/db/test_crypto.py tests/db/test_crypto_known_answer.py tests/core -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

Negative control: fall back to the current key on an unknown kid; the refusal test fails.

## Records

- **TS-008** → 1.6 (`in_review`, first CR-004 task to change it): TC-008.9 (envelope, multi-key,
  unknown key refused), `verifies` SR-022. TASK-194 and TASK-195 add TC-008.10, TC-008.11.
- **SOUP-011** (cryptography): AESGCM with associated data is now relied on; `in_review`.
- **ADD-016** 1.1: confirm `U-PER-Crypto`.

## Definition of Done

- [ ] Backend suite passes; coverage ≥ 85 %.
- [ ] TS-008 1.6, SOUP-011 `in_review`.
- [ ] `traceability-check` shows no error for TASK-193, TS-008, SR-022.
