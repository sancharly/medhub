---
id: "TS-015"
type: test-specification
title: "Deployment secrets and non-root containers verification"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-041"
    relation: verifies
tags: ["level:unit", "level:integration", "class:B", "cr:CR-004"]
---

# TS-015 — Deployment secrets and non-root containers verification

## Scope

Software requirement covered: SR-041. Version 1.0 (TASK-197) covers AC 3, the start-up refusal of
missing or placeholder secrets and of a wrong-length `AT_REST_ENCRYPTION_KEY`, and CR-004 Q-5.
TASK-198 adds TC-015.1 (AC 1), TASK-203 adds TC-015.2 and TC-015.4 (AC 2, AC 4), TASK-196 extends
TC-015.3 with the object-store SSE key (AC 5). Software item under test: SI-DEPLOY
`U-DEP-SecretRule` (`backend/app/core/secret_settings.py`, ADD-026). Levels: unit, integration
(start-up paths).

## Preconditions and environment

Branch `fix/review-2026-07-security`. Backend Python 3.12 with the dependencies locked in
`backend/uv.lock`. No external service: the tests set their environment variables with
`monkeypatch`, and the start-up paths are driven in process (the ASGI lifespan, the Celery
`worker_init` and `beat_init` handlers).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-015.3 | SR-041 AC 3, SR-022 AC 3, CR-004 Q-5 | `backend/tests/core/test_secret_settings.py` (`test_missing_or_placeholder_secret_is_refused_by_name`, `test_database_url_without_a_password_is_refused`, `test_optional_secret_is_checked_only_when_present`, `test_each_retired_key_is_checked`, `test_wrong_length_at_rest_key_is_refused`, `test_32_byte_at_rest_key_is_accepted`, `test_non_base64_at_rest_key_is_refused_without_the_value`, `test_smtp_user_set_requires_a_real_password`, `test_smtp_without_user_needs_no_password`, `test_enforce_raises_system_exit_naming_the_setting_not_the_value`, `test_every_historical_template_value_is_a_known_placeholder`, `test_object_store_rule_shares_the_placeholder_list`), `backend/tests/core/test_object_store_credentials.py`, `backend/tests/test_lifespan.py::test_lifespan_refuses_a_placeholder_secret_before_starting`, `backend/tests/workers/test_celery_start_up.py`, `backend/tests/test_config.py` (`test_smtp_without_user_starts_without_password`, `test_smtp_user_without_password_is_refused_without_echoing_values`) | The API, the worker and beat refuse to start when a secret setting is unset, empty, `changeme`, `change-me`, starts with `change-me`, or is any value the template shipped (any case); `AT_REST_ENCRYPTION_KEY` and each retired key must decode to 32 bytes (31 and 33 refused); the database password is the part checked in `DATABASE_URL`. The message names the setting and never the value, in the exception or in captured logs. SMTP without a user starts without a password; with a user and no password it is refused | Every secret setting has an unset, empty and placeholder case that is refused and a good case that is accepted; negative control: with the placeholder test removed from the rule, the placeholder cases fail |

## Acceptance criteria (class B unit level, §5.5.3)

- Each acceptance criterion of SR-041 covered by this version (AC 3) maps to TC-015.3; AC 1, AC 2, AC 4 and AC 5 are added by TASK-198, TASK-203 and TASK-196.
- Boundary conditions: a 31-byte and a 33-byte key refused, a 32-byte key accepted; a secret of whitespace only is empty.
- Fault handling: a refusal stops the process (`SystemExit`) before the application serves a request or the worker takes a task.

## Notes

The check reads the configured settings; optional settings that are not `Settings` fields
(`DATABASE_OWNER_URL`, `AT_REST_ENCRYPTION_RETIRED_KEYS`, `OBJECT_STORE_SSE_KEY`) are read from the
process environment and checked when present.

## Version history

- 1.0 (2026-10-31) — TASK-197: created with TC-015.3. `in_review`.
- 1.0 (2026-10-31) — QA review (TASK-197): approved (`in_review → approved`). TASK-198, TASK-203 and TASK-196 return it to `in_review` when they add their cases.
