---
id: "PRB-047"
type: problem-report
title: "Locked runtime dependencies carry published advisories that do not affect MedHub's use"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-29"
criticality: minor
links: []
tags: ["soup", "maintenance", "security"]
---

# PRB-047 — Locked runtime dependencies carry published advisories that do not affect MedHub's use

## Observed

The first SOUP anomaly-list review found published advisories against three packages at the
versions `backend/uv.lock` resolves:

| Package (SOUP record) | Advisories | Fixed in | Why MedHub is not affected |
|---|---|---|---|
| anyio 4.14.0, a transitive of Starlette ([SOUP-003](../soup/SOUP-003-starlette.md)) | GHSA-3w57-8xmc-8v26 / CVE-2026-63349: `run_process`/`open_process` ignore `extra_groups`. GHSA-5p39-cfhj-2xmp / CVE-2026-64847: process-pool workers can block on undrained stderr. GHSA-82r6-8w77-94w6 / CVE-2026-63374: `TLSStream` encodes host names with IDNA 2003 | 4.14.2 | No backend module imports anyio. Starlette uses it only for its thread pool: no subprocesses, no process pool, no anyio TLS client stream. TLS terminates at nginx (SOUP-024) |
| urllib3 2.7.0, a transitive of boto3 ([SOUP-019](../soup/SOUP-019-boto3.md)) | GHSA-8988-9cw3-xx77 / CVE-2026-97687: HTTPS-proxy TLS configuration may be ignored. GHSA-vxq7-64xx-v4gw / CVE-2026-97689: unbounded chunk-size line in `stream()`/`read_chunked()`. GHSA-gh4c-6fx4-qh6g / CVE-2026-97688: chunked deflate streaming can loop forever | 2.8.0 | No proxy is configured. The two availability flaws need the object store (`http://minio:9000`, internal network) to send hostile responses. That would first require compromising MinIO, the scenario of RISK-012/PRB-043, and the only added effect is a hung API worker (RISK-007, covered by the healthcheck and restart policy) |
| cryptography 49.0.0 ([SOUP-011](../soup/SOUP-011-cryptography.md)) | GHSA-g6cj-pr64-35w5 / CVE-2026-69247: Bleichenbacher oracle in `pkcs7_decrypt_der`/`_pem`/`_smime` | 50.0.0 | MedHub uses only `AESGCM` (`backend/app/db/crypto.py`, SR-022). It uses no PKCS#7, S/MIME, RSA or X.509 API |

## Impact

None on MedHub's behaviour today. The locked versions stay exposed until the next dependency
change, and a future change that starts using an affected API would inherit the flaw without
noticing.

## Investigation

Mechanism. The lock pins the three versions, and nothing short of a lock refresh moves them:

- In the lock as it stood before CR-003 (`f807bfb`), `backend/uv.lock:55-56` had anyio 4.14.0, `:521-522` cryptography 49.0.0 and `:1655-1656`
  urllib3 2.7.0 (these line numbers describe that lock, not the current one).
- `backend/Dockerfile:7` installs with `uv sync --frozen --no-dev`, so the production image gets
  exactly these versions.
- `cryptography` is a direct dependency with only a floor (`backend/pyproject.toml:19`,
  `>=42.0.0`).
- anyio and urllib3 are transitive. anyio comes in through Starlette (`backend/uv.lock:1588`),
  urllib3 through botocore (`:212`), and neither is declared in `backend/pyproject.toml`. In the
  production set, those are their only dependents: the other dependents in the lock (httpx,
  watchfiles, requests, testcontainers, docker) are dev-only or not installed.

History. The three versions have not changed since the lock was first resolved with them
(commit `845886c`, 2026-06-21). They are identical at `7f1d9ee` (2026-06-30) and after CR-001's
TASK-157 (`c455618`) and TASK-158 (`fac911b`), which ran `uv lock` without `--upgrade` on purpose
(CR-001 A-4 and its plan risk table). The fixes came out after that: anyio 4.14.2 (advisories published
2026-07-07; PyPI upload 2026-07-12) (SOUP-003), cryptography 50.0.0 on 2026-07-31 (SOUP-011) and urllib3 2.8.0 on 2026-09-15
(SOUP-019). Root cause: no upgrade has been made since the lock was resolved. By design the lock
is the pin, and a version changes only through an explicit change. This PRB is that trigger.

Use re-checked 2026-10-29. In `backend/app` and `backend/modules`, the only import from these
packages is `from cryptography.hazmat.primitives.ciphers.aead import AESGCM`
(`backend/app/db/crypto.py:20`). Nothing imports `anyio` or `urllib3` directly. The "why not
affected" column above still holds.

Verification gap relevant to the fix. `backend/tests/db/test_crypto.py` checks AES-GCM by round
trip, wrong key and ciphertext variation (`:41`, `:47`, `:53`, `:61`), always under the installed
version. No test decrypts a ciphertext that an earlier version produced. Such a test is what would
show that field values already at rest (SR-022) still decrypt after the cryptography upgrade.

## Safety evaluation

Not hazard-relevant: no path from MedHub's use to any of the advisories, as judged in SOUP-003,
SOUP-011 and SOUP-019. The RISK-011 field-encryption control (AES-256-GCM) and the SSE request
path are unaffected. Criticality is `minor`: it is a patch-currency obligation (§6.1 f), not a
realized defect.

The upgrade itself touches control-bearing items: cryptography carries the field-encryption
control (SR-022, RISK-001, RISK-011), anyio is the concurrency layer under Starlette's
`BaseHTTPMiddleware`, which both security middlewares subclass
(`backend/app/core/security_middleware.py:33`, `:75`; security headers and CSRF, SR-031,
RISK-005), and urllib3 carries the SSE request to the object store (RISK-007,
RISK-011). A regression in one of them could affect data integrity. The most serious case is
PHI already encrypted at rest becoming unreadable. CR-003's §7.4 analysis and verification
therefore cover these items. The criticality of this PRB stays `minor`.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

