---
id: "TASK-163"
type: task
title: "Upgrade cryptography to 50.0.2 behind a known-answer decryption test"
status: approved
version: "1.1"
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

- [x] CR-003 **AC-7** (cryptography part): `uv.lock` resolves cryptography 50.0.2 and
      `uv lock --check` succeeds. The lock diff changes nothing else, or names each required
      package with its old and new versions.
- [x] CR-003 **AC-8** (cryptography part): the `--no-dev` environment reports 50.0.2.
- [x] CR-003 **AC-9**: the known-answer test, with its fixture produced under 49.0.0, passes under
      50.0.2 in the CI `backend-tests` job, and is recorded as TS-008 TC-008.5.
- [x] CR-003 **AC-13** and **AC-14** for SOUP-011, as in step 4.

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

- [x] `ruff`, `black --check` and `mypy app` pass. The backend suite passes with coverage ≥ 85 %.
- [x] SOUP-011, RISK-011 and TS-008 are `in_review`.
- [x] `traceability-check` shows no error for the touched records.

## Implementation evidence (developer, 2026-10-29)

Handed to QA as `in_review`. No checkbox above is ticked: that is QA's approval.

**Known-answer fixture (AC-9).** Generated before the lock changed, under the locked cryptography
49.0.0, by a scratch script outside the repository that calls MedHub's own `app.db.crypto.encrypt`:

```sh
cd backend
uv run python -c "import cryptography; print(cryptography.__version__)"        # 49.0.0
PYTHONPATH=. uv run python <scratchpad>/gen_kat_fixture.py                      # prints the lines below
# cryptography.__version__ = 49.0.0
# KEY_B64 = AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=      (bytes 0x00..0x1f; test value)
# NONCE_HEX = a0a1a2a3a4a5a6a7a8a9aaab                         (bytes 0xa0..0xab; test value)
# ENVELOPE = oKGio6SlpqeoqaqrqHcITGWobnzPC-6wZkDguh_ANmKywy0eX69F7xzEVeNS4mePzkE6WDHoYehDFfA67jsIi9gTqxs7MiPYZfXcEUkt4G4jS5k_QA==
```

The script replaces `app.db.crypto.get_settings` with a stub that returns the fixed key, patches
`app.db.crypto.os.urandom` to return the fixed nonce (the only patch), encrypts
`"Nota clínica: dolor torácico — paciente José Núñez"` and asserts that `decrypt` returns it. The
key, nonce, plaintext and envelope are the module constants of
`backend/tests/db/test_crypto_known_answer.py`, whose docstring states the 49.0.0 origin.

**KAT under 49.0.0 (before the lock change).** `cryptography.__version__` printed `49.0.0`;
`uv run pytest tests/db/test_crypto_known_answer.py -v`: 3 passed.

**Lock change (AC-7).** `uv lock --upgrade-package cryptography==50.0.2` printed
`Updated cryptography v49.0.0 -> v50.0.2` and nothing else. `git diff --stat backend/uv.lock`:
55 insertions, 42 deletions, all inside the `cryptography` package block (version, sdist, wheel
URLs and hashes). `cffi` 2.0.0 and `pycparser` 3.0 are unchanged, and no package was added or
removed. `backend/pyproject.toml` is unchanged (floor `>=42.0.0`, A-6). `uv lock --check`:
`Resolved 86 packages`, exit 0.

**KAT under 50.0.2.** After `uv sync --frozen`, `cryptography.__version__` printed `50.0.2`;
`uv run pytest tests/db/test_crypto_known_answer.py tests/db/test_crypto.py -v`: 9 passed
(3 known-answer + 6 existing). The installed wheel reports `OpenSSL 4.0.3 29 Sep 2026`.

**Full suite and static checks, under 50.0.2** (`DOCKER_CONTEXT=desktop-linux`, so the real-DB
tests ran): `uv run pytest --cov=app --cov-fail-under=85`: 499 passed, coverage 91.71 %.
`ruff check .`, `black --check .` and `mypy app` pass.

**`--no-dev` environment (AC-8, cryptography part).** `uv sync --frozen --no-dev` into a scratch
`UV_PROJECT_ENVIRONMENT`, then `importlib.metadata.version` printed `50.0.2` for cryptography
(`2.0.0` for cffi, `3.0` for pycparser). The image check for all three packages is TASK-164's.

**Records.** SOUP-011 1.2 (`soup_version` 50.0.2, review of 2026-10-29), RISK-011 1.2 (body line
and TC-008.5 reference, scores unchanged), and TS-008 (version 1.1 was already set by TASK-162; it
gains TC-008.5 and a note) are `in_review`. CR-003 "Escalations" gains the TASK-163 entry: none for
SOUP-011. Out-of-task: PRB-050 opened (frontend has no `.dockerignore`, found by QA of TASK-162),
also listed in the CR escalations. PRB-047 is not touched: it resolves in TASK-164.

## QA review (2026-10-29)

**Verdict: APPROVED** (`in_review → approved`). There is no CRITICAL, HIGH or MEDIUM finding. QA
re-ran every claim on the reference workstation (`desktop-linux` context, arm64). SOUP-011,
RISK-011 and TS-008 are sound, but QA leaves them `in_review` under CR-003 AC-19, and the human
approves them at CR close. The CI part of AC-9 (`backend-tests` collects
`tests/db/test_crypto_known_answer.py` through `uv run pytest`, `.github/workflows/ci.yml:105`)
is confirmed on the branch head by TASK-168 (AC-18).

**Independent KAT provenance (AC-9).**
- QA built a scratch copy of `backend/` (no `.venv`) with the committed `HEAD:backend/uv.lock`,
  then ran `uv sync --frozen` into a scratch venv. That venv printed
  `cryptography 49.0.0, OpenSSL 4.0.1 9 Jun 2026`.
