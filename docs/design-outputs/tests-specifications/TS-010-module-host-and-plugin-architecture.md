---
id: TS-010
type: test-specification
title: Module host and plugin architecture verification
status: approved
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
links:
  - target: SR-016
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-010 — Module host and plugin architecture verification

## Scope

Software requirements covered: SR-016.
Software items under test: SI-MODHOST, SI-MOD-DICOM-BE, SI-FE-MODREG.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (the bundled dicom_viewer module as the fixture). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-010.1 | SR-016 | `backend/tests/modules/test_discovery.py`, `backend/tests/modules/test_platform_services.py` | Modules are discovered by entry point, their manifest validated, and platform services injected | An invalid manifest is rejected |
| TC-010.2 | SR-016 | `backend/tests/modules/test_router_mount.py`, `backend/modules/dicom_viewer/tests/test_module_integration.py` | Module routers mount under the module namespace and work end to end | Mounted path asserted |
| TC-010.3 | SR-016 (AC 3) | `backend/tests/modules/test_module_boundary.py::test_modules_import_only_allowed_platform_interfaces`, `::test_allowed_name_is_defined_in_its_module` | Module source imports platform names only from an allow-list of names per module: `app.modules.contract` (`AuditOutcome`, `PlatformServices`, `RouterRegistry`), `app.api.deps` (`get_current_user`, `get_platform_services`), `app.api.errors` (`AuthorizationError`, `ProblemDetail`, `ValidationProblem`), `app.audit.actions` (`AuditAction`) and `app.modules.module_settings` (`dicom_max_decoded_bytes`, `dicom_max_stored_bytes`). Plain `import app...`, `app.<x>` attribute chains, `from app import x`, `from app.api import deps` and any string constant `app` / `app.*` (dynamic imports in any argument form) are refused. Each allowed name is defined in its module (the contract's `AuditOutcome` is its one declared re-export). `<module>/tests` is not module source. **Limits:** a non-literal dynamic import (`import_module(name)`), an aliased importer (seen only through its string literal), `sys.modules[...]` and a string built at run time are not seen. `app.core.config` is not allowed: a module reads settings through the accessor (decision of 2026-11-14, see Notes) | No import outside the allow-list; the failure names the file and line |
| TC-010.4 | SR-016, SR-017 | `backend/modules/dicom_viewer/tests/test_studies_endpoint.py` | The DICOM endpoint serves bytes only to an authorized caller | Unauthorized request denied |
| TC-010.5 | SR-016 (AC 1) | `backend/tests/modules/test_discovery.py::TestModuleVersionShape`; the bundled module: `backend/modules/dicom_viewer/tests/test_audit_module_key.py::test_real_manifest_passes_discovery` | A manifest version follows the module contract's version rule (SR-016 AC 1): a semver.org version, ASCII only, nothing before or after it | `1.2.3x`, `1.2.3 `, `1.2.3\n`, `1.2.3-evil!`, `1.2.3.4`, `01.2.3`, `v1.2.3`, `1.0.0-01`, `1.0.0-a..b`, `1.2.3` followed by a non-ASCII digit, empty and 100 000-character inputs are rejected (23 cases); `1.2.3`, `0.1.0-rc.1`, `1.0.0+build.5`, `1.0.0--`, `1.0.0+001` are accepted (9 cases); a 1 000 000-character input is rejected in under 2 s |
| TC-010.6 | SR-016 (AC 3) | `backend/tests/modules/test_module_boundary.py::test_boundary_check_catches_planted_import` (one case per form), `::test_boundary_check_accepts_allowed_names_and_scopes_the_tests_exclusion` | The check fails on each planted form: unlisted module, `from app import db`, `from app.api import deps`, `from app.modules import contract`, names re-exported by `app.api.deps` (`DbSession`, `Account`, `AccountRepository`, `get_redis`), `app.core.config` names, `*`, a prefix lookalike, plain `import app...`, an `app.db` attribute chain, and `import_module` / `__import__` with positional, keyword, f-string, conditional and allowed-module literals. Allowed names pass; `<module>/tests` is skipped, a `tests` package inside the shipped package is checked | Every planted form is reported with file and line; the allowed ones are not |
| TC-010.7 | SR-016 (AC 3) | `backend/tests/modules/test_module_settings.py` | `app.modules.module_settings` returns the configured `dicom_max_stored_bytes` and `dicom_max_decoded_bytes` (default and overridden, read on each call) and exports nothing else. The DICOM size bounds are unchanged (TS-019 TC-019.1 to TC-019.4, `modules/dicom_viewer/tests/test_size_bounds.py`) | Configured values returned; `__all__` is the two accessors |

## Acceptance criteria (class B unit level, §5.5.3)

- Interfaces: the module contract is the only import surface.
- Fault handling: a module that raises on import does not prevent the host from starting.

## Notes

- 1.2 (2026-11-02) — Status `in_review`: TC-010.5 added (TASK-200, PRB-028): the module version is fully anchored. Approval record cleared; QA/human re-approve.
- 1.2 (2026-11-02, round 2) — TC-010.5 follows QA round 1: ASCII-only, strict pre-release and build identifiers, rule worded as the module contract's version rule.
- 1.2 (2026-11-02, QA) — Status `approved` on QA approval of TASK-200 round 2.
- 1.3 (2026-11-14) — Status `in_review`: TC-010.3 now checks every `app.*` import of module source against an allow-list and TC-010.6 is its negative control (TASK-223, PRB-030). The note that the boundary test under-verifies the isolation claim is removed. Approval record cleared; QA/human re-approve.
- 1.3 (2026-11-14, QA) — Status `draft`: TASK-223 round 1 CHANGES REQUESTED; TC-010.3/TC-010.6 to cover re-exported names, keyword and non-literal dynamic forms, and stated limits.
- 1.4 (2026-11-14) — Status `in_review`, TASK-223 round 2 (QA R1-1, R1-2, R1-4 to R1-6): the allow-list is by name per module; plain `import app...`, attribute chains, `from app.api import deps`-style imports and any `app`/`app.*` string literal are refused; the limits are stated in TC-010.3; TC-010.6 plants every form. Decision R1-3 (human, 2026-11-14, "Narrow accessor"): `app.core.config` is removed from the allow-list because `Settings` hands a module `database_url`, the object-store keys and the at-rest keys, so a module could open its own database connection or read stored data outside `PlatformServices`; the DICOM module reads the two limits it needs through `app.modules.module_settings` (TC-010.7). Residual: a module can still call any function in an allowed module that is named on the list; the list is the control. Approval record cleared; QA/human re-approve.
- 1.4 (2026-11-14, QA) — Status `approved` on QA approval of TASK-223 round 2.
