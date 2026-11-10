---
id: TS-010
type: test-specification
title: Module host and plugin architecture verification
status: approved
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-02"
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
| TC-010.3 | SR-016 | `backend/tests/modules/test_module_boundary.py` | A module reaches PHI only through `PlatformServices` | Forbidden imports rejected |
| TC-010.4 | SR-016, SR-017 | `backend/modules/dicom_viewer/tests/test_studies_endpoint.py` | The DICOM endpoint serves bytes only to an authorized caller | Unauthorized request denied |
| TC-010.5 | SR-016 (AC 1) | `backend/tests/modules/test_discovery.py::TestModuleVersionShape`; the bundled module: `backend/modules/dicom_viewer/tests/test_audit_module_key.py::test_real_manifest_passes_discovery` | A manifest version follows the module contract's version rule (SR-016 AC 1): a semver.org version, ASCII only, nothing before or after it | `1.2.3x`, `1.2.3 `, `1.2.3\n`, `1.2.3-evil!`, `1.2.3.4`, `01.2.3`, `v1.2.3`, `1.0.0-01`, `1.0.0-a..b`, `1.2.3` followed by a non-ASCII digit, empty and 100 000-character inputs are rejected (23 cases); `1.2.3`, `0.1.0-rc.1`, `1.0.0+build.5`, `1.0.0--`, `1.0.0+001` are accepted (9 cases); a 1 000 000-character input is rejected in under 2 s |

## Acceptance criteria (class B unit level, §5.5.3)

- Interfaces: the module contract is the only import surface.
- Fault handling: a module that raises on import does not prevent the host from starting.

## Notes

The boundary test denies only two import substrings (PRB-030), so TC-010.3 under-verifies the isolation claim.

- 1.2 (2026-11-02) — Status `in_review`: TC-010.5 added (TASK-200, PRB-028): the module version is fully anchored. Approval record cleared; QA/human re-approve.
- 1.2 (2026-11-02, round 2) — TC-010.5 follows QA round 1: ASCII-only, strict pre-release and build identifiers, rule worded as the module contract's version rule.
- 1.2 (2026-11-02, QA) — Status `approved` on QA approval of TASK-200 round 2.
