---
id: TS-013
type: test-specification
title: Lifecycle record and traceability verification
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-22"
links:
  - target: SR-028
    relation: verifies
tags:
  - level:review
  - level:unit
  - class:B
---

# TS-013 — Lifecycle record and traceability verification

## Scope

Software requirements covered: SR-028.
Software items under test: the design record set (review), and SI-DEVINFRA unit
`U-INF-CIPipeline` (ADD-024), specifically `infra/check_image_pins.py` (unit verification, §5.5).
Levels: review (TC-013.1 to TC-013.4), unit (TC-013.5, TC-013.6).

## Preconditions and environment

Build: branch `bug/soup-pinning`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (the repository itself). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/); the pinned image
references (tag and digest) are those recorded in the SOUP records. TC-013.5 and TC-013.6 need only
Python 3 (standard library) and `git`.

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-013.1 | SR-028 | `medical-records:traceability-check` over `docs/` | Zero schema, status and required-link errors | Errors = 0 in the committed gap report |
| TC-013.2 | SR-028 | `backend/tests/test_toolchain.py`, `frontend/tests/toolchain.test.ts` | The declared toolchain matches what the project actually runs | Versions asserted |
| TC-013.3 | SR-028 | `backend/tests/test_export_openapi.py` | The committed OpenAPI export matches the application | Export diff empty |
| TC-013.4 | SR-028 | `git log` on `docs/` plus the record `version` fields | Every record change is version-controlled and versioned | Reviewed at release |
| TC-013.5 | SR-028 (AC-5) | `python3 infra/check_image_pins.py` on the repository (CI job `image-pins`) | Every Compose `image:`, Dockerfile `FROM` and workflow `services.*.image` reference carries `@sha256:<64 hex>` | Exit 0, no output. Only the digest is enforced; that the tag names a full release (SR-028 AC-5 / CR-001 AC-1) remains an inspection. A digest-only reference (`repo@sha256:…`) passes |
| TC-013.6 | SR-028 (AC-5) | `infra/tests/test_check_image_pins.py` (`python3 -m unittest discover -s infra/tests -v`): `UnpinnedReferences`, `AcceptedReferences`, `UsageErrors` | Each unpinned form (Compose, Dockerfile with `--platform` and `AS`, workflow service and container image, `container:` shorthand, short, uppercase, over-long or non-sha256 digest, variable reference) is reported with file and line; `FROM` of an earlier stage and `FROM scratch` are not; an empty `image:` value and a workflow `container: <ref>` shorthand are also reported; the pinned fixtures pass | Exit 1 on each unpinned fixture, 0 on the pinned and stage fixtures, 2 on a missing file; all 11 unit tests pass |

## Acceptance criteria (class B unit level, §5.5.3)

- The check runs before QA approval and before release, per PLAN-001.
- Warnings are triaged, not silenced.
- `infra/check_image_pins.py` (class B unit, §5.5.3): exits 0 only when every Compose `image:`,
  Dockerfile `FROM` and workflow `services.*.image`, `container.image` and `container: <ref>`
  reference ends in `@sha256:<64 lowercase hex>`; exits 1 and prints `<file>:<line>` for every
  other reference, including an empty `image:` value and a reference containing a variable (it
  fails closed); skips `FROM scratch` and `FROM` of an earlier stage; exits 2 on an unreadable file.
  Each form has a negative or positive fixture in `infra/tests/fixtures/`. Matching is line-based:
  an `image` key inside a YAML flow mapping (`svc: {image: …}`) or written as a quoted key
  (`"image": …`) is not detected; neither form occurs in the repository.

## Notes

TC-013.1 to TC-013.4 verify the process requirement by review, which IEC 62304 §5.5 accepts as unit verification evidence alongside tests. TC-013.5 and TC-013.6 are automated unit verification of the pin-check script.

## Version history

- 1.1 (2026-10-21) — Restored from `obsolete` together with SR-028. Content unchanged.
- 1.2 (2026-10-22) — CR-001: test cases TC-013.5 and TC-013.6 for SR-028 AC-5 (image pin check), `U-INF-CIPipeline` as a unit under test with its acceptance criterion; environment
  updated to branch `bug/soup-pinning`. TASK-157, TASK-158 and TASK-159 extend this entry with their cases.
