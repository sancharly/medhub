---
id: "TASK-164"
type: task
title: "Upgrade anyio to 4.14.2 and urllib3 to 2.8.0"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-29"
links:
  - target: "SR-028"
    relation: implements
  - target: "SR-031"
    relation: implements
  - target: "SR-013"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-003"
    relation: relates_to
  - target: "PRB-047"
    relation: relates_to
  - target: "TASK-163"
    relation: relates_to
  - target: "SOUP-003"
    relation: relates_to
  - target: "SOUP-019"
    relation: relates_to
  - target: "RISK-005"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
tags: ["soup", "maintenance", "security", "cr:CR-003", "issue:sancharly/medhub#32", "control:protective"]
---

# TASK-164 — Upgrade anyio to 4.14.2 and urllib3 to 2.8.0

- **Software item / unit:** SI-API middleware chain (ADD-005; `SecurityHeadersMiddleware` and
  `CsrfEnforcementMiddleware` on Starlette `BaseHTTPMiddleware`, which runs on anyio); SI-ATTACH
  object-storage path (ADD-012; boto3/botocore over urllib3); SI-DEVINFRA `U-INF-Toolchain`
  (`backend/uv.lock`)
- **Depends on:** TASK-163, which changes the same lock file and must be merged first
  (`relates_to`)
- **Branch:** `bug/soup-upgrades`
- **Size:** M
- **Needs:** a Docker host (the AC-8 image check and the attachment round trip on the Compose
  stack) and network access (PyPI, OSV, GitHub Advisory Database, NVD)

## Objective

Complete PRB-047 by moving the two transitive packages to the releases that fix its advisories
(CR-003 D-3):

- anyio 4.14.0 → **4.14.2**, pinned explicitly. 4.14.2 is the smallest move that fixes the
  advisories, so do not let the resolver pick 4.15.1.
- urllib3 2.7.0 → **2.8.0**.

Then re-review SOUP-003 and SOUP-019 at the new versions, run the AC-8 check on the built image
(D-4), and resolve PRB-047.

## Interfaces to honor

- Neither package is declared in `backend/pyproject.toml`, and neither gets a declaration. They
  stay transitive (A-4). `soup_version` of SOUP-003 (Starlette 1.3.1) and SOUP-019 (boto3
  1.43.117) stays, unless the lock changes those packages too (AC-13).
- Lock scope (AC-7, Boundaries): only `anyio` and `urllib3` change, plus any package that the new
  versions require, each named with its old and new versions.

## Implementation detail

1. Run:

   ```sh
   cd backend && uv lock --upgrade-package anyio==4.14.2 --upgrade-package urllib3==2.8.0
   ```

   Inspect `git diff backend/uv.lock`: only `anyio` (4.14.0 → 4.14.2) and `urllib3`
   (2.7.0 → 2.8.0) may change. `idna` 3.18 and `typing-extensions` 4.15.0 stay unless anyio 4.14.2
   requires otherwise. Revert any other change and constrain the resolution. Then run
   `uv lock --check`.
2. Run `uv sync --frozen`, then the full suite. TS-011 checks the headers and CSRF over the anyio
   middleware path. TS-007 TC-007.5 checks that the object-storage client is built from the
   declared SDK.
3. **AC-8, all three packages, on the built image (D-4, run once).**

   ```sh
   docker build -t medhub-backend:ci ./backend
   docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.metadata as m; print({p: m.version(p) for p in ('anyio','urllib3','cryptography')})"
   ```

   The expected output is `{'anyio': '4.14.2', 'urllib3': '2.8.0', 'cryptography': '50.0.2'}`.
   Record it in the evidence, and add it to the next TR. The CI step "Check production dependency
   set" is not changed (D-4).
4. **Attachment round trip on the real object store** (§7.4.3; RISK-007, RISK-011). No CI test
   reaches MinIO (PRB-036), so do this on the Compose stack at Checkpoint A, with the user created
   in TASK-161 or a new test user:
   - upload an attachment to a clinical entry through `https://localhost`;
   - download it, and check that the bytes are identical;
   - record the HTTP statuses.

   This confirms that the SSE request path still works over urllib3 2.8.0. End-to-end proof of
   SSE on the stored object stays PRB-036's.
