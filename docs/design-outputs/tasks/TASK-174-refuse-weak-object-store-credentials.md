---
id: "TASK-174"
type: task
title: "Refuse default or weak object-store credentials at start-up"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-040"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-043"
    relation: relates_to
  - target: "PRB-007"
    relation: relates_to
tags: ["security", "configuration", "cr:CR-002", "issue:sancharly/medhub#33", "control:protective"]
---

# TASK-174 — Refuse default or weak object-store credentials at start-up

- **Software item / unit:** SI-OBJSTORE `U-OBJ-Preflight` (ADD-025)
- **Depends on:** none. It is independent of the Q-1 answer and runs against the current
  `minio` and `createbuckets` services. TASK-175 and TASK-176 rename them.
- **Branch:** `bug/minio-object-store`
- **Size:** M (1 new module, Compose, `.env.example`, DEPLOY.md key section, CI and test-fixture
  values, new TS-014)
- **Needs:** a Docker host for the started-stack cases

## Objective

SR-040 AC 2 and CR-002 Q-2, as decided by the human on 2026-10-30. The object store and its bucket
initialiser do not start when the access key or secret key is unset or empty, equals a known
default, or (for the secret key) is shorter than 16 characters. The message names the rejected
setting. No object-store default credential is left in any file (CR-002 Boundaries).

## Interfaces to honor

- The rule is implemented once, in Python, as
  `backend/app/core/object_store_credentials.py`. It provides
  `check(access_key: str | None, secret_key: str | None) -> list[str]`, which returns
  human-readable rejections naming `OBJECT_STORE_ACCESS_KEY` or `OBJECT_STORE_SECRET_KEY`, and a
  `__main__` that reads the two variables from the environment, prints each rejection to stderr
  and exits 1.
  - The known-default set is `minioadmin`, `changeme`, `admin`, `password`, `secret`, compared
    case-insensitively.
  - The access key must not be in the set, whatever its length.
- The rule never prints a key value.
- Only the object-store credentials are in scope. `AT_REST_ENCRYPTION_KEY` and the other
  defaults stay with PRB-007 (Q-3).

## Implementation detail

1. Write the module and its unit tests. The four AC-2 cases are unset, empty, known default, and
   secret shorter than 16, for each key. Add a positive case.
2. **Compose** (`infra/docker-compose.yml`):
   - Add a one-shot service `object-store-preflight`:
     - built from `../backend`, with `env_file: .env`;
     - `network_mode: none` and `restart: "no"`;
     - `command: python -m app.core.object_store_credentials`.
   - `minio` and `createbuckets` gain
     `depends_on: object-store-preflight: condition: service_completed_successfully`.
   - The `minio` environment uses `${OBJECT_STORE_ACCESS_KEY:?OBJECT_STORE_ACCESS_KEY must be
     set}` and the same for the secret, so Compose itself refuses the unset case.
3. **`infra/.env.example`**:
   - `OBJECT_STORE_ACCESS_KEY=` and `OBJECT_STORE_SECRET_KEY=` are empty;
   - a comment gives the rule and the generation commands (`openssl rand -hex 12` for the access
     key, `openssl rand -base64 32` for the secret).

   Leave `DATABASE_URL` and `SMTP_PASSWORD` as they are (PRB-007).
4. **`infra/DEPLOY.md`**: a "Generate the object-store keys" step with the same commands and the
   rule. Do not change the rest of DEPLOY.md here (TASK-180).
5. **Remove `minioadmin` as an object-store credential from every file**:
   - `.github/workflows/ci.yml:76-77,164-165`;
   - `backend/tests/conftest.py`, `backend/tests/test_config.py`,
     `backend/tests/test_lifespan.py` and `backend/modules/dicom_viewer/tests/conftest.py`.

   Use non-default synthetic values, for example `test-access-key` and a 24-character secret.
   Keep `test_config.py:46`'s secret-redaction assertion meaningful by changing it to the new
   value. Extend `backend/tests/test_env_example.py` to assert that the template has empty
   object-store keys and none of the default strings.
6. **TS-014** (new, `in_review`, `verifies` SR-040). It is created here, and TASK-175, 176 and 177
   extend it:
   - TC-014.1: Compose dependency on the preflight, and the `:?` guards;
   - TC-014.2: the four rejection cases, unit and started stack;
   - TC-014.3: no default strings in the template, the Compose file, DEPLOY.md and CI.

## Tests (write first)

