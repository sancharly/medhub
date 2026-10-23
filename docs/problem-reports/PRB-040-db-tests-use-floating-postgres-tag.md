---
id: "PRB-040"
type: problem-report
title: "Database tests start PostgreSQL from a floating tag, not the shipped version"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
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

## Safety evaluation

No hazard is realized: PostgreSQL 16.x patch releases do not change the SQL behaviour the tests
exercise, and the shipped version is pinned. The gap is in verification evidence, hence `minor`.

## Proposed resolution

Use the Compose/CI reference (tag and digest) for `PostgresContainer`, ideally from a single
constant, and consider extending the pin check to test fixtures. Needs a task and a CR.

## Source

Found by QA while reviewing TASK-155 of CR-001 (2026-10-22); outside that task's scope.
