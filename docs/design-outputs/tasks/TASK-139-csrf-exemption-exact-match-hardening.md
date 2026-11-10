---
id: "TASK-139"
type: task
title: "CSRF exemption exact-match hardening"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-02"
links:
  - target: "SR-031"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "PRB-003"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
  - target: "TASK-128"
    relation: relates_to
  - target: "TASK-069"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium", "control:design", "cr:CR-004"]
---

# TASK-139 — CSRF exemption exact-match hardening

- **Software item / unit:** SI-API `U-API-Security` (ADD-005), `backend/app/core/security_middleware.py`.
- **Resolves (through CR-004):** PRB-003. Source: `docs/reports/CODE-REVIEW-2026-07.md` finding F.
- **Depends on:** none. Independent; can run in parallel with any CR-004 task.
- **Branch:** `fix/review-2026-07-security` (CR-004).
- **Size:** S (1 source file, 1 test file, TS-011)

## Objective

SR-031 AC 3: CSRF protection on every state-changing route that is not deliberately exempt.
`CsrfEnforcementMiddleware` exempts by `startswith` (`security_middleware.py:53-61,86-88`), so a
future sibling of `/api/v1/activation` or `/api/v1/auth/password-reset` would be exempt silently.
The PRB-003 Investigation also found that no password-reset route exists.

## Implementation detail

- Replace `_CSRF_EXEMPT_PREFIXES` with two explicit structures: a `frozenset` of exact paths
  (`/api/v1/auth/login`, `/api/v1/healthz`, `/api/v1/openapi.json`, `/healthz`,
  `/api/v1/anonymized-data/retrieve`) and a tuple of compiled `re.fullmatch` patterns for
  routes with a path parameter (`^/api/v1/activation/[^/]+$`). Compare the path with a trailing
  slash removed.
- Remove the `/api/v1/auth/password-reset` entry (no such route).
- Each entry carries a comment naming the route and why it has no session (ADR-0013 for the
  retrieval).

## Tests (write first)

`backend/tests/api/test_csrf_enforcement.py` (extend):

- `POST /api/v1/activation-x`, `POST /api/v1/auth/password-reset-force`,
  `POST /api/v1/anonymized-data/retrieve-all` and `POST /api/v1/activation/abc/extra` without a
  CSRF token → 403 problem+json (sibling routes are enforced);
- the current exempt routes still work without a session or token (login, activation with a
  token, retrieval, health);
- route inventory: enumerate `create_app().routes` for unsafe methods; each is either enforced
  or matched by an exemption that is in a reviewed list in the test; a new route that matches
  no reviewed entry but is exempt fails the test.

## Acceptance criteria

- [x] SR-031 AC 3: sibling routes are CSRF-enforced (`backend/tests/api/test_csrf_enforcement.py`).
- [x] The current exempt routes work sessionless (same file).
- [x] The inventory test fails on an unreviewed exemption (negative control: add a prefix entry back).

## Verification

```sh
cd backend && uv run pytest tests/api/test_csrf_enforcement.py tests/api/test_activation_router.py tests/api/test_anonymized_retrieve.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

## Records

- **TS-011** → 1.2 (`in_review`): TC-011.6 (exact exemptions, siblings enforced, inventory),
  `verifies` SR-031.
- **PRB-003**: `## Resolution`, `resolved`.

## Definition of Done

- [x] Lint, type-check, backend suite pass; coverage ≥ 85 %.
- [x] TS-011 1.2 `in_review` (approved by QA); PRB-003 `resolved`. TASK-113's security-review checklist item for
      CSRF re-run (auth/session code review gate, SR-031 AC 6) is carried to TASK-202 step 4 (QA finding 3).
- [x] `traceability-check` shows no error for TASK-139, TS-011, SR-031, PRB-003.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): rescoped against the current
  tree (no password-reset route; the activation route has a path parameter). Links `mitigates`
  RISK-005, RISK-001 and `relates_to` PRB-003, CR-004, ADD-005 added; tagged `control:design`.
  Tests named by path, TS-011 TC-011.6 planned. Still `draft`.
- 1.2 (2026-11-02) — Implemented (software developer). `in_review`, no checkbox ticked. See "Implementation notes".
- 1.2 (2026-11-02) — QA review: APPROVED (`in_review → approved`); TS-011 1.2 approved, PRB-003 `resolved` (CR-004 D-8). Findings 1 to 5 LOW, non-blocking; carried items listed in the review.

## Implementation notes (2026-11-02, software developer)

Handed to QA as `in_review`. Nothing staged or committed.

### Files

- `backend/app/core/security_middleware.py`: `_CSRF_EXEMPT_PREFIXES` replaced by `_CSRF_EXEMPT_PATHS`
  (frozenset, 5 exact paths) and `_CSRF_EXEMPT_PATTERNS` (one `re.fullmatch` pattern for
  `/api/v1/activation/{token}`), tested through the new module function `is_csrf_exempt(path)` (one trailing
  slash removed with `removesuffix`, so `//` is not exempt). `/api/v1/auth/password-reset` removed. Each entry
  commented with its route and why it has no session.
