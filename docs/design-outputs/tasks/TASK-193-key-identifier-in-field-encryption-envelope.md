---
id: "TASK-193"
type: task
title: "Key identifier in the field-encryption envelope; decrypt under any configured key"
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
  - target: "PRB-056"
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
- **PRB:** PRB-004; PRB-056 (folded in by CR-004 D-6, round 2). **CR:** CR-004.
- **Depends on:** TASK-197 (key settings validated at start-up; both edit `config.py` and the
  secret rule). After Checkpoint C. **Gate** for TASK-194.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`backend/app/db/crypto.py`, `config.py`, `core/secret_settings.py`; 2 test files; TS-008)
- **Design:** [ADR-0018](../../design/adr/0018-field-encryption-key-identifier-and-key-separation.md)

## Scope added in round 2

PRB-056 (empty `CORS_ORIGINS` in the template breaks start-up) is in this task by CR-004 D-6: the
fix is in `backend/app/core/config.py` and `infra/.env.example`, with tests.

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
3. A public `decrypt_legacy(value, key)` (unprefixed, no AAD) exists **only** for TASK-194's
   migration and TASK-195's command, which import it across modules; it has no caller in `app/`
   and `EncryptedString` never calls it. (Amended in round 2: it was "private"; it is not,
   because TASK-194 needs it.)
4. `EncryptedString` (`backend/app/db/types.py`) is unchanged in shape; it calls the new functions.

## Tests (write first)

- `backend/tests/db/test_crypto.py`: round trip under the current key; a value written under a
  retired key decrypts after the current key changes; unknown kid → `UnknownKeyError`, and the
  ciphertext is not returned; edited kid in the prefix (valid other key) → `InvalidTag` (AAD
  binding); unprefixed value → `CiphertextFormatError`; the error text contains no plaintext.
- `backend/tests/db/test_crypto_known_answer.py`: a fixed key, nonce and kid give a fixed envelope.
- `backend/tests/core/test_secret_settings.py`: the key-id and retired-key rules.

## Acceptance criteria

- [x] SR-022 AC 6: identifier in every new value; any configured key decrypts; unknown key
      refused with an error, never decrypted with another key or returned as ciphertext
      (`backend/tests/db/test_crypto.py`).
- [x] SR-022 AC 3: key settings validated at start-up (`backend/tests/core/test_secret_settings.py`).

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

- [x] Backend suite passes; coverage ≥ 85 %.
- [x] TS-008 1.6, SOUP-011 `in_review`.
- [x] `traceability-check` shows no error for TASK-193, TS-008, SR-022.

## Implementation notes (2026-11-01, software developer)

**Envelope as built.** `mh1:<kid>:` + `base64url(nonce(12) || AES-256-GCM(key, nonce, plaintext, aad))`,
`aad = b"mh1:<kid>"`, `kid` matching `[a-z0-9-]{1,32}`. `decrypt` splits at the first two `:`,
finds the key by id in the keyring (current plus retired) and uses that key only. Errors:
`CiphertextFormatError` (no or malformed envelope, a key id outside the pattern is not echoed),
`UnknownKeyError(kid)` (message names the id only), `cryptography.exceptions.InvalidTag`.
`decrypt_legacy(value, key_bytes)` reads the unprefixed format and is called by nothing yet;
`EncryptedString` is unchanged.

