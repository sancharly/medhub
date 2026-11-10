---
id: "TASK-138"
type: task
title: "PII scrubbing for worker and notification logs"
status: approved
version: "1.5"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-07"
links:
  - target: "RISK-008"
    relation: mitigates
  - target: "SR-043"
    relation: implements
  - target: "SR-024"
    relation: implements
  - target: "NFR-004"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "PRB-011"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-017"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
  - target: "TASK-031"
    relation: relates_to
  - target: "TS-017"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium", "control:protective", "control:design", "cr:CR-004"]
---

# TASK-138 — PII scrubbing for worker and notification logs

- **Software item / unit:** SI-WORKER logging (ADD-017), SI-API logging (ADD-005),
  `backend/app/core/logging.py`.
- **Resolves (through CR-004):** PRB-011. Source: `docs/reports/CODE-REVIEW-2026-07.md` finding E.
- **Depends on:** none. Independent of every other CR-004 task; can run in parallel.
- **Branch:** `fix/review-2026-07-security` (CR-004).
- **Size:** M (4 source files: `core/logging.py`, `workers/email_tasks.py`, `workers/celery_app.py`,
  `main.py`; 2 test files; TS-017)
- **Needs:** nothing beyond the unit-test environment.

## Objective

SR-043 AC 1 to AC 3: no email address, name, date of birth or clinical free text in the
operational log stream; one redaction filter on every application logger; tests that fail if an
address reaches the log. The PRB-011 Investigation found two `extra` fields carrying addresses
(`backend/app/workers/email_tasks.py:117-123,168-171`), formatters that drop `extra` today, and a
worker with no logging configuration at all.

## Implementation detail

1. **At the source (AC 1):** `email_tasks.py:117-123` logs `account_id` only;
   `email_tasks.py:168-171` logs the anonymized dataset id (pass it to the task, or log no
   recipient at all). Sweep `backend/app` for other `logger.*` calls with personal data in the
   message or `extra` (`grep -rn "logger\." backend/app | grep -i "email\|name\|birth\|description"`).
2. **Redaction filter (AC 2):** `core/logging.py` gains `RedactionFilter(logging.Filter)` that
   replaces email-shaped values in `record.msg`, `record.args` and every non-standard attribute
   of the `LogRecord` (any field name, nested `dict`/`list` values included) with
   `[REDACTED-EMAIL]`. The JSON formatter also serializes `extra` fields (after the filter), so
   identifiers in `extra` are visible to operators.
3. **Every handler (AC 2):** `configure_logging()` attaches the filter to the root handler. The
   worker and the scheduler call it through Celery's `setup_logging` signal
   (`backend/app/workers/celery_app.py`), so Celery's own loggers (task retry and failure messages)
   go through the same handler and filter.

## Tests (write first)

- `backend/tests/test_log_redaction.py`:
  - a record with `extra={"anything_at_all": "a.person@example.org"}` → emitted JSON contains no
    `a.person@example.org` (AC 3, arbitrary field name);
  - the address in the message, in `%s` args and in a nested dict → redacted;
  - a UUID and an account id survive unchanged.
