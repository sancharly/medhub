---
id: "PRB-085"
type: problem-report
title: "Erasure rollback test fails with 503 when run after the Celery results test in one session"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["test-infrastructure", "celery", "found-in:TASK-141-228-review"]
---

# PRB-085 — Erasure rollback test fails with 503 when run after the Celery results test in one session

## Observed

`backend/tests/api/test_erasure_rollback.py::test_erasure_with_a_working_broker_commits_before_the_response` returns 503
instead of 200 when it runs after `backend/tests/workers/test_celery_results.py` in the same pytest session. It passes in
the full-suite order. QA reproduced it at commit `b2e7a1c` (TASK-141 review).

## Impact

A test run in a non-default order or selection (for example `pytest tests/workers/test_celery_results.py tests/api/test_erasure_rollback.py`)
reports a false failure. The product code is correct. Only test infrastructure is affected, and the full-suite order stays green.

## Investigation

The test builds its client without entering it as a context manager (`test_erasure_rollback.py:115`, `TestClient(...)`
without `with`), so the application lifespan never runs, and neither do `_bind_celery_app()` and `set_default()`.

Celery keeps the "current app" per thread. Importing `app.workers.celery_app` in the main (test) thread makes the
`medhub` app current in that thread. The test's `patch(...send_erasure_code_email.delay)` therefore patches the task
object of the `medhub` app. `TestClient` runs the request in another thread, where Celery resolves its fallback default
app, which holds a different task object whose `.delay` is not patched. The real enqueue is attempted, fails (no broker),
and the endpoint answers 503. When `test_celery_results.py` has not run first, the import order differs and both threads
resolve the same task object, which is why the full-suite order passes.

Root cause: a test-isolation assumption (the patched task object is the one the request thread uses) that holds only for
one import order.

## Safety evaluation

No product behaviour is affected: the failure is in the test, the endpoint and the erasure commit ordering (TASK-228) behave
as designed. No data integrity, safety-related function or clinical decision is involved, and no released version is
affected, so no notification is needed. The risk is a false failure, or a masked real failure if people learn to ignore
that test. Criticality `minor`.

## Resolution

Not fixed here. Options for a later change: enter the client as `with TestClient(...) as client:` so the lifespan runs
`_bind_celery_app()` and `set_default()`, or call `celery_app.set_default()` in the `world` fixture of
`test_erasure_rollback.py`. Either makes the request thread resolve the same app as the patch. Verify by running
`pytest tests/workers/test_celery_results.py tests/api/test_erasure_rollback.py` and the full suite.