5. **SOUP-003.** It is approved, so set `version` 1.2, remove the approval record and set
   `in_review`.
   - In the body, anyio is 4.14.2, plus any other transitive version that step 1 changes. No
     sentence states 4.14.0 as current.
   - **Anomaly list review**, dated on or after 2026-10-29, for Starlette 1.3.1 with anyio 4.14.2
     and idna. Use OSV (PyPI), the GitHub Advisory Database, NVD and the anyio version history
     (https://anyio.readthedocs.io/en/stable/versionhistory.html), by name and URL. Show
     GHSA-3w57-8xmc-8v26, GHSA-5p39-cfhj-2xmp and GHSA-82r6-8w77-94w6 as fixed at 4.14.2.
   - Set `anomaly_review`.
   - Change-log entry `2026-10-29 — anyio 4.14.0 → 4.14.2 (transitive); Starlette 1.3.1 unchanged; PRB-047, CR-003 (D-3)`.
6. **SOUP-019.** It is approved, so set `version` 1.3, remove the approval record and set
   `in_review`.
   - In the body, urllib3 is 2.8.0. No sentence states 2.7.0 as current.
   - **Anomaly list review**, dated on or after 2026-10-29, for boto3 1.43.117 with botocore,
     s3transfer, jmespath and urllib3 2.8.0. Use the same sources, plus the urllib3 `CHANGES.rst`.
     Show GHSA-8988-9cw3-xx77, GHSA-vxq7-64xx-v4gw and GHSA-gh4c-6fx4-qh6g as fixed at 2.8.0.
     Note the 2.8.0 HTTPS-proxy behaviour change as not applicable, because no proxy is
     configured.
   - Set `anomaly_review`.
   - Change-log entry `2026-10-29 — urllib3 2.7.0 → 2.8.0 (transitive); boto3 1.43.117 unchanged; PRB-047, CR-003 (D-3)`.
7. **PRB-047** → `status: resolved`, `version: "1.2"`, with a `## Resolution`. It covers both
   tasks: the lock diff of TASK-163 and of this task, the KAT (TC-008.5), the AC-8 output, the
   suites and the SOUP reviews.
8. **CR-003 Escalations**: add any finding of steps 5 and 6, or "none" for SOUP-003 and SOUP-019.

## Acceptance criteria

- [x] CR-003 **AC-7**: `uv.lock` resolves anyio 4.14.2, urllib3 2.8.0 and cryptography 50.0.2, and
      `uv lock --check` succeeds. Across TASK-163 and this task, no other package changes, or each
      one is named with its old and new versions and covered by AC-14.
- [x] CR-003 **AC-8**: the built backend image reports the three AC-7 versions (step 3).
- [x] CR-003 **AC-13** and **AC-14** for SOUP-003 and SOUP-019, as in steps 5 and 6.
- [x] CR-003 **AC-19** (PRB-047 part): PRB-047 is `resolved` with its `## Resolution`.

## Verification

```sh
cd backend && uv lock --check && git diff --stat uv.lock
cd backend && uv sync --frozen && uv run pytest --cov=app --cov-fail-under=85
cd backend && uv run ruff check . && uv run black --check . && uv run mypy app
docker build -t medhub-backend:ci ./backend && docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.metadata as m; print({p: m.version(p) for p in ('anyio','urllib3','cryptography')})"
docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"   # the CI step, unchanged
```

Step 4 (the attachment round trip) is recorded at Checkpoint A.

## Definition of Done

- [ ] The backend suite passes with coverage ≥ 85 %, and the CI jobs are green.
- [x] SOUP-003 and SOUP-019 are `in_review`, and PRB-047 is `resolved`.
- [x] `traceability-check` shows no error for the touched records.

## Implementation evidence (developer, 2026-10-29)

Handed to QA as `in_review`. No checkbox above is ticked: that is QA's approval.

**Lock change (AC-7).** `cd backend && uv lock --upgrade-package anyio==4.14.2 --upgrade-package urllib3==2.8.0`
printed `Updated anyio v4.14.0 -> v4.14.2` and `Updated urllib3 v2.7.0 -> v2.8.0` and nothing else.
`git diff --stat backend/uv.lock`: 6 insertions, 6 deletions (the two `version` lines and the sdist
and wheel hashes and URLs of the two blocks). A package-by-package comparison (parsed TOML) of
`HEAD:backend/uv.lock` with the working lock found 86 packages on both sides, none added or
removed, the lock header unchanged, and exactly two changed blocks: anyio and urllib3. The same
comparison against `f807bfb:backend/uv.lock` (before CR-003) shows exactly three changed packages
across TASK-163 and this task: anyio 4.14.0 → 4.14.2, cryptography 49.0.0 → 50.0.2, urllib3
2.7.0 → 2.8.0. No other package moved, so none is named in AC-14. `idna` 3.18 and
`typing-extensions` 4.15.0 are unchanged: anyio 4.14.2 does not require otherwise.
`backend/pyproject.toml` is unchanged (neither package is declared, A-4). `uv lock --check`:
`Resolved 86 packages`, exit 0. anyio did not float to 4.15.1.

**Suite and static checks, on the final lock** (`uv sync --frozen`, `DOCKER_CONTEXT=desktop-linux`,
so the real-DB tests ran): `uv run --frozen pytest --cov=app --cov-fail-under=85`: 499 passed,
coverage 91.71 %. That covers TS-011 (`tests/api/test_security_headers.py`,
`tests/api/test_csrf_enforcement.py`, over the anyio middleware path) and TS-007 TC-007.5
(`tests/test_object_storage.py`). `ruff check .`, `black --check .` (220 files) and `mypy app`
(124 files) pass.

**AC-8, all three packages, on the built image (D-4, run once; add to the next TR).**

```sh
docker build -t medhub-backend:ci ./backend
docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.metadata as m; print({p: m.version(p) for p in ('anyio','urllib3','cryptography')})"
# {'anyio': '4.14.2', 'urllib3': '2.8.0', 'cryptography': '50.0.2'}
docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"   # exit 0, the CI step, unchanged
```

The `backend` and `celery-worker` containers of the Compose stack were rebuilt
(`docker compose -f infra/docker-compose.yml up -d --build backend celery-worker`) and report the
same dictionary. The CI step "Check production dependency set" is not changed (D-4).

**Rebuilt stack.** `infra/smoke-test.sh`: 17 passed, 0 failed. The stack is left running.

**Attachment round trip on the real object store (step 4; RISK-007, RISK-011).** Two temporary test
accounts (a doctor and a patient, with a generated password that is not recorded) and a manual
consent grant were created inside the `backend` container, and removed afterwards. Through
`https://localhost`:

| Step | HTTP status |
|---|---|
| Login (doctor) | 200 |
| Create a clinical entry for the patient (with `X-CSRF-Token`) | 201 |
| Upload a 307,200-byte random file to the entry | 201 |
| Download the attachment | 200 |
| List the entry's attachments | 200 |
| Download without a session | 401 |
| Logout | 204 |

The uploaded and downloaded bytes are identical (`cmp`, and the same SHA-256
`a4b15c05…c0135d`). This confirms that the SSE request path (put and get on MinIO) works over
urllib3 2.8.0. End-to-end proof of SSE on the stored object stays PRB-036's. Cleanup: the object
was deleted from MinIO through `ObjectStorageClient`, the attachment, clinical entry and consent
rows and both accounts were deleted (2 accounts), and the scratch files were removed. The audit
rows of the session stay (append-only, no FK).

**Records.** SOUP-003 1.2 (anyio 4.14.2, review of 2026-10-29) and SOUP-019 1.3 (urllib3 2.8.0,
review of 2026-10-29): `in_review`, approval records removed, `soup_version` unchanged (Starlette
1.3.1, boto3 1.43.117), change-log entries as specified. Review sources: OSV (PyPI, exact
versions), the GitHub Advisory Database and the anyio, urllib3 and Starlette repository
advisories, NVD keyword searches, the anyio version history and the urllib3 `CHANGES.rst`. Result
for both: no anomaly applies, and the six PRB-047 advisories are fixed at 4.14.2 and 2.8.0. The
2.8.0 HTTPS-proxy behaviour change is not applicable (no proxy). PRB-047 is `resolved` 1.2 with a
`## Resolution` covering cryptography, anyio and urllib3. CR-003 "Escalations" gains the TASK-164
entry: none for SOUP-003 and SOUP-019. No PRB opened by this task.

**Observations for QA (not findings).**

- The anyio 4.14.2 upload on PyPI is dated 2026-07-12; the advisories (and the CR's earlier
  wording) give 2026-07-07. SOUP-003 cites the advisory date only.
- The stable anyio docs now describe 4.15.1 (PyPI upload 2026-09-05). 4.14.2 is kept deliberately
  (CR-003 D-3).

## QA review (2026-10-29)

**Verdict: APPROVED** (`in_review → approved`). There is no CRITICAL or HIGH finding. QA re-ran
every claim on the reference workstation (`desktop-linux` context, arm64). SOUP-003 and SOUP-019
stay `in_review` and PRB-047 stays `resolved` under CR-003 AC-19, and the human approves them at
CR close. The first Definition of Done item stays unticked: the local part passes (below), and
CI on the branch head cannot run before the branch is pushed. CR-003 assigns AC-18 to TASK-168.

**Lock (AC-7).** A per-block TOML comparison of the working `backend/uv.lock` with
`HEAD:backend/uv.lock` finds 86 packages on both sides, the header unchanged, and two changed
blocks: anyio 4.14.0 → 4.14.2 and urllib3 2.7.0 → 2.8.0, with unchanged dependency lists. Against
`f807bfb` (before CR-003), only anyio, cryptography and urllib3 changed. The sdist and wheel
SHA-256 values of both new blocks match PyPI. `backend/pyproject.toml` is unchanged since
`f807bfb`. `uv lock --check`: "Resolved 86 packages", exit 0.

**AC-8.** The running `backend` and `celery-worker` containers, and a fresh
`docker run --entrypoint python infra-backend:latest`, report
`{'anyio': '4.14.2', 'urllib3': '2.8.0', 'cryptography': '50.0.2'}`. Starlette 1.3.1, boto3 and
botocore 1.43.117 and idna 3.18 are unchanged. The running containers use the same image IDs that a
fresh `docker compose build` produces. The CI "production dependency set" step exits 0.

**Records.** QA spot-checked the sources on 2026-10-29:
- An OSV batch query returns no vulnerability for all 14 locked versions that the two records and
  PRB-047 name. It returns the three GHSAs (with their PYSEC aliases) for anyio 4.14.0 and for
  urllib3 2.7.0.
- The GitHub Advisory Database gives patched versions 4.14.2 and 2.8.0 for the six advisories,
  and `affects=` returns no advisory for either new version.
- The anyio repository advisories are dated 2026-07-07 and the urllib3 ones 2026-09-15.
- NVD reports CVE-2026-63349 as "Awaiting Analysis" (7.0) and CVE-2026-97689 as "Analyzed" (8.9).
- No module in `backend/app` or `backend/modules` imports anyio or urllib3. The backend container
  has no proxy variable, and the object-store endpoint is `http://minio:9000`.

PRB-047's `## Resolution` covers all three packages reproducibly, and CR-003 carries the
incoming `resolves` link.

### Findings

- **[MEDIUM] SOUP-003's change analysis omits an anyio change on a path MedHub uses.**
  - Location: `docs/soup/SOUP-003-starlette.md:67-73`, `:85` and the change log at `:104`.
  - The 4.14.2 version history also lists "Fixed unnecessary CPU spin when delivering
    cancellation from `CancelScope` on asyncio under certain conditions". Starlette 1.3.1's
    `BaseHTTPMiddleware` opens an anyio task group and calls `task_group.cancel_scope.cancel()`
    (`starlette/middleware/base.py:117-121`). Both security middlewares run on that path.
  - The 4.14.1 summary also omits the `Process.aclose()` deadlock fix, which MedHub does not use.
  - So "No entry changes the task-group … behaviour" and "The one change that touches a path
    MedHub uses is the `CapacityLimiter` fix" are inaccurate. The conclusion still holds: the fix
    is CPU-only and in the safe direction, and TS-011 plus the suite pass on 4.14.2.
  - Fix: add both entries to the `:67` paragraph. Name the `CancelScope` fix next to the
    `CapacityLimiter` fix at `:85` and `:104`, judged as a correction in the safe direction that
    TS-011 covers. Do this before the human reviews SOUP-003.
  - The same omission is in the CR-003 §7.4 row (`docs/change-requests/CR-003-upgrade-end-of-life-and-advisory-soup.md:253`,
    "4.14.1 changes only pytest-plugin fixture teardown"). Correct it in the same pass, or note
    it at CR close.
- **[LOW] SOUP-019's 2.8.0 behaviour-change paragraph reads as complete but lists a subset.**
  - Location: `docs/soup/SOUP-019-boto3.md:73-80`.
  - The paragraph omits these 2.8.0 bugfixes on the plain-HTTP pool path that botocore uses:
    `ConnectionPool.pool` resolving `LifoQueue` late, `drain_conn()` reading in 64 KiB chunks,
    stricter RFC 3986 host parsing, and `UnrewindableBodyError` on retry. None changes MedHub's
    behaviour: the host `minio` is valid, the body is a seekable `BytesIO`, and botocore retries
    on its own. The round trip passes.
  - Fix: add one sentence naming them as reviewed and not applicable.

### Pre-existing issues (not blocking)

- `docs/problem-reports/PRB-047-runtime-transitives-with-published-advisories.md:52` (text added
  by TASK-161) reads "anyio 4.14.2 on 2026-07-07". PyPI uploaded 4.14.2 on 2026-07-12, and
  2026-07-07 is the date of the repository advisories, as the developer observed. CR-003 `:321`
  has the right date. Fix: "anyio 4.14.2 on 2026-07-12 (advisories 2026-07-07)".
- PRB-047 `:38-40` gives lock line numbers and versions in the present tense. They are now
  historical. Optional fix: add "at investigation time".

### Test-data cleanup (developer session)

The developer's re-count is confirmed:
- 6 accounts, the pre-task value, all created in June 2026.
- 0 `attachment` rows. One `clinical_entry` and one `consent_grant` remain, both from 2026-06-30
  between the June accounts, so they are not test data.
- 0 `password_history` rows.
- The MinIO bucket `medhub` holds 0 objects, with versioning off and 0 versions or delete markers.

Nothing was left over, and QA deleted nothing from the developer's session.

### Verification run (QA)

- `uv lock --check`: exit 0. Per-block lock comparison vs `HEAD` and `f807bfb`: as above.
- `DOCKER_CONTEXT=desktop-linux uv run --frozen pytest --cov=app --cov-fail-under=85`: 499
  passed, 0 skipped, coverage 91.71 %. `ruff check .`, `black --check .` (220 files) and
  `mypy app` (124 files) pass.
- AC-8 in the containers and the built image: as above.
- Attachment round trip, re-run by QA through `https://localhost`. QA created fresh temporary
  accounts (a doctor and a patient, generated password not recorded) and a manual consent:

  | Step | Result |
  |---|---|
  | Login | 200 |
  | Create entry (with CSRF token) | 201 |
  | Upload 307,200 random bytes | 201 |
  | Download | 200, bytes identical (`cmp`, same SHA-256) |
  | List | 200 |
  | Download without a session | 401 |
  | Upload without a CSRF token | 403 |
  | Logout | 204 |
  | Download after logout | 401 |

  `head_object` on the stored object reported `ServerSideEncryption: AES256` (PRB-036 still owns
  the end-to-end SSE proof). Cleanup: QA deleted the object with an unguarded `delete_object`,
  and `head_object` then returned 404. It deleted the attachment, entry and consent rows (1 each)
  and the 2 accounts. Re-count: 6 accounts, no `qa16%` account, 0 attachments, and an empty
  bucket. Audit rows stay (append-only). The scratch files were removed.
- `traceability-check` (fallback parser, whole project): 350 records, 0 errors, no
  `soup_anomaly_review_stale`. It reports W5 links held `in_review` under AC-19, and the transient
  `soup_without_risk` SOUP-033, which is cleared when TASK-165 sets SOUP-033 obsolete.
