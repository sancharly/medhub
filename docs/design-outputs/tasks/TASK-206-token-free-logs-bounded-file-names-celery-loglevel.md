---
id: "TASK-206"
type: task
title: "Keep the activation token out of logs, bound attachment names, honour Celery's log level"
status: approved
version: "1.5"
author: "Carlos Santiago Liceras"
created: "2026-11-07"
updated: "2026-11-07"
links:
  - target: "SR-043"
    relation: implements
  - target: "SR-033"
    relation: implements
  - target: "SR-013"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "SR-034"
    relation: implements
  - target: "SR-024"
    relation: implements
  - target: "SR-035"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "RISK-006"
    relation: mitigates
  - target: "RISK-009"
    relation: mitigates
  - target: "PRB-068"
    relation: relates_to
  - target: "PRB-069"
    relation: relates_to
  - target: "PRB-070"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-138"
    relation: relates_to
  - target: "TASK-204"
    relation: relates_to
  - target: "TS-017"
    relation: relates_to
  - target: "TS-007"
    relation: relates_to
  - target: "SOUP-014"
    relation: relates_to
  - target: "SOUP-024"
    relation: relates_to
  - target: "PRB-071"
    relation: relates_to
tags: ["security", "privacy", "logging", "attachments", "cr:CR-004", "control:design"]
---

# TASK-206 — Keep the activation token out of logs, bound attachment names, honour Celery's log level

- **Software items / units:** SI-API `U-API-ErrorHandler`, `U-API-Routers` (ADD-005); SI-ATTACH
  `U-ATT-Upload` (ADD-012); SI-WORKER logging (ADD-017); SI-DEPLOY reverse proxy and frontend image
  (ADD-026); SI-FE-CORE attachment upload (ADD-020).
- **PRBs:** PRB-068 (major), PRB-069 (minor), PRB-070 (major), PRB-071 (critical). **CR:** CR-004 (D-14, D-16, D-17). Also the TASK-138 QA follow-up
  (`--loglevel`) and two carried TASK-204 QA items (findings 2 and 3).
- **Depends on:** TASK-138 (be9fb56) and TASK-204 (33daae8), both committed. No open task.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** L (about 10 source and configuration files including `backend/app/workers/email_tasks.py`, 2 new
  infra scripts or checks, 9 test files). It is one task by the human's
  decisions (D-14, D-16). It is built in three slices, each green before the next: **A** logs and the
  activation link (PRB-068, PRB-070), **B** names (PRB-069 and the TASK-204 items), **C** `--loglevel`.
- **Needs:** a Docker daemon for the real-DB tests and the started stack.

### No shared files with TASK-142's remaining fix

TASK-142's working-tree files on 2026-11-07 (`git status`): `frontend/src/app/*`,
`frontend/src/core/nav/*`, `frontend/src/auth/RequireAuth.tsx` and its tests,
`frontend/src/api/queryClient.ts` and its test, TS-002, PRB-014, PRB-067. TASK-206 touches none of
them. Its only frontend files are `frontend/nginx.conf` and `frontend/src/core/clinical/AttachmentUpload.tsx`
with a new test beside it. TASK-142 has since been committed (3eef9fb), so `frontend/src/app/App.tsx`,
`frontend/src/core/nav/routeRoles.ts` and `frontend/src/core/nav/routeRoles.test.ts` are free; slice A reads
them (below) and needs no change to them.

## Objective

- **SR-043 AC 4 (new, SR-043 1.1, approved 2026-11-07):** no credential or secret (activation
  token, retrieval code, session and CSRF tokens, passwords, API keys, encryption keys) appears in the
  application, worker or scheduler logs, the reverse proxy's or frontend container's access and error logs,
  or any URL, path, query string or Referer they record, on success and error paths. Today the only
  credential that reaches a URL is the activation token (PRB-068 Investigation); session and CSRF tokens
  travel in the `Cookie` and `X-CSRF-Token` headers, and no MedHub log records a request header (no backend
  logger formats headers; nginx's default `combined` format records `$http_referer` and
  `$http_user_agent` only). The design below closes the URL paths and pins the header rule with tests.
- **PRB-068:** no log written by MedHub's own processes contains an activation token: not the backend's
  500 record (`backend/app/api/errors.py:189`), not the reverse proxy's access or error log
  (`infra/reverse-proxy/nginx.conf`, no `access_log` today), not the frontend container's access log
  (`frontend/nginx.conf`). The token forms are `/api/v1/activation/{token}` (the 500 record names it `/activation/{token}`), the SPA page
  `/activation/{token}`, the e-mail link `/activate?token=…`, and any of them as a `Referer`.
- **PRB-069:** an attachment name is bounded when it is stored, and the `Content-Disposition` value is
  bounded whatever is stored, so a download always fits the proxy's 4 KB header buffer.
- **PRB-070:** the e-mailed activation link opens the activation page. Today it is
  `/activate?token=…` (`backend/app/workers/email_tasks.py:97`), which the SPA does not route
  (`frontend/src/app/App.tsx:73` serves only `/activation/:token`), so the user ends on the sign-in page.
- **PRB-071 (added in 1.3, D-17):** the API process enqueues every task on the configured Redis broker, so the
  activation e-mail, the session-kill propagation, the erasure-code e-mail and the appointment notification
  are sent (AC-5, AC-6).
- **TASK-138 QA follow-up:** the worker and beat honour `--loglevel` again, and debug records still pass
  the redaction filter.

## Implementation detail

### A. Activation token out of every log (PRB-068)

**Backend 500 record — route template, not the raw path.**

- In `generic_error_handler` (`backend/app/api/errors.py:187-198`), log the matched route's template:
  `route = request.scope.get("route")`, `path = getattr(route, "path", None) or "<unmatched>"`.
  `logger.exception("Unhandled exception for %s %s", request.method, path)`. For the activation routes
  this logs `/activation/{token}` on the real app (the router prefix, without `/api/v1`; TASK-207 tests it through
  `create_app()`). The synthetic test app below declares the full path.
- Why the template and not a list of token routes to redact: it holds no parameter values at all, so a
  future secret in any path parameter is covered with no list to maintain. The record stays useful: it
  names the method, the endpoint and carries the traceback. The patient or account UUIDs that the raw path
  carried are lost from this one record; the traceback and the request's audit rows still identify the
  case.
- The problem body's `instance` still echoes the raw path to the client that sent it. It is a response, not
  a log, so it is unchanged.
- No other backend log record contains a URL (`grep` of `logger.*` with `url`/`path` in `backend/app`:
  only `errors.py:189`).

**Backend access log stays off, and is pinned.** The image `CMD` (`backend/Dockerfile:24`) has no
`--access-logfile`, so `uvicorn.access` has no handler (TASK-138 QA). An infra test fails if the
Dockerfile or a Compose `command:` ever adds `--access-logfile`, `--access-log` or `--log-config`, so
enabling it becomes a deliberate change that must redact first.

