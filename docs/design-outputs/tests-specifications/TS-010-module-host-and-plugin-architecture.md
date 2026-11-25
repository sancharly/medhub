---
id: TS-010
type: test-specification
title: Module host and plugin architecture verification
status: approved
version: "1.7"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-25"
links:
  - target: SR-016
    relation: verifies
  - target: SR-017
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-010 — Module host and plugin architecture verification

## Scope

Software requirements covered: SR-016, SR-017 (AC 7, TC-010.8, TC-010.9).
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
| TC-010.2 | SR-016 | `backend/tests/modules/test_router_mount.py`, `backend/modules/dicom_viewer/tests/test_module_integration.py` | Module routers mount under the module namespace and work end to end; the module suite imports the installed package and needs no import root of its own (TC-010.8) | Mounted path asserted |
| TC-010.3 | SR-016 (AC 3) | `backend/tests/modules/test_module_boundary.py::test_modules_import_only_allowed_platform_interfaces`, `::test_allowed_name_is_defined_in_its_module` | Module source imports platform names only from an allow-list of names per module: `app.modules.contract` (`AuditOutcome`, `PlatformServices`, `RouterRegistry`), `app.api.deps` (`get_current_user`, `get_platform_services`), `app.api.errors` (`AuthorizationError`, `ProblemDetail`, `ValidationProblem`), `app.audit.actions` (`AuditAction`) and `app.modules.module_settings` (`dicom_max_decoded_bytes`, `dicom_max_stored_bytes`). Plain `import app...`, `app.<x>` attribute chains, `from app import x`, `from app.api import deps` and any string constant `app` / `app.*` (dynamic imports in any argument form) are refused. Each allowed name is defined in its module (the contract's `AuditOutcome` is its one declared re-export). `<module>/tests` is not module source. **Limits:** a non-literal dynamic import (`import_module(name)`), an aliased importer (seen only through its string literal), `sys.modules[...]` and a string built at run time are not seen. `app.core.config` is not allowed: a module reads settings through the accessor (decision of 2026-11-14, see Notes) | No import outside the allow-list; the failure names the file and line |
| TC-010.4 | SR-016, SR-017 | `backend/modules/dicom_viewer/tests/test_studies_endpoint.py` | The DICOM endpoint serves bytes only to an authorized caller | Unauthorized request denied |
| TC-010.5 | SR-016 (AC 1) | `backend/tests/modules/test_discovery.py::TestModuleVersionShape`; the bundled module: `backend/modules/dicom_viewer/tests/test_audit_module_key.py::test_real_manifest_passes_discovery` | A manifest version follows the module contract's version rule (SR-016 AC 1): a semver.org version, ASCII only, nothing before or after it | `1.2.3x`, `1.2.3 `, `1.2.3\n`, `1.2.3-evil!`, `1.2.3.4`, `01.2.3`, `v1.2.3`, `1.0.0-01`, `1.0.0-a..b`, `1.2.3` followed by a non-ASCII digit, empty and 100 000-character inputs are rejected (23 cases); `1.2.3`, `0.1.0-rc.1`, `1.0.0+build.5`, `1.0.0--`, `1.0.0+001` are accepted (9 cases); a 1 000 000-character input is rejected in under 2 s |
| TC-010.6 | SR-016 (AC 3) | `backend/tests/modules/test_module_boundary.py::test_boundary_check_catches_planted_import` (one case per form), `::test_boundary_check_accepts_allowed_names_and_scopes_the_tests_exclusion` | The check fails on each planted form: unlisted module, `from app import db`, `from app.api import deps`, `from app.modules import contract`, names re-exported by `app.api.deps` (`DbSession`, `Account`, `AccountRepository`, `get_redis`), `app.core.config` names, `*`, a prefix lookalike, plain `import app...`, an `app.db` attribute chain, and `import_module` / `__import__` with positional, keyword, f-string, conditional and allowed-module literals. Allowed names pass; `<module>/tests` is skipped, a `tests` package inside the shipped package is checked | Every planted form is reported with file and line; the allowed ones are not |
| TC-010.7 | SR-016 (AC 3) | `backend/tests/modules/test_module_settings.py` | `app.modules.module_settings` returns the configured `dicom_max_stored_bytes` and `dicom_max_decoded_bytes` (default and overridden, read on each call) and exports nothing else. The DICOM size bounds are unchanged (TS-019 TC-019.1 to TC-019.4, `modules/dicom_viewer/tests/test_size_bounds.py`) | Configured values returned; `__all__` is the two accessors |
| TC-010.8 | SR-017 (AC 7), SR-016 | `backend/modules/dicom_viewer/tests/test_installed_package.py::test_entry_point_is_discovered`, `::test_distribution_declares_its_runtime_dependencies`, `::test_module_is_imported_from_the_installed_distribution`; `[tool.pytest.ini_options] addopts = "--import-mode=importlib"` in `backend/pyproject.toml` | The `medhub-dicom-viewer` package is installed from `backend/uv.lock` in the test environment: exactly one `medhub.modules` entry point, `dicom-viewer` = `dicom_viewer.manifest:manifest`, loads to a manifest with `module_key == "dicom-viewer"` and is returned by `discover_modules()`; the distribution requires `numpy` and `pydicom` (names parsed with `packaging`) and `numpy` imports (the lock is the authority on the version); `dicom_viewer` is imported from the installed distribution (its files, or its editable source directory from `direct_url.json`). pytest runs in `importlib` import mode, so it does not put `backend/modules/dicom_viewer` on `sys.path` (the default `prepend` mode does, because `tests/` is a package and the module root is not); the module conftest has no `sys.path` mutation. Image half: TS-013 TC-013.15 (CI Docker Build step, TASK-236) | Negative control: with `uv pip uninstall medhub-dicom-viewer`, collection stops with 5 import errors (`test_audit_module_key`, `test_failure_audit_persistence`, `test_module_integration`, `test_size_bounds`, `test_studies_endpoint`); after `uv sync --frozen` the module suite passes (34 passed). Fails on `HEAD` 396e9de before the packaging change |
| TC-010.9 | SR-017 (AC 7) | `infra/smoke-test.sh`, section "DICOM module route" (system level, on a started stack: `bash infra/smoke-test.sh`; executed in TASK-239) | An unauthenticated `GET https://localhost/api/v1/modules/dicom-viewer/studies/<random uuid>` through the reverse proxy answers 401 (the router is mounted and the auth layer refuses the anonymous caller). The status is read with `curl -w '%{http_code}'`, not from Compose output (PRB-059) | `[PASS]` on 401. `[FAIL] ... module route not mounted (404)` on 404 (the image did not discover the module, PRB-048); `[FAIL] ... got HTTP '<code>' (expected 401)` on any other status. `bash -n infra/smoke-test.sh` passes in TASK-236 |

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
- 1.5 (2026-11-25) — Status `in_review`: TC-010.8 added (TASK-233, CR-008, PRB-048): the DICOM viewer module is installed as a uv workspace member and the module tests no longer insert it on `sys.path`; TC-010.2 note updated. Approval record cleared; QA/human re-approve.
- 1.5 (2026-11-25, QA) — Status `draft`: TASK-233 round 1 CHANGES REQUESTED; TC-010.8 claims the module suite cannot pass on a module that is not installed because the conftest has no `sys.path` mutation, but pytest's prepend import mode puts `backend/modules/dicom_viewer` on `sys.path` and the module tests import the source when the package is uninstalled (TASK-233 R1-1).
- 1.6 (2026-11-25) — Status `in_review`, TASK-233 round 2 (QA R1-1): TC-010.8 now relies on `--import-mode=importlib` so the module tests cannot import the module source from `sys.path`; the conftest-text test is replaced by an installed-distribution check; negative control re-recorded. Approval record cleared; QA/human re-approve.
- 1.6 (2026-11-25, QA) — Status `approved` on QA approval of TASK-233 round 2. The image half of TC-010.8 stays with TASK-236 (TASK-233 R1-2).
- 1.7 (2026-11-25) — Status `in_review`, TASK-236 (CR-008): TC-010.9 added (system level: the started stack answers 401, not 404, for an unauthenticated DICOM module route, SR-017 AC 7); the image half of TC-010.8 now points to TS-013 TC-013.15. Approval record cleared; QA/human re-approve.
- 1.7 (2026-11-25, QA) — Status `approved` on QA approval of TASK-236 round 1 (TC-010.9 logic checked in-process; the started-stack run is TASK-239). TASK-236 R1-3 (Levels and preconditions for the system-level case) carried to TASK-239.
