---
id: TS-013
type: test-specification
title: Lifecycle record and traceability verification
status: in_review
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-13"
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
Levels: review (TC-013.1 to TC-013.4, TC-013.9), unit (TC-013.5, TC-013.6, TC-013.11, TC-013.13), integration
(TC-013.7, TC-013.8: automated CI checks of the dependency set the build resolves; TC-013.12: the tool
pins in the repository and on hosted CI, with a review of the SHA-to-tag record; TC-013.14: the
PostgreSQL container the real-database tests start carries the SOUP-020 digest).

## Preconditions and environment

Build: branch `bug/soup-pinning` (TC-013.11, TC-013.12, TC-013.13 and TC-013.14: branch `bug/build-hygiene`, CR-005; the TASK-216 local run of 2026-11-13 is on `f645979` plus the uncommitted TASK-216 changes; the hosted run is on the pushed head, recorded in TASK-216). TC-013.9 and the CR-001 end-to-end run (TASK-159, 2026-10-22) were
executed on commit `7ef8f93` with the TASK-159 record changes only (no source change). TC-013.9 and the
CR-003 end-to-end run (TASK-168, 2026-10-30) were executed on branch `bug/soup-upgrades` at commit
`d57ec72` with the TASK-168 record changes only (no source change). Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24.22.2) with `frontend/package-lock.json`.
Unit and service tests run with no external services (the repository itself). Tests marked *real DB* require a
PostgreSQL 16.15 container (the SOUP-020 reference) through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/); the pinned image
references (tag and digest) are those recorded in the SOUP records. TC-013.5, TC-013.6, TC-013.11 and TC-013.13 need only
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
| TC-013.10 | SR-028 (AC-7) | Manual, steps in TASK-176 Verification: on a Docker daemon with an empty image store (a disposable `docker:dind` pinned by digest, started with no volume of cached images; on an arm64 host the client sets `DOCKER_DEFAULT_PLATFORM=linux/amd64`), from the version-controlled sources of the branch: `docker compose -p <name> build` then `docker compose -p <name> up -d` | Every image is obtained from a public registry by its pinned digest (`chrislusf/seaweedfs:4.51@sha256:f7a49e3f…134b8` included) or built from the repository; no image is taken from a local cache; the stack reaches the state where `object-store` is healthy, `object-store-preflight` and `object-store-init` exited 0 and `backend` is started; the SeaweedFS image runs as `linux amd64` | Build and `up -d` exit 0; container states and `weed version` recorded in the TASK-176 "Verification results". CI evidence for the same on a hosted amd64 runner is TASK-179; the end-to-end run is TASK-182 |
| TC-013.11 | SR-028 (AC-8) | `infra/tests/test_check_image_pins.py` (`python3 -m unittest discover -s infra/tests -v`): `ToolReferences`, with fixtures under `infra/tests/fixtures/tools/` run through `check_image_pins.py --root` | Each unpinned tool form is reported with file and line: an action `uses:` by tag, by short SHA, by SHA without the `# v<tag>` comment, or with no ref; `python-version` / `node-version` without a patch version, as an expression or a list, or different from `FROM python:` / `FROM node:` of the base image; a `python-version-file` / `node-version-file` key; an `astral-sh/setup-uv` action; a `uv` install (`pip` or `pipx`, workflow or Dockerfile, also `\`-continued over several lines or in the Dockerfile exec form `RUN ["pip", "install", "uv"]`) without `==X.Y.Z`; a `uv==` version that differs from the one in `backend/Dockerfile`; an `npx` package without an exact version (also inside a `run: \|` block, after a quote or after a `VAR=value` prefix). The image rule reports a `uses: docker://<image>` without `@sha256:<64 hex>` (also with a `$`). A `uses: ./local`, a `uses: docker://` with a digest, a pinned action, runtime, `uv==` and `npx pkg@X.Y.Z`, and the package `uvicorn`, pass. The check passes on the repository | One passing and one failing fixture per form; exit 1 with the right path, line, message and reference on each failing fixture, exit 0 on the passing ones and on the repository; `--root` with a PATH exits 2, and `--root` on a missing directory or one without workflows or Dockerfiles exits 2. Negative control (CR-005): reverting in a scratch copy of the repository one action to `@v4`, one `python-version` to `"3.12"`, one `node-version` to `"24"`, one `uses:` to `docker://alpine:3.20`, one `python-version` to `python-version-file`, one uv install continued over two lines or in exec form, `astral-sh/setup-uv`, a quoted `npx`, one uv install to `pip install uv` (workflow and Dockerfile), one uv version to a different `uv==`, and the linter to `@redocly/cli` each makes `python3 infra/check_image_pins.py` exit 1 at that file and line |
| TC-013.12 | SR-028 (AC-8) | Integration and review: `python3 infra/check_image_pins.py` on the repository (CI job `image-pins`); the SHA-to-tag record of TASK-209 (`git ls-remote --tags` and `gh api repos/actions/<name>/git/ref/tags/<tag>` per action); `cd backend && uvx --from uv==0.13.7 uv lock --check`; the logs of a hosted run of the branch | Exit 0 and no output on the repository. Every `uses:` SHA is the commit of the release tag in its comment. `uv lock --check` passes with the pinned uv. The hosted logs show Python 3.12.15 (the shipped runtime), Node.js 24.22.2 and uv 0.13.7 in every job that installs them | All four hold. The hosted-log part needs a pushed run and is recorded in TASK-216 (Checkpoint C); until then the case is partial |
| TC-013.13 | SR-028 (AC-9) | `infra/tests/test_check_image_pins.py` (`python3 -m unittest discover -s infra/tests -v`): `TestImagesMatchDeployment`, on fixture trees run through `check_image_pins.py --root` (definition at `backend/postgres_image.py`); and `python3 infra/check_image_pins.py` on the repository | Rule 1: the one-line and the parenthesised definition equal to the Compose `postgres` image pass; implicit and `+` concatenation, an f-string, a name, a missing `)`, an annotation, a trailing comment, a missing file or assignment are reported at the expected line; a later binding (indented under an `if`, annotated, augmented, `global`, tuple unpacking, `:=`, `for`, `with ... as`, `import ... as`, `;`-joined, `globals()` / `locals()` / `vars()`) is reported as a second assignment, a definition file that does not parse is reported, and `OTHER = "postgres:16"` beside the pinned literal is reported as a second image literal, while a `==` comparison passes; a differing tag, a missing digest and a differing digest are reported at the literal's line. Rule 2: a workflow service image that differs from the Compose image of the same repository, or has none, is reported, and so is a service written as an inline mapping (`postgres: {image: …}`, in the workflow and in Compose). Rule 3: a `"postgres:16"` literal in `backend/tests/db/` or `backend/modules/dicom_viewer/tests/`, `"docker.io/library/postgres:16"`, `"library/postgres:16"`, a definition file at the old path `backend/tests/postgres_image.py`, and the host:port or log strings `"postgres:5432"`, `"redis:6379"`, `"redis:connected"` (false positives that fail closed) are reported. Rule 4: `from testcontainers.postgres import PostgresContainer as PC`, `POSTGRES_IMAGE` assigned, unpacked, imported `as` or stored as an attribute in a test file, `PostgresContainer()`, `PostgresContainer("postgres")`, `PostgresContainer(IMAGE)`, `PostgresContainer(image=IMAGE)`, a first argument other than `POSTGRES_IMAGE` and a multi-line call are reported at the call line, while `PostgresContainer(POSTGRES_IMAGE)`, `image=POSTGRES_IMAGE` and multi-line calls with either pass; `"redis://localhost:6379/0"`, a URL with `@postgres:5432`, and files under `.venv/` or outside `backend/` pass. The four TASK-211 LOW forms: a stray trailing `\` before a YAML item, a comment line inside a Dockerfile continuation, and `--root ""` | Exit 1 with the right path, line, message and reference on each failing case, 0 on the passing ones and on the repository, 2 for `--root ""`. Negative control (CR-005, scratch copy of the repository as a throwaway git repository): setting `POSTGRES_IMAGE` to `postgres:16`, dropping its digest, changing the CI `postgres` service image, adding `"postgres:16"` to a test file, a file at `backend/tests/postgres_image.py`, a concatenated definition, a missing definition, an indented second `POSTGRES_IMAGE` assignment, `OTHER = "postgres:16"` in the definition file, `PostgresContainer()`, `PostgresContainer("postgres")`, `"docker.io/library/postgres:16"` and an inline-mapping CI service each make `python3 infra/check_image_pins.py` exit 1 at that file and line |
| TC-013.14 | SR-028 (AC-9) | Integration: `backend/tests/db/test_postgres_image.py` (`cd backend && uv run pytest tests/db/test_postgres_image.py`, needs a Docker daemon) and, for the other test call sites, `cd backend && grep -rnE '"postgres:' . --include='*.py' \| grep -v '/.venv/'`; the real-database and migration tests (`tests/db`, `tests/audit`, `tests/attachments`, `modules/dicom_viewer/tests`) run through `backend/postgres_image.py`; `docker inspect` of a started test container | The definition `POSTGRES_IMAGE` is `postgres:16.15@sha256:9e2cf628…0a97` (SOUP-020, equal to the Compose `postgres` image); a container started by the `pg_container` fixture has the SOUP-020 digest in its image `RepoDigests`; the grep finds only `backend/postgres_image.py`; every test that starts a database container passes against it | All hold: the two assertions pass; the grep finds the one definition; `docker inspect` of a started container gives `Config.Image` equal to the reference and `RepoDigests` `postgres@sha256:9e2cf628…0a97` (PostgreSQL 16.15). Equality of the definition with the Compose file is checked by TC-013.13 (TASK-213) |

Coverage of SR-028 AC-9: the real-database and migration tests run against the shipped PostgreSQL
image (SOUP-020) through one definition, `backend/postgres_image.py`; this is covered by TC-013.14
(and, for equality with the Compose file, TC-013.13). The started-container test of TC-013.14
(`tests/db/test_postgres_image.py`) covers the `pg_container` fixture only; the other ten call sites
are held to the definition by rules 3 and 4 of the pin check (TC-013.13: no image literal, and
`POSTGRES_IMAGE` as the image of every `PostgresContainer(` call), and the definition to the Compose
file by rule 1.

Coverage of SR-028 AC-5, AC-6 and AC-8: AC-8 (build and CI tools by exact version, enforced by the
same check) is covered by TC-013.11 (the rules) and TC-013.12 (the repository, the tags and the
hosted run).

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

- `infra/check_image_pins.py` tool rules (class B unit, §5.5.3; SR-028 AC-8, ADR-0020): over the
  tracked workflows and Dockerfiles (or those under `--root`), exits 1 and prints
  `<file>:<line>: <message>: <reference>` for a workflow `uses:` of a repository action that is not
  `owner/repo[/path]@<40 lowercase hex>` followed by a `# v<tag>` comment (`./` is exempt; a
  `docker://` reference goes to the image rule and is reported there without `@sha256:<64 hex>`),
  an `astral-sh/setup-uv` action, a `python-version` / `node-version` that is not `X.Y.Z` or
  differs from the tag version of `FROM python:` in `backend/Dockerfile` / `FROM node:` in
  `frontend/Dockerfile`, a `python-version-file` / `node-version-file` key, a `uv` `pip` / `pipx`
  install (`\`-continued lines are joined, the Dockerfile exec form is read) that is not
  `uv==X.Y.Z` or whose version differs from the one in `backend/Dockerfile`, and an `npx` package
  that is not `name@X.Y.Z` (also after a quote or a `VAR=value` prefix). A form of these kinds
  that it cannot parse is a finding (it fails closed), for example a folded `uses: >-` (reported
  with the reference `>-`). A stray trailing `\` does not join a workflow line into
  the next YAML key, list item or blank line, and a Dockerfile continuation skips comment lines.
  Matching is line-based, so these are not seen: an `npx` or a `pip
  install uv` reached through a script file, a `uses:` or `run:` assembled by a YAML anchor or
  template expression, and composite actions under `.github/actions/`; for the test images, a job
  `container:` or `uses: docker://` image (checked by the image rule only: a digest is present, not
  equality with Compose), a container class other than `PostgresContainer` (the one that occurs is
  the `DockerContainer` Redis call in `backend/tests/auth/test_session_cap_concurrency.py`, which
  reads the Compose image at run time), a `PostgresContainer` reached under another name without
  `import ... as` (`PC = PostgresContainer`, `getattr`, `import *`), a `POSTGRES_IMAGE` rebound
  through `setattr(...)`, `sys.modules` or `vars()` in a file other than the definition file (inside it,
  a `globals()`, `locals()`, `vars()` or `setattr()` call is a finding), and an import of
  `POSTGRES_IMAGE` from a module other than `backend/postgres_image.py`; none of the others occurs
  in the repository.
- `infra/check_image_pins.py` test image rules (class B unit, §5.5.3; SR-028 AC-9, ADR-0020): over
  the repository (or `--root`), exits 1 and prints `<file>:<line>: <message>: <reference>` when
  `backend/postgres_image.py` is missing, has no or a second `POSTGRES_IMAGE` binding (read with `ast`: at any indentation, plain, annotated, augmented, tuple unpacking, `:=`, `for`, `with ... as`, `import ... as`, `global`, `;`-joined, or a `globals()` / `locals()` / `vars()` call), does not parse, holds it
  in a form other than a one-line or a parenthesised single plain string literal, or holds a value
  without a digest or different from the `image:` of the Compose `postgres` service; when a workflow
  `services.<name>.image` differs from the Compose image of the same repository or has no
  counterpart or is written as an inline mapping; when a `"[registry/namespace/]<repo>:<tag>"`
  literal of a Compose image repository appears in `backend/**/*.py` (in `backend/postgres_image.py`
  only the one `POSTGRES_IMAGE` literal is allowed; the old path `backend/tests/postgres_image.py`
  is not exempt); when a `PostgresContainer(` call does not take `POSTGRES_IMAGE` as its image; when `PostgresContainer` is imported under an alias; or when `POSTGRES_IMAGE` is bound in a `backend/**/*.py` file other than the definition.
  `redis://localhost:6379/0` and `@postgres:5432` in a URL pass; `"postgres:5432"` and
  `"redis:connected"` do not (false positives that fail closed). Exits 2 for `--root ""`.

## Notes

TC-013.1 to TC-013.4 and TC-013.9 verify the process requirement by review, which IEC 62304 §5.5 accepts as unit verification evidence alongside tests. TC-013.5, TC-013.6, TC-013.11 and TC-013.13 are automated unit verification of the pin-check script. TC-013.7 and TC-013.8 are automated CI checks of the dependency set (job `backend-quality` and the Docker Build job).

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
- 1.4 (2026-10-29) — CR-003 (TASK-162). Version 1.3 was approved, so this change bumps the version and
  clears the approval record. The environment line names Node 24 LTS (build stage
  `node:24.22.2-trixie-slim`, CI `node-version` 24) instead of Node 20. The test cases do not change.
  TASK-168 (2026-10-30) adds to the environment the branch and commit of the TC-013.9 and CR-003
  end-to-end run. The test cases still do not change.
- 1.5 (2026-10-30) — CR-002 (TASK-176). Version 1.4 was approved, so this change bumps the version and
  clears the approval record. Added TC-013.10 for SR-028 AC-7 (pull and build on a daemon with no
  cached images, amd64). Existing test cases unchanged (TC-013.9 reads the object-store pin from
  SOUP-036 once the record is approved).
- 1.6 (2026-11-12) — CR-005 (TASK-211). Version 1.5 was approved, so this change bumps the version,
  sets `in_review` and clears nothing else (the record carried no approval fields). Added TC-013.11
  (unit: the tool rules of the pin check, with the negative control) and TC-013.12 (integration and
  review: the tool pins in the repository and on hosted CI) for SR-028 AC-8, the AC-8 coverage note
  and the tool-rule acceptance criterion; environment names branch `bug/build-hygiene`. Existing test
  cases unchanged. Later CR-005 tasks (TASK-212, TASK-213) add their cases to this version.
  TASK-212 added TC-013.14 (integration: test containers start from the SOUP-020 reference, SR-028 AC-9)
  to the scope, environment, coverage note and test cases; version unchanged.
  TASK-213 added TC-013.13 (unit: the test image rules of the pin check and the negative control, SR-028
  AC-9), the TC-013.14 coverage note, the test image acceptance criterion and the shared "not seen"
  list of the tool rules; version unchanged. QA round 1 (TASK-213): TC-013.13 extended with the
  later-assignment forms, rule 4 (`PostgresContainer` takes `POSTGRES_IMAGE`), registry-prefixed
  literals, the host:port false positive, inline-mapping services and the extended "not seen" list.
  TASK-216 (TASK-213 QA round 2, LOW 1-3): TC-013.13 extended with the `ast`-read rebinding forms in the
  definition file, the aliased `PostgresContainer` import and the `POSTGRES_IMAGE` binding outside the
  definition; the shared "not seen" list names the `DockerContainer` Redis call. Version unchanged.
  TASK-216 (QA L-1): TC-013.13 also covers `def` / `async def` / `class` of the name, `match` captures,
  a bare `import` / `from x import POSTGRES_IMAGE` and `setattr()` in the definition file, and a function
  parameter named `POSTGRES_IMAGE` in a test file (174 infra unit tests); the shared "not seen" list
  says `setattr` is seen inside the definition file only.
  TASK-216 (2026-11-13): environment names the commit of the local run and CI `node-version` 24.22.2; version unchanged.
