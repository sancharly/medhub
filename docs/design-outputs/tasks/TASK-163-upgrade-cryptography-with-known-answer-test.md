---
id: "TASK-163"
type: task
title: "Upgrade cryptography to 50.0.2 behind a known-answer decryption test"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-29"
links:
  - target: "SR-022"
    relation: implements
  - target: "SR-028"
    relation: implements
  - target: "RISK-011"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-003"
    relation: relates_to
  - target: "PRB-047"
    relation: relates_to
  - target: "SOUP-011"
    relation: relates_to
tags: ["soup", "maintenance", "security", "cr:CR-003", "issue:sancharly/medhub#32", "control:design", "control:protective"]
---

# TASK-163 — Upgrade cryptography to 50.0.2 behind a known-answer decryption test

- **Software item / unit:** SI-PERSIST `U-PER-Crypto` (`backend/app/db/crypto.py`, ADD-016,
  SR-022); SI-DEVINFRA `U-INF-Toolchain` (`backend/uv.lock`)
- **Depends on:** none. It must be committed before TASK-164, because both change
  `backend/uv.lock`. It can be worked in parallel with TASK-161 and TASK-162.
- **Branch:** `bug/soup-upgrades`
- **Size:** M
- **Needs:** network access (PyPI, OSV, GitHub Advisory Database, NVD, OpenSSL advisories). A
  Docker daemon is needed only for the *real DB* tests of the full suite.

## Objective

Resolve the cryptography part of PRB-047: 49.0.0 carries GHSA-g6cj-pr64-35w5 (PKCS#7
decryption oracle). Move to **50.0.2** (CR-003 D-3).

Before upgrading, prove that field values already encrypted at rest under 49.0.0 still decrypt
after the upgrade (Q-4, AC-9, §7.4.3). This keeps RISK-011's and RISK-001's AES-256-GCM
field-encryption control verified across a change of the SOUP item it runs on. That control is
"AES-256-GCM field encryption at rest", and its harm is "old rows fail to decrypt".

## Interfaces to honor

- `app.db.crypto.encrypt(value: str) -> str` and `decrypt(value: str) -> str`, with the envelope
  `urlsafe_b64(nonce[12] ‖ ciphertext ‖ tag[16])`. No change to `crypto.py`.
- `cryptography>=42.0.0` in `backend/pyproject.toml` stays (A-6). The lock is the pin.
- Lock scope (AC-7, Boundaries): only `cryptography` changes, plus any package that 50.0.2
  requires. Each such package is named with its old and new versions.

## Tests (write first, under the current lock)

Write and commit the known-answer test **before** touching `backend/uv.lock`, so that its fixture
is produced under cryptography 49.0.0. If the fixture were generated after the upgrade, it would
prove nothing about data at rest.

1. Confirm the version: `cd backend && uv run python -c "import cryptography; print(cryptography.__version__)"`
   must print `49.0.0`.
2. Generate the fixture with MedHub's own `encrypt`, from a fixed test key, nonce and plaintext.
   Patch `os.urandom` only for the nonce. Run it as a scratch script, outside the repository:
   - key: 32 fixed bytes, URL-safe base64. A test value, never a real key.
   - nonce: 12 fixed bytes.
   - plaintext: a UTF-8 clinical-style string with non-ASCII characters, for example
     `"Nota clínica: dolor torácico — paciente José Núñez"`.

   Record the printed `cryptography.__version__` and the output envelope.
3. New test `backend/tests/db/test_crypto_known_answer.py`. Follow the settings patch used by
   `tests/db/test_crypto.py` (monkeypatch `app.db.crypto.get_settings`).
   - Keep the key, nonce, plaintext and envelope as module constants (committed test data). The
     module docstring states that the envelope was produced under cryptography 49.0.0 on
     `<date>`, by the procedure above (AC-9).
   - `test_decrypts_ciphertext_written_under_49_0_0`: `decrypt(ENVELOPE) == PLAINTEXT`.
   - `test_encrypt_is_byte_identical_for_fixed_nonce`: `encrypt(PLAINTEXT)` with `os.urandom`
     patched to return `NONCE` equals `ENVELOPE`. AES-GCM is deterministic for a fixed key and
     nonce, so this also shows that the new version writes data the old version could read.
   - `test_tampered_tag_is_rejected`: flip one byte of the tag, and `decrypt` raises
     `cryptography.exceptions.InvalidTag`, never partial plaintext (TS-008 fault-handling
     criterion).
4. Run the tests under 49.0.0: all pass. Commit nothing else yet. Then go to the upgrade.

## Implementation detail