- A QA-written script (not the developer's) called `app.db.crypto.encrypt` there, with key bytes
  `0x00..0x1f`, nonce `0xa0..0xab` and the same plaintext. It patched only `get_settings` and
  `os.urandom`. The envelope it printed is **byte-identical** to `ENVELOPE` in the test, and
  `decrypt` returned the plaintext.
- The three tests pass under 49.0.0 in that venv, together with the 6 tests of `test_crypto.py`
  (9 passed).
- A third-party AES-GCM implementation, pycryptodome (`AES.MODE_GCM`, run outside the repo),
  gave the same result. It decrypts and verifies the envelope (12-byte nonce, 57-byte ciphertext,
  16-byte tag), and it re-encrypts the plaintext to the identical envelope. So the fixture is
  standard AES-256-GCM in MedHub's `nonce ‖ ciphertext ‖ tag` URL-safe base64 envelope, and does
  not depend on the cryptography release.

**The KAT detects breakage.** QA mutated `app/db/crypto.py` in the scratch copy:

| Mutation | Result |
|---|---|
| Associated data added | 2 failed |
| Envelope order changed to `ct ‖ nonce` | 2 failed |
| Key derivation changed (a wrong key) | 2 failed |
| Standard base64 instead of URL-safe | 1 failed |
| `decrypt` swallows `InvalidTag` | 1 failed (the tamper test) |

The test data is synthetic: an invented name with no other identifier. The key appears only in
this test and this record.

### Findings

- **[LOW] The fixture was not committed before the lock change, as planned.**
  - This task's "Tests" step and the CR-003 plan-risk row ("writes and commits the fixture under the
    current lock before touching `uv.lock`") required that commit. The test and the lock change
    arrive in one commit, so the 49.0.0 origin rested on the developer's evidence alone.
  - The deviation is mitigated: QA regenerated the fixture independently under 49.0.0 (above), and
    anyone can repeat that, because AES-GCM is deterministic. No code change is needed. This
    section records the deviation.
- **[LOW] Redundant entry in the "Verified by" cell.**
  `docs/risks/RISK-011-encryption-key-management-failure.md:64` reads
  `TS-008, TS-008 TC-008.5`, which follows step 5 literally. Fix, optional, at the human's RISK
  review: `TS-008 (incl. TC-008.5)`.

### Observations (not findings)

- **Lock.** A per-block comparison of `HEAD:backend/uv.lock` with the working copy found 0 packages
  added or removed. The only changed block is `cryptography`, and the header is unchanged. The
  sdist SHA-256 matches PyPI. `pyproject.toml` is unchanged, and `uv lock --check` reports
  "Resolved 86 packages" with exit 0. In the lock, only `medhub-backend` depends on cryptography.
- **AC-8 under D-4.** QA reproduced the scratch `--no-dev` environment: cryptography 50.0.2, cffi
  2.0.0, pycparser 3.0, and no pytest. QA also built the backend image (temporary tag, then
  removed). The image reports the same three versions and `OpenSSL 4.0.3 29 Sep 2026`. The
  evidence is therefore adequate, and TASK-164 still owns the recorded image check (D-4).
- **SOUP-011 review.** QA spot-checked these sources on 2026-10-29, and each matches the record:
  - OSV, for the four versions;
  - the GitHub Advisory Database (high) and the repository advisory (medium);
  - the pyca repository advisories, the newest three published on 2026-07-31;
  - NVD CVE-2026-69247: "Awaiting Analysis", CVSS 4.0 score 8.2, no configurations;
  - the changelog for 50.0.0–50.0.2: no AEAD or GCM entry, and the wheels are built with OpenSSL
    4.0.3;
  - the OpenSSL vulnerability list: no entry reaches 4.0.3, and exactly 14 entries read "from
    4.0.0 before 4.0.3", in the categories the record gives. The GCM-related 4.0 entries
    (CVE-2026-34182 CMS AuthEnvelopedData, CVE-2026-45446 AES-GCM-SIV/SIV) were fixed at 4.0.1.

  `app/db/crypto.py:20` is the only import of `cryptography` in `backend/app` and
  `backend/scripts`.
- **PRB-050.** The PRB is genuine and its facts check out:
  - no `.dockerignore` in `frontend/` or at the root;
  - `frontend/Dockerfile:6`/`:8`, `.gitignore:25-26` and 339 host `node_modules` entries are as
    stated;
  - its safety evaluation includes the statement that no version has been released;
  - it is `open` with no fix applied, and it is outside CR-003.
- **The running Compose `backend` container** predates this lock change. CR-003 AC-17 rebuilds the
  stack in TASK-168.
- **Whole-project `traceability-check`** reports `soup_without_risk` for SOUP-033. It is transient:
  TASK-161 removed RISK-010's link before TASK-165 sets SOUP-033 `obsolete`. It is not caused by
  this task.

### Verification run (QA)

- `uv run --frozen pytest --cov=app --cov-fail-under=85` (`DOCKER_CONTEXT=desktop-linux`): 499
  passed, coverage 91.71 %.
- `ruff check .`, `black --check .` (220 files) and `mypy app` (124 files): pass.
- `pytest tests/db/test_crypto_known_answer.py -v` under 50.0.2: 3 passed.
- Fallback `traceability-check`, scoped to TASK-163, SOUP-011, RISK-011, TS-008, CR-003, PRB-050,
  PRB-047, RISK-001, RISK-010, SR-022 and SR-028: 0 errors and 23 warnings, all W5 from records
  held `in_review` under AC-19. Over the whole project: 0 errors.
