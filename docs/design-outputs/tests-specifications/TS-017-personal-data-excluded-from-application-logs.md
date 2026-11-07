---
id: "TS-017"
type: test-specification
title: "Personal data excluded from application logs verification"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-06"
updated: "2026-11-07"
links:
  - target: "SR-043"
    relation: verifies
tags: ["level:unit", "level:integration", "class:B", "cr:CR-004"]
---

# TS-017 — Personal data excluded from application logs verification

## Scope

Software requirement covered: SR-043 AC 1, AC 2, AC 3 (TASK-138). Software items under test: SI-API
logging `U-API-Logging` (`backend/app/core/logging.py`, ADD-005) and SI-WORKER logging
(`backend/app/workers/email_tasks.py`, `backend/app/workers/celery_app.py`, ADD-017). Levels: unit
(TC-017.1, TC-017.2) and integration (TC-017.2 handler wiring, TC-017.3 over Celery's own task
retry and failure logging).

## Preconditions and environment

Branch `fix/review-2026-07-security`. Backend Python 3.12 with the dependencies locked in
`backend/uv.lock`; Celery 5.6.3 (SOUP-014). No Redis, SMTP or database is needed: `_send_smtp` and the
repositories are patched. Log output is captured from the real root handler: `configure_logging()`
for the API, and Celery's `setup_logging` signal (`setup_logging.send`) for the worker and scheduler.
A failing task runs through `Task.apply()`, so Celery's own `celery.app.trace` retry and failure
records are emitted.

## Test cases

| ID | Verifies (SR / AC) | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-017.1 | SR-043 AC 1 | `backend/tests/workers/test_email_tasks_logging.py`: `test_success_records_hold_no_address_at_the_source`, `test_activation_email_success_logs_no_address`, `test_erasure_code_email_success_logs_no_address`, `test_appointment_notification_failure_logs_no_address`; `backend/tests/test_log_redaction.py`: `test_identifiers_survive`, `test_failed_insert_with_personal_data_does_not_reach_the_log` (engine with `hide_parameters=True`; negative control: remove it and the test fails). Negative control: restore `extra={"recipient": recipient_email}` in `send_erasure_code_email`: the source-record test fails | The records the tasks create (before any filter) hold no address; the logs name the account, appointment and dataset by id; UUIDs and account ids survive redaction | All listed tests pass; the negative control fails `test_success_records_hold_no_address_at_the_source` |
| TC-017.2 | SR-043 AC 2 | `backend/tests/test_log_redaction.py`: `test_extra_field_under_an_arbitrary_name_is_redacted`, `test_message_args_and_nested_values_are_redacted`, `test_exception_text_and_traceback_are_redacted`, `test_personal_and_credential_fields_are_redacted_by_name`, `test_malformed_format_string_does_not_leak_or_raise`, `test_every_handler_gets_the_filter_including_non_propagating_loggers`, `test_filter_is_what_redacts`, `test_unicode_idn_and_percent_encoded_addresses_are_redacted`, `test_celery_node_name_with_a_container_id_is_kept`, the linear-time, fail-closed and key tests named under the unit criteria; `backend/tests/workers/test_email_tasks_logging.py::test_setup_logging_signal_installs_the_filtered_handler`. Negative controls: no filter attached; filter blind to extra fields and exception text | Email-shaped values (also `%40`) in the message, `%s` args, nested dict/list values, dict keys, exception text and traceback are replaced by `[REDACTED-EMAIL]`; names, date of birth, clinical text, tokens and task arguments are replaced by field name; the filter is on the root handler (API, worker, scheduler through `setup_logging`) and on handlers of non-propagating loggers; configuring twice adds it once | All listed tests pass; filter not attached fails 8 tests; filter blind to extra and exceptions fails 5 (TASK-138 "Verification results") |
| TC-017.3 | SR-043 AC 3 | `backend/tests/workers/test_email_tasks_logging.py`: `test_erasure_code_email_failure_logs_no_address` (SMTPRecipientsRefused with the address, three Celery retries and the final failure record), `test_erasure_code_email_success_logs_no_address`, `test_activation_email_success_logs_no_address`; `backend/tests/test_log_redaction.py::test_extra_field_under_an_arbitrary_name_is_redacted` | With a known recipient address the captured worker output, success and failure, does not contain it, nor the retrieval code or activation token; an address in a field with an arbitrary name does not reach the record | All listed tests pass; both negative controls fail the failure-path test |

## Acceptance criteria (class B unit level)

Unit acceptance (§5.5.3): `redact_text` and `redact_value` are pure; scalars and objects whose text
has no address (UUID) are returned unchanged; containers are rebuilt, not mutated; a record whose
format string is malformed is emitted without its arguments; the filter never raises and never drops a record (evidence: `test_extra_whose_str_raises_does_not_raise_or_lose_the_record`, `test_self_referencing_and_very_deep_values_are_cut_not_raised`, `test_a_failure_inside_the_filter_fails_closed_and_keeps_the_record`, `test_extra_that_breaks_the_walk_is_dropped_not_raised`, `test_non_string_dict_keys_do_not_drop_the_record`); redaction runs in linear time (`test_redaction_runs_in_linear_time`, `test_a_long_message_with_an_address_is_still_redacted_quickly`, each under 50 ms).

## Verification results

Recorded in TASK-138 "Verification results" (2026-11-06): 1387 passed, coverage 94.38 %, three negative controls fail as listed in TC-017.1 to TC-017.3.

## Version history

- 1.0 (2026-11-06): TASK-138. Created for SR-043 AC 1 to AC 3 (TC-017.1 to TC-017.3). `in_review`.
- 1.1 (2026-11-07): TASK-138 round 2 (QA round 1). Unit criterion evidence updated (never raises, linear time); Unicode/IDN, database error text and fail-closed cases added to TC-017.1 and TC-017.2. `in_review`.
- 1.1 (2026-11-07): TASK-138 QA review round 2: `approved` (status only; content unchanged).
