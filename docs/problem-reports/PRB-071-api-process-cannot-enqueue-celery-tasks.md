---
id: "PRB-071"
type: problem-report
title: "The API process cannot enqueue Celery tasks, so no e-mail is sent and no session kill is propagated"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-07"
updated: "2026-11-07"
criticality: critical
links: []
tags: ["celery", "availability", "notifications", "hazard:availability", "found-in:TASK-206-started-stack"]
---

# PRB-071 — The API process cannot enqueue Celery tasks, so no e-mail is sent and no session kill is propagated

## Observed

Found on a scratch started stack while checking PRB-070 (TASK-206, 2026-11-07). An administrator created an
account (`POST /api/v1/accounts` answered 201) and the backend logged
`Failed to enqueue activation email for account <id>; admin resend required`. No task reached the worker's
queue and no mail was sent. Reproduced inside the backend container:
`send_activation_email.delay(...)` raises `kombu.exceptions.OperationalError: [Errno 111] Connection refused`.

## Impact

Every task the API dispatches is lost: the activation e-mail (first and resent, `account_service.py:109`,
`activation.py:144`), the session-kill propagation (`lifecycle.py:69`), the erasure retrieval-code e-mail
(`erasure.py:140`) and the appointment notification (`appointments/service.py:69`). On the delivered Compose
stack a new account can therefore never be activated by its owner, and a deactivated account's sessions are not
killed by the worker. Each call site catches the exception and logs a warning (PRB-013), so the API still
answers 2xx.

## Investigation

The tasks are `@shared_task`s (`backend/app/workers/email_tasks.py`, `session_tasks.py`). A shared task binds
to Celery's *current* app. Nothing in the API process imported `app.workers.celery_app` (the only module that
builds `Celery("medhub", broker=settings.redis_url)`), so the API used Celery's built-in app and its broker
`amqp://guest@localhost//`. The worker imports `celery_app` (`-A app.workers.celery_app`) and was correct.

The Compose file already gives the backend `REDIS_URL` (`infra/docker-compose.yml`, `backend.environment`), so
no Compose change is needed. Scratch evidence: `CELERY_BROKER_URL=redis://redis:6379/0` in the backend container
made the mail reach the worker, confirming the cause.

A first fix (import `celery_app` in the API) was not enough on the started stack: the route still failed with
"No hostname was supplied. Reverting to default 'localhost'". Celery's *current* app is thread-local
(`Celery.set_current()` stores it in a thread-local), and a sync FastAPI route runs in a worker thread, which
falls back to the global *default* app. Only `set_default()` is process-global. A unit test that checked the app
from the importing thread passed and hid this; the test now checks from a worker thread.

Call sites affected (all dispatch from the API process): `identity/account_service.py:109` and
`identity/activation.py:144` (activation e-mail, first and resend), `identity/lifecycle.py:69` (session-kill
propagation after deactivation), `identity/erasure.py:140` (erasure retrieval-code e-mail) and
`appointments/service.py:69` (appointment notification). The unit tests patch the task or call `.run()`, so none
dispatched through a broker.

PRB-013 pattern (not changed): every one of these call sites wraps `.delay()` in `except Exception` and goes on.
`account_service.py`, `activation.py` and `erasure.py` log a warning; `lifecycle.py` and `appointments/service.py`
have `pass` with no log. On the session-kill path the synchronous `invalidate_all` runs first, so the sessions
were still ended on the stack (the patient's next request answered 401); the worker task is the redundant
propagation (SR-034 AC 2) and its failure was silent.

## Safety evaluation

Availability of account onboarding and of a security control (session kill after deactivation, RISK-005,
RISK-009). The failure is silent for the caller. Criticality **critical** (human decision 2026-11-07, CR-004 D-17): the main flow
cannot complete on the delivered stack. No release exists (CR-004 A-1).

## Resolution

Fixed by TASK-206 (CR-004 D-17, human decision 2026-11-07: critical, fixed now); status stays `open` until QA
approves the task (D-8).

- `backend/app/main.py`: `_bind_celery_app()` imports `app.workers.celery_app` and calls
  `celery_app.set_default()`; the API lifespan calls it right after the secret rule. It runs once per gunicorn
  worker, reads no settings at import time, and only connects Celery receivers: the start-up secret rule stays on
  `worker_init`/`beat_init`, and the API's logging is unchanged (the `setup_logging` receiver never fires in the
  API).
- `backend/tests/workers/test_api_celery_broker.py`: for the activation e-mail, session-kill, erasure-code and
  appointment tasks, a fresh interpreter starts the API lifespan and a worker thread must see the configured
  Redis broker. Negative controls: with no call, and with the import but no `set_default()`, the test sees
  `amqp://guest:**@localhost:5672//`.
- Started stack with no broker override: an administrator-created account produced the mail at the catcher
  (link `/activation/<token>`), no "Failed to enqueue" in the backend log; the activation page rendered in a real
  browser; the account activated and signed in; a SYSADMIN deactivation answered 204, the patient's session ended
  and the worker logged `propagate_session_kill` received and succeeded; no log held the token or any password.
- Not changed (reported): the PRB-013 swallow-and-continue call sites listed above.

## Source

TASK-206 started-stack check, step 3 (activation through a real e-mail).

## Version history

- 1.0 (2026-11-07) — Created by the Software Developer role. `open`, proposed `critical`.
- 1.1 (2026-11-07) — CR-004 D-17: Investigation and Resolution written (TASK-206). `critical` confirmed by the human. `open` (D-8).
- 1.2 (2026-11-07) — QA approved TASK-206: status `resolved` (CR-004 D-8).