- Unit: `backend/tests/core/test_object_store_credentials.py`, all cases above, plus "the value
  never appears in the output".
- Infrastructure: `infra/tests/test_compose_object_store.py`, standard library only, as in
  `infra/tests`. Parse `docker compose -f infra/docker-compose.yml config --format json` with a
  complete throwaway env file. Skip with a message when `docker` is absent. Assert the preflight
  service, `network_mode`, the dependency condition, and the absence of the default strings.

## Acceptance criteria

- [x] CR-002 **AC-2** / SR-040 AC 2: the template, the Compose file and DEPLOY.md contain neither
      `minioadmin` nor `changeme` as an object-store credential. Each of the four cases stops
      `minio` and `createbuckets` from starting, with a message naming the setting. A test covers
      each case. DEPLOY.md documents key generation.
- [x] CR-002 Boundaries: no object-store default credential is left in any file
      (`git grep -n minioadmin -- ':!docs'` is empty).
- [x] CR-002 **AC-15** (SR-040 part): TS-014 exists, `verifies` SR-040, and lists TC-014.1..3.

## Verification

```sh
cd backend && uv run pytest tests/core/test_object_store_credentials.py tests/test_env_example.py tests/test_config.py -v
python3 -m unittest discover -s infra/tests -v
git grep -n "minioadmin" -- ':!docs'        # empty
# started stack, once per case, with infra/.env edited (test values only):
docker compose -f infra/docker-compose.yml up -d; docker compose -f infra/docker-compose.yml ps -a
docker compose -f infra/docker-compose.yml logs object-store-preflight   # names the setting
```

Record, for each of the four cases, the preflight exit code, the message and the fact that
`minio` and `createbuckets` are `Created` but not started.

## Definition of Done

- [x] Lint, type-check and the backend suite pass (coverage ≥ 85 %). The infrastructure tests
      pass, and all CI jobs are green with the new test values.
- [x] `traceability-check` shows no error for this task and TS-014.

## QA review (2026-10-30, round 1): CHANGES REQUESTED

`in_review → draft` (TASK-174 and TS-014).

### Ruling on the `git grep` check

The check's intent is CR-002 Boundaries: "leave an object-store default credential in any
file". The rule module's known-default set and the tests that assert against it name the
strings, but they do not use them as credentials. Three paths name `minioadmin`, not two:
`backend/app/core/object_store_credentials.py`, `backend/tests/core/test_object_store_credentials.py`
and `infra/tests/test_compose_object_store.py`. Excluding exactly these three paths meets
the intent. The check becomes:

```sh
git grep -n -i --untracked minioadmin -- ':!docs' ':!backend/app/core/object_store_credentials.py' \
  ':!backend/tests/core/test_object_store_credentials.py' ':!infra/tests/test_compose_object_store.py'   # empty
```

On 2026-10-30 this check returned nothing. With the same exclusions, `changeme` still matches
`infra/.env.example:14,46` (`DATABASE_URL`, `SMTP_PASSWORD`). Those lines stay as they are under
PRB-007, as this task requires. TS-014 TC-014.3 already states the same exclusion.

### Findings

- **[HIGH] The preflight checks different values from the ones the store uses.**
  The problem is at `infra/docker-compose.yml:97-105` (`env_file: .env`) and `:114-115`
  (`${OBJECT_STORE_*:?}`). `minio` takes its root credentials from Compose interpolation, which
  uses the shell environment first, then `--env-file` or the project `.env`. The preflight
  instead reads `infra/.env` through `env_file`, so a key exported in the shell or passed with
  `--env-file` reaches `minio` without being checked.
  QA reproduced this on a started stack (project `qa174`). `infra/.env` held good keys, and the
  shell exported `OBJECT_STORE_ACCESS_KEY=minioadmin OBJECT_STORE_SECRET_KEY=changeme`. The
  preflight exited 0, `minio` started, and `mc alias set … minioadmin changeme` inside `minio`
  was **ACCEPTED**. `docker compose config` shows the same split: `minio`'s
  `MINIO_ROOT_PASSWORD` was `changeme` while the preflight's `OBJECT_STORE_SECRET_KEY` was the
  `.env` value. As a result, SR-040 AC 2 and the RISK-012 control claimed by this task do not
  hold on these paths.
  → Fix: in `object-store-preflight`, replace `env_file: .env` with
  `environment: {OBJECT_STORE_ACCESS_KEY: "${OBJECT_STORE_ACCESS_KEY:?OBJECT_STORE_ACCESS_KEY must be set}", OBJECT_STORE_SECRET_KEY: "${OBJECT_STORE_SECRET_KEY:?OBJECT_STORE_SECRET_KEY must be set}"}`.
  These are the same expressions `minio` uses. The preflight then also stops receiving every
  other secret in `.env`. Add a `ComposeWiring` test that runs `docker compose config` with a
  key overridden in the subprocess environment and asserts that the preflight's two values equal
  `minio`'s `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`. Extend TS-014 TC-014.1 to cover it, then
  rerun one bad case with the shell override on a started stack.