- `backend/tests/api/test_csrf_enforcement.py`: classes `TestCsrfExemptionIsExact` and
  `TestCsrfRouteInventory`; the existing activation test now posts to `/api/v1/activation/invalid-token`
  (the bare `/api/v1/activation` was only exempt through the prefix and has no route).
- Records: TS-011 1.2 `in_review` (TC-011.6, approval record cleared), PRB-003 `## Resolution` (status left
  `open`, per CR-004 D-8), this task.

### Characterisation before the change (POST; GET/HEAD/OPTIONS are never enforced)

Prefix matching, 25 paths: exempt = 20, enforced = 5 (`/api/v1/auth/password`, `/api/v1/auth/logout`,
`/api/v1/anonymized-data`, `/api/v1/appointments`, `/api/v1/accounts/1/resend-activation`).
Wrongly exempt siblings: `/api/v1/auth/login-x`, `/api/v1/auth/login/extra`, `/api/v1/auth/password-reset`,
`/api/v1/auth/password-reset-force`, `/api/v1/activation` (bare), `/api/v1/activation-x`,
`/api/v1/activation/abc/extra`, `/api/v1/activation/`, `/api/v1/anonymized-data/retrieve-all`,
`/api/v1/anonymized-data/other`, `/api/v1/healthz-x`, `/api/v1/openapi.json.bak`, `/healthz/deep`.
After: exempt only `/api/v1/auth/login` (and with one trailing slash), `/api/v1/activation/{token}` (one
segment), `/api/v1/anonymized-data/retrieve`, `/api/v1/healthz`, `/api/v1/openapi.json`, `/healthz`.

### Acceptance criteria

- AC 1 (siblings enforced): `TestCsrfExemptionIsExact::test_sibling_path_without_token_is_403_problem_json`
  (14 cases), `::test_is_csrf_exempt_table`, `::test_new_sibling_route_is_enforced_not_silently_exempt`.
- AC 2 (exempt routes sessionless): `::test_exact_exempt_paths_work_without_session_or_token` (7 paths),
  `TestCsrfExemptPaths::test_login_post_exempt_from_csrf`, `::test_activation_post_exempt_from_csrf`.
- AC 3 (inventory fails on an unreviewed exemption): `TestCsrfRouteInventory`
  (`test_exempt_routes_equal_the_reviewed_list`, `test_every_other_unsafe_route_is_403_without_a_token`,
  `test_exemption_constants_equal_the_reviewed_list`, `test_inventory_finds_the_application_routes`).

### Verification

- Targeted (csrf, activation router, anonymized retrieve): 59 passed.
- Negative control 1, prefix matching restored in `is_csrf_exempt`: 16 failed (14 sibling cases, the table,
  the new-route test). Control 2, `"/api/v1/activation"` added to `_CSRF_EXEMPT_PATHS`: 3 failed (bare
  activation sibling, the table, the constants/inventory test). Source restored after both.
- Full suite with coverage: 1322 passed, 6 skipped, 94.15 % (gate 85 %). ruff and black clean.
- `mypy app` reports one error in `app/auth/session.py:126` (untyped `watch`), a file TASK-199 has
  in progress; `mypy app/core/security_middleware.py` is clean.

### Notes for QA

