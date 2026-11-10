---
id: "TASK-140"
type: task
title: "Auth config hygiene: remove dead session_signing_key, make lockout_svc required"
status: approved
version: "1.4"
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

- [x] SR-030: the app boots without `SESSION_SIGNING_KEY`; nothing references it
      (`backend/tests/test_config.py`; `grep -rn -i session_signing_key . --exclude-dir=docs` empty).
- [x] SR-029 AC 1: the login flow cannot be called without a lockout service
      (`backend/tests/auth/test_login_service.py`, `mypy app`).
- [x] The auth and lockout suites pass (`backend/tests/auth`, `backend/tests/api/test_lockout_integration.py`).

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

- [x] Lint, type-check, backend suite pass; coverage ≥ 85 %; CI env updated.
- [x] TS-001 1.2 `in_review`; PRB-018 `resolved`.
- [x] `traceability-check` shows no error for TASK-140, TS-001, SR-029, SR-030, PRB-018.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-005 (risk register bootstrap, TASK-147).
  Traceability only: the requirement content is unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.3 (2026-10-31) — CR-004 Plan stage (Software Architect role): every mention of the setting
  listed from the current tree; ordered before TASK-197/203. Links `relates_to` PRB-018, CR-004,
  ADD-006 added. Tests named by path, TS-001 TC-001.7 planned. Still `draft`.
- 1.4 (2026-10-31) — Implemented (Software Developer role); handed to QA, `in_review`. See
  Implementation notes.
- 1.4 (2026-10-31) — QA review: APPROVED (`in_review → approved`); TS-001 approved. Findings 1 to 4 non-blocking, carried as listed in the review.

## Implementation notes

- `backend/app/core/config.py`: `session_signing_key` removed; `extra="ignore"` added. Needed:
  pydantic-settings rejects unknown keys read from a `.env` file (`extra_forbidden`), so a stale
  `session_signing_key=` line in an operator's `.env` would have stopped the app (an unknown
  environment variable was already ignored).
- `backend/app/auth/login.py`: `lockout_svc: LockoutService` required, no default; the five `None`
  guards and their `type: ignore[attr-defined]` comments removed. TASK-192 order kept:
  `record_failure` before the audit write on both failure paths.
- Mentions removed in `infra/.env.example`, `infra/DEPLOY.md` (plus a removal note),
  `.github/workflows/ci.yml` (two jobs), `backend/tests/conftest.py`, `test_config.py`,
  `test_lifespan.py`, `backend/modules/dicom_viewer/tests/conftest.py` and
  `backend/tests/audit/test_audit_no_secrets.py` (the signing key was one of its forbidden values;
  nothing generates it any more, so it is dropped with its unused `get_settings` import).
- Tests: `test_login_service.py` passes a `MagicMock(spec=LockoutService)` to every call and adds
  three tests; `test_config.py` adds two.
- The `grep -rni session_signing_key` check is not literally empty: it matches the removal note in
  `infra/DEPLOY.md`, one comment in `config.py` and the two tests that prove the setting is
  gone and a stale value is ignored. No setting, template, CI or Compose file references it.
  `infra/docker-compose.yml` never referenced it.
- The untracked local `infra/.env` and `backend/.env` still hold the line; harmless, by design.
- Records: TS-001 1.2 `in_review` (TC-001.7; the 1.1 approval record removed for re-approval);
  PRB-018 `resolved`.

## QA review (QA engineer, 2026-10-31): APPROVED

No CRITICAL or HIGH finding. TASK-140 `in_review → approved`; TS-001 1.2 `in_review → approved`.
PRB-018 `resolved` is valid: CR-004 carries `resolves` PRB-018, and the Resolution's commands and
both negative controls reproduce.

### Findings (non-blocking)