- `backend/tests/workers/test_email_tasks_logging.py` (captures the root handler's stream after
  `configure_logging()`):
  - `send_erasure_code_email` and `send_activation_email` success path with a known address →
    the captured output does not contain it;
  - failure path: `_send_smtp` raises `smtplib.SMTPRecipientsRefused({addr: (550, b"no")})`, the
    task's retry or failure logging runs → the output does not contain the address;
  - the Celery `setup_logging` handler is installed (the worker's root handler has the filter).

## Acceptance criteria

- [x] SR-043 AC 1: no log call under `backend/app` emits personal data; ids are used
      (`backend/tests/workers/test_email_tasks_logging.py`).
- [x] SR-043 AC 2: the filter is on every handler of the API, worker and scheduler, any field name
      (`backend/tests/test_log_redaction.py`).
- [x] SR-043 AC 3: success- and failure-path tests with a known recipient address pass, and fail
      with the filter removed (negative control).

## Verification

```sh
cd backend && uv run pytest tests/test_log_redaction.py tests/workers tests/test_logging.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

Negative controls: remove the filter (failure-path test fails); restore the `extra` email
(success-path test fails). Record both in the handoff.

## Records

- **TS-017** (new, `verifies` SR-043): TC-017.1 (no personal data at the source), TC-017.2
  (filter on every handler, any field), TC-017.3 (worker success and failure paths).
- **SOUP-014** (Celery): add to "Functional and performance requirements" that MedHub relies on
  the `setup_logging` signal to own the worker's logging; `in_review`.
- **PRB-011**: `## Resolution` with commit, tests, negative-control result; `resolved`.

## Definition of Done

- [x] Lint, type-check, backend suite pass; coverage ≥ 85 %.
- [x] TS-017 `in_review`; SOUP-014 `in_review`; PRB-011 `resolved`.
- [x] `traceability-check` shows no error for TASK-138, TS-017, SR-043, PRB-011.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-008 (risk register bootstrap, TASK-147).
  Traceability only: the requirement content is unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.3 (2026-10-31) — CR-004 Plan stage (Software Architect role): rescoped to SR-043 against the
  current tree (two `extra` fields; formatters drop `extra`; the worker has no logging
  configuration). Links `implements` SR-043, `relates_to` PRB-011, CR-004, ADD-017, ADD-005 added.
  Tests named by path, TS-017 planned. Still `draft`.
- 1.4 (2026-11-06) — Build stage: implemented; `draft → in_review`. `relates_to` TS-017 added. See
  "Implementation notes". (SOUP-014 was edited afterwards, at the coordinator's request: 1.2, `in_review`.)
- 1.5 (2026-11-07) — Round 2 after QA round 1 (CHANGES REQUESTED): findings 1 to 8 fixed, see
  "Round 2 notes". `draft → in_review`.

## Implementation notes

Files: `backend/app/core/logging.py` (`RedactionFilter`, `redact_text`, `redact_value`; the JSON
formatter now serializes `extra` under `"extra"`, after the filter), `backend/app/workers/celery_app.py`
(`setup_logging` receiver calling `configure_logging()`), `backend/app/workers/email_tasks.py` (the two
address fields removed), `backend/tests/test_log_redaction.py`, `backend/tests/workers/test_email_tasks_logging.py`,
TS-017. `main.py` needed no change (the lifespan already calls `configure_logging()`).

- The filter folds `msg % args` into the message (so arguments cannot leak through a handler that
  formats later), redacts email-shaped values (also `%40`) in every non-standard `LogRecord`
  attribute under any name, nested containers included, and in `exc_text`/`stack_info`. Fields named
  like personal data, clinical text, credentials or task arguments (`first_name`, `surname`, `birth`,
  `description`, `token`, `args`, `kwargs`, ...) are replaced whole, because a name or a date of
  birth has no recognizable shape. Celery's failure record carries `args`/`kwargs`, which is why those
  keys are replaced.
- `configure_logging()` also attaches the filter to the handlers of loggers that keep their own
  handlers (uvicorn, gunicorn); it is idempotent.
- Call-site sweep of `backend/app`: only the two `email_tasks.py` fields carried an address. Other
  `logger.*` calls log ids, counts, module keys or paths; `print` calls are CLI tools (credential
  init, reencrypt, export) outside the application log stream.
- SOUP-014 (Celery) "Functional and performance requirements" now records the reliance on the
  `setup_logging` signal and which Celery records carry task arguments (1.2, `in_review`; corrected in
  round 2).
- Out of scope (Q-9): activation tokens and retrieval codes are Celery task arguments
  (`email_tasks.py`), stored in Redis in plaintext. The redaction only keeps them out of logs.

## Verification results

2026-11-06, branch `fix/review-2026-07-security`.

- `cd backend && uv run pytest tests/test_log_redaction.py tests/workers tests/test_logging.py`: 35 passed (13 new).
- `cd backend && uv run pytest --cov=app --cov-fail-under=85`: 1387 passed, 6 skipped, coverage 94.38 %.
  (An earlier full run failed 4 new worker-log tests: another test leaves existing loggers disabled
  by Alembic's `fileConfig`; the fixtures now re-enable them.)
- `uv run pytest modules/dicom_viewer/tests`: 25 passed. `ruff check .`, `black --check .`, `mypy app`: clean.
- Negative controls: filter not attached, 8 tests fail; filter blind to extra fields and exception
  text, 5 fail (including the failure-path test); address restored in `send_erasure_code_email`'s
  `extra`, `test_success_records_hold_no_address_at_the_source` fails (the filter masks it on the
  output tests, which is why the source-record test exists). Source and filter restored afterwards.

## QA review — round 1 (2026-11-06): CHANGES REQUESTED

The wiring is right and QA reproduced it with a real worker. A `celery worker` and a `celery beat`, started
from `backend/` against a scratch Redis, with a local SMTP stub that refuses every recipient (550), wrote JSON
to stdout through the filter. QA sent `send_erasure_code_email("qa138.person+tag@example.org", "QA138-CODE-ZX81")`
twice: once on the retry path and once with `retries=3`, which gives the final failure. QA also sent
`send_activation_email(..., "QA138-TOKEN-77")`. The real output had the Celery `received` records (`data.args`/`kwargs`
→ `[REDACTED]`), the `retry` record, and the `raised unexpected: SMTPRecipientsRefused({'[REDACTED-EMAIL]': ...})`
failure record with its traceback. A grep found 0 hits for the address, `person+tag`, `example.org`, the code and the
token, on both stdout and stderr. In the negative control, the same worker with `RedactionFilter.filter` patched to a
no-op printed the address and the code. Under gunicorn (the image CMD, run locally), the lifespan's `configure_logging()`
covers `app.*` and the shared gunicorn/uvicorn error handler. The image CMD emits no access log: there is no
`--access-logfile`, so `uvicorn.access` has no handler. `GET /healthz?email=...%40...&x=...@...` therefore appeared in
neither stream. The only API query parameters are `page` and `page_size`. Every mutant QA ran was caught: exception
text not redacted (3 tests fail), `args`/`kwargs` keys kept (2), `%40` dropped (1), signal receiver a no-op (5), root
handler only (1), key list empty (1). Alembic `fileConfig` (`backend/app/db/alembic/env.py:22`, `alembic.ini` with the
default `disable_existing_loggers=True`) runs only in `db-migrate` and in test processes. Neither the API nor the worker
imports it, and `roles`/`reencrypt` start fresh interpreters. Migration 0010 logs to `alembic.runtime.migration`, which
`fileConfig` keeps, so the fixture's re-enabling hides no production log loss. The `print` output of the CLIs lies
outside SR-043's stated stream (backend, worker, scheduler), and it carries only labels, counts and row ids. The verdict
is CHANGES REQUESTED for findings 1 and 2.

1. **HIGH — the email expression is quadratic and runs on every record.** `backend/app/core/logging.py:18`: the
   unanchored `[A-Za-z0-9._+\-]+(?:@|%40)` restarts at every position of a long run and backtracks it to the end.
   QA timings for `redact_text`: 1 000 chars 5 ms, 4 094 chars (gunicorn's request-line limit, logged by
   `errors.py:189` on a 500) 92 ms, 8 000 chars 0.53 s, 16 000 chars 1.25 s, 1 000 000 chars did not finish. The same
   happens with no `@` at all (`"x"*n`, a hex run). Logging is synchronous, so one long token, blob or path in a
   message, an extra, an exception or a traceback blocks the API event loop or the worker (RISK-007). → Return early
   when the text has neither `@` nor `%40` (case-insensitive). Anchor the start with a lookbehind so each run is tried
   once (e.g. `(?<![\w.+%'\-])`), and bound the parts (`{1,64}` local, `{1,253}` domain). Add a test: 1 000 000 × `x`
   and 100 000 × `a` followed by `@!` are each redacted in under ~50 ms.
2. **HIGH — names reach the log through SQLAlchemy exception text (SR-043 AC 1).** `backend/app/db/repositories/session.py:16`
   creates the engine without `hide_parameters=True`, so every `StatementError` renders `[parameters: ...]`. QA probe
   through `configure_logging()`, logged as `errors.py:189` does: an IntegrityError on an insert of
   `(email, first_name, surname)` emitted `[parameters: ('[REDACTED-EMAIL]', 'Ada', 'Lovelace')]`. The 500 handler and
   uvicorn's "Exception in ASGI application" traceback both carry it. Any DataError, IntegrityError or timeout on an
   account or patient write leaks names or a date of birth. → `create_engine(..., hide_parameters=True)`, as
   `backend/app/db/reencrypt.py:344` already does (optional for `roles.py:119`). Add a test that a failed insert's
   logged exception holds no name. Record the remaining limit (a name in other free exception text) in this task and in
   PRB-011's Resolution.
3. **MEDIUM — the filter can raise into application code and lose the record.** `logging.py:88-103` and `60-77`: filters
   run in `Handler.handle`, outside `handleError`. QA probe: `log.info("x", extra={"thing": obj})`, where `str(obj)`
   raises, propagates `RuntimeError` to the caller. A self-referential or very deeply nested container raises
   `RecursionError`. This contradicts TS-017's unit criterion "the filter never drops a record", and it can turn a log
   call into a 500 or break Celery's failure handling. → Wrap the body of `filter` in `try/except Exception`. On failure,
   fail closed: set `msg` to a fixed "[log record could not be redacted: <ExcType>]", set `args = None`, delete the custom
   attributes, `exc_text` and `stack_info`, and return `True`. Give `redact_value` a depth limit (e.g. > 20 →
   `FIELD_PLACEHOLDER`) and use a `repr` fallback that cannot raise. Add tests for all three cases.
4. **MEDIUM — Unicode and IDN addresses are not "email-shaped" to the filter (SR-043 AC 2).** `logging.py:18` is
   ASCII-only. `jöhn.dœ@example.org`, `ada@bücher.de` and `ada@例え.テスト` pass unchanged. `email` is a plain `str` in
   `backend/app/api/schemas/account.py:19,28` (no validator), so such an address can be stored and then appear in an
   `SMTPRecipientsRefused`. `ada%2Btag%40example.org` leaves `ada%` in front of the placeholder, so part of the local part
   leaks. → Use Unicode classes (`[\w.+'\-]` plus `%[0-9A-Fa-f]{2}` in the local part, labels `[^\W_][\w\-]*`, TLD
   `[^\W\d_]{2,}` or `xn--[\w\-]+`) together with finding 1's anchoring. Add those cases to `test_log_redaction.py`.
   (Quoted local parts, IP literals and single-label domains are rare. Cover them or list them as accepted limits.)
5. **LOW — non-`str` dict keys drop the record.** `logging.py:66-71`: a `bytes` or `tuple` key is kept, so
   `json.dumps` (`:118`) raises `TypeError` and `handleError` prints "--- Logging error ---". No leak, but the record is
   lost. → Turn every key into `redact_text(str(k))`.
6. **LOW — SOUP-014's relied-on text does not match Celery 5.6.3.** Retry records (`celery/app/trace.py` `info()`,
   line 128) carry only `id`, `name` and `exc`. The real worker confirms it. The failure record (`_log_error`, 297-311)
   carries `args`/`kwargs`/`traceback`. The `celery.worker.strategy` "received" record carries `args`/`kwargs` for every
   task, success included, and is the most frequent carrier. → Correct the bullet in
   `docs/soup/SOUP-014-celery.md`. Also note that with the receiver connected, `--loglevel` is ignored (the root logger
   is always INFO).
7. **LOW — stale record text.** This task's "Implementation notes" ("Not done: SOUP-014 …", line 152) and the 1.4
   history entry ("SOUP-014 not edited", line 130) contradict SOUP-014 1.2, which was edited. → Update both. Record the
   known limit (finding 2).
8. **LOW — test leaves global logging state behind.** `backend/tests/workers/test_email_tasks_logging.py:155-158`
   calls `_enable_loggers()` without restoring, and leaves `email_tasks`' logger at INFO. → Restore both in the
   `finally`, as the `worker_log` fixture does.

Observations (not blocking):
- Matching by key substring also hides some non-personal names: `notification_id` and `annotation_count` (`note`),
  `token_count` (`token`), `description_length`, `recipient_count`, `emails_sent`. No current call site uses such a name
  (the extras in `backend/app` are `account_id`, `appointment_id`, `dataset_id`, `erased`, `failed`, `ts`,
  `environment`, `cors_origins`). This fails safe. Switch to exact or suffix matching only if a real field gets hidden.
- Celery's node name `celery@<host>.<domain>` is redacted (a false positive on an FQDN host). In Compose the host is the
  container id, which has no dot, so it is kept.
- The gunicorn master and anything logged before the lifespan (`Booting worker`, `Waiting for application startup`) are
  unfiltered and not JSON. They carry no personal data.

### Pre-existing issues (not blocking, outside SR-043's AC)

- `backend/app/api/errors.py:189` logs `request.url.path`. For `/api/v1/activation/{token}` that is the raw activation
  token, observed as `Unhandled exception for GET /api/v1/activation/QA138TOKENPATH`. The filter replaces fields named
  `token`, not a token inside a path. If gunicorn access logging is ever enabled, the access log would show it on every
  activation. `infra/reverse-proxy/nginx.conf` has no `access_log` directive, so nginx's default access log records the
  request line, token included. Suggest a PRB (credential in logs).

### Verification run (QA, 2026-11-06)

- `uv run pytest tests/test_log_redaction.py tests/workers tests/test_logging.py -q`: 35 passed.
- `uv run pytest --cov=app --cov-fail-under=85 -q`: 1467 passed, 6 skipped, 94.41 %. Other tasks' tests are in the same
  tree; nothing failed.
- `ruff check .`, `black --check app tests`, `mypy app`: clean.
- Real worker and beat (local processes, scratch Redis container `qa138-redis`, removed afterwards), as above.
  `infra/.env` sha256 is unchanged (`a4933b8c…96da`).
- Traceability on TASK-138, TS-017, PRB-011, SOUP-014, SR-043, CR-004, RISK-008: 0 errors. One warning, W5
  RISK-008 → SOUP-014 `in_review`, is expected while SOUP-014 waits for the human. SR-043's W1 is cleared (TS-017
  `verifies` SR-043). PRB-011 has `resolves` from CR-004.

## Round 2 notes (2026-11-07)

1. Quadratic expression: `redact_text` returns at once when the text has no `@` or `%40`; the expression is
   anchored with a lookbehind and every part is bounded (local part 1 to 64, labels 1 to 63, at most 126
   labels). Timings (`redact_text`): 1 MB of `x` 0.7 ms; 100 000 `a` then `@!` 1.4 ms; 50 000 `a@` 8 ms;
   200 000 characters on each side of an address 6 ms. Tests bound each at 50 ms.
2. Bound values in database error text: `hide_parameters=True` on the application engine
   (`app/db/repositories/session.py`) and on the other engines (`app/db/roles.py`, `app/db/alembic/env.py`,
   `scripts/setup_test_data.py`, `scripts/migrate_object_store.py`; `reencrypt.py` already had it).
   Test: a failing insert (unique constraint) logged as `app/api/errors.py` logs it holds no name.
   **Known limit (also in PRB-011):** a name that appears inside other free exception text, in a message
   or in a path cannot be recognized by shape; only email-shaped values and fields named like personal data
   are redacted. Call sites must not put names into messages or exceptions.
3. The filter never raises: the body is wrapped, and on failure the record is emitted with the fixed
   message `[log record could not be redacted: <ExcType>]` and without arguments, extra fields, exception
   text and stack. `redact_value` is depth-limited (20) and cycle-safe, and falls back from `str` to `repr`
   to a fixed label. A value that is not a container is emitted as its redacted text.
4. Unicode and IDN addresses and `%XX` in the local part are matched (`jöhn.dœ@example.org`,
   `ada@bücher.de`, `ada@例え.テスト`, `ada%2Btag%40example.org`). Accepted limits: a local part over 64
   characters, quoted local parts, IP literals and single-label domains are not matched.
   `celery@<container-id>` is kept (single label); a dotted node name such as `celery@host.example` is
   redacted (false positive, harmless).
5. Every dict key becomes a redacted string, so a `bytes` or tuple key cannot drop the record.
6. SOUP-014 text corrected: retry records carry no arguments; the failure and "task received" records do;
   `--loglevel` is ignored, the root level is fixed at INFO in `configure_logging()`.
7. This task's text on SOUP-014 corrected (history 1.4 and the notes above).
8. `test_success_records_hold_no_address_at_the_source` restores the logger level and disabled state.

Also fixed: the `stream` fixture of `test_log_redaction.py` re-enables loggers disabled by other tests
(the database test failed in suite order only).

Out of scope, reported to the coordinator: `app/api/errors.py:189` logs `request.url.path`, and the
reverse proxy's default access log records the request line, so `/api/v1/activation/{token}` puts the
activation token in logs (PRB candidate).

## QA review — round 2 (2026-11-07): APPROVED

All eight round-1 findings are closed. QA re-ran its probes against the new code.

1. **Closed.** Linear time. Adversarial inputs near the bounds: 1 MB of `x` 0.9 ms; 100 000 `a` then `@!` 2.1 ms;
   `(a@)×50k` 8.5 ms; `(a@b.)×50k` 63 ms (200 kB); a 64-character local part with `@!!` garbage, ×10k (670 kB), 51 ms;
   a 64-character local part with 126 or 200 labels and a numeric TLD, ×1-2k, 37-50 ms; `"."×1M` then `@x.org` 16 ms;
   `a@b.` followed by 1 M `c` 38 ms. Scaling is linear: `(a@b.)` 20/80/320 kB took 2/7.5/29 ms. With the lookbehind
   removed, 3 tests fail. Without the early return no test fails, because the anchor alone keeps it linear; the early
   return is only a speed-up.
2. **Closed.** `hide_parameters=True` is on every engine. With it removed, the new SQLite test fails. In
   `alembic/env.py` it hides only bound values in online-migration error text, and `alembic.ini` keeps
   `sqlalchemy.engine` at WARN, so no SQL echo is lost. Authors still see the SQL and the error. That is acceptable, and
   desirable, because data migrations here touch personal and clinical columns.
3. **Closed.** An extra whose `str`/`repr` raises (even with an address in the exception) prints `<unprintable Bad2>`.
   Self-referencing and 3 000-deep values are cut, not raised. A failure forced inside redaction (`MemoryError`) emits
   `[log record could not be redacted: MemoryError]` with no args, extras or exception text. Mutants: without the
   try/except, 2 tests fail; without the depth limit, 1 fails.
4. **Closed.** `jöhn.dœ@…`, `ada@bücher.de`, `ada@例え.テスト`, `ada%2Btag%40…`, `o'brien@…` and
   `ada@my_host.example.org` are redacted whole. An `re.ASCII` mutant fails 3 tests. The documented limits are as
   stated: a local part over 64 characters (`a×65@b.org` kept whole), quoted local parts, IP literals and single-label
   domains. Cosmetic: a quote or `b` prefix right before an address goes into the placeholder (`P(email=[REDACTED-EMAIL]')`).
5. **Closed.** `bytes` and tuple keys are emitted as redacted strings, and the record is kept.
6. **Closed.** The SOUP-014 text matches Celery 5.6.3 (`trace.py:128` retry; `_log_error` and `strategy.py` "received"
   carry args). The anomaly-review date of 2026-10-22 is untouched, and the record stays `in_review` for the human.
7. **Closed.** The text is corrected. QA moved the misplaced 1.5 history line (it had been appended inside the QA
   round-1 section) into "Version history".
8. **Closed.** Logger state is restored. `pytest tests/db tests/test_log_redaction.py tests/workers` in one process
   (Alembic first): 212 passed.

**Carried LOW, not blocking: `--loglevel` is ignored.** Before this task the worker's verbosity could be raised with
`--loglevel=debug`. Now `configure_logging()` fixes the root logger at INFO (`backend/app/core/logging.py`, last
function). The fix is small and is not a new setting: Celery's `setup_logging` signal already passes `loglevel`, so the
receiver in `backend/app/workers/celery_app.py` could pass it on (`configure_logging(level=loglevel or INFO)`). Debug
records would still go through the filter. Recorded in SOUP-014, so operators are told. This is a minor loss of
operability, not a safety or privacy issue. Left to the coordinator: take it as a follow-up or accept it.

**Correction to round 1's observations:** `notification_id` and `annotation_count` do not contain `note`, and they are
kept (probe: `notification_id` survives). The over-redaction examples that hold are `token_count`,
`description_length`, `recipient_count` and `emails_sent`.

Real worker, re-run: local `celery worker` against scratch Redis `qa138-redis` (removed afterwards), with the SMTP stub
refusing every recipient. QA sent `send_erasure_code_email` with `jöhn.qa138+tag@bücher.de` on the retry path and on
the final failure, and with `qa138.person@example.org` on the final failure (`SMTPRecipientsRefused({[REDACTED-EMAIL]': …})`).
Grep of stdout and stderr for `qa138`, `bücher`, `example.org` and the code: 0 hits.

### Verification run (QA, 2026-11-07)

- `uv run pytest --cov=app --cov-fail-under=85 -q`: **1507 passed, 6 skipped, 94.46 %** (shared tree with TASK-142 and
  TASK-205; no failure).
- `uv run pytest tests/db -q`: 159 passed. `uv run pytest modules/dicom_viewer/tests -q`: 25 passed.
- `uv run pytest tests/test_log_redaction.py tests/workers tests/test_logging.py -q`: 55 passed.
- `ruff check .`, `black --check .`, `mypy app`: clean.
- Traceability on TASK-138, TS-017, PRB-011, SOUP-014 and SR-043: 0 errors.
- `infra/.env` sha256 unchanged (`a4933b8c…96da`).

Status: TASK-138 `approved`, TS-017 `approved`, PRB-011 `resolved` (CR-004 D-8). SOUP-014 stays `in_review` for the human.
