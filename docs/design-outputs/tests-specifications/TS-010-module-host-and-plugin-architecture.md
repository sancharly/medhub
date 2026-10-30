---
id: TS-010
type: test-specification
title: Module host and plugin architecture verification
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-30"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-30"
approved_digest: 300bd530bc71765eb7caee10a0c6a1fcbb917bff40001a4aaa36e0577bf13bc8
approval_note: self-approved
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

## Acceptance criteria (class B unit level, §5.5.3)

- Interfaces: the module contract is the only import surface.
- Fault handling: a module that raises on import does not prevent the host from starting.

## Notes

The boundary test denies only two import substrings (PRB-030), so TC-010.3 under-verifies the isolation claim.