1. **MEDIUM — TS-009 TC-009.12 and the test docstring still claim a check the test no longer
   makes.** `backend/tests/audit/test_audit_no_secrets.py:7` ("signing key") and
   `docs/design-outputs/tests-specifications/TS-009-audit-logging.md:50` (approved; "contain no
   ... session signing key") describe the flow scan's forbidden list. TASK-140 dropped the key
   from it (`test_audit_no_secrets.py:247-254`) and nothing replaced it. The list now holds no
   secret that `Settings` holds: `AT_REST_ENCRYPTION_KEY`, `SMTP_PASSWORD`, the password in
   `DATABASE_URL` and the object-store keys were never in it, before or after this change. The
   unit cases cover those kinds by shape (`_SECRETS` `base64_key`, `object_store_access_key`).
   → Add the live secrets to `forbidden`: `s = get_settings()`, then
   `s.at_rest_encryption_key.get_secret_value()`, `s.smtp_password.get_secret_value()`,
   `s.object_store_access_key.get_secret_value()`, `s.object_store_secret_key.get_secret_value()`,
   `s.database_url.hosts()[0]["password"]`. Change the docstring to "or any configured secret".
   Bump TS-009 to 1.8 with TC-009.12 saying the same, for re-approval. Do this in the next task
   that touches TS-009, or in TASK-197, which owns the secret-settings list.
2. **LOW — `extra="ignore"` also hides a misspelled key in a `.env` file**
   (`backend/app/core/config.py:16-18`). Probed with pydantic-settings 2.14.2:
   - Process environment variables are never "extra", under `forbid` or `ignore`. Only `.env`
     file keys and init kwargs are.
   - With `forbid`, `TRUSTED_PROXIE=` in a `.env` failed with `extra_forbidden`. With `ignore`
     it is silent, and `trusted_proxies` falls back to `""`.
   - A misspelled required secret (`AT_REST_ENCRYPTION_KEYY=`) still fails with `missing`.

   Deployed containers get their settings as process environment from Compose `env_file:`, and
   the image has no `.env`. There, nothing changes. Every optional default is the safe one:
   `trusted_proxies` `""` trusts no proxy, `session_cookie_secure` and `smtp_use_tls` are True,
   `cors_origins` is `[]`. SR-041 / TASK-197 read the environment and the required fields, so
   their fail-closed rule is not weakened. TASK-140's own plan text authorised `extra="ignore"`.
   → Optional, narrower alternative, verified: keep the default `forbid` and drop only the
   retired name with
   `@model_validator(mode="before")` → `data.pop("session_signing_key", None)`. A stale line
   then starts, and a typo still fails. Otherwise add one line to `infra/DEPLOY.md`: key names
   in a local `.env` are not spell-checked.
3. **LOW — arc42 and the ADR still list the session signing key as a deployed secret.**
   `docs/design/07-deployment-view.md:39`, `docs/design/adr/0010-deployment-model.md:16`. Not
   design elements, so traceability is unaffected. → document-writer: drop it from 07; for
   ADR-0010, add a dated note pointing to PRB-018 rather than rewriting the decision.
4. **LOW — records that still name the key** (no change needed in this task):
   - ADD-006:58 (approved) and ADD-026:89 (in_review) already say it is removed. Correct.
   - TASK-003:39,61 and TASK-175:196 (approved) are historical statements of the state at the
     time. Leave them.
   - TASK-192:126 (approved) describes the Checkpoint B scan as it was. It is superseded by
     finding 1. Optional dated pointer.
   - PRB-007:74 (open) says "TASK-140 removes `SESSION_SIGNING_KEY` ... Not yet fixed". Update
     it when TASK-197/203 write PRB-007's Resolution.
   - TASK-197 (draft): its scope is unaffected. Its dependency on TASK-140 is now met. Its
     `SECRET_SETTINGS` never listed the key. `KNOWN_PLACEHOLDERS` should keep
     `change-me-to-a-random-32-byte-secret`, because the template shipped it.
   - CODE-REVIEW-2026-07 and the remediation plan are historical. CR-004:499,574 is accurate.
   - TASK-176 and SOUP-036 "filer signing key" are SeaweedFS and unrelated.

### Checks

- Callers of `login()`: only `backend/app/api/routers/auth.py:63`, which passes `lockout_svc`.
  Nothing calls it from scripts, `setup-test-data` scripts or modules. `smtp.login` in
  `workers/email_tasks.py` is a different method. `mypy` on a probe call without `lockout_svc`
  gives `call-arg`.
- TASK-192 order preserved: `record_failure` runs before the audit write on both failure paths
  (`login.py:82-83,112`). Mutation (known-account `record_failure` moved after the audit write)
  → `test_known_account_failure_counts_before_a_refused_audit_write` fails.
- Stale references: `grep -rni session_signing_key` (excluding docs, .git, .venv, node_modules,
  graphify-out) matches only the `DEPLOY.md:24` note, the `config.py:16` comment and
  `test_config.py`. CI, `infra/smoke-test.sh`, `infra/docker-compose.yml` and
  `compose.ci-object-store.yml` have none. The untracked `infra/.env:17` and `backend/.env` still
  hold the key. They are harmless: the backend `.env` load ignores it, and Compose passes it as
  an environment variable, which is ignored.
- Negative controls, run in a scratch copy:
  - `HEAD` `login.py` → `test_login_without_lockout_svc_raises_type_error` fails.
  - `extra="ignore"` removed → `test_stale_session_signing_key_is_ignored` fails with
    `extra_forbidden`.

### Verification run

| Command | Result |
|---|---|
| `uv run pytest tests/auth tests/api/test_lockout_integration.py tests/test_config.py tests/test_lifespan.py tests/audit` | 241 passed |
| `uv run pytest --cov=app --cov-fail-under=85` (re-run after the developer's final edit) | 966 passed, 4 skipped; coverage 93.74 % |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `uv run ruff check . && uv run black --check . && uv run mypy app` | clean; 243 files unchanged; no issues in 127 files |
| `cd infra && python3 -m unittest discover -s tests` | 37 OK |
| OpenAPI export vs `backend/openapi/openapi.json` | identical |
| traceability (TASK-140, TS-001, PRB-018, SR-029, SR-030, TS-009) | 0 errors. 2 warnings: W5 TP-001 → TS-001 `in_review` (cleared by this approval); W6 ADD-004 → ADD-002 obsolete (pre-existing) |