**Files.** `backend/app/db/crypto.py` (envelope, `Keyring`, cached `_build_keyring`),
`backend/app/core/config.py` (`at_rest_encryption_key_id` required, `at_rest_encryption_retired_keys`
optional, a model validator that refuses a bad key ring), `backend/app/core/secret_settings.py`
(`key_id_problems`, `split_retired_keys`, `keyring_problems`; `check` and `settings_env` use them,
C3: both new values are read from Settings, not `os.environ`; the per-key 32-byte check is kept),
tests `backend/tests/db/test_crypto.py`, `test_crypto_known_answer.py`,
`backend/tests/core/test_secret_settings.py`; baseline test environments gain
`AT_REST_ENCRYPTION_KEY_ID`; `infra/docker-compose.yml`, `infra/.env.example`, `infra/DEPLOY.md`,
`.github/workflows/ci.yml`; infra tests `test_compose_settings_coverage.py` (new, R2-3),
`test_compose_secrets.py`, `test_compose_object_store.py`, `test_ci_compose_env.py`;
TS-008 1.6, SOUP-011 1.3, PRB-004 and PRB-056 interim notes.

**Retired keys format.** The task text says `id:base64key,...`; ADR-0018 says the same. The old
bare-key list (TASK-197, never wired to a reader) is replaced.

**Decisions to confirm.**
- With `decrypt_legacy` unused by `EncryptedString`, a database that already holds
  `clinical_entry.description` values cannot be read through the ORM until TASK-194 converts them.
  This window is accepted in CR-004 D-5 (human, 2026-11-01): the branch is not merged, tagged or
  deployed to a database holding field-encrypted values until TASK-194 lands. No start-up guard.
- `AT_REST_ENCRYPTION_KEY_ID` has a `:?` guard in backend, celery-worker, celery-beat and
  db-migrate; `AT_REST_ENCRYPTION_RETIRED_KEYS` is passed bare (no default, no guard), like
  `SMTP_PASSWORD`. The CI object-store step writes `AT_REST_ENCRYPTION_KEY_ID=ci`.
- `OBJECT_STORE_SSE_KEY` is the one entry in the R2-3 exception list (TASK-196 removes it).

**Verification results.**
- `cd backend && uv run pytest tests/db/test_crypto.py tests/db/test_crypto_known_answer.py tests/core -q`: 207 passed.
- `cd backend && uv run pytest --cov=app --cov-fail-under=85`: 1141 passed, 4 skipped, coverage 94.01 %.
- `cd backend && uv run pytest modules/dicom_viewer/tests`: 25 passed.
- `uv run ruff check .`, `uv run black --check .`, `uv run mypy app`: clean.
- `cd infra && python3 -m unittest discover -s tests`: 76 passed (one earlier run showed one failure whose output was not captured; three re-runs passed).
- Negative controls: (1) associated data replaced by `b""` in `_aad`: 3 failed
  (`test_edited_key_id_with_the_same_key_under_both_ids_fails_authentication` and both
  known-answer tests); (2) unknown id falling back to the current key: 2 failed
  (`test_unknown_key_id_is_refused_without_the_value`,
  `test_encrypted_string_refuses_an_unknown_key_instead_of_returning_ciphertext`); (3)
  `AT_REST_ENCRYPTION_KEY_ID` removed from celery-beat only:
  `test_every_setting_without_a_default_is_in_every_python_service` failed; (4)
  `AT_REST_ENCRYPTION_RETIRED_KEYS` removed from every service:
  `test_every_setting_is_in_some_python_service_or_excepted` failed. Each restored afterwards.

**Records for the human (approved, not edited).** ADD-016 (confirm `U-PER-Crypto` at 1.1, mention
the keyring and `decrypt_legacy`); SR-022 AC 6 text unchanged; ADR-0018 unchanged (matches the
build); RISK-011 and RISK-007 control evidence now includes TC-008.9; CR-004: PRB-056 is not
linked, see the PRB.

## QA review round 1 (QA engineer, 2026-11-01): CHANGES REQUESTED

Status `in_review` → `draft`. TS-008 1.6 stays `in_review`; SOUP-011 1.3 stays `in_review` (human).
The crypto core is sound: nonce from `os.urandom(12)` per call, AAD `mh1:<kid>` binds version and
id, the id pattern keeps `:` out of the prefix, no fallback, no key or plaintext in any message
or log, and the known-answer envelope reproduces with `AESGCM` directly. Every reported result
reproduced. The findings are at the edges.

