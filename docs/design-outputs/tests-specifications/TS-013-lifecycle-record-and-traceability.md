---
id: TS-013
type: test-specification
title: Lifecycle record and traceability verification
status: in_review
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-29"
links:
  - target: SR-028
    relation: verifies
tags:
  - level:review
  - level:unit
  - level:integration
  - class:B
---

# TS-013 — Lifecycle record and traceability verification

## Scope

Software requirements covered: SR-028.
Software items under test: the design record set (review), and SI-DEVINFRA unit
`U-INF-CIPipeline` (ADD-024), specifically `infra/check_image_pins.py` (unit verification, §5.5).
Levels: review (TC-013.1 to TC-013.4, TC-013.9), unit (TC-013.5, TC-013.6), integration (TC-013.7,
TC-013.8: automated CI checks of the dependency set the build resolves).

## Preconditions and environment

Build: branch `bug/soup-pinning`. TC-013.9 and the CR-001 end-to-end run (TASK-159, 2026-10-22) were
executed on commit `7ef8f93` with the TASK-159 record changes only (no source change). Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (the repository itself). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/); the pinned image
references (tag and digest) are those recorded in the SOUP records. TC-013.5 and TC-013.6 need only
Python 3 (standard library) and `git`; TC-013.7 needs `uv`; TC-013.8 needs a Docker daemon; TC-013.9 needs read access to
`backend/uv.lock`, `frontend/package-lock.json`, the Compose file and the Dockerfiles, and
`docs/medtrace.yml` for `soup_anomaly_max_age_days`.

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-013.1 | SR-028 | `medical-records:traceability-check` over `docs/` | Zero schema, status and required-link errors | Errors = 0 in the committed gap report |
| TC-013.2 | SR-028 | `backend/tests/test_toolchain.py`, `frontend/tests/toolchain.test.ts` | The declared toolchain matches what the project actually runs | Versions asserted |
| TC-013.3 | SR-028 | `backend/tests/test_export_openapi.py` | The committed OpenAPI export matches the application | Export diff empty |
| TC-013.4 | SR-028 | `git log` on `docs/` plus the record `version` fields | Every record change is version-controlled and versioned | Reviewed at release |
| TC-013.5 | SR-028 (AC-5) | `python3 infra/check_image_pins.py` on the repository (CI job `image-pins`) | Every Compose `image:`, Dockerfile `FROM` and workflow `services.*.image` reference carries `@sha256:<64 hex>` | Exit 0, no output. Only the digest is enforced; that the tag names a full release (SR-028 AC-5 / CR-001 AC-1) remains an inspection. A digest-only reference (`repo@sha256:…`) passes |
| TC-013.6 | SR-028 (AC-5) | `infra/tests/test_check_image_pins.py` (`python3 -m unittest discover -s infra/tests -v`): `UnpinnedReferences`, `AcceptedReferences`, `UsageErrors` | Each unpinned form (Compose, Dockerfile with `--platform` and `AS`, workflow service and container image, `container:` shorthand, short, uppercase, over-long or non-sha256 digest, variable reference) is reported with file and line; `FROM` of an earlier stage and `FROM scratch` are not; an empty `image:` value and a workflow `container: <ref>` shorthand are also reported; the pinned fixtures pass | Exit 1 on each unpinned fixture, 0 on the pinned and stage fixtures, 2 on a missing file; all 11 unit tests pass |
| TC-013.7 | SR-028 (AC-5) | `cd backend && uv lock --check` (CI job `backend-quality`, step "Check the lock file is current") | Every Python runtime dependency, `boto3` included, resolves to one locked version: `uv.lock` is in sync with `[project] dependencies` | Exit 0; `boto3` is declared under `[project] dependencies` (not an extra or a dependency group) and `uv.lock` holds exactly one `boto3` entry. CI job `backend-quality`, step "Check the lock file is current", runs it on every pull request, before `uv sync --frozen` (which does not itself compare the lock with the manifest) |
| TC-013.8 | SR-028 (AC-5) | CI job Docker Build (`.github/workflows/ci.yml`), step "Check production dependency set": `docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"` | The production image, built with `uv sync --frozen --no-dev`, contains every runtime SDK the code imports and does not contain `fakeredis`, which only the tests use and which lives in the `dev` dependency group (PRB-033) | Exit 0 in the built backend image: `import boto3` succeeds and `fakeredis` is absent (exit 1 if `fakeredis` is present; a missing `boto3` raises and also fails the step). Locally, `uv sync --frozen --no-dev` into a scratch environment gives the same result |
| TC-013.9 | SR-028 (AC-6) | Review, before QA approval and at release: for each `soup` record whose status is not `obsolete`, compare `soup_version` with the version the build resolves (`backend/uv.lock` for Python packages, `frontend/package-lock.json` top-level entries for npm packages, the release tag of the pinned image reference in `infra/docker-compose.yml`, `backend/Dockerfile` and `frontend/Dockerfile` for images and the Python runtime); read the record's `anomaly_review` date and its "Anomaly list review" section; then run `medical-records:traceability-check` over `docs/` | Every non-obsolete `soup_version` equals the version the build resolves (one version per item; for images, the identical tag at every reference). Every non-obsolete record has an `anomaly_review` date no older than `soup_anomaly_max_age_days` (`docs/medtrace.yml`, 365) on the day of the check, and its "Anomaly list review" section cites each source reviewed by name and URL for that exact version and does not read "Not yet performed" | No version mismatch; no record without a dated, sourced review; no `soup_anomaly_review_stale` finding for a non-obsolete record in the committed gap report. At release, the age is measured to the release date |

