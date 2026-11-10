---
id: "PRB-068"
type: problem-report
title: "The activation token is written to the backend error log and the proxy access log"
status: resolved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-11-07"
updated: "2026-11-07"
criticality: major
links: []
tags: ["logging", "credentials", "hazard:security", "found-in:TASK-138-qa"]
---

# PRB-068 — The activation token is written to the backend error log and the proxy access log

## Observed

Found by QA while reviewing TASK-138 (2026-11-06, committed as be9fb56). An unhandled exception on
`GET /api/v1/activation/QA138TOKENPATH` produced the log record
`Unhandled exception for GET /api/v1/activation/QA138TOKENPATH`: the raw activation token is in the
message. TASK-138's redaction filter replaces values of fields named `token`, not a token inside a URL
path. The reverse proxy logs every request line with nginx's default access log, so the token is also
recorded on every activation, error or not.

## Impact

The activation token is a credential: together with the account id it lets the holder set the password
of an account that is waiting for activation (`POST /api/v1/activation/{token}`, SR-033) during the
token's 72-hour validity. Anyone who can read the operational logs (operators, a log shipper, a support
copy of the logs) can therefore take over a new account before its owner activates it, including a
doctor's account with access to PHI (RISK-005). The token stays in the logs after it has been used or
has expired; only the live window is exploitable.

## Investigation

Every place a token-bearing URL reaches a log, on the current tree (HEAD 820cfd6 + be9fb56):

| Where | Mechanism | Token form |
|---|---|---|
| `backend/app/api/errors.py:189` | `logger.exception("Unhandled exception for %s %s", request.method, request.url.path)` on any unhandled exception | `/api/v1/activation/{token}` (`backend/app/api/routers/activation.py:35`, `:55`) |
| `infra/reverse-proxy/nginx.conf:11-48` | no `access_log` or `log_format`, so the image default `combined` format logs `$request` (path and query string) and `$http_referer` for every request on both servers (`:4-9`, `:11-48`) | API path `/api/v1/activation/{token}`; SPA page `/activation/{token}` (`frontend/src/app/App.tsx:73`); the e-mail link's query string `/activate?token=…` (`backend/app/workers/email_tasks.py:97`); and the `Referer` of every asset and API request made from the activation page |
| nginx error log (same file) | on upstream errors nginx writes `request: "GET …"` and `referrer:` into the error log; its format cannot be changed | same as above, only on proxy errors |
| `frontend/nginx.conf:1-9` | default access log of the frontend container, which receives the SPA requests from the proxy | `/activation/{token}`, `/activate?token=…`, referrers |
| backend access log | **not affected today**: the image `CMD` (`backend/Dockerfile:24`) has no `--access-logfile`, so `uvicorn.access` has no handler (TASK-138 QA). Nothing prevents enabling it later | would be every activation request |

Other token-like values checked and **not** in a URL: the anonymized-data retrieval code is a JSON body
field (`backend/app/api/routers/anonymized_data.py:67-76`); resend activation takes the account id
(`backend/app/api/routers/accounts.py:113`); session and CSRF tokens are cookies and headers, which the
default formats do not log. No password-reset route exists. No other route has a non-UUID path
parameter that is a secret (`activation.py` is the only one).

Root cause: two log sources record request URLs verbatim, and the only credential carried in a URL is the
activation token. The redaction filter (SR-043 AC 2) works on field names and e-mail shapes, not on URL
structure, and nginx logging was never configured.

Side observation (not this PRB): the e-mail link is `/activate?token=…` (`email_tasks.py:97`) while the
SPA route is `/activation/:token` (`App.tsx:73`). Recorded for the human; it does not change this
investigation, because both forms must stay out of the logs.

## Safety evaluation

Confidentiality and integrity: a log reader can take over a pending account and then read PHI or write
clinical entries in its owner's name (RISK-005, harm severity 3). It needs log access and a pending
account inside the 72-hour window, so it is not `critical`. Criticality **major**: a credential is stored
in plaintext outside its controlled store. No requirement states explicitly that credentials stay out of
operational logs (SR-043 covers personal data; SR-023 AC 9 covers the audit trail). No release exists
(CR-004 A-1), so no released version in use is affected and no notification is needed. The human sets the
final criticality.

## Resolution

Fixed by TASK-206 (CR-004 D-14, D-16); status `resolved` on QA approval (D-8).

- Backend: the 500 record names the matched route template (`/activation/{token}`: the router prefix, without `/api/v1`) or `<unmatched>`,
  never the raw path (`backend/app/api/errors.py`); the traceback is kept.
- Reverse proxy: an allow-list `medhub_redacted` JSON access log (normalised path with the two activation
  routes replaced by `[redacted]`; no request line, query string or header variable, so no Referer, Cookie or
  X-CSRF-Token) in both `server` blocks; `error_log ... crit` on the activation locations; the activation page
  sends `Referrer-Policy: no-referrer`. Frontend container: `access_log off`, `error_log ... crit`.
- Pinned by `backend/tests/api/test_error_logging.py` and `infra/tests/test_proxy_access_log.py`; checked on a
  started stack by `infra/smoke-test.sh` (every run) and `infra/log-secrets-check.sh` (24 checks, 0 matches of
  the activation, session and CSRF tokens and the password in the logs of the six services).
- Found while verifying: at `--loglevel=debug` Celery's `TaskPool: Apply` record prints the task headers with
  `argsrepr`, which holds the activation token. The redaction filter now replaces the value of `argsrepr` and
  `kwargsrepr` (`backend/app/core/logging.py`, `backend/tests/workers/test_celery_logging_level.py`).
- Accepted residuals (human, CR-004 D-16): the 500 record no longer carries the request's UUIDs; nginx does not
  write upstream-error entries for the two activation locations.

## Source

TASK-138 QA review (`docs/design-outputs/tasks/TASK-138-pii-scrubbing-for-worker-and-notification-logs.md`,
"Pre-existing issues"); human decision 2026-11-07.

## Version history

- 1.0 (2026-11-07) — Created from the TASK-138 QA review. `open`, `major`.
- 1.1 (2026-11-07) — Resolution written by the Software Developer role (TASK-206). Left `open` (CR-004 D-8).
- 1.2 (2026-11-07) — QA approved TASK-206: status `resolved` (CR-004 D-8).
- 1.3 (2026-11-07) — TASK-207 (TASK-206 QA finding 3): the Resolution's route template corrected to `/activation/{token}`, the form the real app logs. Status stays `resolved`.
