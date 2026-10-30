---
id: "TASK-174"
type: task
title: "Refuse default or weak object-store credentials at start-up"
status: draft
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

- [ ] CR-002 **AC-2** / SR-040 AC 2: the template, the Compose file and DEPLOY.md contain neither
      `minioadmin` nor `changeme` as an object-store credential. Each of the four cases stops
      `minio` and `createbuckets` from starting, with a message naming the setting. A test covers
      each case. DEPLOY.md documents key generation.
- [ ] CR-002 Boundaries: no object-store default credential is left in any file
      (`git grep -n minioadmin -- ':!docs'` is empty).
- [ ] CR-002 **AC-15** (SR-040 part): TS-014 exists, `verifies` SR-040, and lists TC-014.1..3.

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

- [ ] Lint, type-check and the backend suite pass (coverage ≥ 85 %). The infrastructure tests
      pass, and all CI jobs are green with the new test values.
- [ ] `traceability-check` shows no error for this task and TS-014.
