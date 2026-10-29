---
id: "PRB-049"
type: problem-report
title: "Test-data script fails on datetime.UTC, so it cannot create or update any account"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-29"
criticality: minor
links: []
tags: ["tooling", "test-data", "found-by:TASK-161"]
---

# PRB-049 — Test-data script fails on datetime.UTC, so it cannot create or update any account

## Observed

`backend/scripts/setup_test_data.py` imports the class (`from datetime import datetime`, line 5)
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
CR of its own; it is outside CR-003.
