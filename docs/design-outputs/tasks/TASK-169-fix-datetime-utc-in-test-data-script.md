---
id: "TASK-169"
type: task
title: "Fix datetime.UTC in the test-data script"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "NFR-006"
    relation: implements
  - target: "SR-028"
    relation: implements
  - target: "CR-003"
    relation: relates_to
  - target: "PRB-049"
    relation: relates_to
tags: ["tooling", "test-data", "cr:CR-003", "issue:sancharly/medhub#32"]
---

# TASK-169 — Fix datetime.UTC in the test-data script

- **Software item / unit:** none. `backend/scripts/setup_test_data.py` is developer tooling that
  seeds a local database for manual verification. It is not in the backend image's application
  code path and belongs to no software item. The `implements` links follow the other tooling tasks
  (TASK-001, TASK-005).
- **Depends on:** none
- **Branch:** `bug/soup-upgrades`
- **Size:** XS
- **Needs:** a Docker host (the test uses the testcontainers PostgreSQL of `tests/db/conftest.py`).

## Objective

Resolve PRB-049 (CR-003 D-7). The script imports the class (`from datetime import datetime`) and
calls `datetime.now(datetime.UTC)`, which raises `AttributeError`, so it creates and updates no
account. Use the module's `UTC`, as the application code and the tests do, and add the test whose
absence let the defect through.

## Interfaces to honor

- The script's functions keep their signatures and return values. `main()` is not changed.
- The printed test passwords are not changed (CR-003 Out of scope).

## Implementation detail

1. Test first: `backend/tests/db/test_setup_test_data.py` loads the script by path with
   `importlib.util` (it is not a package module) and, on the `db_session` fixture, calls
   `create_doctor`, `create_patient`, then `set_password` on the patient. Each account gets a
   `password_changed_at` that is timezone-aware with a zero UTC offset. Run it on the unfixed
   script and confirm it fails with the PRB-049 `AttributeError`.
2. In the script, change the import to `from datetime import UTC, datetime` and the three calls
   (`set_password`, `create_doctor`, `create_patient`) to `datetime.now(UTC)`.

## Acceptance criteria

- [x] CR-003 **AC-20**: no `datetime.UTC` is left in the script. The three functions set a
      timezone-aware UTC `password_changed_at`. The new test runs in the CI backend suite and
      fails on the unfixed script with the PRB-049 `AttributeError`.

## Verification

```sh
grep -c 'datetime.UTC' backend/scripts/setup_test_data.py                      # 0
cd backend && DOCKER_CONTEXT=desktop-linux uv run pytest tests/db/test_setup_test_data.py -v
cd backend && uv run ruff check scripts tests/db/test_setup_test_data.py && uv run ruff format --check scripts tests/db/test_setup_test_data.py
cd backend && DOCKER_CONTEXT=desktop-linux uv run pytest --cov=app --cov-fail-under=85
```

## Definition of Done

- [x] Lint and format pass for the changed files.
- [x] The backend suite passes with coverage at or above 85 %.
- [x] PRB-049 is `resolved`, with a `## Resolution`.
- [x] `traceability-check` shows no error for the touched records.

## Evidence (developer handoff, 2026-10-30)

Run from `backend/` with `DOCKER_HOST=unix://$HOME/.docker/run/docker.sock` (the `desktop-linux`
endpoint) and `TESTCONTAINERS_RYUK_DISABLED=true`, after `uv sync --frozen`.

- **Test first:** `tests/db/test_setup_test_data.py` on the unfixed script fails at
  `scripts/setup_test_data.py:100` (`create_doctor`) with
  `AttributeError: type object 'datetime.datetime' has no attribute 'UTC'` (1 failed).
- **Fix:** `from datetime import UTC, datetime`; the three calls are `datetime.now(UTC)`
  (`git diff --stat`: 4 lines changed). `grep -c 'datetime.UTC'` gives 0.
- **After:** the new test passes (1 passed). `ruff check` and `ruff format --check` are clean for
  both files. Full suite: `uv run ruff check .` clean, `uv run pytest --cov=app
  --cov-fail-under=85`: 500 passed, coverage 91.71 %.
- PRB-049 is `resolved` 1.1 with its `## Resolution`.
- **Not run:** the CI `backend-tests` job (needs the pushed branch).

## QA review (2026-10-30)

**Verdict: APPROVED** (`in_review → approved`). There is no CRITICAL, HIGH, MEDIUM or LOW finding.
QA re-ran every claim on the working tree of `bug/soup-upgrades-prb-049-050` (base 8c9fa35), and ran
the new test against the unfixed script from a scratch copy, so the working tree was not touched.

The acceptance criterion is ticked. Its CI part ("runs in the CI backend suite") was checked by
configuration: the test is under `backend/tests/` (`testpaths = ["tests"]`), and the
`backend-tests` job runs `uv run pytest` from `backend/` (`.github/workflows/ci.yml:105`), with the
existing testcontainers tests in `tests/db/`. The CI run itself belongs to AC-18 (TASK-168) on the
pushed branch head.

**Review notes.**
- The diff is the import and the three calls, nothing else. `main()`, signatures, return values and
  the printed passwords are unchanged (CR-003 Out of scope).
- The test reads each `password_changed_at` back from PostgreSQL: the session expires the objects
  on commit, and `set_password` is followed by `refresh`. So it checks the stored `timestamptz`, not
  only the Python value. The script commits, so the rows stay in the test module's container. That
  is harmless, because `pg_container` is module-scoped and this module has one test.
- Observation, not a finding: the TASK and PRB-049 name the branch `bug/soup-upgrades`. The work is
  on `bug/soup-upgrades-prb-049-050`, which branches from it. The records are right once that
  branch is merged into `bug/soup-upgrades`. If it goes to `main` some other way, correct them.

### Findings

None.

### Verification run (QA, 2026-10-30)

Run from `backend/` with `DOCKER_HOST=unix://$HOME/.docker/run/docker.sock` and
`TESTCONTAINERS_RYUK_DISABLED=true`.

| Check | Result |
|---|---|
| `git diff backend/scripts/setup_test_data.py` | 4 lines: `from datetime import UTC, datetime`, and `datetime.now(UTC)` at `:76`, `:100`, `:126` |
| `grep -c 'datetime.UTC' scripts/setup_test_data.py` | 0 |
| `uv run ruff check scripts tests/db/test_setup_test_data.py`; `ruff format --check` on the same paths | Clean; already formatted |
| `uv run pytest tests/db/test_setup_test_data.py -v` (fixed script) | 1 passed |
| Same test against `git show HEAD:backend/scripts/setup_test_data.py` (scratch copy of the script, the test with `SCRIPT` pointed at it, and both conftests) | 1 failed at `setup_test_data.py:100` (`create_doctor`): `AttributeError: type object 'datetime.datetime' has no attribute 'UTC'`, the PRB-049 failure |
| `uv run ruff check .` | All checks passed |
| `uv run pytest --cov=app --cov-fail-under=85` | 500 passed, coverage 91.71 % |
| PRB-049 | `resolved` 1.1. `## Resolution` names both files, and its commands reproduce the results above. CR-003 1.4 has `resolves` PRB-049 |
| `traceability-check` (fallback parser, whole project) | 0 errors, no class-gated finding. No warning names TASK-169, PRB-049 or CR-003 |
