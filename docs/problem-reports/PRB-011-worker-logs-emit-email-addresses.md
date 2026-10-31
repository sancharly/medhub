---
id: "PRB-011"
type: problem-report
title: "Worker logs emit email addresses, bypassing audit scrubbing"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
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

Planned in CR-004: TASK-138 (identifiers instead of addresses at the source; one redaction
filter on every handler of the API, worker and scheduler processes; log-capture tests of both
worker paths and of an arbitrary field, SR-043). Not yet fixed.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding E.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
