---
id: "PRB-040"
type: problem-report
title: "Database tests start PostgreSQL from a floating tag, not the shipped version"
status: resolved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-11-12"
criticality: minor
links: []
tags: ["soup", "verification", "configuration-management"]
---

# PRB-040 — Database tests use a floating PostgreSQL tag

## Observed

`backend/tests/db/conftest.py:14` and `backend/tests/db/test_migration.py:26` start the test
database with `PostgresContainer("postgres:16")`. After CR-001 (TASK-155) the shipped and CI
PostgreSQL is `postgres:16.15@sha256:9e2cf628…` (SOUP-020), so the real-database and migration
tests can run against a different patch release than the one deployed.

## Impact

- Verification evidence for the database (TR-002's real-database suite, migrations) is not tied to
  the SOUP-020 version, which weakens the claim that tests ran against the shipped SOUP (CR-001
  Assumption A-2, IEC 62304 §8.1.2).
- Not caught by the CR-001 pin check, which scans Compose, Dockerfiles and workflow files only.

## Investigation

Re-checked against the tree on 2026-11-12. The defect stands and now covers **nine** call sites,
not two. CR-004 added seven of them. Every one is `PostgresContainer("postgres:16")`:

- `backend/tests/db/conftest.py:14`, `backend/tests/db/test_migration.py:26`,
  `backend/tests/db/test_migration_0010_key_id.py:62`,
  `backend/tests/db/test_audit_append_only_privileges.py:40`;
- `backend/tests/audit/test_audit_client_address.py:49`,
  `backend/tests/audit/test_authz_decision_audit.py:45`,
  `backend/tests/audit/test_audit_no_secrets.py:134`,
  `backend/tests/audit/test_failure_audit_persistence.py:48`;
- `backend/tests/attachments/test_attachment_integrity_persistence.py:36`.

(`conftest.py` provides the fixture that the other `tests/db` tests share.)

- **Mechanism.** Each test names the image itself, with no shared definition, and `postgres:16`
  resolves to whichever 16.x the host's cache or the registry holds when the test runs. That can be
  older or newer than 16.15. The shipped and CI-service reference is
  `postgres:16.15@sha256:9e2cf628…` (`infra/docker-compose.yml:126`, `.github/workflows/ci.yml:51`,
  SOUP-020). `infra/check_image_pins.py` scans Compose, Dockerfiles and workflows only, so Python
  test code is outside its scope.
- No other SOUP component is started as a test container (no `RedisContainer` or generic
  container in the backend tests). The testcontainers reaper image is selected by the locked
  `testcontainers` version and is test tooling, not SOUP.

## Safety evaluation

No hazard is realized. PostgreSQL 16.x patch releases do not change the SQL behaviour the tests
exercise, and the shipped version is pinned. The weakness is in the verification evidence, and
since CR-004 it includes evidence for risk controls: the append-only grants of the audit log
(SR-023 AC 8, RISK-006) and the key-identifier migration (SR-022, RISK-011). That evidence is not
tied to the SOUP-020 version. Nothing indicates that the result would differ on 16.15, hence
`minor`, unchanged. No `release` record exists, so no notification is needed.

## Proposed resolution

Use the Compose/CI reference (tag and digest) for `PostgresContainer`, ideally from a single
constant, and consider extending the pin check to test fixtures. Needs a task and a CR.

## Resolution

Resolved by CR-005 in two tasks (verified in the working tree on branch `bug/build-hygiene`;
QA approved TASK-212 and, on 2026-11-12 in round 2, TASK-213; the PRB is `resolved` and becomes
`closed` once a release ships the change).

- **TASK-212 (commit `e984559`).** One definition, `backend/postgres_image.py`
  (`POSTGRES_IMAGE = (` with the `"postgres:16.15@sha256:9e2cf628…0a97"` literal on line 13 and `)`, equal to `infra/docker-compose.yml:126`
  and SOUP-020). All eleven `PostgresContainer(...)` call sites (the nine files listed under
  Investigation, counted per call by TASK-212) import it, so no test names a floating tag. The
  definition sits beside `conftest.py` rather than in `tests/` because the DICOM suite's own
  `tests` package shadows `backend/tests`. A started-container test
  (`backend/tests/db/test_postgres_image.py`) asserts the `pg_container` fixture has the SOUP-020
  digest.
- **TASK-213 (the next commit).** `infra/check_image_pins.py` (CI job `image-pins`) enforces it: the
  definition is read as text and must carry a digest and equal the Compose `postgres` image; every
  workflow `services.<name>.image` must equal the Compose image of the same repository; a
  `"<repo>:<tag>"` literal of a Compose image repository in `backend/**/*.py` is a finding (the
  definition's own literal apart); and every `PostgresContainer(` call must take `POSTGRES_IMAGE`
  as its image, so a later edit to a `PostgresContainer` call cannot bring the floating tag back
  (the way this PRB grew from two call sites to eleven). Fixtures: `TestImagesMatchDeployment` in
  `infra/tests/test_check_image_pins.py` (TS-013 TC-013.13).
- **Verification.** `python3 -m unittest discover -s infra/tests -v` (all pass);
  `python3 infra/check_image_pins.py` exits 0 on the repository; on a scratch copy, reverting the
  definition to `postgres:16`, dropping its digest, changing the CI `postgres` service image, adding
  `"postgres:16"` to a test file, a `PostgresContainer()` call and putting a file at
  `backend/tests/postgres_image.py` each exit 1 at that file and line (the scratch files are
  `git add`ed first, because the default mode reads `git ls-files`). Records: TS-013 1.6 (TC-013.13, TC-013.14 coverage note), ADD-024 1.3,
  ADR-0020 (amended 2026-11-12).

## Source

Found by QA while reviewing TASK-155 of CR-001 (2026-10-22); outside that task's scope.

## Version history

- 1.1 (2026-11-12) — `## Investigation` added for CR-005 (Specify stage): nine call sites in nine test files (CR-004 added seven), the mechanism, and the risk-control evidence now affected. Criticality unchanged.
- 1.2 (2026-11-12) — `## Resolution` written for CR-005 (TASK-212 `e984559`, TASK-213); status `open` until QA approves.
- 1.3 (2026-11-12) — QA approved TASK-213 (round 2; verification reproduced, see TASK-213 "QA review round 2"); `open → resolved`. Criticality unchanged. Residual: the check covers `PostgresContainer` call sites only (see TASK-213 findings, carried to TASK-216).
