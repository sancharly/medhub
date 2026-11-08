---
id: "TASK-207"
type: task
title: "Close the TASK-206 QA follow-ups: fast enqueue, case-insensitive redaction, enqueue warnings"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-07"
updated: "2026-11-07"
links:
  - target: "SR-043"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-206"
    relation: relates_to
  - target: "PRB-013"
    relation: relates_to
tags: ["security", "logging", "workers", "cr:CR-004", "control:design"]
---

# TASK-207 — Close the TASK-206 QA follow-ups: fast enqueue, case-insensitive redaction, enqueue warnings

- **Software items / units:** SI-WORKER (ADD-017), SI-DEPLOY reverse proxy (ADD-026), SI-IDENTITY
  (ADD-008), SI-APPT (ADD-010).
- **PRB:** none resolved. Touches PRB-013, which **stays `open`**. **CR:** CR-004 (D-18).
- **Depends on:** TASK-206 (committed, 75fbd6d). No open task; the working tree was clean on 2026-11-07.
  Runs before TASK-201 and TASK-202.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** S (human's decision, D-18). Every code change is a few lines; by file count alone it would
  be M (4 source files, 2 scripts, 5 test files).
- **Needs:** a Docker daemon for the started-stack check.

## Objective

The two MEDIUM and five LOW findings of the TASK-206 QA review, plus the silent enqueue sites:

- **(a) Finding 1:** `.delay()` can block a request for about 20 s inside its open transaction, because
  `RedisBackend.on_task_call` retries the result store 20 times. Measured with Redis stopped: 19.88 s, and
  0.93 s with `task_ignore_result=True`. `retry=False` does not help.
- **(b) Finding 2:** the redaction and the activation locations are case-sensitive, but React Router matches
  without case, so `/Activation/<token>` is a working URL that is logged verbatim, sends no
  `Referrer-Policy`, and writes an upstream error entry. SR-043 AC 4's general sentence does not hold for it.
- **(c) PRB-013 call sites:** the two `except Exception: pass` at the enqueue calls stay silent. Silence is
  what hid the critical PRB-071.
- **(d) Findings 3 to 7:** the 500 record's template, the Referer limit, the multipart parser's 400, the width
  of `log-secrets-check.sh`, and the record gaps.

## Implementation detail

### (a) No result store on dispatch

- Add `task_ignore_result=True` to `celery_app.conf.update` (`backend/app/workers/celery_app.py:50`). Keep the
  `backend=` argument: only the per-task result write and the call-time subscription go.
- **Checked on 2026-11-07, no code reads a result:** the five `.delay()` calls
  (`identity/account_service.py:109`, `identity/activation.py:144`, `identity/erasure.py:140`,
  `identity/lifecycle.py:69`, `appointments/service.py:69`) discard the return value, and `AsyncResult`,
  `.ready()`, `.get(timeout` and `.result` do not occur in `backend/app`, `backend/modules` or `backend/tests`.
  The static test below keeps it that way.
- It also stops the `celery-task-meta-*` keys. A task failure is still in the worker's log.
- `identity/erasure.py:135` says "not blocking"; after this it is true. PRB-072's stall is unrelated: QA
  reproduced it with this setting.

### (b) Case-insensitive activation matching

In `infra/reverse-proxy/nginx.conf`, change `~` to `~*` at four places: the two `map` entries (`:10`, `:11`) and
the two locations (`:52`, `:64`). Nothing else in the file changes.

- `$medhub_log_path` then holds the fixed redacted text for every case variant, and the variants reach the
  activation locations: `error_log crit`, and `Referrer-Policy: no-referrer` for the page.
- **Behaviour change:** `/API/V1/ACTIVATION/x` now goes to the backend (404 problem+json; FastAPI routes are
  case-sensitive) instead of the frontend (the SPA). No MedHub URL uses that form.
- `~* ^/activat` also matches `/ACTIVATE…`. No other SPA route starts with those letters.

### (c) Enqueue failures logged

At both sites, replace `pass` with one warning, on the pattern of `identity/erasure.py:142`, and keep the
best-effort behaviour (the request still succeeds):

- `backend/app/identity/lifecycle.py:69`:
  `logger.warning("Failed to enqueue session-kill propagation for account %s", account_id)`
- `backend/app/appointments/service.py:69`:
  `logger.warning("Failed to enqueue notification for appointment %s", appointment.id)`

Ids only: no `exc_info`, because a broker exception can carry the connection URL. Neither module has a logger
today, so each gets `import logging` and `logger = logging.getLogger(__name__)`. SR-023 relevance: a failed
session-kill enqueue also means no `SESSION_KILL_PROPAGATED` audit row, and this warning is the only signal.

Out of scope: `lifecycle.py:69` stays best effort (`invalidate_all` runs first, so SR-034 AC 2 holds), and the
retrieval-code loss at `erasure.py:140` stays with PRB-013 and TASK-141.

### (d) Findings 3 to 7

- **Finding 3 (500 template):** no code change. On the real app the record says `/activation/{token}`, with no
  `/api/v1`, and the endpoint is identifiable. Add a test through the real app and correct the records (see
  Records).
- **Finding 4 (Referer limit):** record it (see Records). No code change. **Human decision 2026-11-07 (CR-004 D-19):**
  a hand-crafted Referer or a token in another path's query string can reach the proxy error log on an upstream
  failure or a 413; accepted as a residual against SR-043 AC 4, listed for the release's residual-anomaly
  evaluation. SR-043's text is not edited (it is approved); TASK-201 carries the note.
- **Finding 5 (multipart 400):** accept it. Names around 8 KB and over are refused by the multipart parser
  with a plain 400 (`application/json`, "There was an error parsing the body"), and 2 MB gives 413. Nothing is
  stored and the user sees a reason, so no code change; AC-2's wording in TASK-206 and TC-007.11 say so.
- **Finding 6 (`infra/log-secrets-check.sh`):** widen it.
  - Send the activation `POST`, with a wrong and a right body.
  - Run an erasure and a retrieval, and add the retrieval code to the known values.
  - Add to the known values, read from `infra/.env` and never printed: the database passwords, the object-store
    secret key, `AT_REST_ENCRYPTION_KEY` and the object-store SSE key.
  - The object-store **access** key stays out, and so does the `object-store` service: the store logs that key
    itself at start-up (`auth_credentials.go`), and its log is not in SR-043 AC 4's list.
  - The report still prints counts only.
- **Finding 7 (record gaps):** see Records. ADD-017's missing `_bind_celery_app()` goes to TASK-201, as all ADD
  edits do.

## Tests (write first)

- `backend/tests/workers/test_celery_results.py` (new; import `celery_app` inside the tests, as
  `test_celery_start_up.py` explains):
  - `test_task_ignore_result_is_set`;
  - `test_no_code_reads_a_task_result`: a text scan of `backend/app` and `backend/modules` for `AsyncResult` and
    for a `.delay(` whose value is used;
  - `test_enqueue_with_unreachable_redis_fails_fast`: a scratch `Celery` app with this configuration and broker
    and backend on a closed port; `.delay()` raises or returns within 5 s (19.88 s before).
- `infra/tests/test_proxy_access_log.py`:
  - `test_the_map_redacts_the_activation_paths` and `test_both_activation_locations_set_the_error_log_to_crit`
    (lines 64 to 75) expect `~*`;
  - new `test_activation_matching_ignores_case`: no `~ ^/` remains on an activation pattern, in the map or a
    location.
- `infra/smoke-test.sh` section 14: add `/ACTIVATION/$MARKER`, `/Activation/$MARKER`, `/API/V1/ACTIVATION/$MARKER`
  and `/api/v1/Activation/$MARKER`; the page variant answers `Referrer-Policy: no-referrer`.
- `infra/log-secrets-check.sh` step 3: the upstream-error requests also use a case variant (finding 2), plus the
  finding-6 widening.
- `backend/tests/identity/test_lifecycle.py`: `test_deactivate_logs_a_warning_when_enqueue_fails` (`.delay`
  raises; the deactivation still succeeds; one WARNING naming the account id).
- `backend/tests/appointments/test_notify.py`: `test_create_logs_a_warning_when_enqueue_fails` (same, with the
  appointment id; the record holds no e-mail address or name).
- `backend/tests/api/test_error_logging.py`: `test_real_app_500_logs_the_router_template`: through
  `create_app()` with the activation service patched to raise, the record contains `/activation/{token}` and
  not the token.

Negative controls (record the results in this task):

1. Remove `task_ignore_result`: `test_task_ignore_result_is_set` and the fast-fail test fail.
2. Put `~` back on any one of the four patterns: `test_activation_matching_ignores_case` fails; on a started
   stack, the smoke check fails.
3. Put `pass` back at either site: the warning tests fail.

## Acceptance criteria

- [x] **AC-1 (finding 1):** `task_ignore_result` is set, no code reads a result, and a `.delay()` with Redis
      unreachable ends within 5 s
      (`backend/tests/workers/test_celery_results.py`).
- [x] **AC-2 (SR-043 AC 4; finding 2):** every case variant of the activation paths is redacted in the access
      log, takes the activation locations, and the page variant sends `Referrer-Policy: no-referrer`
      (`infra/tests/test_proxy_access_log.py::test_activation_matching_ignores_case`, `infra/smoke-test.sh`
      section 14; started-stack check below).
- [x] **AC-3 (SR-043 AC 1, SR-023; PRB-013 call sites):** a failed enqueue at both sites writes one WARNING with
      the id only, and the request still succeeds
      (`backend/tests/identity/test_lifecycle.py::test_deactivate_logs_a_warning_when_enqueue_fails`,
      `backend/tests/appointments/test_notify.py::test_create_logs_a_warning_when_enqueue_fails`).
- [x] **AC-4 (SR-043 AC 4; findings 3 to 7):** the 500 record's real form is tested
      (`backend/tests/api/test_error_logging.py::test_real_app_500_logs_the_router_template`);
      `infra/log-secrets-check.sh` covers the activation `POST`, the retrieval code and the keys, and passes; the
      records below are corrected.

## Verification

```sh
cd backend && uv run pytest tests/workers tests/identity/test_lifecycle.py tests/appointments/test_notify.py tests/api/test_error_logging.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
cd backend && uv run pytest ../infra/tests -v
```

**Started-stack check** (b), short. Use a scratch Compose project; `log-secrets-check.sh` is destructive.

1. `docker compose -f infra/docker-compose.yml up -d --build`; `nginx -t` is clean in `reverse-proxy`.
2. `infra/smoke-test.sh` passes, including the variants.
3. `curl -skD - -o /dev/null https://localhost/Activation/<marker>` shows `Referrer-Policy: no-referrer`; the
   access-log line for it reads `/activation/[redacted]`.
4. A real activation through `/activation/<token>` still works (the exact form is unaffected).
5. `infra/log-secrets-check.sh` passes; record its counts.

## Records

- **TS-017** 1.2 → 1.3 (approval cleared, `in_review`): TC-017.4 adds the case variants and the widened script,
  and states the 500 record's real form `/activation/{token}`; new TC-017.6 enqueue failure logged with the id only
  (AC-3).
- **TS-003** 1.5 → 1.6 (`in_review`): new TC-003.7 dispatch does not wait on a result store (AC-1).
- **TS-007** 1.6 → 1.7 (`in_review`): TC-007.11 records the multipart parser's plain 400 at about 8 KB and over.
- **SOUP-014** (`in_review`): `task_ignore_result` relied on. **SOUP-024** (`in_review`): `~*` in `map` and
  `location`.
- **RISK-005** (`in_review`): add TASK-207 to the "No credential or secret in operational or proxy logs" row.
  **RISK-007** (`in_review`): one control row, "Dispatch does not wait on a result store (`task_ignore_result`) |
  Design | TASK-207 | TS-003 TC-003.7". Residuals unchanged.
- **PRB-068** (stays `resolved`): the Resolution's `/api/v1/activation/{token}` becomes `/activation/{token}`;
  bump the version.
- **PRB-013** 1.0 → 1.1 (stays **`open`**): current line numbers (`lifecycle.py:69`, `appointments/service.py:69`),
  both now logged by TASK-207. What remains open: `erasure.py:140`, surfacing failures, and failing the request
  where the side effect is security-relevant (TASK-141).
- **TASK-206** 1.4 → 1.5. It is `approved`, and these are content corrections, so its approval is cleared
  (`in_review`) and QA re-approves it with this task (CR-004 Boundaries):
  - finding 3: the template wording at the Implementation and Tests sections;
  - finding 4: in Accepted residuals, replace the struck-through line's "closes it" with the limit: true of
    conforming browsers only. A token-bearing `Referer`, or a query string on another path, sent by hand to a
    non-activation location during an upstream failure or a 413 is written to the proxy error log. No MedHub URL
    or browser flow produces these; QA did not capture a real browser's requests;
  - finding 5: AC-2's wording accepts the parser's plain 400;
  - finding 7: the header and Objective name PRB-071; `implements` links to SR-034, SR-024 and SR-035, which AC-6
    cites; the Definition of Done says TS-003 1.5.
- **TASK-201:** add one carried line: ADD-017 describes `_bind_celery_app()` (finding 7).

## Definition of Done

- [x] AC-1 to AC-4 met; negative controls and started-stack steps recorded.
- [x] Backend suite with coverage ≥ 85 %, `infra/tests`; `ruff`, `mypy` clean.
- [x] TS-003, TS-007, TS-017, SOUP-014, SOUP-024, RISK-005, RISK-007 and TASK-206 `in_review`; PRB-013 still `open`.
- [x] On QA approval: this task, TASK-206 and the three TS `approved`.
- [x] `traceability-check` shows no error for TASK-207 and the records above.
- [x] `graphify update .` run after the code change (also closes TASK-206's unticked item).

## Implementation notes and verification results (Software Developer role, 2026-11-07)

Counts only; no token or secret was printed.

**Files changed.** `backend/app/workers/celery_app.py` (`task_ignore_result=True`), `backend/app/identity/lifecycle.py`
and `backend/app/appointments/service.py` (logger and one WARNING each, id only, no `exc_info`),
`infra/reverse-proxy/nginx.conf` (`~` to `~*` at the four places, nothing else), `infra/smoke-test.sh` (section 14),
`infra/log-secrets-check.sh`; tests `backend/tests/workers/test_celery_results.py` (new), `test_lifecycle.py`,
`test_notify.py`, `test_error_logging.py`, `infra/tests/test_proxy_access_log.py`.

**Suites.** Backend `pytest --cov=app --cov-fail-under=85`: 1543 passed, 6 skipped, coverage 94.51 % (before: 1537 / 94.50 %).
`modules/dicom_viewer`: 25 passed. `infra/tests`: 110 passed. `ruff check`, `black --check`, `mypy app` clean. Frontend not
touched, not run. OpenAPI untouched. `graphify update .` run.

**Negative controls.**

1. `task_ignore_result` removed: `test_task_ignore_result_is_set` and `test_enqueue_with_unreachable_redis_fails_fast`
   fail (19.4 s run); the third test still passes. Restored.
2. `~` put back on the `map` entry for the API path: `test_the_map_redacts_the_activation_paths` and
   `test_activation_matching_ignores_case` fail (2 failed, 108 passed). On a started stack with `~` back on
   `location ~ ^/activat`: smoke section 14 fails (77 passed, 1 failed: "page variants answer Referrer-Policy: no-referrer, header
   on 0 of 2"). Restored; 78 passed.
3. `pass` put back at both sites: `test_deactivate_logs_a_warning_when_enqueue_fails` and
   `test_create_logs_a_warning_when_enqueue_fails` fail (2 failed, 10 passed). Restored.

**Started stack** (scratch project `task207`, scratch copy of the tree, its own env file; the real `infra/.env` was not used).
`up -d --build`; `nginx -t` clean. `smoke-test.sh`: 78 passed, 0 failed, including the four case variants and the
`Referrer-Policy: no-referrer` check of `/ACTIVATION/` and `/Activation/` (2 of 2). `curl` of `/Activation/<marker>`: 1
`Referrer-Policy: no-referrer`, the access-log line reads `/activation/[redacted]`, 0 lines hold the marker. The exact form
`/activation/<token>` still answers the page (200) and activates an account through the `POST` (204).
`log-secrets-check.sh`: 38 passed, 0 failed (activation `POST` 400 and 204; erasure and retrieval 200; upstream error
on the lower-case and the case-variant path 504 each, 1 control error line, 0 activation lines; 12 known values over 6 service
logs, 0 matches each).

**Deviations and notes.**

- The two new warning tests re-enable their logger with `monkeypatch`: an Alembic `fileConfig` in another test leaves
  existing loggers disabled, and the first full-suite run failed on it (they passed alone).
- `test_enqueue_with_unreachable_redis_fails_fast` takes `task_ignore_result` from the real `celery_app`, so the control
  in point 1 fails it; the scratch app is otherwise independent.
- `log-secrets-check.sh` reads the secrets from `ENV_FILE` (default `infra/.env` beside the script) into files in its
  temporary directory; the report labels them "env ..." and prints counts only. The erasure runs in the backend container
  with the application's `ErasureService` as the account's owner, because the API never returns the retrieval code; the
  e-mail task is really enqueued, and the worker's SMTP attempt fails in the scratch stack (no relay).
- TASK-206 acceptance checkboxes were left ticked when the record returned to `in_review`; QA ticks or unticks on
  re-approval.
- Records not in the task list but changed: TASK-201 (carried lines) and CR-004 1.18 (D-19, change-analysis, coverage and
  TS rows).

## QA review (2026-11-08): APPROVED

TASK-206 review findings 1 to 7 are closed. No new finding blocks. Counts only below; no value was printed.

**Closed findings**
- 1 (MEDIUM): `task_ignore_result=True`. Started stack, broker and result store pointed at a closed port by a scratch
  `celery_app.py`, sessions healthy: create account 0.73 s, appointment 0.66 s, deactivation 0.66 s (were 19.28,
  19.27, 19.27 s); one id-only WARNING each, 0 with a URL. `.delay()` from a worker thread with Redis stopped: 0.94 s
  (was 19.88 s). 0 `celery-task-meta-*` keys after a dispatch.
- 2 (MEDIUM): `~*` in the four places. `/ACTIVATION/`, `/Activation/`, `/API/V1/ACTIVATION/` and
  `/api/v1/Activation/` with a marker: 0 log lines, with upstreams up and with the backend or frontend stopped. Page
  variants send `Referrer-Policy: no-referrer` and the three security headers. `nginx -t` clean.
- 3 to 7: the records now match the code and the stack. The real-app 500 test passes. `log-secrets-check.sh` covers the
  activation `POST`, the erasure and retrieval, a case variant and 13 known values. The multipart 400 is accepted in
  AC-2 and TC-007.11. ADD-017 is carried to TASK-201. PRB-071 and the SR-034, SR-024 and SR-035 links are in TASK-206.
- D-19 is worded as reproduced. A hand-sent token `Referer` to `/api/v1/me`, `/healthz` or `/assets/x.js`, or a token
  in `/api/v1/patients?token=`, during an upstream failure: 1 error-log line each. `POST /api/v1/foo?token=` with a
  413: 1 line. Nothing else.

**Observations (not findings)**
- The phrase "the router prefix, not/without `/api/v1`" in `test_error_logging.py` and PRB-068 reads backwards. The
  template is the route path *without* the router prefix. The tested string `/activation/{token}` is right.
- `/activate/<k>`, `/activation;<k>`, `/activation\<k>`, `/activation%0A/<k>` and `/activation%09/<k>` are logged with the
  marker. None is a route the SPA serves for the token, so none is a working activation URL. A browser turns `\` into
  `/` before sending.

**Verification run**
- `pytest tests/workers tests/identity/test_lifecycle.py tests/appointments/test_notify.py tests/api/test_error_logging.py`:
  56 passed. `infra/tests`: 110 passed. `ruff`, `black --check`, `mypy app` clean.
- Mutants, 12 of 12 killed:
  - `task_ignore_result` removed, or set to `False` (each 2 tests fail, 19.5 s);
  - `pass` back at either site;
  - `exc_info=True` at either site;
  - raw path in the 500;
  - `~` on each of the four patterns;
  - a `[aA]` character class instead of `~*`.
- Scratch project `qa207` (scratch tree and env): smoke 80 passed, 0 failed. `log-secrets-check.sh` 38 passed, 0 failed.
- Teardown: `down -v --remove-orphans`, `qa207-*` images removed, no prune. Container, volume, network and image lists
  equal to the start; `infra/.env` sha256 unchanged (`a4933b8c82d6f81e...`).
- `traceability-check` on TASK-206, TASK-207, TS-003, TS-007, TS-017, PRB-013, PRB-068 to PRB-074, CR-004 and TASK-201:
  0 errors.

## Version history

- 1.0 (2026-11-07) — Created by the Software Architect role for the TASK-206 QA follow-ups (CR-004 D-18). `draft`.
- 1.1 (2026-11-07) — Built by the Software Developer role; D-19 recorded (human decision: the Referer and query-string case is an accepted residual); results and deviations added. `in_review`.
- 1.2 (2026-11-08) — QA review: APPROVED. `in_review → approved`; AC-1 to AC-4 ticked. TASK-206 re-approved; TS-003, TS-007, TS-017 approved; PRB-068 to PRB-071 stay `resolved`.
