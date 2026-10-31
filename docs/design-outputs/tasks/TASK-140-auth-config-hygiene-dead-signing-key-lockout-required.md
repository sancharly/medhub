---
id: "TASK-140"
type: task
title: "Auth config hygiene: remove dead session_signing_key, make lockout_svc required"
status: draft
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-10-31"
links:
  - target: "RISK-005"
    relation: mitigates
  - target: "SR-030"
    relation: implements
  - target: "SR-029"
    relation: implements
  - target: "PRB-018"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-006"
    relation: relates_to
  - target: "TASK-118"
    relation: relates_to
  - target: "TASK-003"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:low", "control:protective", "control:design", "cr:CR-004"]
---

# TASK-140 — Auth config hygiene: remove dead session_signing_key, make lockout_svc required

- **Software item / unit:** SI-AUTH `U-AUTH-Login` (ADD-006); settings.
- **Resolves (through CR-004):** PRB-018. Source: `docs/reports/CODE-REVIEW-2026-07.md` findings G, J.
- **Depends on:** none. **Must be committed before TASK-197 and TASK-203**, which edit
  `backend/app/core/config.py`, `infra/.env.example` and `infra/DEPLOY.md` after it.
- **Branch:** `fix/review-2026-07-security` (CR-004).
- **Size:** S (2 source files plus the setting's mentions in tests, CI and docs; TS-001)

## Objective

SR-029 AC 1 (lockout on every login path) and SR-030 (opaque sessions, AC 5): no call path can
omit the lockout service, and no setting implies signed sessions. PRB-018 Investigation lists
every place the setting appears and the five `None` guards in `backend/app/auth/login.py`.

## Implementation detail

- Remove `session_signing_key` from `backend/app/core/config.py:31` and from every mention:
  `infra/.env.example:38`, `infra/DEPLOY.md:18`, `backend/tests/conftest.py:21`,
  `backend/tests/test_config.py:15`, `backend/tests/test_lifespan.py:17`,
  `backend/modules/dicom_viewer/tests/conftest.py:25`, `.github/workflows/ci.yml:79,167`. A stale
  `SESSION_SIGNING_KEY` in an operator's `.env` is ignored (pydantic-settings ignores unknown
  variables only if configured so; confirm and, if not, set `extra="ignore"`). DEPLOY.md notes
  the removal.
- `LoginService.login(..., lockout_svc: LockoutService)` (`login.py:66`): required, typed with
  the real class (or a `Protocol`), no default; remove the `if lockout_svc is not None` guards
  (`login.py:88-90,97,118-119,123-124`). Tests pass a fake that implements the protocol.

## Tests (write first)

- `backend/tests/auth/test_login_service.py`: calling `login` without `lockout_svc` raises
  `TypeError`; `mypy app` rejects a call without it (checked by the type-check step).
- `backend/tests/test_config.py`: `Settings()` builds without `SESSION_SIGNING_KEY`; with a stale
  one present it still builds.
- Existing `backend/tests/api/test_lockout_integration.py` passes unchanged.

## Acceptance criteria

- [ ] SR-030: the app boots without `SESSION_SIGNING_KEY`; nothing references it
      (`backend/tests/test_config.py`; `grep -rn -i session_signing_key . --exclude-dir=docs` empty).
- [ ] SR-029 AC 1: the login flow cannot be called without a lockout service
      (`backend/tests/auth/test_login_service.py`, `mypy app`).
- [ ] The auth and lockout suites pass (`backend/tests/auth`, `backend/tests/api/test_lockout_integration.py`).

## Verification

```sh
cd backend && uv run pytest tests/auth tests/api/test_lockout_integration.py tests/test_config.py tests/test_lifespan.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
grep -rni "session_signing_key" . --exclude-dir=docs --exclude-dir=node_modules --exclude-dir=.venv   # expect nothing
```

## Records

- **TS-001** → 1.2 (`in_review`, first CR-004 task to change it): TC-001.7 (lockout required;
  no signing key), `verifies` SR-029, SR-030. TASK-199 adds TC-001.6 under the same version.
- **PRB-018**: `## Resolution`, `resolved`.

## Definition of Done

- [ ] Lint, type-check, backend suite pass; coverage ≥ 85 %; CI env updated.
- [ ] TS-001 1.2 `in_review`; PRB-018 `resolved`.
- [ ] `traceability-check` shows no error for TASK-140, TS-001, SR-029, SR-030, PRB-018.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-005 (risk register bootstrap, TASK-147).
  Traceability only: the requirement content is unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.3 (2026-10-31) — CR-004 Plan stage (Software Architect role): every mention of the setting
  listed from the current tree; ordered before TASK-197/203. Links `relates_to` PRB-018, CR-004,
  ADD-006 added. Tests named by path, TS-001 TC-001.7 planned. Still `draft`.