**Reverse proxy — an allow-list log format.** In `infra/reverse-proxy/nginx.conf` (it is included inside
nginx's `http {}` block, so `map` and `log_format` are allowed there):

- `map $uri $medhub_log_path` with regex entries `~^/api/v1/activation/` → `/api/v1/activation/[redacted]`,
  `~^/activation/` → `/activation/[redacted]`, `default $uri`.
- `log_format medhub_redacted escape=json` with only: `$time_iso8601`, `$remote_addr`, `$request_method`,
  `$medhub_log_path`, `$server_protocol`, `$status`, `$body_bytes_sent`, `$request_time`,
  `$upstream_status`. It never uses `$request`, `$request_uri`, `$args`, `$query_string`, `$arg_*`, and
  **no header variable at all** (`$http_*`, `$cookie_*`, `$sent_http_*`, `$upstream_http_*`,
  `$upstream_cookie_*`): no `Referer`, `Cookie` (session and CSRF cookies), `X-CSRF-Token` or
  `Set-Cookie` value can be logged. Query strings are therefore never logged on any path (this covers
  `/activate?token=`), and referrers are never logged (this covers every request made from the
  activation page).
- `access_log /var/log/nginx/access.log medhub_redacted;` in **both** `server` blocks (the port-80
  redirect block also sees the request line).
- Why an allow-list format over `access_log off` on token locations: the access log stays complete for
  every request, including activations, and nothing new can leak by default. `access_log off` would need
  a location per token form and would still log referrers elsewhere.
- **Error log:** nginx writes `request:`, `host:` and `referrer:` into error-log entries and its format
  cannot be changed; it never writes the `Cookie` or `X-CSRF-Token` headers. Two measures:
  1. Two locations that carry the token in their path, `location ~ ^/api/v1/activation/` (same `proxy_*`
     lines as `/api/`) and `location ~ ^/activat` (same as `/`; covers `/activation/…` and the old
     `/activate?…`), each with `error_log /var/log/nginx/error.log crit;`. Confirmed sufficient for the
     upstream-error case of SR-043 AC 4: nginx logs per-request upstream failures (`connect() failed`,
     `upstream timed out`, `upstream prematurely closed connection`, `upstream sent too big header`) at
     level `error`, below `crit`, so none is written for these locations. `crit` and above are process-level
     conditions with no request line. Trade-off: upstream errors on activation requests are not in nginx's
     error log; the backend still logs its own 500s with the route template.
  2. **No Referer carries the token**, so an error entry for any *other* location cannot either: the
     `~ ^/activat` location adds `Referrer-Policy: no-referrer`, so the activation page's own asset and API
     requests send no `Referer`. Because `add_header` in a location replaces the server-level ones, that
     location repeats `Strict-Transport-Security`, `X-Content-Type-Options` and `X-Frame-Options` (all
     `always`). The `~ ^/api/v1/activation/` location needs no policy (JSON responses load no resources).
- `proxy_buffer_size` stays at its default: slice B bounds the header instead.

**Frontend container.** `frontend/nginx.conf` gets `access_log off;` in its `server` block. The reverse
proxy is the access log of record; the frontend container only serves static files behind it. It also
gets `error_log /var/log/nginx/error.log crit;`, for the same reason as above. SOUP-024 (nginx) gains the
relied-on behaviour: `map`, `log_format … escape=json`, per-location `error_log`.

**Activation link: one canonical form, `/activation/<token>` (PRB-070).**

- Change the link in `send_activation_email` (`backend/app/workers/email_tasks.py:97`) to
  `f"{settings.public_base_url}/activation/{activation_token}"`. The token is `secrets.token_urlsafe(32)`
  (`identity/activation.py:40`), safe as a path segment. The resend path uses the same task, so it is fixed
  too.
- Why the path form and not a new `/activate` route: the SPA route, `ActivationPage` and its API calls
  already use it; the log redaction above already covers `/activation/`; and a query string would be one
  more form to keep out of logs and referrers. No release exists (CR-004 A-1), so no link of the old form
  is in a user's mailbox and no compatibility route is needed.
- No change to `frontend/src/app/App.tsx` or `frontend/src/core/nav/routeRoles.ts`. In
  `frontend/src/core/nav/routeRoles.test.ts:13-14` `/activation/:token` is already an exempt public route
  (root element `ActivationPage` only); that stays.
- Tie the two definitions together: a cross-tree test reads the link template in `email_tasks.py` and the
  route in `App.tsx` and fails if they diverge (see Tests).
- The redaction regex `~^/activat` and the map keep covering the old `/activate` form, in case an old link
  is ever followed.

### B. Bounded attachment names and header (PRB-069; TASK-204 QA findings 2 and 3)

**Bound at upload: 255 UTF-8 bytes, 400 otherwise.**

- In `AttachmentService.store` (`backend/app/attachments/service.py`), after authorization and next to the
  size check: if `len(filename.encode("utf-8", "surrogatepass")) > 255`, raise `ValidationProblem` (400,
  `application/problem+json`) with one `ProblemDetail(field="file", rule="filename_max_bytes", message=
  "The file name is longer than 255 bytes.")`. No object is written and no row is created.
- **Human decision (2026-11-07, CR-004 D-16):** the limit is 255 UTF-8 bytes, refused with a 400.
  SR-013 states no length; SR-013 is not changed, and the bound is an input-validation rule within
  SR-013 AC 1.
- Why a 400 and not truncation: the stored name is part of the clinical record (SR-013 AC 2). A silent
  truncation changes it without the user knowing, and two different names could truncate to the same one.
- Why 255 **bytes**: it is `NAME_MAX` on Linux file systems, it keeps the storage key
  (`attachments/{uuid}/{uuid}/{name}`, `service.py:78`) under S3's 1,024-byte limit, and it bounds the
  header (below). It rejects names that some file systems allow: on Windows and macOS a name of more
  than 85 CJK characters (3 bytes each) is legal.
- **Frontend:** `frontend/src/core/clinical/AttachmentUpload.tsx` shows no upload error today (the mutation's
  error is never rendered), so a 400 would be silent. Render the problem's `detail` in an MUI `Alert` under
  the button when the mutation fails. New test `frontend/src/core/clinical/AttachmentUpload.test.tsx`.

**Header budget, for any stored name (existing over-long names still download).** In
`backend/app/api/content_disposition.py`:

- Before encoding, cut the neutralised name to at most 255 UTF-8 bytes at a character boundary, keeping
  the extension (the part after the last `.`, if it is at most 16 characters), so `filename*` is at most
  765 bytes.
- Cut the ASCII fallback to at most 150 characters, keeping the extension in the same way.
- The whole value is then below about 1 KB, far under the 4,042-byte limit QA measured with the default
  4 KB `proxy_buffer_size`, with room for the other response headers. No nginx buffer change is needed.
- Names already stored with more than 255 bytes download, under a shortened name; the content is
  unchanged.

**TASK-204 QA finding 3 — bidi controls.** `_neutralise_controls` also maps the Unicode bidi control
characters (U+061C, U+200E, U+200F, U+202A–U+202E, U+2066–U+2069) to `_`. Not every `Cf` character:
U+200D (zero-width joiner) is part of emoji sequences and must survive. Firefox already replaces U+202E
when saving (TASK-204 QA); Chrome, Safari and Edge were not verified, so the server does it.

**TASK-204 QA finding 2 — address on FAILURE rows.** Add `assert rows[0].ip == "testclient"` to the three
FAILURE tests in `backend/tests/attachments/test_attachment_integrity_persistence.py` (lines 130, 142, 157
on 33daae8; SR-023 AC 6).

### C. Celery `--loglevel` honoured (TASK-138 QA follow-up)

- `configure_logging(level: int | str = logging.INFO)` in `backend/app/core/logging.py` sets the root
  level from the argument (an int, or a level name such as `"DEBUG"`). The API lifespan keeps calling it
  without an argument.
- The `setup_logging` receiver (`backend/app/workers/celery_app.py:32-36`) takes Celery's `loglevel`
  keyword and passes `configure_logging(loglevel or logging.INFO)`.
- The redaction filter sits on the handler, not on a level, so debug records pass it too (SR-043 AC 2).
- SOUP-014 (Celery): replace "the worker's `--loglevel` option is ignored" (`SOUP-014-celery.md:29-33`) with
  the relied-on behaviour: the `setup_logging` signal passes `loglevel`, MedHub applies it.

## Tests (write first)

**Slice A**

- `backend/tests/api/test_error_logging.py` (new):
  - `test_unhandled_exception_logs_route_template_not_token` — a test route `/api/v1/activation/{token}`
    raising inside a synthetic app: the captured record contains `/api/v1/activation/{token}` and not the
    token value; status 500. On the real app the record reads `/activation/{token}`
    (TASK-207 `test_real_app_500_logs_the_router_template`).
  - `test_unhandled_exception_on_unmatched_path_logs_placeholder` — a middleware-level failure with no
    matched route logs `<unmatched>`.
  - `test_unhandled_exception_log_keeps_method_and_traceback`.
- `infra/tests/test_proxy_access_log.py` (new, standard library only, reads the two nginx files, the
  Dockerfile and the Compose file as text, like the other `infra/tests`):
  - every `access_log` in `infra/reverse-proxy/nginx.conf` names `medhub_redacted`, and both `server`
    blocks have one;
  - the `medhub_redacted` format uses none of `$request`, `$request_uri`, `$args`, `$query_string`,
    `$arg_`, `$http_referer`, `$http_cookie`;
  - the `map` redacts `/api/v1/activation/` and `/activation/`;
  - both activation locations set `error_log … crit`;
  - `frontend/nginx.conf` has `access_log off`;
  - no `--access-logfile`, `--access-log` or `--log-config` in `backend/Dockerfile` or any Compose
    `command:`.
  - the `medhub_redacted` format contains no `$http_`, `$cookie_`, `$sent_http_`, `$upstream_http_` or
    `$upstream_cookie_` variable;
  - the `~ ^/activat` location sets `Referrer-Policy "no-referrer" always` and repeats the three
    server-level security headers.
- `infra/smoke-test.sh`: a new non-destructive check. Request `GET /api/v1/activation/SMOKE<random>`,
  `GET /activation/SMOKE<random>` and `GET /activate?token=SMOKE<random>` through the proxy, then
  `docker compose logs` of every service must not contain `SMOKE<random>`; the page response carries
  `Referrer-Policy: no-referrer`. `infra/tests/test_smoke_test_env.py` is extended if it enumerates the
  checks.
- `infra/log-secrets-check.sh` (new, started stack, **destructive**: stops and restarts services; run
  by hand, not in CI). It runs SR-043 AC 4's pass criterion end to end with known values and fails if any
  of them is found in `docker compose logs` of every service (backend, celery-worker, celery-beat,
  reverse-proxy, frontend, db-migrate):
  1. a known activation token (a real account's, issued through the API) used on the API path, the page
     path and the e-mail query form;
  2. one unhandled exception: `docker compose stop postgres`, `GET /api/v1/activation/<token>` → 500, then
     start `postgres`;
  3. one reverse-proxy upstream error: `docker compose stop backend`, `GET /api/v1/activation/<token>` and
     `GET /activation/<token>` with a page `Referer` → 502 (or the SPA), then start `backend`;
  4. sign in as a seeded test user (credentials from the project's seed or example configuration), take the
     session and CSRF cookie values, and make authenticated requests including one state-changing request
     with `X-CSRF-Token`;
  5. `grep -F` each known value (activation token, session token, CSRF token, the test password) over the
     logs: zero matches.

**Slice B**

- `backend/tests/api/test_content_disposition.py`: `test_value_is_bounded_for_any_name` (255 × U+FDFA,
  10,000 CJK, 10,000 emoji: value ≤ 1,024 bytes, extension kept in both parameters);
  `test_fallback_cut_to_150_keeping_extension`; `test_filename_star_cut_at_character_boundary`
  (decodes as valid UTF-8); `test_bidi_controls_mapped_to_underscore`; `test_zero_width_joiner_kept`.
  The TASK-204 worked-examples table still passes unchanged.
- `backend/tests/attachments/test_attachment_upload.py`: `test_filename_over_255_bytes_is_rejected_with_400`
  (no `put_object`, no row); `test_filename_of_exactly_255_bytes_is_accepted`.
- `backend/tests/api/test_attachments_router.py`: upload of a 256-byte name answers 400
  `application/problem+json` with `errors[0].rule == "filename_max_bytes"`; download of an attachment whose
  stored name is 255 × U+FDFA answers 200 with a header ≤ 1,024 bytes.
- `backend/tests/attachments/test_attachment_integrity_persistence.py`: the three `ip` assertions
  (finding 2).
- `frontend/src/core/clinical/AttachmentUpload.test.tsx` (new): a failed upload shows the problem's
  `detail`; a successful one shows no alert.

**Slice C**

- `backend/tests/workers/test_celery_logging_level.py` (new): the receiver called with `loglevel=10`
  sets the root level to DEBUG; with no `loglevel`, INFO; a DEBUG record carrying an e-mail address in a
  field is emitted redacted. `backend/tests/test_log_redaction.py` unchanged and green.

**Slice A, activation link (PRB-070)**

- `backend/tests/workers/test_email_tasks.py`: `test_activation_email_link_uses_the_activation_route` —
  `send_activation_email` run with a mocked SMTP sender and `PUBLIC_BASE_URL=https://medhub.example`;
  the sent body contains `https://medhub.example/activation/<token>` and no `?token=`.
- `infra/tests/test_activation_link_route.py` (new, text only): the link template in
  `backend/app/workers/email_tasks.py` is `/activation/{…}`, and `frontend/src/app/App.tsx` has
  `<Route path="/activation/:token"`. Fails if either side changes alone.
- `frontend/src/core/nav/routeRoles.test.ts` unchanged and green (`/activation/:token` exempt).

**Negative controls** (record the results in this task):

1. On be9fb56 / 33daae8: `test_unhandled_exception_logs_route_template_not_token` fails (token in the
   record); the new infra test fails (no `access_log`); the bounded-value tests fail (6,927 bytes for
   255 × U+FDFA); the 400 test fails (201).
2. Put `$request` back in `medhub_redacted`: the infra test fails. Remove `access_log off` from
   `frontend/nginx.conf`: the infra test fails.
3. Remove the receiver's argument: the DEBUG-level test fails.
4. On 3eef9fb: `test_activation_email_link_uses_the_activation_route` and
   `test_activation_link_route.py` fail (`/activate?token=`).

## Acceptance criteria

- [x] **AC-1 (SR-043 AC 4 (new, SR-043 1.1, approved 2026-11-07); SR-043 AC 2; SR-033; PRB-068):** SR-043
      AC 4's pass criterion holds: after the activation flow with a known activation token on the API path,
      the page path and the e-mail query form, one unhandled exception, one reverse-proxy upstream error,
      and authenticated requests with a known session token and CSRF token, none of those values is in the
      application, worker, scheduler, proxy or frontend-container logs (`infra/log-secrets-check.sh`,
      started stack). Supporting tests: the backend's 500 record names the route template, never the raw
      path, and keeps the traceback (`backend/tests/api/test_error_logging.py`); the proxy format logs no
      request line, query string or header variable, the activation paths are redacted, their error log is
      at `crit` and the activation page sends no Referer, the frontend container logs no access, and no
      backend access log can be enabled (`infra/tests/test_proxy_access_log.py`); the non-destructive
      regression on every smoke run (`infra/smoke-test.sh` token check).
- [x] **AC-2 (SR-013 AC 1, AC 3; SR-023 AC 2; PRB-069):** an upload whose name is longer than 255 UTF-8
      bytes is refused with 400 and nothing is stored, and the user sees the reason (problem+json from the service check;
      names around 8 KB and over are refused first by the multipart parser with a plain 400, `application/json`,
      "There was an error parsing the body", and 2 MB gives 413: accepted, TASK-207); the
      `Content-Disposition` value is at most 1,024 bytes for any stored name, with the extension kept, so
      an over-long name stored earlier still downloads
      (`backend/tests/attachments/test_attachment_upload.py`,
      `backend/tests/api/test_content_disposition.py`, `backend/tests/api/test_attachments_router.py`,
      `frontend/src/core/clinical/AttachmentUpload.test.tsx`; started-stack step 4 below).
- [x] **AC-3 (SR-023 AC 6; SR-013 AC 3; TASK-204 QA findings 2, 3):** the FAILURE-row tests assert the
      client address, and bidi control characters are `_` in both header parameters while U+200D is kept
      (`backend/tests/attachments/test_attachment_integrity_persistence.py`,
      `backend/tests/api/test_content_disposition.py::test_bidi_controls_mapped_to_underscore`,
      `::test_zero_width_joiner_kept`).
- [x] **AC-4 (SR-043 AC 2; TASK-138 QA follow-up):** `--loglevel` sets the worker's and beat's root level,
      and debug records are still redacted (`backend/tests/workers/test_celery_logging_level.py`;
      started-stack step 5).
- [x] **AC-5 (SR-033 AC 1, AC 3, AC 7; PRB-070, PRB-071):** the activation e-mail, first or resent, is sent
      by the worker and links to `/activation/<token>`, the route the app serves; the two definitions cannot
      diverge silently (`backend/tests/workers/test_email_tasks.py::test_activation_email_link_uses_the_activation_route`,
      `infra/tests/test_activation_link_route.py`, `frontend/src/core/nav/routeRoles.test.ts`); on the shipped
      stack, with no broker override, a real e-mail reaches the SMTP catcher, its link renders the activation page
      in a browser, activates a new account and signs in, and its token appears in no log (started-stack step 3).
- [x] **AC-6 (SR-033 AC 7, SR-034 AC 2, SR-024, SR-035; PRB-071):** every task the API dispatches goes to the
      configured Redis broker, from a sync route's worker thread: the API lifespan sets the configured Celery app as
      the process default (`backend/tests/workers/test_api_celery_broker.py`: activation e-mail, session-kill,
      erasure-code and appointment tasks); on the started stack a deactivation reaches the worker.

## Verification

```sh
cd backend && uv run pytest tests/api/test_error_logging.py tests/api/test_content_disposition.py tests/api/test_attachments_router.py tests/attachments tests/workers tests/test_log_redaction.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
cd backend && uv run pytest ../infra/tests -v
cd frontend && npm run typecheck && npm test -- --run src/core/clinical src/core/nav
```

The real-DB tests need Docker. No OpenAPI change: the 400 uses the existing `ValidationProblem`
schema (check `git diff backend/openapi/openapi.json` is empty after an export).

**Started-stack check** (needed: PRB-068 is about the proxy's and containers' real logs, and PRB-069 was
seen only through the proxy). Recorded in this task:

1. `docker compose -f infra/docker-compose.yml up -d --build` from the template (DEPLOY.md).
2. `infra/smoke-test.sh` passes, including the new token check; then `infra/log-secrets-check.sh` passes
   (SR-043 AC 4 pass criterion, AC-1); record its output.
3. **Activation through a real e-mail (AC-5, AC-1).** Create an account as an administrator; take the
   e-mail from the configured relay (a local SMTP catcher on the started stack); open its link in a
   browser through the proxy; the activation page appears (not the sign-in page); set a password; sign in
   with it. Then `docker compose logs` of every service contains neither the token nor any URL with it.
   This is the started-stack confirmation PRB-070 defers to this task.
4. As a doctor with consent, through the proxy: upload a name of 256 bytes → 400 and the alert in the
   UI; upload 85 CJK characters + `.txt` (258 bytes) → 400; upload 84 CJK + `.txt` → 201 and download → 200.
   For an over-long name stored before this task, insert a row directly (255 × U+FDFA, object copied from
   an existing attachment) and download it through the proxy → 200, identical bytes, header ≤ 1,024 bytes.
5. Restart `celery-worker` with `--loglevel=debug` (Compose override): debug records appear, and an e-mail
   task's debug output contains no address. Restore `--loglevel=info`.

## Records

- **TS-017** 1.1 → 1.2 (content change: approval cleared, `in_review`): TC-017.4 SR-043 AC 4 pass
  criterion (`infra/log-secrets-check.sh`, `infra/tests/test_proxy_access_log.py`,
  `backend/tests/api/test_error_logging.py`, smoke token check; AC-1); TC-017.5 `--loglevel` honoured and
  redacted (AC-4). `verifies` SR-043 (now including AC 4); adds `verifies` SR-033.
- **TS-007** 1.5 → 1.6 (`in_review`): TC-007.11 name bounded at upload and header bounded for any name
  (AC-2); TC-007.6 pass criterion adds the client address; TC-007.9 adds the bidi case (AC-3).
- **ADD-012** (`U-ATT-Upload` validates the name length), **ADD-017** (worker logging level),
  **ADD-026** (proxy and frontend logging): each a short revision, `in_review`.
- **RISK-005** (`in_review`, 1.3): not edited at planning. The developer adds one control row in this
  task's commit: "No credential or secret in operational or proxy logs: route templates in the backend
  error log; allow-listed proxy log format with no request line, query string or header; activation
  locations' error log at `crit` and `Referrer-Policy: no-referrer`; no access log in the frontend
  container (CR-004, PRB-068) | Design | SR-043 AC 4, SR-033; TASK-206 | TS-017 TC-017.4". Residual
  unchanged.
- **RISK-007** (approved, re-approval collected at the end): one control row for the bounded header and
  the name bound (TS-007 TC-007.11). Residual unchanged.
- **SOUP-014** (in_review, 1.2): `--loglevel` text corrected. **SOUP-024** (nginx): `map`, `log_format …
  escape=json`, per-location `error_log` relied on, `in_review`.
- **TS-003** 1.3 → 1.4 (approval cleared, `in_review`): TC-003.3 adds the link-route tests (AC-5).
- **RISK-009** 1.1 → 1.2 (`in_review`): new cause "the e-mailed link does not reach the activation page
  (PRB-070)" and a control row "Activation link built in the route's form and tied to the SPA route by a
  test | Design | SR-033; TASK-206 | TS-003 TC-003.3". Residual unchanged.
- **PRB-068, PRB-069, PRB-070:** `## Resolution`; status `resolved` on QA approval (CR-004 D-8).
- **SR-043:** not edited by this task. The Product Owner adds AC 4 (credentials and secrets in operational
  and proxy logs), `in_review` until the human approves it. AC-1 cites it; the AC number is confirmed when
  the Product Owner reports back.

### Accepted residuals (human decision 2026-11-07, CR-004 D-16)

- The backend 500 record carries the route template, so the request's UUIDs are no longer in it; the
  traceback and the audit rows still identify the case.
- nginx does not write upstream-error entries for the activation locations (`error_log … crit`); the backend
  still logs its own 500s.
- ~~A referrer can still appear in nginx error-log entries on proxy errors outside the activation
  locations.~~ No longer a residual: accepted on 2026-11-07, then removed the same day because SR-043 AC 4
  names Referer values in error logs; `Referrer-Policy: no-referrer` on the activation page closes it.
- Limit of the Referer closure (QA finding 4, TASK-207): "closes it" is true of conforming browsers only. A
  token-bearing `Referer`, or a token in the query string of another path, sent by hand to a non-activation
  location during an upstream failure or a 413 is written to the proxy error log. No MedHub URL or browser flow
  produces these; QA did not capture a real browser's requests. **Human decision 2026-11-07 (CR-004 D-19):**
  accepted as a residual against SR-043 AC 4, listed for the release's residual-anomaly evaluation (TASK-201
  carries the note; SR-043's text is not edited).
- Names over 255 UTF-8 bytes are refused, including legal Windows and macOS names of more than 85 CJK
  characters.

## Definition of Done

- [x] AC-1 to AC-6 met; negative controls recorded; started-stack steps 1 to 5 recorded.
- [x] Backend suite with coverage ≥ 85 %, `infra/tests`, frontend `src/core/clinical` tests and
      `src/core/nav` tests and typecheck green; `ruff`, `mypy` clean.
- [x] TS-017 1.2, TS-007 1.6, TS-003 1.5, ADD-012, ADD-017, ADD-026, RISK-005, RISK-007, RISK-009,
      SOUP-014, SOUP-024 `in_review`.
- [x] On QA approval: this task `approved`; PRB-068, PRB-069 and PRB-070 `resolved` (CR-004 D-8).
- [x] `traceability-check` shows no error for TASK-206 and the records above.
- [x] `graphify update .` run after the code change.

## Implementation notes and verification results (Software Developer role, 2026-11-07)

Built in the three slices; each slice's targeted tests were green before the next.

**Files.** Backend: `app/api/errors.py`, `app/api/content_disposition.py`, `app/attachments/service.py`,
`app/core/logging.py`, `app/workers/celery_app.py`, `app/workers/email_tasks.py`. Frontend:
`nginx.conf`, `src/core/clinical/AttachmentUpload.tsx`. Infra: `reverse-proxy/nginx.conf`, `smoke-test.sh`,
`log-secrets-check.sh` (new). Tests: `backend/tests/api/test_error_logging.py`,
`backend/tests/workers/test_celery_logging_level.py`, `frontend/src/core/clinical/AttachmentUpload.test.tsx`,
`infra/tests/test_proxy_access_log.py`, `infra/tests/test_activation_link_route.py` (new); extended:
`test_content_disposition.py`, `test_attachment_upload.py`, `test_attachments_router.py`,
`test_attachment_integrity_persistence.py` (three `ip` assertions), `test_email_tasks.py`,
`infra/tests/test_images_non_root.py`. No OpenAPI change (export identical to the committed file).

**Suites (first run, before PRB-071; the final run is below).** Backend `pytest --cov=app --cov-fail-under=85`: 1533 passed, 6 skipped, coverage 94.50 %.
`modules/dicom_viewer/tests`: 25 passed. Frontend `npm test -- --run`: 32 files, 315 tests passed; `lint` and
`typecheck` clean. `infra/tests`: 109 passed. `ruff check`, `black --check`, `mypy app` clean.

**Negative controls (run against the working tree with one file put back at HEAD 3eef9fb, or one line changed).**
1. HEAD `errors.py`: `test_unhandled_exception_logs_route_template_not_token` and
   `test_unhandled_exception_on_unmatched_path_logs_placeholder` fail (token in the record). HEAD `nginx.conf`:
   `test_proxy_access_log.py` fails 5 tests and errors on 1 (no `access_log`, no format, no map). HEAD
   `content_disposition.py`: 8 of the new tests fail (fallback 404 and 431 characters, `filename*` 904 bytes,
   bidi controls kept). HEAD `service.py`: `test_filename_over_255_bytes_is_rejected_with_400`,
   `test_filename_bound_counts_utf8_bytes_not_characters` and the router 400 test fail (the router test answers 500
   in its mocked harness, not 201, because the mocked repository returns a mock; the service stores the file).
2. `$request` added to `medhub_redacted`: two infra tests fail. `access_log off;` removed from
   `frontend/nginx.conf`: `test_the_frontend_container_logs_no_access` fails.
3. Receiver calls `configure_logging()` without the argument: three tests fail (DEBUG level, level name, DEBUG
   record emitted).
4. HEAD `email_tasks.py`: `test_activation_email_link_uses_the_activation_route` and
   `test_the_email_link_is_the_activation_path_form` fail (`/activate?token=`).
5. (Started stack) HEAD `reverse-proxy/nginx.conf` on the running stack: `smoke-test.sh` fails 2 checks (no
   `Referrer-Policy`; 3 log lines hold the marker) and `log-secrets-check.sh` fails 3 (9 proxy log lines hold the
   activation token; no redacted path; an upstream error entry names an activation request).

**Started stack for slices A to C** (scratch Compose project `task206`, a scratch copy of the tree, scratch `.env`, an SMTP catcher
added only by a scratch override; torn down with `down -v --remove-orphans` and the project's images removed;
container, volume and network lists equal to the start, image list equal after removing five dangling build
layers; `infra/.env` sha256 `a4933b8c...3c696da` before and after; `peaceful_pike` untouched).
1. `db-migrate` via `up --build --exit-code-from db-migrate db-migrate`: exit 0; `up -d --build`: all services up.
2. `smoke-test.sh`: 79 passed, 0 failed, including the token check and `Referrer-Policy: no-referrer`.
   `log-secrets-check.sh`: 24 passed, 0 failed (activation, session and CSRF tokens and the password: 0 matches in
   the logs of the six services; the proxy logged the activation requests with the path redacted; with the backend
   stopped the activation request answered 504 and a token-free control request's upstream error was in the
   error log while none named an activation request; with postgres stopped the activation API answered 500).
   Re-run on the final code: 24 passed, 0 failed. A last smoke run failed one unrelated check
   ("object store holds every attachment", 5 rows against 4 objects) only because step 4 had inserted an extra
   attachment row sharing an object.
3. Real e-mail: an administrator created an account; the catcher held one mail whose only link was
   `https://localhost/activation/<token>`; through the proxy the page answered 200 (the SPA) with
   `Referrer-Policy: no-referrer`; the token validated, `POST` activated the account (204), the new password
   signed in. Neither the token nor the password nor the address is in any service log. **Limits:** the page
   was not rendered in a browser in that first run, and the mail was only sent after a scratch-only
   `CELERY_BROKER_URL` override, because of PRB-071; both are redone without an override in the PRB-071 paragraph.
4. Doctor with consent, through the proxy: 256-byte ASCII name, 84 CJK + `.txt` (256 bytes) and 85 CJK + `.txt`
   (259 bytes) answered 400 `application/problem+json` (`filename_max_bytes`); 83 CJK + `.txt` (253 bytes) and
   83 CJK + `ab.txt` (255 bytes) answered 201 and downloaded with 200 and identical bytes. A row inserted directly
   with 255 x U+FDFA (765 bytes) and an existing object downloaded with 200, identical bytes and a 957-byte ASCII
   header. The alert in the UI is covered by `AttachmentUpload.test.tsx`; it was not exercised in a browser.
5. Worker with `--loglevel=debug` (scratch Compose override): 38 to 40 DEBUG records in the JSON format; an
   activation e-mail task ran; the address was absent. The first run showed the activation token inside Celery's
   debug `TaskPool: Apply` record (`argsrepr`); the filter now replaces `argsrepr`/`kwargsrepr` and the token was
   absent on the re-run. `--loglevel=info` restored.

**PRB-071 (found here, fixed here; CR-004 D-17).** On the delivered stack the API process could not enqueue any
Celery task: the tasks are `@shared_task`s and the API used Celery's built-in app (`amqp://localhost`), so no
activation e-mail, session-kill propagation, erasure code or appointment notification was sent; each call site
logged a warning (or nothing) and answered 2xx. Fix: `backend/app/main.py` `_bind_celery_app()`, called by the
lifespan after the secret rule, imports `app.workers.celery_app` and calls `set_default()`. Import alone is not
enough: Celery's current app is thread-local and sync routes run in a worker thread (a first attempt passed its
unit test and still failed on the stack; the test now checks from a worker thread). `infra/docker-compose.yml` already
gives the backend `REDIS_URL`; no Compose change. Test: `backend/tests/workers/test_api_celery_broker.py` (four tasks
across five call sites). Negative controls: no call, and import without `set_default()`, both show
`amqp://guest:**@localhost:5672//`. Started stack, no override, fresh scratch project: 1 mail at the catcher, 0
"Failed to enqueue" in the backend log; link `/activation/<token>` rendered the activation page in the built-in
browser (reached through a scratch redirect so the token was never printed), activated through the API, signed in;
SYSADMIN deactivation of a patient answered 204, the patient's next request 401, the worker logged
`propagate_session_kill` received and succeeded; `smoke-test.sh` 79 passed, 0 failed; `log-secrets-check.sh` 24
passed, 0 failed; token, new password, address and the three seeded passwords: 0 matching lines in 10 service logs.
Teardown: `down -v --remove-orphans`, project images and five dangling build layers removed, container, volume,
network and image lists equal to the start, `infra/.env` sha256 `a4933b8c...3c696da` unchanged. Not done: the form
in the browser was not filled in (the password would have been typed into the transcript), the activation POST
was made through the API.

PRB-013 pattern, reported and not changed: `.delay()` wrapped in `except Exception` at `account_service.py:109`
(warning), `activation.py:144` (warning), `erasure.py:140` (warning), `lifecycle.py:69` (silent `pass`, session
kill) and `appointments/service.py:69` (silent `pass`). On the session-kill path the synchronous
`invalidate_all` still ends the sessions, so the failed task was a silent loss of the redundant propagation.

**Final suites (after the PRB-071 fix).** Backend `pytest --cov=app --cov-fail-under=85`: 1537 passed, 6 skipped, coverage 94.50 % (the four new `test_api_celery_broker.py` tests included; `tests/conftest.py` gained an autouse fixture that restores Celery's default app after each test, because the lifespan now sets it). `modules/dicom_viewer/tests`: 25 passed. Frontend: 32 files, 315 tests passed; `lint` and `typecheck` clean. `infra/tests`: 109 passed. `ruff check`, `black --check`, `mypy app` clean. OpenAPI export unchanged. Two full-suite attempts were slowed or abandoned while other test runs and a leaked testcontainer competed for Docker; the run that completed (117 s) is the one reported.

**Deviations from this task text.**
- Step 4: "84 CJK + `.txt` (258 bytes)" is arithmetic that does not hold: 84 CJK + `.txt` is 256 bytes (refused) and
  85 CJK + `.txt` is 259. The accepted boundary cases used were 253 and 255 bytes; unit tests use 83 CJK + `ab.txt`.
- `log-secrets-check.sh` seeds the accounts from inside the backend container: the activation token comes from the
  application's `issue_activation_token()` (the API never returns it), and the test user from
  `backend/scripts/setup_test_data.py::create_doctor` with a generated password. Upstream errors may end in 504 as
  well as 502; the script accepts both and adds a token-free control request.
- Added: redaction of `argsrepr`/`kwargsrepr` (SR-043 AC 4 at `--loglevel=debug`), tests for it, and a change to
  `infra/tests/test_images_non_root.py` (the proxy now has two `proxy_pass http://frontend:8080` lines).
- PRB-071 fixed in this task (human decision, CR-004 D-17, 1.16): `backend/app/main.py`, `backend/tests/workers/test_api_celery_broker.py`; ADD-005 and the arc42 sections are unchanged.

## QA review (2026-11-07): APPROVED

No CRITICAL or HIGH finding. Two MEDIUM and five LOW findings are carried; none blocks the ACs. Values were never
printed: all evidence below is counts.

### Findings (carried)

1. **[MEDIUM] `.delay()` can block a request for about 20 s, in its open transaction** —
   `backend/app/workers/celery_app.py:50`, new with `_bind_celery_app()` (`backend/app/main.py:33`). The wait comes from the
   **result store**, not the broker: `RedisBackend.on_task_call` retries 20 times at 1 s ("Retry limit exceeded while
   trying to reconnect to the Celery result store backend"). Measured with Redis stopped, from a worker thread: 19.88 s;
   with `retry=False` still 19.88 s; with `task_ignore_result=True` 0.93 s. **Exposure on the delivered topology is small:**
   sessions use the same Redis, so with Redis stopped every authenticated request fails first (see the measurement
   below). It is reached when Redis goes away between the session check and the dispatch, or when only the broker
   path fails. With a scratch `celery_app.py` pointing broker and results at a closed port and sessions healthy:
   create account 19.28 s, appointment 19.27 s, deactivation 19.27 s (answered 201/201/204), the `/me` of another
   user 25.6 s during 45 parallel creates. `erasure.py:135` calls this path "not blocking". → Add
   `task_ignore_result=True` to `celery_app.conf.update` (no code reads a result; it also stops the
   `celery-task-meta-*` keys). `retry=False` alone does not help.
2. **[MEDIUM] The redaction and the activation locations are case-sensitive, and the app is not** —
   `infra/reverse-proxy/nginx.conf:10-11,52,64`. `/ACTIVATION/<token>`, `/Activation/<token>`,
   `/API/V1/ACTIVATION/<token>` and `/api/v1/Activation/<token>` are logged verbatim (1 access-log line each) and take
   the default locations, so the page has no `Referrer-Policy` and an upstream error entry is written. React Router
   matches without case (`compilePath(path, caseSensitive = false)`), so the page variant is a working activation URL.
   Only a link altered by hand reaches this: the e-mailed form is exact. SR-043 AC 4's pass criterion holds; its
   general sentence does not for this variant. → Use `~*` in the two `map` entries and the two locations; add the
   variant to `infra/tests/test_proxy_access_log.py` and the smoke check.
3. **[LOW] The 500 record's template has no `/api/v1`** — `backend/app/api/errors.py:191`. On the real app it logs
   `/activation/{token}` and `/clinical-entries/{entry_id}/attachments` on the stack, while this task, PRB-068
   and TS-017 state `/api/v1/activation/{token}`; `backend/tests/api/test_error_logging.py:21` passes because its
   synthetic app declares the full path. No token leaks and the endpoint is identifiable. → Correct the records, or
   test through the real router.
4. **[LOW] "No Referer carries the token" is true of conforming browsers only** — this task's Accepted residuals, and
   `infra/log-secrets-check.sh` step 3, whose control request has no Referer. A token-bearing Referer sent to a
   non-activation location during an upstream failure is written to the proxy error log (`/api/v1/me`, `/healthz`,
   `/assets/x.js`: 1 line each), and a query string on another path likewise (`/api/v1/patients?token=`, and a 413
   on `/api/v1/foo?token=`). No MedHub URL or browser flow produces these: the header is sent, the SPA has no `referrer`
   meta tag. QA did not capture a real browser's requests. → State the limit in the residuals.
5. **[LOW] Names around 8 KB and over get a 400 that is not problem+json** — AC-2 says problem+json. The multipart parser
   refuses the part first: `application/json`, "There was an error parsing the body" (4,000 bytes reach the service
   check, 8,000 do not; 2 MB gives 413). Nothing is stored and the user sees a reason. → Accept it in AC-2's wording or
   map the parse error.
6. **[LOW] `infra/log-secrets-check.sh` does not cover the whole of SR-043 AC 4's list** — `infra/log-secrets-check.sh:29`.
   It never sends the activation `POST`, and its known values leave out the retrieval code and the object-store and
   encryption keys. QA ran all of these by hand: 0 matches. → Add them when the script is next touched.
7. **[LOW] Record gaps** — ADD-017 does not describe `_bind_celery_app()` (SOUP-014 and RISK-009 do); the task
   header, Objective and `implements` links do not mention PRB-071 or SR-034, SR-024 and SR-035, which AC-6 cites;
   the Definition of Done says TS-003 1.4 (it is 1.5). `graphify update .`: `graphify-out/graph.json` is older than
   `backend/app/main.py`, so that item stays unticked for the orchestrator.

### Pre-existing issues (not blocking)

- **Concurrent writes collapse the API.** 20 parallel `POST /accounts` on a healthy stack: all 502, gunicorn
  `WORKER TIMEOUT`. Same with HEAD `main.py` (no `set_default`) and with `task_ignore_result=True`, so this change does not
  cause it. A thread dump shows a request waiting on the SQLAlchemy pool checkout in `backend/app/api/deps.py:81`; the
  root cause was not established. 8 parallel clients ran at about 100 requests/s without error. → Raise a PRB.
- **A name with `..` answers 500.** `../../etc/passwd` reaches the storage key (`backend/app/attachments/service.py:100`)
  and the store refuses it (`InvalidRequest`). → Raise a PRB; SR-013 AC 1 input validation.
- **PRB-013 call sites.** The silent `pass` at `identity/lifecycle.py:69` is tolerable for now and not a blocker:
  `invalidate_all` runs first, so SR-034 AC 2 holds; what is lost is the repeat invalidation and the
  `SESSION_KILL_PROPAGATED` audit row. It should still get a `logger.warning` with the id, as should
  `appointments/service.py:69`: silence is what hid the critical PRB-071. The worst site is the one that does log:
  `identity/erasure.py:140`, because the retrieval code exists nowhere else and has no recovery. No new PRB is needed:
  PRB-013 (open, major) and TASK-141 (draft) cover it, but they are outside CR-004 and PRB-013's line numbers are stale.
  The human should decide whether to pull TASK-141 forward.
- The object store logs its access key once at start-up (`auth_credentials.go`). That log is not in SR-043 AC 4's list.
- At root DEBUG, botocore prints the access key in the `Authorization` header (1 line in a local probe). No worker
  task uses the object store today, so `--loglevel=debug` does not reach it; SQLAlchemy keeps its own WARN level.

### Verification run

All independently re-run on a fresh scratch project (`qa206`), `infra/.env` never touched.

- Backend `pytest --cov=app --cov-fail-under=85`: 1537 passed, 6 skipped, 94.50 %. `modules/dicom_viewer/tests` 25 passed.
  `infra/tests` 109 passed. Frontend 32 files, 315 passed; typecheck and lint clean. `ruff`, `black --check`, `mypy app`
  clean. OpenAPI export identical to the committed file.
- `smoke-test.sh` 79 passed, 0 failed. `log-secrets-check.sh` 24 passed, 0 failed.
- Negative controls of the script: `$request_uri` in the format, 2 failed; `error_log crit` removed from the API
  location, 2 failed. Mutants of the code: 15 of 15 killed (no `_bind_celery_app()` call, no `set_default()`, raw path in
  the 500, limits 254 and 256, characters for bytes, U+200D mapped, U+202E kept, fallback 151, name 256, extension
  dropped, broken character cut, `argsrepr` unredacted, level ignored, old link).
- SR-043 AC 4, known values: real e-mail, page, `GET`, wrong and right `POST`, sign-in, deactivation, erasure, retrieval
  (right, malformed and wrong-type bodies), and `POST`s with postgres and with Redis stopped (6 unhandled exceptions).
  Activation token, new password, session and CSRF tokens of two accounts, retrieval code, address, four seeded
  passwords, and the database passwords, object-store secret key, at-rest key and SSE key: 0 lines in 12 services
  (stdout and stderr). Only match: the object store's access key, above. Both nginx images link their logs to
  stdout and stderr, and the proxy, backend and worker containers hold no application log file.
- 67 marker probes on the proxy (58 with the upstreams up, 9 with the backend or the frontend stopped). `//`, `%2F`, `%69`, `/./`, `/../`, `/activation/tok/extra`, absolute URI, port 80, plain
  HTTP on 443, bad version, control character, oversize header, URLs of 7,000 to 20,000 characters (414 above about 8 KB), 413 on the API
  path: 0 lines. Referers and other-path query strings in the access log: 0 lines. HSTS, `nosniff` and `X-Frame-Options` are
  sent on `/`, `/activation/`, `/activate`, `/api/` and `/healthz`; `no-referrer` on the page locations.
- `--loglevel=debug`: 42 DEBUG records from the worker; full value, first 16 and first 8 characters of two tokens,
  the code and the address: 0 matches (Celery's 1,024-character cut falls after `argsrepr`). Beat: 4 DEBUG records. The
  new regex is linear (700 kB adversarial: at most 0.103 s).
- Names through the proxy: 255 bytes accepted and 256 refused for ASCII, CJK and emoji, with identical bytes on download.
  `filename*` alone is not read as a file (400), and with `filename` the plain name wins, so it is no way round the
  limit. Percent-encoded names count as literal bytes. Stored 255 x U+FDFA, 10,000 CJK, 3,000 emoji and 3,000 ASCII
  names download: 200, identical bytes, headers of 957, 880, 861 and 447 bytes. Fuzz: 120,000 cases, 0 failures, largest
  value 957 bytes, `filename*` at most 255 bytes, fallback at most 150 characters.
- PRB-071: real mail with no broker override, 0 "Failed to enqueue". With `-w 3`: 3 workers started and dispatched,
  0 "Failed to enqueue" (20 of 120 parallel requests answered 502: the pre-existing stall above); the event-loop thread, a worker thread and a new thread all see the configured app. Worker
  process: `default_app` is `None`, current app `medhub`, so it is unaffected.
- **Redis down (shipped stack):** `GET /me`, create account, deactivation and appointment each answer 500 in 0.02 s,
  sign-in in 0.06 s, retrieval in 0.08 s, as the session or rate check fails first. Redis killed under 8 parallel clients:
  225 requests, 210 created, 15 answered 500, 8 of them after 5.1 s; none at 19 s, 0 "Failed to enqueue".
- `traceability-check` on the 22 records in scope: 0 errors, 9 W5 warnings after these status changes (TASK-206,
  RISK-006 and three SRs are approved and point at `in_review` RISK and SOUP records awaiting the human).
- Not re-run by QA, relying on the developer's record and unit tests: the activation page in a browser (the proxy's answer,
  the SPA document and the API steps were), and the upload alert in the UI (`AttachmentUpload.test.tsx`).
- `tests/conftest.py` fixture: it hides no failure. Removed in a scratch copy, 1,315 tests passed before the run was stopped, but
  each test that reaches an unmocked `.delay()` after a lifespan took about 19.4 s (`tests/identity/test_erasure.py`,
  `tests/authz/test_decision_table.py`). What it masks is the latency of finding 1, which no test measures.
- Teardown: `down -v --remove-orphans`, the 8 `qa206-*` images removed, no global prune; container, volume, network
  and image lists equal to the start; `infra/.env` sha256 `a4933b8c82d6f81e...` before and after. `peaceful_pike` and
  `nice_dijkstra` untouched.

## Version history

- 1.0 (2026-11-07) — Created by the Software Architect role for PRB-068 and PRB-069 and the TASK-138 QA
  `--loglevel` follow-up (CR-004 D-14). `draft`.
- 1.1 (2026-11-07) — Human decisions D-16: PRB-070 (activation link) folded in (slice A, AC-5, started-stack
  step 3, TS-003 and RISK-009 records, `mitigates` RISK-009); AC-1 cites SR-043 AC 4 (new, pending approval at 1.1);
  the 255-byte name limit and the residuals recorded as the human's decisions. Then aligned with SR-043 AC 4
  (SR-043 1.1): AC-1 is AC 4's pass criterion (`infra/log-secrets-check.sh`), no header variable in any log
  format, `Referrer-Policy: no-referrer` on the activation page (removes the referrer residual), the `crit`
  error-log choice confirmed for the upstream-error case, RISK-005 row listed for the developer. Still `draft`.
- 1.2 (2026-11-07) — Built by the Software Developer role; records updated; verification results and deviations added. `in_review`.
- 1.3 (2026-11-07) — CR-004 D-17: PRB-071 (critical) fixed here. AC-5 updated, AC-6 added, `backend/app/main.py` and `test_api_celery_broker.py` added, started stack redone with no broker override. `in_review`.
- 1.4 (2026-11-07) — QA review: APPROVED, two MEDIUM and five LOW findings carried. `in_review → approved`; AC-1 to AC-6 ticked. TS-003, TS-007, TS-017 approved; PRB-068, PRB-069, PRB-070, PRB-071 `resolved` (CR-004 D-8).
- 1.5 (2026-11-07) — TASK-207 content corrections to the QA findings 3, 4, 5 and 7 (route template wording, Referer limit and D-19, multipart 400 in AC-2, PRB-071 in header and Objective, `implements` SR-034, SR-024, SR-035, Definition of Done TS-003 1.5). Approval cleared: `approved → in_review`; QA re-approves it with TASK-207.
- 1.5 (2026-11-08) — QA re-approval with TASK-207: corrections for findings 3, 4, 5 and 7 checked against the code and the started stack; D-19 residual recorded correctly. `in_review → approved` (status only); `graphify update .` item ticked (run in TASK-207).
