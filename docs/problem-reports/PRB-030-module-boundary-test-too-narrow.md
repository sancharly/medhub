---
id: "PRB-030"
type: problem-report
title: "Module boundary test denies only two import substrings"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["verification"]
---

# PRB-030 — Module boundary test denies only two import substrings

## Observed

`backend/app/modules/.../test_module_boundary.py` asserts against two import substrings, so a module importing most `app.*` internals would pass.

## Impact

The architectural boundary behind SR-016 and ADR-0005 is only nominally verified.

## Safety evaluation

No direct hazard; it weakens the verification of the module isolation claim.

## Resolution

Fixed in CR-006 by TASK-223. `backend/tests/modules/test_module_boundary.py` parses every module source file with
`ast` and fails, naming file and line, on anything outside an allow-list of names per platform module, kept in the
test (ADD-014): `app.modules.contract` (`AuditOutcome`, `PlatformServices`, `RouterRegistry`), `app.api.deps`
(`get_current_user`, `get_platform_services`), `app.api.errors` (`AuthorizationError`, `ProblemDetail`,
`ValidationProblem`), `app.audit.actions` (`AuditAction`) and `app.modules.module_settings`. The check refuses
plain `import app...`, `app.<x>` attribute chains, `from app import x`, `from app.api import deps`, names an allowed
module only re-exports (`DbSession`, `Account`, `AccountRepository`, `get_redis` from `app.api.deps`), and any string
constant `app` or `app.*` (so `import_module` / `__import__` in positional, keyword, f-string and conditional form).
A test checks each allowed name is defined in its module. Because `app.core.config` would give a module the
database URL and the storage and encryption keys, it is not allowed (human decision, 2026-11-14): the DICOM module
now reads its two size limits through the new `app/modules/module_settings.py`. Limits (static check): non-literal
dynamic imports, an aliased importer and `sys.modules[...]` are not seen. TS-010 TC-010.3, TC-010.6 and TC-010.7
record this. Reproduce: `cd backend && uv run pytest tests/modules -v && uv run pytest modules/dicom_viewer/tests`.
Negative controls (by hand, reverted): `from app.core.config import get_settings` re-planted in `dicom.py`,
`from app.api.deps import DbSession`, `import app.api.errors` with an `app.db` chain, `import_module(name="app.db")`,
`import_module(f"app.db.{x}")` and `from app.api import deps` in `router.py` each failed the test at the planted line;
an allow-listed accessor import passed.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Low.
