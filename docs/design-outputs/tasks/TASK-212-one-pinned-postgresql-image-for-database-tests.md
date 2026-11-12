---
id: "TASK-212"
type: task
title: "Start every test PostgreSQL from one pinned definition"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-12"
updated: "2026-11-12"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-005"
    relation: relates_to
  - target: "PRB-040"
    relation: relates_to
  - target: "SOUP-020"
    relation: relates_to
  - target: "RISK-006"
    relation: relates_to
  - target: "RISK-011"
    relation: relates_to
  - target: "TS-013"
    relation: relates_to
tags: ["verification", "soup", "cr:CR-005", "control:design"]
---

# TASK-212 — Start every test PostgreSQL from one pinned definition

- **Software item / unit:** backend test code (not shipped); verification evidence of SI-PERSIST
  and SI-AUDIT. SOUP-020.
- **PRB:** PRB-040. **CR:** CR-005 (AC-5, AC-7).
- **Depends on:** none (parallel with TASK-209..211). Ordered before TASK-213.
- **Branch:** `bug/build-hygiene`.
- **Size:** M by effort, although it touches 12 files: one new module and one identical one-line
  change (plus an import) in each of 11 test files. Not split: the change is mechanical and only
  meaningful when every call site moves at once.
- **Needs:** a Docker daemon.

## Objective

SR-028 AC-9: the real-database and migration tests run against the shipped PostgreSQL
(`postgres:16.15@sha256:9e2cf628…0a97`, SOUP-020), so the evidence for the RISK-006 append-only
grants and the RISK-011 key-identifier migration applies to the deployed version.

## Implementation detail

1. New `backend/tests/postgres_image.py`: a docstring naming SR-028 AC-9, SOUP-020 and the rule
   that it must equal `infra/docker-compose.yml`'s `postgres` image (checked by TASK-213), and one
   assignment line:
   `POSTGRES_IMAGE = "postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97"`.
2. Every `PostgresContainer("postgres:16")` becomes `PostgresContainer(POSTGRES_IMAGE)` with
   `from tests.postgres_image import POSTGRES_IMAGE`. **Eleven call sites, not nine** (the CR
   counted `backend/tests/` only):
   - `backend/tests/db/conftest.py:14`, `db/test_migration.py:26`,
     `db/test_migration_0010_key_id.py:62`, `db/test_audit_append_only_privileges.py:40`;
   - `backend/tests/audit/test_audit_client_address.py:49`, `audit/test_authz_decision_audit.py:45`,
     `audit/test_audit_no_secrets.py:134`, `audit/test_failure_audit_persistence.py:48`;
   - `backend/tests/attachments/test_attachment_integrity_persistence.py:36`;
   - `backend/modules/dicom_viewer/tests/test_audit_module_key.py:78`,
     `modules/dicom_viewer/tests/test_failure_audit_persistence.py:36` (their `conftest.py` puts
     `backend/` on `sys.path`, so `tests.postgres_image` imports there too).
3. testcontainers accepts a `name:tag@digest` reference (docker-py pulls by digest); confirm on
   the first run. If it does not, stop and ask rather than dropping the digest.

## Tests (write first)

The existing real-database tests are the tests. Add one assertion in `backend/tests/db/conftest.py`
or a small `backend/tests/db/test_postgres_image.py`: the started container's image digest
(`container.get_wrapped_container().image.attrs["RepoDigests"]`) contains the SOUP-020 digest.
This makes AC-7 an automated check, not only a record.

## Acceptance criteria

- [ ] CR-005 AC-5: all eleven call sites use `POSTGRES_IMAGE`; `grep -rnE '"postgres:' backend
      --include='*.py'` finds only `backend/tests/postgres_image.py`.
- [ ] CR-005 AC-7: the real-database and migration tests pass locally and in CI; a started test
      container carries the SOUP-020 digest (the new test, plus `docker inspect` output recorded
      here).
- [ ] Records: TS-013 gains TC-013.14 (integration: test containers started from the SOUP-020
      reference) under the TS-013 rule of TASK-211.

## Verification

```sh
cd backend
uv run pytest tests/db tests/audit tests/attachments -q
uv run pytest modules/dicom_viewer/tests -q
uv run pytest --cov=app --cov-fail-under=85 -q
grep -rnE '"postgres:' . --include='*.py' | grep -v '/.venv/'
# while a real-DB test runs: docker ps --format '{{.Image}}' ; docker inspect <id> --format '{{.Image}} {{index .Config.Image}}'
```

## Records

TS-013 (see TASK-211's rule). PRB-040's `## Resolution` is written by TASK-213, which completes
the PRB-040 work.

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