Coverage of SR-028 AC-5 and AC-6: AC-5 (one exact version per component; images by tag and
digest; CI fails on a reference without a digest) is covered by TC-013.5 and TC-013.6 (digest and
CI check), TC-013.7 (packages resolved by the committed lock) and TC-013.8 (the production image
holds the runtime SDKs it imports and no test-only package). That the tag names a full release
stays an inspection (TC-013.5 pass criteria). AC-6 (version matches the build; dated, sourced
anomaly review within the age limit) is covered by TC-013.9.

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

TC-013.1 to TC-013.4 and TC-013.9 verify the process requirement by review, which IEC 62304 §5.5 accepts as unit verification evidence alongside tests. TC-013.5 and TC-013.6 are automated unit verification of the pin-check script. TC-013.7 and TC-013.8 are automated CI checks of the dependency set (job `backend-quality` and the Docker Build job).

## Version history

- 1.1 (2026-10-21) — Restored from `obsolete` together with SR-028. Content unchanged.
- 1.2 (2026-10-22) — CR-001: test cases TC-013.5 and TC-013.6 for SR-028 AC-5 (image pin check), `U-INF-CIPipeline` as a unit under test with its acceptance criterion; environment
  updated to branch `bug/soup-pinning`. TASK-157, TASK-158 and TASK-159 extend this entry with their cases.
  TASK-157 adds TC-013.7 (the lock resolves every runtime dependency to one version, `boto3`
  declared) and TC-013.8 (the production image imports `boto3`), for SR-028 AC-5; environment of
  TC-013.8: Docker daemon. TASK-158 extends TC-013.8 with the absence of `fakeredis` from the
  image (PRB-033, SR-028 AC-5) and adds the CI step "Check the lock file is current"
  (`uv lock --check`, job `backend-quality`) as the procedure of TC-013.7, so the lock check runs
  on every pull request instead of by hand (CR-001 Verification approach).
- 1.3 (2026-10-22) — CR-001 (TASK-159). Version 1.2 was approved after TASK-158, so this change
  bumps the version and clears the approval record instead of extending the 1.2 entry. Added
  TC-013.9 for SR-028 AC-6 (each non-obsolete `soup_version` matches the build, with a dated,
  sourced anomaly review within `soup_anomaly_max_age_days`) and the AC-5/AC-6 coverage note.
  TC-013.7 moved from the review level to the integration level with TC-013.8: since TASK-158 it is
  an automated CI step, not a review (carried LOW finding from TASK-158's QA); `level:integration`
  tag added for TC-013.7/8. Environment states the commit tested.
