---
id: "TASK-138"
type: task
title: "PII scrubbing for worker and notification logs"
status: draft
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-10-31"
links:
  - target: "RISK-008"
    relation: mitigates
  - target: "SR-043"
    relation: implements
  - target: "SR-024"
    relation: implements
  - target: "NFR-004"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "PRB-011"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-017"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
  - target: "TASK-031"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium", "control:protective", "control:design", "cr:CR-004"]
---

# TASK-138 — PII scrubbing for worker and notification logs

- **Software item / unit:** SI-WORKER logging (ADD-017), SI-API logging (ADD-005),
  `backend/app/core/logging.py`.
- **Resolves (through CR-004):** PRB-011. Source: `docs/reports/CODE-REVIEW-2026-07.md` finding E.
- **Depends on:** none. Independent of every other CR-004 task; can run in parallel.
- **Branch:** `fix/review-2026-07-security` (CR-004).
- **Size:** M (4 source files: `core/logging.py`, `workers/email_tasks.py`, `workers/celery_app.py`,
  `main.py`; 2 test files; TS-017)
- **Needs:** nothing beyond the unit-test environment.

## Objective

SR-043 AC 1 to AC 3: no email address, name, date of birth or clinical free text in the
operational log stream; one redaction filter on every application logger; tests that fail if an
address reaches the log. The PRB-011 Investigation found two `extra` fields carrying addresses
(`backend/app/workers/email_tasks.py:117-123,168-171`), formatters that drop `extra` today, and a
worker with no logging configuration at all.

## Implementation detail

1. **At the source (AC 1):** `email_tasks.py:117-123` logs `account_id` only;
   `email_tasks.py:168-171` logs the anonymized dataset id (pass it to the task, or log no
   recipient at all). Sweep `backend/app` for other `logger.*` calls with personal data in the
   message or `extra` (`grep -rn "logger\." backend/app | grep -i "email\|name\|birth\|description"`).
2. **Redaction filter (AC 2):** `core/logging.py` gains `RedactionFilter(logging.Filter)` that
   replaces email-shaped values in `record.msg`, `record.args` and every non-standard attribute
   of the `LogRecord` (any field name, nested `dict`/`list` values included) with
   `[REDACTED-EMAIL]`. The JSON formatter also serializes `extra` fields (after the filter), so
   identifiers in `extra` are visible to operators.
3. **Every handler (AC 2):** `configure_logging()` attaches the filter to the root handler. The
   worker and the scheduler call it through Celery's `setup_logging` signal
   (`backend/app/workers/celery_app.py`), so Celery's own loggers (task retry and failure messages)
   go through the same handler and filter.

## Tests (write first)

- `backend/tests/test_log_redaction.py`:
  - a record with `extra={"anything_at_all": "a.person@example.org"}` → emitted JSON contains no
    `a.person@example.org` (AC 3, arbitrary field name);
  - the address in the message, in `%s` args and in a nested dict → redacted;
  - a UUID and an account id survive unchanged.
- `backend/tests/workers/test_email_tasks_logging.py` (captures the root handler's stream after
  `configure_logging()`):
  - `send_erasure_code_email` and `send_activation_email` success path with a known address →
    the captured output does not contain it;
  - failure path: `_send_smtp` raises `smtplib.SMTPRecipientsRefused({addr: (550, b"no")})`, the
    task's retry or failure logging runs → the output does not contain the address;
  - the Celery `setup_logging` handler is installed (the worker's root handler has the filter).

## Acceptance criteria

- [ ] SR-043 AC 1: no log call under `backend/app` emits personal data; ids are used
      (`backend/tests/workers/test_email_tasks_logging.py`).
- [ ] SR-043 AC 2: the filter is on every handler of the API, worker and scheduler, any field name
      (`backend/tests/test_log_redaction.py`).
- [ ] SR-043 AC 3: success- and failure-path tests with a known recipient address pass, and fail
      with the filter removed (negative control).

## Verification

```sh
cd backend && uv run pytest tests/test_log_redaction.py tests/workers tests/test_logging.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

Negative controls: remove the filter (failure-path test fails); restore the `extra` email
(success-path test fails). Record both in the handoff.

## Records

- **TS-017** (new, `verifies` SR-043): TC-017.1 (no personal data at the source), TC-017.2
  (filter on every handler, any field), TC-017.3 (worker success and failure paths).
- **SOUP-014** (Celery): add to "Functional and performance requirements" that MedHub relies on
  the `setup_logging` signal to own the worker's logging; `in_review`.
- **PRB-011**: `## Resolution` with commit, tests, negative-control result; `resolved`.

## Definition of Done

- [ ] Lint, type-check, backend suite pass; coverage ≥ 85 %.
- [ ] TS-017 `in_review`; SOUP-014 `in_review`; PRB-011 `resolved`.
- [ ] `traceability-check` shows no error for TASK-138, TS-017, SR-043, PRB-011.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-008 (risk register bootstrap, TASK-147).
  Traceability only: the requirement content is unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.3 (2026-10-31) — CR-004 Plan stage (Software Architect role): rescoped to SR-043 against the
  current tree (two `extra` fields; formatters drop `extra`; the worker has no logging
  configuration). Links `implements` SR-043, `relates_to` PRB-011, CR-004, ADD-017, ADD-005 added.
  Tests named by path, TS-017 planned. Still `draft`.
