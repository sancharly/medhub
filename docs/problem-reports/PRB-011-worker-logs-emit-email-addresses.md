---
id: "PRB-011"
type: problem-report
title: "Worker logs emit email addresses, bypassing audit scrubbing"
status: resolved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-07"
criticality: major
links: []
tags: ["privacy", "hazard:privacy"]
---

# PRB-011 — Worker logs emit email addresses, bypassing audit scrubbing

## Observed

`workers/email_tasks.py:170` logs the recipient address in a structured `extra` field. `AuditService` scrubbing protects audit rows only, so the JSON stdout stream carries raw PII to whatever log sink collects it.

## Impact

An uncontrolled copy of personal data outside the retention and erasure machinery (SR-024, NFR-004): erasure cannot reach log archives.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **Present, with a correction
to the mechanism.**

- Two log calls attach an address as a structured field:
  `backend/app/workers/email_tasks.py:117-123` (`extra={"email": account.email, …}`, activation
  email sent) and `email_tasks.py:168-171` (`extra={"recipient": recipient_email, …}`, erasure
  retrieval-code email sent).
- Correction: the formatters in use today do **not** serialize `extra`. The API process's
  `_JsonFormatter` writes only level, message, logger and `exc_info`
  (`backend/app/core/logging.py:12-21`). The worker never calls `configure_logging()` (its only
  caller is the API lifespan, `backend/app/main.py:20`; `backend/app/workers/celery_app.py` sets
  no logging), so it uses Celery's default text format, which does not print `extra` either. The
  address is on the `LogRecord`, and any handler or formatter that serializes record attributes
  (a JSON log shipper, an error tracker) emits it.
- Not yet checked, and the reason SR-043 AC 3 tests the **failure path**: an SMTP refusal raised
  from `_send_smtp` (`email_tasks.py:33-65`) is retried by Celery (`autoretry_for=(Exception,)`),
  and Celery logs the exception text on retry and on final failure. An `smtplib` recipient
  refusal names the recipient. Whether the address then reaches stdout is what the test decides.
- No redaction filter exists on any logger; the worker logs are outside the application's
  logging configuration altogether.

Criticality `major` is kept: the copy is not present on stdout today through the two `extra`
fields, but it is one formatter change away, and the failure path is unverified.

## Safety evaluation

Contributes to RISK-008 (personal data retained, copied or erased contrary to its lawful basis).

## Resolution

TASK-138 (CR-004), 2026-11-06. Left `open` until the closing change request resolves it (D-8).

- Source: the two `extra` address fields in `email_tasks.py` removed; logs name accounts by id.
- `RedactionFilter` (`backend/app/core/logging.py`) on the root handler and on handlers of loggers that
  keep their own; replaces email-shaped values in the message, args, every extra field under any name,
  exception text and traceback, and replaces personal-data, credential and task-argument fields by name.
  The JSON formatter now serializes `extra` after the filter.
- The worker and scheduler call `configure_logging()` through Celery's `setup_logging` signal
  (`celery_app.py`), so Celery's retry and failure records use the same handler.
- Failure path (the open question of the Investigation): Celery's retry and failure records did name
  the address in the exception text (`SMTPRecipientsRefused({...})`); with the filter they print
  `[REDACTED-EMAIL]`. Tests: TS-017 (`tests/test_log_redaction.py`, `tests/workers/test_email_tasks_logging.py`).
- Round 2 (QA): the expression is linear-time and Unicode/IDN-aware; the filter fails closed and never
  raises; the database engines hide bound parameters (`hide_parameters=True`), so names in
  IntegrityError/DataError text no longer reach the log.
- Known limit: personal data that is neither email-shaped nor in a field named like personal data (for
  example a name written into a message, a path or free exception text) is not detected.
- Negative controls: filter not attached, 8 tests fail; filter blind to extra fields and exception text,
  5 fail; address restored at the source, 1 fails.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding E.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.2 (2026-11-06) — TASK-138: `## Resolution` written. Status stays `open` (D-8).
- 1.3 (2026-11-07) — TASK-138 round 2: Resolution extended (linear-time and Unicode matching, fail-closed filter, `hide_parameters`, known limit). Status stays `open` (D-8).
- 1.4 (2026-11-07) — TASK-138 QA approval (round 2): `resolved` (CR-004 D-8). `major`.