- **[MEDIUM] The started-stack evidence is not recorded.**
  The gap is in this file's Verification section and in TS-014 TC-014.2 ("recorded in TASK-174").
  The Verification section asks for the preflight exit code, the message and the
  `minio`/`createbuckets` state for each case. TS-014 points to this task for those results, but
  the TASK body has none, so the evidence exists only in a chat summary.
  → Fix: add a "Verification results" section listing each case (unset and empty refused by the
  `:?` guard, plus the direct preflight run; known default; secret ≤ 15 characters; good keys;
  shell override after the fix). For each, give the project name, exit code, message and
  container states.
- **[LOW] Whitespace-only keys pass the rule.**
  The cause is `backend/app/core/object_store_credentials.py:18-28`. QA ran the preflight image
  with an access key of 3 spaces and a secret key of 16 spaces, and it exited 0. Q-2 does not
  name this case, so this finding does not block.
  → Fix: treat `value.strip() == ""` as empty and compare `value.strip().lower()` against the
  defaults. Add one unit case for each.
- **[LOW] The coverage figure in the hand-off does not match QA's rerun.** The developer
  reported 95.62 %. QA's rerun of `uv run pytest --cov=app --cov-fail-under=85` gave 91.66 %
  (536 passed). The gate holds either way, but evidence should quote the CI command's figure.
  `object_store_credentials.py` is at 81 % because `main()` runs only in a subprocess.

### Pre-existing (not blocking)

- `createbuckets` (`infra/docker-compose.yml:131-143`) has a related split. It authenticates
  with the `env_file` values while `minio` uses the interpolated values, so a shell override
  makes it fail. It still exits 0 (PRB-039). TASK-175 replaces the initialiser and should take
  its keys from the same interpolation.
- `ruff format --check` would reformat `backend/tests/test_env_example.py` and
  `tests/api/test_openapi_contract.py`. HEAD has the same result. CI runs Black, which passes.

### Verification run (QA, 2026-10-30)

- `uv run pytest tests/core/test_object_store_credentials.py tests/test_env_example.py tests/test_config.py -v`: 37 passed.
- Backend suite: `uv run pytest --cov=app --cov-fail-under=85`: 536 passed, 91.66 %.
  `ruff check .` passed, `black --check .` passed, and `mypy app` reported no issues in 125 files.
- `python3 -m unittest discover -s infra/tests -v`: 17 OK. `python3 infra/check_image_pins.py` exited 0.
- Started stack, `DOCKER_CONTEXT=desktop-linux -p qa174`, `up -d minio createbuckets`, with a
  temporary `infra/.env` (the original was restored and `cmp` and `shasum` confirmed it identical):
  - access key `MinioAdmin`: `up` exited 1, the preflight exited 1 with
    "OBJECT_STORE_ACCESS_KEY is a known default value", and `minio`/`createbuckets` stayed `Created`;
  - access key `minioadmin`: the same result;
  - secret key `exactly15chars!`: the preflight exited 1 with "OBJECT_STORE_SECRET_KEY is shorter
    than 16 characters";
  - secret key `PASSWORD`: the preflight exited 1 with both rejections, naming only the setting;
  - empty secret key: `up` exited 15 at interpolation ("OBJECT_STORE_SECRET_KEY must be set");
  - preflight image run directly with an unset or empty access key: exit 1, "is not set" or "is empty";
  - good keys: the preflight exited 0 (silent), `minio` came up, and `createbuckets` exited 0
    (bucket created, set private);
  - good `.env` with a weak shell override: the bypass described in the HIGH finding.
  - No rejection message printed a key value.
- `traceability-check` (fallback parser over the whole project) reported 0 errors. SR-040 has
  W2 (no TR yet; TR comes at release) and W5 (→ RISK-012 `in_review`). TASK-174 and TS-014 have
  no findings.