- The first full run showed 8 failures in `tests/auth/test_session_cap_concurrency.py` (TASK-199's new file);
  a second run passed. Not touched.
- Starlette redirects a trailing slash only for routes declared with one; the matcher ignores one trailing slash
  so `/api/v1/auth/login/` stays exempt exactly as `/api/v1/auth/login`.
- `deps.py` is not touched (the misleading `require_csrf` docstring at ~51-53 is left; `deps.py` is in the
  auth/session area TASK-199 is changing).

## QA review (2026-11-02): APPROVED

QA Engineer role, branch `fix/review-2026-07-security` at `ed22a70` plus the TASK-139 working-tree diff
(`security_middleware.py`, `test_csrf_enforcement.py`, TS-011, PRB-003, this task). Other tasks' files in the
shared tree were not reviewed.

### Findings (all LOW, non-blocking)

1. **Login-CSRF protection is incidental, not a stated control** (pre-existing; login was always exempt) —
   `backend/app/core/security_middleware.py:57`. A cross-site form post to `/api/v1/auth/login` (`text/plain`,
   `application/x-www-form-urlencoded`, `multipart/form-data`) is refused with 400 by FastAPI's JSON body
   parsing before the login service runs, and a cross-origin `application/json` post needs a CORS preflight,
   which gets 405 (no CORS middleware). Nothing documents or tests this, so adding form parsing or a CORS
   allow-list would open login-CSRF silently. → Add a test that a non-JSON `POST /api/v1/auth/login` is
   refused without calling `LoginService.login`, and name the reliance in SR-031's control measures or
   ADD-005. Carried to TASK-202 step 4 (security review).
2. **The route inventory does not see module routers** — `backend/tests/api/test_csrf_enforcement.py:55`
   (`create_app()` without the lifespan, so `register_all_modules` never runs). Module routes live under
   `/api/v1/modules/{key}/`, which no exempt path or pattern can match, and the middleware is app-wide, so
   there is no gap today; QA checked that the walker finds a router mounted through `RouterRegistry`. →
   Add `assert not is_csrf_exempt("/api/v1/modules/x/y")` to the table test, or mount the discovered
   manifests in the inventory fixture.
3. **DoD item "TASK-113 security-review checklist item for CSRF re-run" not done here** — TASK-113 is
   `draft`; the review runs in TASK-202 step 4. → TASK-202's security review covers the exact exemption set
   and finding 1.
4. **RISK-001 control row still says "TS-011 TC-011.6 (planned)"** —
   `docs/risks/RISK-001-unauthorized-clinical-data-disclosure.md:70`. → Update in TASK-202 step 6 (risk
   re-evaluation).
5. **The `deps.py` `require_csrf` docstring is still misleading** (`backend/app/api/deps.py` ~51-53, left by
   the developer because TASK-199 is changing that file). → Fix in TASK-199 or after it.

Observation (not a finding): `[^/]+` exempts any future one-segment literal route under
`/api/v1/activation/` (for example `POST /api/v1/activation/resend`); the inventory catches it (mutation run below).

### Path-normalisation probes (real app, uvicorn 0.49.0, `--lifespan off`, `curl --path-as-is`, POST, no token)

uvicorn percent-decodes the path into `scope["path"]` and does not merge slashes or resolve dot segments;
the middleware and the router read the same decoded path. No probe reached a non-exempt route without a token.

- Enforced (403 CSRF): `//api/v1/auth/login`, `/api/v1//auth/login`, `/api/v1/auth//login`,
  `/api/v1/auth/login//`, `/api/v1/auth/./login`, `/api/v1/auth/x/../login`, `/api/v1/auth/logout/../login`,
  `/api/v1/auth/login/../logout`, `/api/v1/auth/login%2F..%2Flogout`, `/API/v1/auth/login`, `/api/v1/auth/Login`,
  `/api/v1/auth/login;x`, `/api/v1/auth/login%00`, `/api/v1/auth/login%20`, `/api/v1/auth/logout?/api/v1/auth/login`,
  `/api/v1/activation/abc%2Fextra`, `/api/v1/activation/a%2F..%2F..%2Fauth%2Flogout`, `/api/v1/activation/../auth/logout`,
  `/api/v1/activation//`, `/api/v1/activation/%2F`, `/api/v1/anonymized-data/./retrieve`.
- Exempt, and routed to the same exempt route: `/api/v1/auth%2Flogin` and `/api/v1/auth/%6Cogin` (decode to
  `/api/v1/auth/login`), `/api/v1/auth/login?x=1` (query is not in the path), `/api/v1/activation/..`,
  `/api/v1/activation/abc;x`, `/api/v1/activation/abc%0A` (all `{token}` values of the activation route).
  `%2F` is decoded before the middleware, so `[^/]+` never sees an encoded slash.
- Trailing slash: `/api/v1/auth/login/` and `/api/v1/anonymized-data/retrieve/` get a 307 to the exact path.
  `/api/v1/auth/login%3Fx` → 404.

### Mutations (plugin in the scratchpad, no source edited)

- `/api/v1/auth/logout` added to `_CSRF_EXEMPT_PATHS`: 4 failed (table, exempt-routes inventory,
  every-other-route-403, constants).
- Extra pattern `/api/v1/accounts/[^/]+/resend-activation`: the same 4 failed.
- Prefix matching restored in `is_csrf_exempt` (without the password-reset entry): 14 failed (12 sibling cases,
  table, new-route test). The developer's 16 includes the password-reset prefix.
- New `POST /api/v1/activation/resend` (matches the pattern): 2 failed (exempt-routes inventory, every-other-403).
- The same route nested two routers deep: 2 failed.
- New `DELETE /api/v1/widgets/{wid}` and a `POST` module route mounted through `RouterRegistry` as
  `dicom-viewer`: pass (both enforced); the walker lists both.
- Walker against `app.openapi()`: 23 unsafe operations, none missing, none extra. No mounted sub-apps exist.

### Verification run

- `uv run pytest tests/api/test_csrf_enforcement.py tests/api/test_activation_router.py tests/api/test_anonymized_retrieve.py`: 59 passed.
- `uv run pytest modules/dicom_viewer/tests`: 25 passed.
- `uv run pytest --cov=app --cov-fail-under=85`: 1334 passed, 6 skipped, 94.15 %.
- `uv run ruff check .`: clean. `uv run black --check .`: 255 files unchanged.
- `uv run mypy app/core/security_middleware.py`: clean. `uv run mypy app`: clean (132 files) at review time.
- `traceability-check` (TASK-139, TS-011, PRB-003, SR-031 and their neighbours, 411 records): 0 errors,
  10 W5 warnings (approved RISK/ADD/TP records linking to `in_review` SOUP and TS, pre-existing or cleared
  by this approval). PRB-003 `resolved` has the incoming `resolves` from CR-004 (E9).