In CR-003, a separate CR because CR-001 A-4 forbids upgrades:

- Raise anyio to ≥ 4.14.2, urllib3 to ≥ 2.8.0 and cryptography to ≥ 50.0.0. Apply `uv lock`
  only for these packages and check the lock diff.
- Re-run the backend suite (including the TS-008 encryption tests) and the anomaly review for
  the new versions.
- Update SOUP-003, SOUP-011 and SOUP-019.

## Resolution

Resolved in the working tree by [CR-003](../change-requests/CR-003-upgrade-end-of-life-and-advisory-soup.md)
(D-3), in two tasks, one per lock change. The resolving `resolves` link is on CR-003. `closed`
waits for a shipped release (none exists yet).

**What changed.**

| Package | Before | After | Task | SOUP record |
|---|---|---|---|---|
| cryptography | 49.0.0 | 50.0.2 | TASK-163 | [SOUP-011](../soup/SOUP-011-cryptography.md) 1.2 |
| anyio | 4.14.0 | 4.14.2 | TASK-164 | [SOUP-003](../soup/SOUP-003-starlette.md) 1.2 |
| urllib3 | 2.7.0 | 2.8.0 | TASK-164 | [SOUP-019](../soup/SOUP-019-boto3.md) 1.3 |

- `backend/uv.lock`: each task changed only its own package blocks (versions, sdists, wheel URLs
  and hashes). A package-by-package comparison of `f807bfb:backend/uv.lock` (before CR-003) with
  the working lock shows 86 packages on both sides, none added or removed, and exactly these
  three changed. cffi 2.0.0, pycparser 3.0, idna 3.18 and typing-extensions 4.15.0 are unchanged,
  so no further package had to move. `backend/pyproject.toml` is unchanged: anyio and urllib3 stay
  transitive, and cryptography keeps its `>=42.0.0` floor.
- anyio is pinned to 4.14.2 on purpose (`uv lock --upgrade-package anyio==4.14.2`). It is the
  smallest move that fixes the three advisories; 4.15.1 exists and was not taken (CR-003 D-3).
- The three advisories of each package are fixed at the new version: GHSA-g6cj-pr64-35w5 at
  cryptography 50.0.0; GHSA-3w57-8xmc-8v26, GHSA-5p39-cfhj-2xmp and GHSA-82r6-8w77-94w6 at anyio
  4.14.2; GHSA-8988-9cw3-xx77, GHSA-vxq7-64xx-v4gw and GHSA-gh4c-6fx4-qh6g at urllib3 2.8.0. OSV
  and the GitHub Advisory Database return no vulnerability for the three locked versions, and the
  same query returns each advisory for the old versions.

**Why this approach.** The lock is the pin, so the fix is an explicit, narrow lock refresh per
package (`uv lock --upgrade-package <pkg>==<version>`), with the lock diff inspected block by
block. The cryptography change went in behind a known-answer test, because the control it carries
(SR-022, RISK-011) protects data already at rest.

**How it was verified (reproducible).**

- Known-answer test (TS-008 TC-008.5, `backend/tests/db/test_crypto_known_answer.py`): the
  ciphertext fixture was produced by MedHub's own `encrypt` under cryptography 49.0.0. Under
  50.0.2 it decrypts to the original plaintext, `encrypt` with the same key and nonce gives the
  identical envelope, and a tampered tag raises `InvalidTag`. Run:
  `cd backend && uv run pytest tests/db/test_crypto_known_answer.py tests/db/test_crypto.py -v`
  (9 passed).
- Backend suite on the final lock: `cd backend && DOCKER_CONTEXT=desktop-linux uv run --frozen
  pytest --cov=app --cov-fail-under=85`: 499 passed, coverage 91.71 %, including the real-DB
  tests, TS-011 (security headers and CSRF over the anyio middleware path) and TS-007 TC-007.5.
  `ruff check .`, `black --check .` and `mypy app` pass, and `uv lock --check` passes.
- AC-8 on the built backend image (CR-003 D-4, run once):
  `docker build -t medhub-backend:ci ./backend`, then
  `docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.metadata as m; print({p: m.version(p) for p in ('anyio','urllib3','cryptography')})"`
  printed `{'anyio': '4.14.2', 'urllib3': '2.8.0', 'cryptography': '50.0.2'}`. The `backend` and
  `celery-worker` containers rebuilt from the same Dockerfile report the same three versions.
- Rebuilt Compose stack: `infra/smoke-test.sh` 17 passed, 0 failed. Attachment round trip through
  `https://localhost` (RISK-007, RISK-011): login 200, clinical entry created 201, a 307,200-byte
  attachment uploaded 201 and downloaded 200 with identical bytes (same SHA-256), unauthenticated
  download 401, logout 204. This confirms the SSE request path over urllib3 2.8.0 on the real
  object store. End-to-end proof of SSE on the stored object stays with PRB-036.
- SOUP re-reviews, all dated 2026-10-29 at the new versions: SOUP-011, SOUP-003 and SOUP-019 each
  find no anomaly that applies, show the PRB-047 advisories as fixed, and state the upgrade
  impact. No RISK and no new PRB came from them.

**Result.** No locked runtime dependency carries a published advisory at the versions
`backend/uv.lock` resolves. Criticality stays `minor`. The three SOUP records stay `in_review`
for human approval under CR-003 AC-19.

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12, backend slice), on
2026-10-22. The evidence is in the "Anomaly list review" sections of SOUP-003, SOUP-011 and
SOUP-019.
