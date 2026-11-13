---
id: "TASK-212"
type: task
title: "Start every test PostgreSQL from one pinned definition"
status: approved
version: "1.2"
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

- [x] CR-005 AC-5: all eleven call sites use `POSTGRES_IMAGE`; `grep -rnE '"postgres:' backend
      --include='*.py'` finds only `backend/tests/postgres_image.py` (as built: `backend/postgres_image.py`,
      see Verification results and the QA review).
- [x] CR-005 AC-7: the real-database and migration tests pass locally and in CI; a started test
      container carries the SOUP-020 digest (the new test, plus `docker inspect` output recorded
      here). Locally verified by QA; the hosted CI run is evidenced at TASK-216 (Checkpoint C).
- [x] Records: TS-013 gains TC-013.14 (integration: test containers started from the SOUP-020
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

## Verification results (Software Developer, 2026-11-12)

**Deviation from the plan (location of the definition).** The definition is
`backend/postgres_image.py`, not `backend/tests/postgres_image.py`. The DICOM module tests
(`backend/modules/dicom_viewer/tests/`, an importable `tests` package of their own) shadow
`backend/tests` on `sys.path`, so `from tests.postgres_image import ...` failed at collection
there (`ModuleNotFoundError`). `backend/` is on `sys.path` for both suites (rootdir `conftest.py`;
the DICOM `conftest.py` inserts it), so the top-level module imports in all eleven files. It is not
shipped: `backend/Dockerfile` copies only `app/`, `modules/`, `scripts/` and named files.

**Changes.** New `backend/postgres_image.py` (`POSTGRES_IMAGE`, equal to the `postgres` image in
`infra/docker-compose.yml:126`, confirmed); the eleven `PostgresContainer(...)` call sites now use
it (`tests/db/conftest.py`, `test_migration.py`, `test_migration_0010_key_id.py`,
`test_audit_append_only_privileges.py`; `tests/audit/` x4; `tests/attachments/` x1;
`modules/dicom_viewer/tests/` x2); new `backend/tests/db/test_postgres_image.py` (TC-013.14: the
reference carries the SOUP-020 digest; the started `pg_container` has it in `RepoDigests`).
testcontainers/docker-py accepted the `name:tag@digest` reference on the first run.

**AC-5.** `cd backend && grep -rnE '"postgres:' . --include='*.py' | grep -v '/.venv/'` finds only
`postgres_image.py:13`. The unrestricted `grep -rn "postgres:" backend/` also lists connection-URL
hosts (`@postgres:5432`, `.env`, `scripts/setup_test_data.py`); those are not image references.

**AC-7 (local).**
- `uv run pytest tests/db tests/audit tests/attachments -q`: 350 passed.
- `uv run pytest modules/dicom_viewer/tests -q`: 25 passed.
- `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85 -q` (as CI): 1549 passed,
  6 skipped; total coverage 94.51% (floor 85%).
- `uv run ruff check .`, `uv run black --check .`, `uv run mypy app`: clean.
- A container started from `POSTGRES_IMAGE` by a one-off script (same definition), inspected while
  running:
  - `docker inspect <id> --format '{{.Image}} | {{index .Config.Image}}'`:
    `sha256:94a8e663…2abacae7279 | postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97`
  - `docker image inspect … --format '{{json .RepoDigests}}'`:
    `["postgres@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97"]`
  - `postgres --version` in the container: `PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2)`.
- CI run of the same: pending a pushed run (TASK-216).

**Records.** TS-013 (version 1.6, not bumped) gains TC-013.14 in scope, environment, coverage note,
test cases and version history.

## QA review (2026-11-12): APPROVED

Verified by QA on the working tree of `bug/build-hygiene` (HEAD `6bff85c` + this task's changes):

- **AC-5.** All eleven `PostgresContainer(...)` call sites use `POSTGRES_IMAGE`. Repository-wide
  search (tracked and untracked, `docs/` excluded) for a `postgres:<tag>` image string outside URL
  hosts: only `backend/postgres_image.py:13`, the Compose `postgres` service
  (`infra/docker-compose.yml:126`), the CI service container (`.github/workflows/ci.yml:51`), the
  pin-check fixtures and their unit tests, and the service list of `infra/smoke-test.sh:196-197`
  (container names, not images). The only other testcontainers user,
  `tests/auth/test_session_cap_concurrency.py`, starts Redis from the Compose reference it reads.
- **AC-7.** `uv run pytest tests/db tests/audit tests/attachments -q`: 350 passed;
  `uv run pytest modules/dicom_viewer/tests -q`: 25 passed (also a CI step, `ci.yml:115`). A test
  container seen live during the full run had `Config.Image` =
  `postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97`. An
  independent container started from `POSTGRES_IMAGE` (QA script):
  `Image sha256:94a8e6634f91…` | `Config.Image` = the reference above; image `RepoDigests`
  `["postgres@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97"]`;
  `postgres (PostgreSQL) 16.15 (Debian 16.15-1.pgdg13+2)`; the digest equals SOUP-020.
- **The RepoDigests test discriminates.** Scratch copy of `backend/`, `tests/db/conftest.py`
  changed to `"postgres:16"` (the local floating image, `081f1bc7…`) and to `"postgres:16.15"` (pulled:
  Docker Hub now serves `f9a7b9eb…` for both tags, a later build than the pinned one): each makes
  `test_started_container_image_carries_the_soup_020_digest` fail; the unmutated copy passes.
- **Location deviation confirmed.** In a scratch copy, a DICOM-suite test doing
  `from tests.postgres_image import POSTGRES_IMAGE` fails with `ModuleNotFoundError` (the
  `modules/dicom_viewer/tests/__init__.py` package wins), while the same import works from
  `backend/tests`. `backend/postgres_image.py` is not shipped: `backend/Dockerfile` copies only
  `pyproject.toml`, `uv.lock`, `alembic.ini`, `modules/`, `app/`, `scripts/` and `entrypoint.sh`
  (no `COPY .`, so no `.dockerignore` is needed); `pyproject.toml` has no build system or package
  list, and coverage is `--cov=app`, so the module is neither packaged nor measured.

**Checkpoint A (CR-005 Plan):** `python3 -m unittest discover -s infra/tests`: 135 tests OK;
`python3 infra/check_image_pins.py`: exit 0, no output; `uv run pytest --cov=app
--cov-report=term-missing --cov-fail-under=85` (as `ci.yml:110`): 1549 passed, 6 skipped, total
coverage 94.51%; DICOM suite 25 passed; `ruff check .`, `black --check .` (265 files), `mypy app`
(133 files): clean; `uvx --from uv==0.13.7 uv lock --check`: passes. Backend image installed set:
evidenced by TASK-210 (AC-10); `backend/Dockerfile`, `uv.lock`, `pyproject.toml` and
`entrypoint.sh` are unchanged since that commit, and the new module is not copied. Checkpoint A holds.

**Traceability** (CR-005 and two link hops, fallback parser): 439 records, 170 in scope, 0 errors;
18 warnings, all W5 (approved records linking to SOUP-001, ADD-024, TS-013 in review, and the older
TASK-142→101, TASK-202→113) or W6 (links to obsolete records), as at TASK-211.

Findings (none blocking this task):

1. **MEDIUM: ADR-0020 and TASK-213 name the old path.** ADR-0020 (Accepted) lines 52 and 69
   ("Test definition in the test tree. `backend/tests/postgres_image.py` …") and TASK-213 lines 50,
   60 and 62 (rule 1, the rule-3 exclusion and the message example). Fix, before TASK-213 starts:
   amend ADR-0020's decision to `backend/postgres_image.py` with the shadowing reason and a dated
   note (Software Architect role; the human acknowledges, the ADR is Accepted), and change TASK-213's
   rules, exclusion, messages and fixture paths to the actual path.
2. **MEDIUM: the definition is not "one assignment line".** ADR-0020 line 61 (the script reads
   the definition as text, "one assignment line") and TASK-213 rule 1 ("exactly one
   `POSTGRES_IMAGE = "<ref>"` line") do not match `backend/postgres_image.py:12-14`, which is a
   three-line parenthesised assignment. The single-line form is 105 characters and fails
   `ruff check` E501 (line length 100; `black` alone accepts it). Fix in TASK-213: either make the
   definition one line with `# noqa: E501` and keep the rule, or let rule 1 read the parenthesised
   form (fixtures for both); record the choice in ADR-0020 with finding 1.
3. **LOW: the started-container test covers one fixture.** `tests/db/test_postgres_image.py`
   checks only `pg_container`; the other ten call sites are held to the definition by the AC-5
   search today and by TASK-213 rule 3 from then on. No change needed if TASK-213 lands as planned;
   say so in TC-013.14's coverage note at TASK-213.

TS-013 stays `in_review` (TASK-213 adds TC-013.13 to version 1.6). PRB-040 stays `open`; its
`## Resolution` is written by TASK-213.

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
- 1.1 (2026-11-12) — Implemented; definition placed at `backend/postgres_image.py` (see Verification results); `draft → in_review` (Software Developer role).
- 1.2 (2026-11-12) — QA review: APPROVED (2 MEDIUM, 1 LOW, carried to TASK-213 and ADR-0020). `in_review → approved`;
  acceptance-criteria boxes ticked; TS-013 stays `in_review`; PRB-040 stays `open`.