## Verification results (2026-10-30, developer, round 2)

Started-stack runs used `DOCKER_CONTEXT=desktop-linux`, Compose project `medhub174` and a temporary
`infra/.env` with throwaway values (the dev `infra/.env` was restored byte-identical). Only
`medhub174` containers were created and removed.

| Case | Project | Preflight exit | Message | `minio` / `createbuckets` |
|---|---|---|---|---|
| Access key unset or empty | n/a (Compose refuses) | `docker compose` errors before any container | `OBJECT_STORE_ACCESS_KEY must be set` | not created |
| Secret key unset or empty | n/a (Compose refuses) | same | `OBJECT_STORE_SECRET_KEY must be set` | not created |
| Preflight image run directly (`--network none`): access unset / empty; secret unset / empty | none | 1 (each) | `OBJECT_STORE_ACCESS_KEY is not set` / `is empty`; `OBJECT_STORE_SECRET_KEY is not set` / `is empty` | n/a |
| Access key a known default (`.env`) | `medhub174` | 1 | `OBJECT_STORE_ACCESS_KEY is a known default value` | `Created`, not started |
| Secret key a known default, uppercase (`.env`) | `medhub174` | 1 | `OBJECT_STORE_SECRET_KEY is a known default value` and `is shorter than 16 characters` | `Created`, not started |
| Secret key of 15 characters (`.env`) | `medhub174` | 1 | `OBJECT_STORE_SECRET_KEY is shorter than 16 characters` | `Created`, not started |
| Shell override with the two defaults, good keys in `.env` (QA round 1 reproduction, after the fix) | `medhub174` | 1 | known default for both keys, and the secret shorter than 16 | `Created`, not started |
| Good keys | `medhub174` | 0 | none | `minio` Up, `createbuckets` Exited (0) |

Checks, with the CI coverage command: `uv run pytest --cov=app --cov-fail-under=85` gave 539 passed
and 91.66 %; `uv run ruff check .` and `uv run mypy app` clean; `python3 -m unittest discover -s
infra/tests` gave 18 tests OK; the three-path `git grep` is empty.

## QA review (2026-10-30, round 2): APPROVED

`in_review → approved` (TASK-174 and TS-014 1.1). All four round-1 findings are fixed:

- **HIGH, fixed.** `object-store-preflight` now takes `OBJECT_STORE_*` from the same
  `${…:?}` expressions as `minio` and has no `env_file` (`infra/docker-compose.yml:97-108`).
  `test_preflight_checks_the_values_the_store_receives` passes. QA reran the round-1 bypass on a
  started stack (project `qa174`, `up -d --build`): good keys in `.env`, shell
  `OBJECT_STORE_ACCESS_KEY=minioadmin OBJECT_STORE_SECRET_KEY=changeme`. The preflight exited 1
  with three rejections (known default for each key, secret shorter than 16), and
  `minio`/`createbuckets` stayed `Created`.
- **MEDIUM, fixed.** The "Verification results" section above records every case.
- **LOW, fixed.** Whitespace is stripped before the empty and default checks, and unit cases cover it.
  On a started stack, an 18-space secret gave preflight exit 1 with "OBJECT_STORE_SECRET_KEY is empty".
- **LOW, fixed.** The evidence now quotes the CI command's figure (91.66 %).

The `git grep` Boundaries criterion is ticked under the round-1 ruling: the three-path exclusion
returns nothing.

QA rerun, 2026-10-30:

- TASK pytest command: 40 passed.
- `uv run pytest --cov=app --cov-fail-under=85`: 539 passed, 91.66 %.
- `ruff check .`, `black --check .` and `mypy app` (125 files) are clean.
- `python3 -m unittest discover -s infra/tests`: 18 OK.
- `python3 infra/check_image_pins.py`: exit 0.
- Good keys on a started stack: preflight exit 0, `minio` Up, `createbuckets` Exited (0) with the
  bucket created and set private.
- The dev `infra/.env` was restored byte-identical (`cmp`).
- `traceability-check` reported 0 errors. SR-040 keeps W2 (TR at release) and W5 (→ RISK-012 `in_review`).
  TASK-174 and TS-014 have no findings.

Still open for TASK-175: `createbuckets` keeps `env_file: .env` and therefore the credential split.
TASK-175, 176 and 177 extend TS-014: each moves it back to `draft`/`in_review` and bumps its version.
