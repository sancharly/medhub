---
id: "PRB-054"
type: problem-report
title: "The test-data seeder ships in the backend image and creates accounts with published weak passwords"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["security", "backend", "tooling"]
---

# PRB-054 — The test-data seeder ships in the backend image and creates accounts with published weak passwords

## Observed

While verifying CR-002 TASK-177 on 2026-10-30, the software developer found that
`backend/scripts/setup_test_data.py` hard-codes the group name, user emails and passwords. QA
confirmed that the script is present in the running backend container.

## Impact

Anyone with a shell in a deployed backend container can create active accounts whose passwords
are published in the repository, outside the activation flow and without an audit event.

## Investigation

- `backend/Dockerfile:15` copies `scripts/` into the runtime image, so the seeder ships with the
  application. This contradicts PRB-049's statement that the script "is not part of the shipped
  application".
- The script creates active doctor and patient accounts with the passwords `doctor123` and
  `patient123` (`backend/scripts/setup_test_data.py:214`, `:218`, `:220`, printed at `:230`-`:232`;
  also listed in `docs/reports/SMOKE-RESULTS.md:7`). Both are shorter than the policy minimum
  (`MIN_LENGTH = 12`, `backend/app/auth/password.py:28`).
- It skips the activation flow and records no audit event.
- It adds the first SYSADMIN to the group "Test Clinic" (`:210`-`:211`).
- Nothing stops it from running when `ENVIRONMENT=production`.

## Safety evaluation

Running the script needs a shell in the backend container, which already holds the database
credentials and keys, so it gives no new access path. A seeded doctor still needs patient consent
to see clinical data. It does not affect data integrity, a safety-related function or a clinical
decision. No released version exists, so no notification is needed. Hence `minor`.

## Proposed resolution

Leave `scripts/` out of the runtime image; make the seeder refuse to run when
`ENVIRONMENT=production`; generate policy-compliant passwords (or take them, the emails and the
group name as arguments). Correct PRB-049's statement. Needs a task and a CR; outside CR-002's scope.

## Source

Software developer and QA, CR-002 TASK-177 (2026-10-30).
