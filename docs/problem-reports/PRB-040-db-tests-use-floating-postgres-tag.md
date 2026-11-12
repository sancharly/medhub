---
id: "PRB-040"
type: problem-report
title: "Database tests start PostgreSQL from a floating tag, not the shipped version"
status: open
version: "1.1"
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

## Source

Found by QA while reviewing TASK-155 of CR-001 (2026-10-22); outside that task's scope.

## Version history

- 1.1 (2026-11-12) — `## Investigation` added for CR-005 (Specify stage): nine call sites in nine test files (CR-004 added seven), the mechanism, and the risk-control evidence now affected. Criticality unchanged.
