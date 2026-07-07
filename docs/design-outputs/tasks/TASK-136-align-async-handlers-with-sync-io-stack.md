---
id: "TASK-136"
type: task
title: "Align async handlers/dependencies with the sync IO stack"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "NFR-008"
    relation: implements
  - target: "SR-026"
    relation: relates_to
  - target: "TASK-025"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium"]
---

- **Phase:** Review 2026-07 — performance/architecture
- **Implements:** NFR-008 (performance)
- **Depends on:** TASK-135 (touches the same attachments router)
- **Branch:** `fix/async-sync-alignment`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — finding B (Medium)

## Objective

The stack is sync (redis-py, sync SQLAlchemy, boto3), but several dependencies/handlers are declared
`async def`, so their blocking IO runs on the event loop instead of the threadpool and stalls every
concurrent request: `get_session` and `get_current_user` (`app/api/deps.py:44,71` — sync Redis + DB
on **every authenticated request**), `require()._dependency` (L126 — sync authorize + audit DB
write), `require_module_enabled._dependency` (L198 — sync DB), and `upload_attachment`
(`app/api/routers/attachments.py` — sync boto3 put + DB).

## Implementation detail

- Convert the listed dependencies to plain `def` so FastAPI runs them in the threadpool. Do **not**
  migrate to asyncpg/async SQLAlchemy — out of scope, sync stack is the accepted design.
- `upload_attachment` must stay `async` for `UploadFile` streaming (TASK-135); push its blocking
  work (`svc.store`) through `run_in_threadpool`.
- Sweep remaining routers for the same pattern (`grep -n "^async def" app/api/routers app/api/deps.py`)
  and align any stragglers.

## Acceptance criteria

- [ ] No `async def` dependency or handler performs direct sync Redis/SQLAlchemy/boto3 calls.
- [ ] Existing API test suite passes unchanged.
- [ ] A concurrency smoke check (e.g. 20 parallel authenticated requests with an artificial slow
  query) shows the event loop is not blocked (health endpoint stays responsive).

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Regression test or CI check guards the pattern (e.g. simple AST/grep check in CI)
- [ ] Traceability row updated (NFR-008 → TASK-136 → tests)