### Findings

1. **HIGH: a key id with surrounding whitespace passes start-up validation, and every value written
   under it can never be read.** Location: `backend/app/core/secret_settings.py:97-99`
   (`key_id_problems` checks `key_id.strip()`), `:122`; used unstripped at
   `backend/app/core/config.py:52` → `backend/app/db/crypto.py:83`, `:92`.
   - **Evidence.** With `AT_REST_ENCRYPTION_KEY_ID="k1 "`, `Settings()` and `check(settings_env())`
     accept it. `encrypt` writes `mh1:k1 :…`. `decrypt` of that value raises `CiphertextFormatError`,
     because the stored id fails the pattern. A quoted value in `infra/.env` (`Q="k1 "`) reaches the
     container with its space (`docker compose config` shows `'k1 '`). A secret mounted from a file
     with a trailing newline would do the same.
   - **Effect.** Clinical descriptions are written, the request succeeds, and every later read
     returns 500 (RISK-007). SR-022 AC 3 says key settings are validated at start-up, but this
     invalid setting passes. Repairing the stored values needs custom code, because the AAD is
     bound to `mh1:k1 `.
   - **Fix.** Validate the value exactly as it will be used: no `.strip()` in the pattern check, so
     whitespace is refused with the existing message. Keep the empty or blank → "is not set" rule.
     Alternatively, normalise once with a `field_validator` that strips and stores the stripped id,
     and have `settings_env()` pass that stored value. Tests: `" k1"`, `"k1 "` and `"k1\n"` are
     refused by `check` and by `Settings()`. If you normalise instead, the round trip must work.
2. **MEDIUM: `infra/smoke-test.sh` no longer parses without an `infra/.env`.** Location:
   `infra/smoke-test.sh:24-29`.
   - **Cause.** The awk that fills throwaway values does not fill `AT_REST_ENCRYPTION_KEY_ID`.
   - **Evidence.** A scratch copy of the template and compose file went through that awk.
     `docker compose config -q` then exited 15 with "AT_REST_ENCRYPTION_KEY_ID must be set". The
     "docker-compose.yml is valid" check fails. The later `config`-based checks read empty output
     (their stderr is discarded).
   - **Fix.** Add `|| $1 == "AT_REST_ENCRYPTION_KEY_ID"` to the awk. Add an infra test that runs the
     same awk over `.env.example` into a temp dir and asserts `compose config` succeeds, so the next
     required setting cannot break it silently.
