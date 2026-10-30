---
id: "PRB-049"
type: problem-report
title: "Test-data script fails on datetime.UTC, so it cannot create or update any account"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["tooling", "test-data", "found-by:TASK-161"]
---

# PRB-049 — Test-data script fails on datetime.UTC, so it cannot create or update any account

## Observed

`backend/scripts/setup_test_data.py` imports the class (`from datetime import datetime`, line 6)
and then calls `datetime.now(datetime.UTC)` at three places: `set_password` (line 76),
`create_doctor` (line 100) and `create_patient` (line 126). The class `datetime.datetime` has no
`UTC` attribute (`UTC` belongs to the module), so each call raises:

```
AttributeError: type object 'datetime.datetime' has no attribute 'UTC'
```

Reproduced on 2026-10-29 in the running `backend` container of the Compose stack (Python 3.12.15)
by calling `create_patient(...)` directly. `main()` catches the error, prints it and exits 1, so
the script's seed path (doctor and patients) fails at its first account. The application code uses
the module form correctly (`backend/app/auth/password.py:147`,
`backend/app/audit/service.py:55`).

## Impact

Developer tooling only. The script is not part of the shipped application, but several docs name it
as the way to seed accounts for manual testing (`docs/implementation-plan/SMOKE-RESULTS.md:5`,
TASK-161 step 5). Anyone following those instructions cannot create the test users. It also
hard-codes the passwords it prints (`doctor123`, `patient123`).

## Investigation

Root cause: the script was written against `from datetime import datetime`, and the call was
written as if the import were `import datetime`. No test imports the script, so nothing exercised
the lines. Found while TASK-161 (CR-003) needed a test account for the session round trip on the
real Redis server. TASK-161 did not edit the script. It called the script's own `set_password` with
`datetime` replaced by a subclass that carries `UTC`, so the account was created through the
script's code path without a change to the file.

## Safety evaluation

No effect on patient data, on a safety-related function or on a clinical decision: the script runs
only when a developer calls it by hand against a local database. No released version exists
(`docs/releases/` is absent), so no notification is needed. Criticality `minor`.

## Proposed resolution

Replace the three calls with `datetime.now(timezone.utc)` (import `timezone`), or import the module.
Optionally take the passwords from the environment instead of printing fixed ones. Resolve it in a
CR of its own; it is outside CR-003. (Superseded on 2026-10-30: CR-003 D-7 brought it into CR-003.)

## Resolution

Resolved by CR-003 (`resolves` link on the CR, decision D-7) in
[TASK-169](../design-outputs/tasks/TASK-169-fix-datetime-utc-in-test-data-script.md), on branch
`bug/soup-upgrades`. The first option of the proposal was taken, in the form the backend already
uses (`from datetime import UTC, datetime`, as in `backend/tests/db/test_repositories.py:3`). The
fixed passwords are not changed (CR-003 Out of scope).

Changes:
- `backend/scripts/setup_test_data.py`: the import becomes `from datetime import UTC, datetime`,
  and the three calls in `set_password`, `create_doctor` and `create_patient` become
  `datetime.now(UTC)`. Nothing else changes.
- `backend/tests/db/test_setup_test_data.py` (new): loads the script by path and, on the
  testcontainers PostgreSQL `db_session`, calls `create_doctor`, `create_patient` and then
  `set_password`. Each `password_changed_at` must be timezone-aware with a zero UTC offset. The
  test is in `tests/`, so the CI `backend-tests` job runs it.

Verification, reproducible from `backend/` with Docker running (on the reference workstation:
`DOCKER_HOST=unix://$HOME/.docker/run/docker.sock`, the endpoint of the `desktop-linux` context):

```sh
grep -c 'datetime.UTC' scripts/setup_test_data.py                  # 0
uv run pytest tests/db/test_setup_test_data.py -q                  # 1 passed
# against the unfixed script (git show <TASK-169 parent>:backend/scripts/setup_test_data.py):
uv run pytest tests/db/test_setup_test_data.py -q                  # fails: AttributeError ... UTC
uv run ruff check . && uv run pytest --cov=app --cov-fail-under=85  # 500 passed, coverage 91.71 %
```

Results on 2026-10-30: before the fix, the new test failed at `scripts/setup_test_data.py:100`
with `AttributeError: type object 'datetime.datetime' has no attribute 'UTC'`, which is the
PRB-049 failure. After the fix, it passes, and so does the whole backend suite (500 passed,
coverage 91.71 %, `ruff check` clean).
