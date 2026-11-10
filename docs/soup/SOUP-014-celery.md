---
id: SOUP-014
type: soup
title: Celery
status: approved
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-11-10"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-10"
approval_note: approved by the human in chat at the close of CR-004
manufacturer: Celery project
soup_version: 5.6.3
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-014 — Celery 5.6.3

## Functional and performance requirements

Asynchronous tasks with retry and backoff: activation and appointment notifications (SR-033, SR-035), session-revocation propagation (SR-034) and retention erasure (SR-024).

MedHub also relies on, and tests (TS-017), these Celery behaviors for SR-043 (personal data excluded from
logs):

- The `setup_logging` signal: when a receiver is connected, Celery does not configure logging itself, and it
  passes the `--loglevel` value (an int) as the `loglevel` keyword. The receiver in
  `app/workers/celery_app.py` calls `configure_logging(loglevel)`, so the worker and beat share the API's JSON
  handler and redaction filter, Celery's own loggers (`celery.app.trace`, `celery.worker.strategy`) propagate to
  that handler, and `--loglevel` sets the root level (INFO when absent). Relied on, and tested in
  `backend/tests/workers/test_celery_logging_level.py` (TS-017 TC-017.5).
- `@shared_task` binds to the *current* app, which is thread-local (`Celery.set_current`); only `Celery.set_default()` is process-global. The API sets the configured app as default at start-up so tasks dispatched from sync routes (worker threads) reach the Redis broker (PRB-071; `backend/tests/workers/test_api_celery_broker.py`).
- At `--loglevel=debug` the `TaskPool: Apply` record (`celery.pool`) prints the task message headers, whose
  `argsrepr` and `kwargsrepr` hold the task arguments (the activation token among them); MedHub's filter
  replaces both values (TASK-206, found on a started stack).
- Which Celery log records carry task arguments (Celery 5.6.3): the task-failure record
  (`celery/app/trace.py`, `_log_error`) carries `args`, `kwargs`, `exc` and `traceback` in its `data`
  field, and the "task received" record (`celery/worker/strategy.py`) carries `args` and `kwargs` for
  every task, successful or not. Task retry records carry only `id`, `name` and `exc`. Activation
  tokens, retrieval codes and recipient addresses are task arguments, so MedHub's redaction filter
  replaces `args`/`kwargs` fields and email-shaped values (also in `exc` and `traceback`) before a record
  is emitted.
- `task_ignore_result=True` (TASK-207): with it Celery neither writes a per-task result nor subscribes to the result store at call time. Without it `RedisBackend.on_task_call` retries the result store 20 times at 1 s when Redis is unreachable and `.delay()` blocks the request for about 20 s (19.88 s measured, 0.93 s with the setting); `retry=False` does not help. MedHub relies on it, and on no code reading a task result (`backend/tests/workers/test_celery_results.py`).

## Required hardware and software environment

Python 3.12; Redis server 7 as broker and result backend.

Transitive dependencies covered by this record: kombu 5.6.2, billiard 4.2.4, amqp 5.3.1.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for Celery 5.6.3 with kombu 5.6.2, billiard 4.2.4, amqp 5.3.1, vine 5.1.0, click 8.4.1, click-didyoumean 0.3.1, click-plugins 1.1.1.2, click-repl 0.3.0, prompt-toolkit 3.0.52, wcwidth 0.8.1, tzlocal 5.4.3, tzdata 2026.2 and python-dateutil 2.9.0.post0, the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database, https://github.com/celery/celery/security/advisories and https://github.com/celery/kombu/security/advisories; NVD; https://github.com/celery/celery/releases/tag/v5.6.3

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `celery` 5.6.3 and each transitive dependency at the version above.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `celery@5.6.3`, `kombu@5.6.2`.
- Repository advisories — https://github.com/celery/celery/security/advisories and https://github.com/celery/kombu/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `celery`.
- Release notes — https://github.com/celery/celery/releases/tag/v5.6.3. 5.6.3 and kombu 5.6.2 are the latest releases (PyPI release history, `https://pypi.org/pypi/<package>/json`).

### Findings

**None found** on 2026-10-22. No advisory for Celery or any listed dependency in OSV, the GitHub
Advisory Database or the repositories. NVD's recent `celery` matches are other products that use
Celery (RELATE, Apache Airflow, Flower, BottleCRM, Open Zaak). 5.6.3's notes are bug fixes, among
them a worker that failed to reconnect after a Redis failover. There is no later release.

### MedHub use and judgement

MedHub runs asynchronous notification, session-revocation and retention-erasure tasks
(SR-033/034/035, SR-024; RISK-008 and RISK-007) on a Redis broker and result backend. It accepts
the JSON serializer only (`accept_content=["json"]`, `app/workers/celery_app.py`), so the classic
pickle-deserialization class of Celery issues does not apply. Not hazard-relevant; no RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 5.6.3 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): none found for 5.6.3 or its transitive dependencies; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
- 2026-11-06 — 5.6.3 (unchanged). Version 1.2: relied-on requirements extended with the `setup_logging` signal and the task-argument content of retry and failure log records (TASK-138, SR-043, PRB-011). No version change; anomaly review (2026-10-22) is unchanged and within 365 days. Approval record cleared for re-approval.
- 2026-11-06 — 5.6.3 (unchanged). Version 1.2 text corrected after QA (TASK-138 round 1): retry records carry no task arguments (the failure and "task received" records do), and the worker's `--loglevel` is ignored. Still `in_review`.
- 2026-11-07 — Version 1.3 (TASK-206): relied-on behavior corrected: `--loglevel` is passed by the `setup_logging` signal and applied by MedHub (it was documented as ignored); debug task-header records redacted. No version change of Celery. Approval record cleared; `in_review`.
- 2026-11-07 — Version 1.4 (TASK-206, PRB-071): relied-on behavior added (`set_default()` is process-global, the current app is thread-local). No version change of Celery. `in_review`.
- 2026-11-07 — Version 1.5 (TASK-207): relied-on behavior added (`task_ignore_result`, dispatch does not wait on the result store). No version change of Celery. `in_review`.