3. **MEDIUM: no recorded decision covers the window in which legacy rows become unreadable.**
   Location: CR-004 "Decisions" (`docs/change-requests/CR-004-…md:408`). The review brief, the
   task's "Decisions to confirm" and PRB-004 all rely on it.
   - **Gap.** D-4 covers only the window between TASK-190 and TASK-191, and its condition ("until
     TASK-191 lands") is already met.
   - **Window, as measured.** On a real database (scratch probe through `create_app()` and the real
     `get_db`), a pre-envelope `clinical_entry.description` row gives these responses. None of them
     returns ciphertext, and the log names only `CiphertextFormatError`, with no value.
     - `GET /api/v1/patients/{id}/clinical-entries`: generic RFC 7807 500.
     - `GET /api/v1/clinical-entries/{id}/attachments`: 500.
     - Upload to that entry: 500 by the same `ClinicalRepository.get` path
       (`attachments/service.py:48`). The DICOM module goes through it as well, via
       `PlatformServices.attachments`.
     - Nothing else reads `description` (no erasure or export path loads `ClinicalEntry`).
   - **Fix (human decision).** Record a D-5 in CR-004: the branch is not merged, tagged or deployed
     to a database holding field-encrypted values between the TASK-193 and TASK-194 commits. Then
     cite D-5 in this task and in the PRB-004 interim note, instead of "ship together".
   - **QA view.** A start-up guard is not needed once D-5 exists. After TASK-194, `db-migrate`
     (migration 0010) completes before `backend`, `celery-worker` and `celery-beat` start
     (`service_completed_successfully`), so the window closes structurally. A guard written now
     would be throw-away code.
4. **LOW: `parse` accepts non-canonical payloads, and its docstring says it refuses them.**
   Location: `backend/app/db/crypto.py:112-122`.
   - **Evidence.** `urlsafe_b64decode` is non-strict. A payload with an inserted `:` or `!`, a
     trailing newline, trailing junk after the padding, or the standard alphabet all decrypt to the
     plaintext (probe).
   - **Impact.** Authenticity is unaffected: GCM checks the bytes.
   - **Fix.** Use `base64.b64decode(parts[2], altchars=b"-_", validate=True)` with a test, or
     correct the docstring.
5. **LOW: "retired key equal to the current key" compares strings, not decoded keys.** Location:
   `backend/app/core/secret_settings.py:138`. The same 32 bytes in the standard alphabet
   (`openssl rand -base64 32` output) and in the URL-safe alphabet pass the check.
   - **Fix.** Compare `urlsafe_b64decode` results, after `_key_problem` has passed.
6. **LOW: `decrypt_legacy` is public; task item 3 says private.** Location:
   `backend/app/db/crypto.py:144`.
   - **Fix.** TASK-194's migration imports it across modules, so either rename it `_decrypt_legacy`
     or amend item 3 to "public, used only by TASK-194/195; no caller in `app/`". Optionally add a
     static test that only those two call it.
7. **LOW (carry to TASK-196): the R2-3 parser has silent gaps.** Location:
   `infra/tests/test_compose_settings_coverage.py:39`. Probe on synthetic lines:
   - `b: Annotated[str, Field(alias=…)]` is skipped entirely, because the annotation contains `=`.
   - `a: str = Field(...)` is classed as having a default.
   - `validation_alias`/`alias` names are ignored.

   None occurs in `config.py` today. **Fix:** count every `^    name:` line in the class body and
   assert that each one was parsed, and fail on `alias`/`Field(...)` until they are handled.

### Pre-existing issues (not blocking)

- `backend/tests/db/test_no_raw_sql.py:16-31` flags any f-string on a line with `from`, `where`,
  `select` and similar, case-insensitively. That makes ordinary English error messages false
  positives (the developer worded messages around it). Suggest matching upper-case keywords only,
  or only arguments to `text()`/`execute()`. LOW, for a later task.

### Assessment of the brief's other points

- **Settings, C3:** honoured. `settings_env()` reads both new values from `Settings`
  (`test_settings_env_reads_the_key_settings_from_settings_not_the_process_environment`). The
  retired-key rules cover all of these, and the messages never contain a key:
  - a duplicate id;
  - the current id reused;
  - a key equal to the current key (see 5);
  - the wrong length;
  - a placeholder;
  - no `id:`;
  - a bad id.
- **Keyring cache:** keyed on the setting values (`lru_cache(maxsize=8)`), so a test that changes
  settings gets a new ring. Production `get_settings()` is itself cached, so a stale ring is not
  possible.
- **Flaky infra failure:** not reproduced. 7 runs (4 sequential, 3 concurrent): 76/76 OK each.
- **PRB-056:** staying `open` is correct, because `Settings` still cannot read an empty or
  comma-separated `CORS_ORIGINS` outside Compose. QA recommends not linking it to CR-004 (it is
  outside CR-004's security scope). The human may instead fold it in as a small task. That is a
  human scope decision.
- **SOUP-011 1.3:** accurate. `AESGCM` with associated data and several keys, the only
  `cryptography` import in `app/`, re-checked. The approval fields were removed correctly, and it
  stays `in_review` for the human.

### Verification run (QA, 2026-11-01)

- `cd backend && uv run pytest tests/db/test_crypto.py tests/db/test_crypto_known_answer.py tests/core -q`: 207 passed.
- `cd backend && uv run pytest --cov=app --cov-fail-under=85`: 1141 passed, 4 skipped, 94.01 %.
- `cd backend && uv run pytest modules/dicom_viewer/tests`: 25 passed.
- `ruff check .`, `black --check .`, `mypy app`: clean. OpenAPI export identical to `backend/openapi/openapi.json`.
- `cd infra && python3 -m unittest discover -s tests`: 7 runs, 76 OK each.
- Known answer recomputed with `AESGCM` directly (cryptography 50.0.2): `mh1:` envelope and legacy
  envelope both match. AAD `b""` or `b"k1"` does not match.
- Negative controls (scratch copies of `backend/`):
  - Nonce made constant: 2 fail (`test_different_ciphertexts_for_same_plaintext` and the
    byte-identical known-answer test).
  - Key id dropped from the AAD (`aad = b"mh1"`): 3 fail (the same-key edited-id test and both
    `mh1` known-answer tests).
- Traceability (TASK-193, TS-008, SOUP-011, PRB-004, PRB-056, SR-022): 0 errors, 19 warnings
  (W5 on `in_review` SOUP/TS bases, W6 on obsolete SOUP; all pre-existing in kind).

## Round 2 (software developer, 2026-11-01): findings 1 to 7 addressed

Status `draft` → `in_review`, 1.2 → 1.3. D-5 and D-6 are recorded in CR-004 1.4.

1. **Whitespace in the key id (HIGH).** Chose to validate the exact value, not to normalise: the id
   is bound into the associated data, so what is configured must be what is written; silently
   rewriting `"k1 "` to `"k1"` would hide a mis-set secret and make two deployments with different
   raw values interchangeable. `key_id_problems` no longer strips (blank is still "is not set");
   the pattern uses `fullmatch`, so `"k1\n"` fails. Retired ids follow the same rule: the entry
   list is split on `,` without stripping, so `" k1:key"`, `"k1 :key"` and `"k1\n:key"` are
   refused (the key part is still stripped by its readers, as a file-mounted key ends in a
   newline). Tests: `test_key_id_with_surrounding_whitespace_is_refused_by_name`,
   `test_settings_refuse_a_key_id_with_surrounding_whitespace`,
   `test_retired_key_id_with_surrounding_whitespace_is_refused_by_name`,
   `test_settings_refuse_a_retired_key_id_with_surrounding_whitespace` (each for `" k1"`, `"k1 "`,
   `"k1\n"`).
2. **smoke-test.sh (MEDIUM).** `AT_REST_ENCRYPTION_KEY_ID` added to the awk fill. New
   `infra/tests/test_smoke_test_env.py` extracts the awk program from the script, runs it over
   `.env.example` and requires `docker compose config` to exit 0. While repeating the infra suite
   I also found the cause of the intermittent failure reported in round 1:
   `test_the_template_alone_is_refused` expected one of a fixed list of setting names in Compose's
   error, but Compose reports whichever guard it interpolates first, and the new key-id guard was
   not in the list. Added.
3. **D-5 (MEDIUM).** Recorded in CR-004 1.4 and cited here and in PRB-004 1.3.
4. **Canonical payload (LOW).** `parse` decodes with `b64decode(altchars=b"-_", validate=True)` and
   requires `urlsafe_b64encode(raw) == payload`. Tests: `test_non_canonical_payloads_are_refused`
   (trailing newline, `!`, junk after padding, stripped padding, leading space, standard
   alphabet), `test_a_colon_in_the_payload_is_refused`, `test_the_canonical_payload_still_decrypts`.
5. **Retired key equals current key (LOW).** Compares decoded bytes. Test
   `test_retired_key_equal_to_the_current_key_in_the_other_alphabet_is_refused`, both directions.
6. **`decrypt_legacy` (LOW).** Chose to amend item 3 (public, used only by TASK-194/195), not to
   rename: TASK-194 imports it across modules.
7. **PRB-056 (D-6).** Root cause: `cors_origins: list[str]` is a complex field, which
   pydantic-settings decodes as JSON before any validator, so an empty string failed and the
   template's "comma-separated" comment was wrong. Fix: `Annotated[list[str], NoDecode]` plus a
   `mode="before"` validator: empty or blank is `[]`, a value starting with `[` is parsed as JSON
   (a malformed list is refused), anything else is split on commas. The template comment now lists
   the three forms. The Compose default `${CORS_ORIGINS:-[]}` is no longer needed (`Settings`
   reads an empty value), so it is now `${CORS_ORIGINS:-}`, a plain pass-through with no warning
   when unset. Tests in `backend/tests/test_env_example.py`: the template itself loads through
   `Settings` with only the secrets filled; eight `CORS_ORIGINS` forms parse; unset is `[]`;
   malformed lists are refused.

**Verification (round 2).**
- Targeted: `pytest tests/db/test_crypto.py tests/db/test_crypto_known_answer.py tests/core tests/test_env_example.py tests/test_config.py`: 254 passed.
- Full backend with coverage: 1172 passed, 4 skipped, 94.05 %. DICOM: 25 passed.
- `ruff check .`, `black --check .`, `mypy app`: clean. Infra: 78 passed (15 consecutive runs).
- Negative controls: `.strip()` restored in the key-id check, the retired-entry split and the
  retired-id check: 14 whitespace tests failed. Non-canonical decoding restored
  (`urlsafe_b64decode`, no re-encode check): `test_non_canonical_payloads_are_refused` and
  `test_a_colon_in_the_payload_is_refused` failed. `AT_REST_ENCRYPTION_KEY_ID` removed from the
  awk: both tests in `test_smoke_test_env.py` failed (exit 15, "AT_REST_ENCRYPTION_KEY_ID must be
  set"). All restored.

**Carried.** The R2-3 parser gaps (Annotated, alias, `Field(...)` required) go to TASK-196; the
over-broad `test_no_fstring_sql` to TASK-201/202. Note: `cors_origins` is now `Annotated[...]`; the
R2-3 parser still reads it correctly (it has a default).

## QA review round 2 (QA engineer, 2026-11-01): APPROVED

Status `in_review` → `approved`. TS-008 1.6 → `approved`. SOUP-011 1.3 stays `in_review` (human).
All seven round-1 findings are closed and were re-verified independently. No CRITICAL, HIGH or
MEDIUM finding remains.

### Round-1 findings, re-checked

1. **Key id whitespace: closed.**
   - Measured: `key_id_problems` refuses `" k1"`, `"\tk1"`, `"k1 "` and `"k1\n"`. `Settings()` with
     `AT_REST_ENCRYPTION_KEY_ID="k1 "` now raises at start-up (the round-1 scratch probe).
   - A retired key with a trailing newline is still accepted; its key part is stripped.
   - Mutation: restoring `.strip()` in the pattern check alone fails 16 tests.
2. **Smoke-test awk: closed.**
   - `infra/tests/test_smoke_test_env.py` extracts the awk from the script itself.
   - Mutation: with the key id removed from a copy of the script, both tests fail (exit 15).
3. **D-5: closed.** CR-004 1.4 records it, and TASK-193, PRB-004 1.3 and DEPLOY.md cite it.
4. **Canonical payload: closed.**
   - All five round-1 forms now raise `CiphertextFormatError`: an inserted `:` or `!`, a trailing
     newline, junk after the padding, and the standard alphabet.
   - Mutation: restoring `urlsafe_b64decode` without the re-encode check fails 9 tests.
5. **Retired key equal to the current key: closed.** The same 32 bytes in the standard and the
   URL-safe alphabet are refused.
6. **`decrypt_legacy`: closed.** Item 3 was amended (public, used only by TASK-194/195).
7. **R2-3 parser gaps: carried.** Recorded in TASK-196, "Carried from the TASK-193 QA review".

### Round-2 findings

1. **LOW (carry to TASK-202): `CORS_ORIGINS` accepts values that are not origins.**
   Location: `backend/app/core/config.py:109-119`.
   - Measured: each of these becomes a single origin: `{"a":1}`, `"https://a.example"` (with its
     quotes), `null` and `*`. Each is a value that does not start with `[`, so it is comma-split.
   - Current risk: none. `cors_origins` is only logged (`backend/app/main.py:34`); no
     `CORSMiddleware` is installed, so no origin is ever allowed.
   - Fix, when CORS is wired: validate each entry as `scheme://host[:port]` (no path, no `*`) and
     refuse anything else, naming the setting.
2. **LOW (carry to TASK-202): the PRB-056 tests are in no test specification.** The tests in
   `backend/tests/test_env_example.py` (the template loads, the eight `CORS_ORIGINS` forms, unset,
   malformed) back PRB-056 `resolved` and SR-041 AC 4. TS-015 TC-015.4 (`approved` 1.4) does not
   name them.
   - Fix: add them to TC-015.4 in the next TS-015 revision, before PRB-056 is closed.
3. **LOW (observation): a space after a comma in `AT_REST_ENCRYPTION_RETIRED_KEYS` is refused** as
   "has an invalid key id". This fails safe, and DEPLOY.md says ids have no spaces. A hint in the
   message ("no whitespace") would help the operator.

### Other checks

- **Flaky infra test: the explanation holds.** Thirty `docker compose config` runs over the
  unfilled template named the first guard Compose reached:

  | Guard named first | Runs |
  |---|---|
  | `OBJECT_STORE_ACCESS_KEY` | 13 |
  | `POSTGRES_PASSWORD` | 6 |
  | `OBJECT_STORE_SECRET_KEY` | 4 |
  | `AT_REST_ENCRYPTION_KEY_ID` | 3 |
  | `AT_REST_ENCRYPTION_KEY` | 2 |
  | `DATABASE_OWNER_URL` | 1 |
  | `DATABASE_URL` | 1 |

  The old regex could not match `AT_REST_ENCRYPTION_KEY_ID must be set`, so it failed in about 1
  run in 10. The regex now lists all 7 `:?` guards in the Compose file.
- **PRB-056 Resolution reproduces.** HEAD's `config.py` (scratch copy) gives `SettingsError` for an
  empty value and for a comma-separated one. The working tree gives `[]` and the list. A trailing
  comma and whitespace around entries are dropped. Empty is `[]` for every service: only `backend`
  receives `CORS_ORIGINS`, and the others use the default `[]`.
- **CR-004 1.4.** The edit is limited to the D-5 and D-6 text, the `resolves` PRB-056 link, the
  Scope row and the history line.

### Verification run (QA, round 2)

- Targeted (`tests/db/test_crypto.py`, `test_crypto_known_answer.py`, `tests/core`,
  `tests/test_env_example.py`): 244 passed.
- Full with coverage: 1172 passed, 4 skipped, 94.05 %. DICOM: 25 passed.
- `ruff`, `black --check`, `mypy app`: clean. OpenAPI export unchanged.
- Infra: 6 consecutive runs, 78 OK each.
- QA negative controls (scratch copies, same targeted set):

  | Mutation | Tests failed |
  |---|---|
  | Key-id strip restored | 16 |
  | Lax decode | 9 |
  | `NoDecode` removed from `cors_origins` | 12 |
  | Constant nonce | 9 |
  | Key id dropped from the AAD | 10 |
  | Key id removed from the smoke awk | 2 |

- Traceability (TASK-193, TS-008, SOUP-011, PRB-004, PRB-056, CR-004, SR-022): 0 errors, 30
  warnings (W5/W6 kinds as in round 1).
