---
id: "TASK-223"
type: task
title: "Module boundary test with an allow-list of platform imports"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-14"
links:
  - target: "SR-016"
    relation: implements
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-030"
    relation: relates_to
  - target: "RISK-001"
    relation: relates_to
  - target: "ADD-014"
    relation: relates_to
  - target: "TS-010"
    relation: relates_to
tags: ["cr:CR-006", "verification", "modules"]
---

# TASK-223 — Module boundary test with an allow-list of platform imports

- **Software item / unit:** SI-MODHOST boundary (ADD-014); test only.
- **PRB:** PRB-030. **CR:** CR-006 (verification; no behaviour change).
- **Depends on:** TASK-218 (it edits the DICOM module's imports; run the test on the final shape).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** XS (`backend/tests/modules/test_module_boundary.py`; records TS-010).

## Objective

SR-016 AC 3: a module obtains data only through the platform's authorized interfaces. The boundary test
(`test_module_boundary.py:9-12`) denies only `app.db` and `app.core.object_storage`; any other `app.*` import
passes.

## Implementation detail

- Parse every `.py` under `backend/modules/*/` with `ast`; collect `import app…` / `from app… import` targets
  (including relative-looking and `importlib.import_module("app…")` string literals).
- Allow-list: the platform interfaces the module host publishes (today `app.api.deps` for
  `get_current_user` / `get_platform_services`, `app.api.errors`); anything else fails with the file and line.
  The list lives in the test with a comment pointing to ADD-014.

## Tests (write first)

- `test_modules_import_only_allowed_platform_interfaces` (SR-016 AC 3).
- `test_boundary_check_catches_planted_import` (SR-016 AC 3): a temporary module file importing
  `app.identity.service` makes the check fail.
- TS-010 (1.2 → 1.3, approval cleared) TC-010.x.

## Acceptance criteria

- [x] SR-016 AC 3: allow-list check green on the code, red on every planted form (TS-010 TC-010.3, TC-010.6, TC-010.7).

## Definition of Done

- [x] `uv run pytest tests/modules modules/dicom_viewer/tests` green; `traceability-check` no error for this record

## QA review — round 1 (2026-11-14): CHANGES REQUESTED

Verified: suite green (1708 passed, 10 skipped; dicom 31 passed), ruff/mypy clean, trace 0 errors. QA
negative control: `from app.db.repositories.session import DbSession` appended to `dicom.py` failed the test
at `dicom.py:83`; file restored, `cmp` identical. Relative imports are not a bypass (the module package is
top level; `from ...app` raises ImportError). The other four allow-list entries are genuine platform
surfaces used by the DICOM module (`router.py:11-15`, `dicom.py:7-8`, `manifest.py:8`).

- **R1-1 HIGH — the allow-list is name-blind, so allowed modules re-export forbidden internals.**
  `test_module_boundary.py:20-26,63-64` match only the module path. `from app.api.deps import DbSession`
  (a DB session, the SI-PERSIST access `12-interfaces.md:41` forbids), `from app.api.deps import Account,
  AccountRepository` and `from app.api.deps import get_redis, get_session_service` all pass (deps.py:15-20
  imports them). `import app.api.errors` binds the root package `app`, so `app.db.models.account.Account`
  then passes too. Fix: allow-list names per module for `from` imports (e.g. `app.api.deps`:
  `get_current_user`, `get_platform_services`, `require_module_enabled`; or require
  `getattr(mod, name).__module__` to be the allowed module), and reject plain `import app.…` or any
  `app.<x>` attribute chain outside the list; add these forms to the planted test and TC-010.6.
- **R1-2 MEDIUM — the old assertions are not fully subsumed.** The removed substring test caught, and the
  new AST check misses: `import_module(name='app.db')` (keyword), `import_module(f'app.db.{m}')`,
  `import_module('app.db' if c else 'y')`, `__import__(name='app.db')` (`test_module_boundary.py:47-56`
  read only a positional `ast.Constant`). Fix: flag every `str` constant (and the leading literal of a
  JoinedStr) in module source that equals `app` or starts with `app.` and is not allow-listed, or at least
  inspect keywords and nested constants of the call; add the forms to the planted test.
- **R1-3 MEDIUM — the `app.core.config` widening is not recorded as a decision.** `get_settings()` hands a
  module `database_url`, the object-store keys and the at-rest keys (`app/core/config.py:31-60`), so a module
  can open its own DB connection. The developer reports a human decision, but no record holds it (this TASK
  says the list is `app.api.deps`, `app.api.errors`; ADD-014 names no list). Fix: record the decision, its
  rationale and this residual in this TASK and TS-010 (and in ADD-014/12-interfaces through TASK-225), or
  replace it with a module-config accessor on `PlatformServices` in a later CR.
- **R1-4 LOW — stated limits missing.** Non-literal dynamic imports (`import_module(n)`), an aliased
  `import_module` (`from importlib import import_module as im`), `sys.modules[...]` are not seen. State them
  in the test docstring and TC-010.3 (project convention, PRB-027).
- **R1-5 LOW — test exclusion too wide.** `test_module_boundary.py:33` drops any `tests` directory below the
  module, including one inside the shipped package (`<module>/<pkg>/tests/helper.py` importing `app.db` is
  not checked). Fix: exclude only `parts[1] == "tests"`.
- **R1-6 LOW — `from app.api import deps` / `from app.modules import contract` are rejected** although they
  name allowed modules (target `app.api`). Conservative; either expand `from <pkg> import <sub>` to
  `<pkg>.<sub>` as for `from app import x`, or state that the form is not allowed.
- Note: PRB-030 is already `resolved`; keep it there only if the fix lands in this CR, and update its
  Resolution text with the round-2 forms.

## Round 2 (Software Developer, 2026-11-14)

- R1-1: the allow-list is by name per module; plain `import app...`, `app.<x>` chains and re-exported names are refused;
  each allowed name is checked to be defined in its module (`AuditOutcome` in the contract is its one declared re-export).
- R1-2: any string constant `app` / `app.*` is refused, so keyword, f-string, conditional and `__import__` forms are caught.
- R1-4: limits in the test docstring and TC-010.3 (non-literal dynamic imports, aliased importer, `sys.modules[...]`).
- R1-5: only `<module>/tests` is excluded. R1-6: `from app.api import deps` and `from app.modules import contract`
  are refused; import the names from the defining module.
- **R1-3 decision (human, 2026-11-14, "Narrow accessor"):** `app.core.config` is not allowed. `Settings` carries
  `database_url`, the object-store keys and the at-rest keys, so a module could open its own database connection
  or read stored data outside `PlatformServices` (SR-016 AC 3). The new `app/modules/module_settings.py` exposes
  only `dicom_max_stored_bytes()` and `dicom_max_decoded_bytes()` (read on each call); `router.py` and `dicom.py`
  use it. Files added: `backend/app/modules/module_settings.py`, `backend/tests/modules/test_module_settings.py`;
  changed: `modules/dicom_viewer/dicom_viewer/{router,dicom}.py`. No behaviour change (same values, TS-019 unchanged).
  Residual: each future module setting needs one accessor and a list entry (a design decision); the allowed names
  are the control. ADD-014 and `docs/design/12-interfaces.md` should record the name-level allow-list and the
  accessor (TASK-225).

## QA review — round 2 (2026-11-14): APPROVED

All round-1 findings closed. QA probes re-run against the new check: 15 of 16 forms caught
(re-exported `DbSession`/`Account`/`AccountRepository`/`get_redis`, `import app.api.errors` + `app.db` chain,
`from app.api import deps`, `app.core.config` names, keyword / f-string / concatenated / variable / aliased
`import_module`, `sys.modules['app.db']`, `TYPE_CHECKING` and function-local imports); the one miss is
`from ...app import db`, which cannot resolve from a top-level module package (not a bypass). The four
dynamic forms only the old substring test caught are now caught; a `tests` package inside the shipped package
is checked. QA negative control: `from app.core.config import get_settings` re-planted at `dicom.py:83` failed
the test at that line; file restored, `cmp` identical. `module_settings.py` exposes only the two accessors
(`__all__`); its `get_settings` attribute is not on the allow-list, so a module importing it fails the check.
DICOM behaviour unchanged: `test_size_bounds.py` 6/6 green; run with `DICOM_MAX_STORED_BYTES=1000
DICOM_MAX_DECODED_BYTES=10` three bound tests fail as expected, so the environment still reaches the module.
Suite 1743 passed / 10 skipped, DICOM 31 passed, ruff/mypy clean, format only the 3 known files, trace 0 errors.

Carried (LOW, not blocking):
- R2-1: the `app.<x>` attribute rule (`test_module_boundary.py:80-83`) also refuses a local name `app`
  (e.g. `app = FastAPI()` in module source). Conservative; state it in the docstring/TC-010.3 or narrow it to
  a bound `import app`.
- R2-2: state the run-time limit: objects returned by allowed names reach internals (the `Account` from
  `get_current_user` carries its SQLAlchemy session via `sqlalchemy.inspect(actor).session`). The docstring's
  `sys.modules[...]` limit is over-stated (a literal key is caught; only a computed one is not).
- R2-3 (records, for TASK-225 / Software Architect): `app/modules/module_settings.py` is a new published
  platform interface of SI-MODHOST. ADD-014 (approved) needs a reopened 1.1 naming it as a unit (or under
  `U-MH-PlatformServices`) with human re-approval; `docs/design/05-building-blocks.md:100-102` and the module
  contract in `docs/design/12-interfaces.md:28-42` should state the name-level allow-list and the settings
  accessor. TASK-225's scope table and links do not list ADD-014, 05's U-MH units or the 12 module-contract
  rule yet: add them. No SR change (SR-016 AC 3 already requires authorized interfaces only), no new RISK.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-030.
- 1.1 (2026-11-14) — Implemented (Software Developer): allow-list check and planted-import control in `test_module_boundary.py`; TS-010 1.3; PRB-030 resolved. Allow-list is wider than the 'today' list in this record (see TS-010 TC-010.3). Handed to QA (`in_review`).
- 1.1 (2026-11-14, QA) — Round 1 CHANGES REQUESTED (R1-1 HIGH, R1-2/R1-3 MEDIUM, R1-4..6 LOW). Status `draft`.
- 1.2 (2026-11-14) — Round 2 (Software Developer): R1-1, R1-2, R1-4, R1-5, R1-6 fixed; R1-3 decided (narrow accessor) and implemented; TS-010 1.4; PRB-030 Resolution updated. Handed to QA (`in_review`).
- 1.2 (2026-11-14, QA) — Round 2 APPROVED; R2-1/R2-2 LOW carried, R2-3 to TASK-225. Status `approved`.
