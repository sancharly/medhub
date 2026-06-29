# MedHub — Runtime Smoke Test Results

Audit branch: `enabler/audit-and-design-review`. Stack: `infra/docker-compose.yml` (postgres, redis,
minio, backend, celery-worker, frontend, reverse-proxy) over HTTPS at `https://localhost`.
Seeded via `backend/scripts/setup_test_data.py`.

Test accounts: `doctor@medhub.local / doctor123`, `john.doe@example.com / patient123`,
`jane.smith@example.com / patient123`. (Admin/sysadmin password not reset by the seeder — admin UI
flows not smoke-tested; not a defect.)

Method: `curl` against the real reverse proxy, capturing the actual serialized JSON. This is what the
unit tests (MSW mocks) cannot see.

---

## BASELINE (pre-fix) — `2026-06-29`

| #  | Flow                                             | Request                          | Result                                                                            | Verdict                  |
|----|--------------------------------------------------|----------------------------------|-----------------------------------------------------------------------------------|--------------------------|
| 1  | Stack health                                     | `GET /healthz`                   | `{"status":"ok"}` 200                                                             | PASS                     |
| 2  | DB schema                                        | `\dt` in postgres                | 13 tables present (migrations were run manually earlier on the persistent volume) | PASS*                    |
| 3  | Login (doctor)                                   | `POST /auth/login`               | 200 — `user.accountType:"DOCTOR"`                                                 | PASS (but see F4)        |
| 4  | `/me` (doctor)                                   | `GET /me`                        | 200 — `userType:"DOCTOR"`                                                         | PASS                     |
| 5  | Doctor patient list                              | `GET /clinical-entries/patients` | **404 Not Found**                                                                 | **FAIL (F2)**            |
| 6  | Appointments list                                | `GET /appointments`              | 200 `[]`                                                                          | PASS                     |
| 7  | Create appointment **without** CSRF header       | `POST /appointments`             | **201 Created**                                                                   | **FAIL — security (F3)** |
| 8  | Create appointment **with** `medhub_csrf` header | `POST /appointments`             | 201 Created                                                                       | PASS                     |
| 9  | Patient consent grant **without** CSRF header    | `POST /consents`                 | 401 "CSRF token missing or invalid"                                               | enforced here            |
| 10 | Logout **without** CSRF header                   | `POST /auth/logout`              | 401 "CSRF token missing or invalid"                                               | enforced here            |

`*` The persistent volume already had tables; a *fresh* deploy would have none (see F5).

---

## Confirmed defects (root causes of "basic functionality doesn't work")

### F1 — Frontend reads the wrong CSRF cookie name → all protected writes fail from the UI  ★ SHOWSTOPPER
- Backend sets the CSRF cookie as **`medhub_csrf`** (`backend/app/auth/csrf.py:18`, HttpOnly=False so JS-readable).
- Frontend reads a cookie named **`csrftoken`** (`frontend/src/api/csrf.ts:5`) — which never exists — so it
  sends an empty/absent `X-CSRF-Token` header.
- Routes that DO enforce CSRF (`require_csrf`): **logout, change-password, session-extend**
  (`auth.py`), **consent grant/revoke** (`consents.py`), **account deactivate/reactivate/delete**
  (`lifecycle.py`). From the UI these all return **401 "CSRF token missing or invalid"**, which the
  client treats as an auth failure and bounces the user to login.
- Evidence: rows 9–10 above (401 without header). Fix = read `medhub_csrf` in `csrf.ts`.

### F2 — Doctor patient list endpoint is missing → 404  ★ SHOWSTOPPER / MISSING FUNCTIONALITY
- Frontend `client.ts:122 listPatients()` → `GET /clinical-entries/patients`.
- No such endpoint exists. The clinical router (`backend/app/api/routers/clinical.py`, prefix
  `/patients`) only implements `POST/GET /{patient_id}/clinical-entries`. There is **no doctor
  patient-list endpoint anywhere** in the backend.
- Effect: the doctor's landing page (`/patients`, TASK-091) is dead; doctors cannot reach clinical
  entries. Maps to **SR-006** (doctor sees patients they have access to). This is the "deferred but
  never implemented" pattern — to be filed as a new backend task.
- Evidence: rows 5 above (404).

### F3 — CSRF enforcement is missing on most mutating routes  ★ SECURITY DEFECT
- `require_csrf` is applied only in `auth.py`, `lifecycle.py`, `consents.py`. It is **absent** from the
  mutating routes in `appointments.py`, `accounts.py`, `groups.py`, `clinical.py`, `attachments.py`.
- Effect: state-changing requests to those routers succeed with **no CSRF token** (row 7: `POST
  /appointments` → 201 without header). Violates **SR-031 / TASK-022 / TASK-069**, which are marked
  Completed. To be filed as a security task.

### F4 — `LoginResponse.user` field name inconsistent with the rest of the contract
- `LoginResponse.user.accountType` (`backend/app/api/schemas/auth.py:27` `account_type`) vs `userType`
  everywhere else (`/me`, accounts). Currently both login sides happen to use `accountType`, so login
  works — but it is a single-source-of-truth violation (CLAUDE.md §5) and a latent bug. Fix in-branch.

### F5 — No database migration step in the deployment (DEPLOY GAP)
- Neither the backend `Dockerfile`/entrypoint, the compose stack, nor the app lifespan
  (`app/main.py:_lifespan`) runs `alembic upgrade head`. Also `alembic.ini` is not copied into the
  backend image. A fresh `docker compose up` comes up with an **empty database**, so every DB-backed
  endpoint 500s until someone runs migrations by hand. To be filed as a task / finding.

---

## AFTER FIX — `2026-06-29` (backend + frontend images rebuilt)

| # | Flow                    | Result                                             | Verdict        |
|---|-------------------------|----------------------------------------------------|----------------|
| 3 | Login (doctor)          | 200 — `user.userType:"DOCTOR"` (was `accountType`) | **FIXED (F4)** |
| — | CSRF cookie set         | `medhub_csrf`                                      | —              |
| — | Rebuilt frontend bundle | reads `medhub_csrf`, no `csrftoken`                | **FIXED (F1)** |
| 4 | `/me`                   | 200 — `userType:"DOCTOR"` consistent with login    | PASS           |

**Fixed in this branch:**
- **F1** — `frontend/src/api/csrf.ts` now reads the `medhub_csrf` cookie (was `csrftoken`). Frontend
  writes to CSRF-protected endpoints (logout, change-password, consent, lifecycle) now send a valid
  `X-CSRF-Token`. Also corrected the 3 frontend tests that mocked the wrong cookie name.
- **F4** — `backend/app/api/schemas/auth.py` `account_type`→`user_type`; OpenAPI + frontend types
  regenerated; `LoginPage.tsx` and login tests updated. Login response now uses `userType`,
  consistent with `/me` and the rest of the contract. Frontend typecheck + 110 vitest tests pass;
  backend auth tests pass.
- **F5** — uppercased all lowercase `userType` mocks in 5 frontend test files so tests exercise the
  real contract.

**Deferred to tracked tasks (not fixed in-branch — require design/feature work):**
- **F2** — doctor patient-list endpoint (new backend task).
- **F3** — CSRF coverage gap on appointments/accounts/groups/clinical/attachments routers (security task).
- **F5b/F6** — see `AUDIT-FINDINGS.md` and the new TASK files.
- **F5(deploy)/F5-orig** — no migration step in deployment (task/finding).