1. `cd backend && uv lock --upgrade-package cryptography==50.0.2`. Inspect `git diff backend/uv.lock`:
   - only `cryptography` (49.0.0 → 50.0.2, with its wheel hashes) may change;
   - cffi 2.0.0 and pycparser 3.0 stay unless 50.0.2 requires otherwise, in which case they are
     named here.

   Revert any other change and constrain the resolution instead. Then run `uv lock --check`.
2. `uv sync --frozen`, then the known-answer test, `tests/db/test_crypto.py` and the full suite.
3. **AC-8 (cryptography part).** In a scratch `--no-dev` environment,
   `importlib.metadata.version("cryptography") == "50.0.2"`. The image check for all three
   packages is in TASK-164.
4. **SOUP-011.** It is approved, so set `version` 1.2, remove the approval record and set
   `in_review`.
   - `soup_version: "50.0.2"`, and update the heading.
   - Environment section: cffi and pycparser at the locked versions, and the bundled OpenSSL as
     the changelog states it (50.0.2 wheels are built with OpenSSL 4.0.3).
   - **Anomaly list review** at 50.0.2, dated on or after 2026-10-29. Use the sources of the
     2026-10-22 review, by name and URL:
     - OSV (PyPI) for `cryptography` 50.0.2, `cffi` and `pycparser`;
     - the GitHub Advisory Database;
     - NVD;
     - https://cryptography.io/en/latest/changelog/;
     - OpenSSL vulnerabilities for 4.0.3.

     List each applicable anomaly with a hazard-relevance judgement, or state "none found".
     Record GHSA-g6cj-pr64-35w5 as fixed at 50.0.0. Set `anomaly_review`.
   - Change-log entry `2026-10-29 — 49.0.0 → 50.0.2; PRB-047, CR-003 (D-3)`.
   - The body must not state 49.0.0 as current (AC-13).
5. **RISK-011** (D-5). It is approved, so set `version` 1.2, remove the approval record and set
   `in_review`.
   - "Software items involved": replace `SOUP: cryptography 49.0.0, MinIO.` with
     `SOUP: cryptography (SOUP-011), MinIO (SOUP-022); versions in the SOUP records.`
   - Add `TS-008 TC-008.5` to the "Verified by" cell of the AES-256-GCM row.
   - Add a version-history entry citing CR-003. The scores do not change.
6. **TS-008.** Use the version set by TASK-162. If TASK-162 has not landed yet, bump to 1.1 here,
   clear the approval record and set `in_review`. Add:
   `TC-008.5 | SR-022 | backend/tests/db/test_crypto_known_answer.py | A field value encrypted under cryptography 49.0.0 decrypts to its original plaintext under the locked version, and the locked version produces the identical envelope for the same key and nonce | Both assertions pass; a tampered tag raises InvalidTag`.
   Note in "Notes" that the fixture comes from 49.0.0 (CR-003 AC-9).
7. **CR-003 Escalations**: add any hazard-relevant or MedHub-affecting finding of step 4, or
   "none" for SOUP-011.

## Acceptance criteria

- [ ] CR-003 **AC-7** (cryptography part): `uv.lock` resolves cryptography 50.0.2 and
      `uv lock --check` succeeds. The lock diff changes nothing else, or names each required
      package with its old and new versions.
- [ ] CR-003 **AC-8** (cryptography part): the `--no-dev` environment reports 50.0.2.
- [ ] CR-003 **AC-9**: the known-answer test, with its fixture produced under 49.0.0, passes under
      50.0.2 in the CI `backend-tests` job, and is recorded as TS-008 TC-008.5.
- [ ] CR-003 **AC-13** and **AC-14** for SOUP-011, as in step 4.

## Verification

```sh
cd backend && uv run pytest tests/db/test_crypto_known_answer.py -v       # before the lock change: passes on 49.0.0
cd backend && uv lock --upgrade-package cryptography==50.0.2 && git diff --stat uv.lock && uv lock --check
cd backend && uv sync --frozen && uv run pytest tests/db/test_crypto_known_answer.py tests/db/test_crypto.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85
cd backend && UV_PROJECT_ENVIRONMENT="$(mktemp -d)/venv" sh -c 'uv sync --frozen --no-dev && "$UV_PROJECT_ENVIRONMENT/bin/python" -c "import importlib.metadata as m; print(m.version(\"cryptography\"))"'
```

Record the 49.0.0 run and the 50.0.2 run of the known-answer test, with
`cryptography.__version__` printed in each.

## Definition of Done

- [ ] `ruff`, `black --check` and `mypy app` pass. The backend suite passes with coverage ≥ 85 %.
- [ ] SOUP-011, RISK-011 and TS-008 are `in_review`.
- [ ] `traceability-check` shows no error for the touched records.
