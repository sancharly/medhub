---
id: "TS-015"
type: test-specification
title: "Deployment secrets and non-root containers verification"
status: approved
version: "1.7"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-08"
links:
  - target: "SR-041"
    relation: verifies
tags: ["level:unit", "level:integration", "class:B", "cr:CR-004"]
---

# TS-015 — Deployment secrets and non-root containers verification

## Scope

Software requirement covered: SR-041. Version 1.0 (TASK-197) covers AC 3, the start-up refusal of
missing or placeholder secrets and of a wrong-length `AT_REST_ENCRYPTION_KEY`, and CR-004 Q-5.
Version 1.1 (TASK-203) adds TC-015.2 and TC-015.4 (AC 2, AC 4) and the `hide_input_in_errors` guard to TC-015.3. Version 1.2 (TASK-198) adds TC-015.1 (AC 1, AC 6). Version 1.3 (TASK-191) extends TC-015.2 with the owner-URL guard and TC-015.1 with the Celery UID checks, and TC-015.3 with the owner/runtime role rule. Version 1.5 (TASK-196) extends
TC-015.3 with the object-store SSE key (AC 5: separate settings, equal keys refused) and TC-015.2 with its guard. Software item under test: SI-DEPLOY
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
| TC-015.1 | SR-041 AC 1, AC 6 | `infra/tests/test_images_non_root.py` (`ImageUsers`: `test_backend_image_ends_as_an_unprivileged_user`, `test_frontend_image_ends_as_an_unprivileged_user`, `test_every_built_compose_image_is_covered_and_non_root`, `test_compose_does_not_override_a_built_image_to_root`; `FrontendPort`: `test_frontend_listens_on_an_unprivileged_port`, `test_proxy_targets_the_frontend_port`, `test_pid_and_temp_paths_are_writable_by_the_unprivileged_user`); `infra/smoke-test.sh` section 11 on a started stack; started-stack record below | The last stage of every Dockerfile used by a Compose service with `build:` ends with a `USER` that is not root or 0 (backend `medhub`, frontend `nginx`, UID 101); the frontend listens only on 8080 and the proxy and `expose:` use 8080. On a started stack, for `backend`, `celery-worker`, `frontend` (running) and `object-store-init`, `object-store-preflight` (one-shot, image only): `Config.User` of the image is non-empty and not root/0, PID 1 and `id -u` of each running one are not 0, and `https://localhost/` through the proxy returns 200 with the app root | Tests pass; smoke section 11 reports no FAIL; negative controls: `USER nginx` removed from `frontend/Dockerfile` fails two unit tests and three smoke checks (`Config.User` empty, PID 1 UID 0, `id -u` 0); the proxy pointed back at `frontend:80` fails `test_proxy_targets_the_frontend_port` |
| TC-015.3 | SR-041 AC 3, SR-022 AC 3, CR-004 Q-5 | `backend/tests/core/test_secret_settings.py` (`test_missing_or_placeholder_secret_is_refused_by_name`, `test_database_url_without_a_password_is_refused`, `test_optional_secret_is_checked_only_when_present`, `test_each_retired_key_is_checked`, `test_wrong_length_at_rest_key_is_refused`, `test_32_byte_at_rest_key_is_accepted`, `test_non_base64_at_rest_key_is_refused_without_the_value`, `test_smtp_user_set_requires_a_real_password`, `test_smtp_without_user_needs_no_password`, `test_enforce_raises_system_exit_naming_the_setting_not_the_value`, `test_every_historical_template_value_is_a_known_placeholder`, `test_object_store_rule_shares_the_placeholder_list`, `test_distinct_owner_and_runtime_roles_pass`, `test_runtime_url_naming_the_owner_user_is_refused`, `test_runtime_password_equal_to_the_owner_password_is_refused_without_the_value`, `test_owner_url_placeholder_is_refused`), `backend/tests/core/test_object_store_credentials.py` (including the SSE-key cases of TASK-196: `test_sse_key_equal_to_the_field_key_is_refused_naming_both_settings`, `test_sse_key_equal_to_a_retired_field_key_is_refused`, `test_equality_is_compared_as_decoded_bytes_not_text`, `test_main_refuses_a_bad_sse_key_naming_the_setting_and_never_the_value`), `backend/tests/core/test_secret_settings.py` (`test_sse_key_must_be_32_bytes_and_distinct_from_the_field_keys`, `test_settings_env_reads_the_sse_key_from_settings`, `test_settings_refuse_an_sse_key_equal_to_the_field_key`), `backend/tests/test_lifespan.py::test_lifespan_refuses_a_placeholder_secret_before_starting`, `backend/tests/workers/test_celery_start_up.py`, `backend/tests/test_config.py` (`test_smtp_without_user_starts_without_password`, `test_smtp_user_without_password_is_refused_without_echoing_values`, `test_validation_error_never_echoes_a_rejected_value`) | The API, the worker and beat refuse to start when a secret setting is unset, empty, `changeme`, `change-me`, starts with `change-me`, or is any value the template shipped (any case); `AT_REST_ENCRYPTION_KEY` and each retired key must decode to 32 bytes (31 and 33 refused); `OBJECT_STORE_SSE_KEY` must be set, not a placeholder, 32 bytes, and **not equal (decoded bytes) to `AT_REST_ENCRYPTION_KEY` or a retired key**: the `object-store-preflight` refuses it, naming `OBJECT_STORE_SSE_KEY` and the other setting (SR-041 AC 5); the database password is the part checked in `DATABASE_URL`. The message names the setting and never the value, in the exception or in captured logs. SMTP without a user starts without a password; with a user and no password it is refused; a rejected `DATABASE_URL` value (`mysql://u:SENTINEL@h:5432/d`) never appears in the `ValidationError` text | Every secret setting has an unset, empty and placeholder case that is refused and a good case that is accepted; negative control: with the placeholder test removed from the rule, the placeholder cases fail; with `hide_input_in_errors=False` in `Settings.model_config`, the sentinel test fails; with the equality check removed from `sse_key_problems`, seven tests fail |
| TC-015.2 | SR-041 AC 2 | `infra/tests/test_compose_secrets.py` (`StaticGuards`: `test_every_secret_expression_is_required_and_names_its_setting`, `test_no_secret_is_set_to_a_literal`, `test_services_that_use_a_secret_guard_it_in_environment`, `test_the_secret_list_is_the_application_rule_list`; `infra/tests/test_compose_db_roles.py` (`StaticWiring`: `test_owner_url_is_guarded_in_db_migrate_only`, `test_no_service_reads_env_file`, `test_postgres_healthcheck_uses_tcp`; `RenderedWiring`: `test_owner_url_unset_or_empty_is_refused_naming_it`, `test_no_owner_credential_value_reaches_a_service_but_postgres_and_db_migrate`, `test_no_service_reads_env_file`, `test_each_application_service_gets_only_the_settings_it_reads`, `test_an_owner_url_in_the_shell_does_not_reach_the_backend`, `test_application_services_connect_as_the_runtime_role`); `BringUpRefusal`: `test_complete_environment_renders`, `test_unset_secret_is_refused_naming_it`, `test_empty_secret_is_refused_naming_it`, `test_the_template_alone_is_refused`); `infra/tests/test_ci_compose_env.py` (`test_the_step_writes_the_secret_variables`, `test_compose_renders_the_object_store_services_with_exactly_those_names`, `test_a_missing_guarded_name_would_stop_the_job`); bring-up record below | No secret setting has a `:-` default in `infra/docker-compose.yml`; `POSTGRES_PASSWORD`, `DATABASE_URL`, `AT_REST_ENCRYPTION_KEY` and the object-store keys are `${NAME:?NAME must be set}`, and `DATABASE_OWNER_URL` is guarded in `db-migrate` only; no service has `env_file`, so the owner password (`POSTGRES_PASSWORD`) and URL reach `postgres` and `db-migrate` only (round 2: the first version passed `POSTGRES_PASSWORD` through `env_file` and the name-only checks did not see it; the infra test is value-based, with the same values also in the project `.env`). On a started stack the smoke test reads the owner password from `postgres` and fails when it is in `/proc/1/environ` or `Config.Env` of any other running container in every service that uses them (`backend` and `celery-worker` in `environment:`); `docker compose config` with one of them unset or empty fails with a message naming it; the unfilled template alone fails | Tests pass; negative controls: a `:-` default on one secret, a guard removed from `celery-worker`, a literal password, each fails the test; `POSTGRES_PASSWORD` deleted from the CI step that writes `infra/.env` fails the CI-environment test; TASK-191: `DATABASE_OWNER_URL` given to `backend` fails `test_owner_url_is_guarded_in_db_migrate_only`; `env_file: .env` put back on `backend` fails 4 infra tests (including the value-based one) and the smoke check `'backend' holds no owner credential` |
| TC-015.4 | SR-041 AC 4 | `backend/tests/test_env_example.py` (`test_env_example_secret_settings_are_present_and_empty`, `test_env_example_secret_list_covers_the_application_rule`, `test_env_example_holds_no_placeholder_value`, `test_env_example_has_no_object_store_default_strings`; PRB-056: `test_env_example_loads_through_settings_with_the_secrets_filled`, `test_cors_origins_accepts_empty_json_and_comma_separated`, `test_cors_origins_unset_is_empty`, `test_cors_origins_refuses_a_malformed_list`); review of the "Secret settings" table in `infra/DEPLOY.md` | The template has every required secret setting with an empty value, holds no value of the shared placeholder list (any case) and no exception for `changeme`; the guide has a row (used by, how to generate, rotation) for each secret setting | Tests pass; negative control: a placeholder written into one template line fails `test_env_example_holds_no_placeholder_value`; guide reviewed by QA |

## Acceptance criteria (class B unit level, §5.5.3)

- Acceptance criteria covered by this version: AC 1 maps to TC-015.1, AC 2 maps to TC-015.2, AC 3 to TC-015.3, AC 4 to TC-015.4; AC 1 and AC 6 map to TC-015.1 (TASK-198); AC 5 maps to TC-015.3 (rule) and TC-014.7 in TS-014 (Compose wiring and the copy) as of TASK-196.
- Boundary conditions: a 31-byte and a 33-byte key refused, a 32-byte key accepted; a secret of whitespace only is empty.
- Fault handling: a refusal stops the process (`SystemExit`) before the application serves a request or the worker takes a task.

## Bring-up record (TC-015.2, TASK-203)

See the TASK-203 implementation notes: `docker compose config` with each of `POSTGRES_PASSWORD`, `DATABASE_URL` and `AT_REST_ENCRYPTION_KEY` unset and empty, and with the unfilled template, exits non-zero naming the setting.

## Started-stack record (TC-015.1, TASK-198)

See the TASK-198 implementation notes: project `task198` built from the working tree and started with a temporary env file; `infra/smoke-test.sh` 38 passed, 0 failed; `Config.User` and PID 1 UID per service; the SPA served through the proxy on the new upstream port. TASK-191 repeats the check with the real Celery processes: `celery-worker` and `celery-beat` PID 1 UID is non-zero and PID 1 is `celery ... worker` / `celery ... beat` (project `task191`, `infra/smoke-test.sh` 59 passed, 0 failed; see the TASK-191 implementation notes).

## Notes

The check reads the configured settings; optional settings that are not `Settings` fields
(`DATABASE_OWNER_URL`, `AT_REST_ENCRYPTION_RETIRED_KEYS`, `OBJECT_STORE_SSE_KEY`) are read from the
process environment and checked when present.

## Version history

- 1.0 (2026-10-31) — TASK-197: created with TC-015.3. `in_review`.
- 1.0 (2026-10-31) — QA review (TASK-197): approved (`in_review → approved`). TASK-198, TASK-203 and TASK-196 return it to `in_review` when they add their cases.
- 1.1 (2026-11-01) — TASK-203 (round 2 adds the CI-job environment test to TC-015.2): TC-015.2 and TC-015.4 added, TC-015.3 gains the `hide_input_in_errors` test. Content change, `in_review`.
- 1.1 (2026-11-01) — QA review (TASK-203 round 2): approved (`in_review → approved`).
- 1.2 (2026-11-01) — TASK-198: TC-015.1 added (AC 1, AC 6: non-root user in every built image, unprivileged frontend port, started-stack UID checks). Content change, `in_review`.
- 1.2 (2026-11-01) — QA review (TASK-198): approved (`in_review → approved`). Started-stack record re-run by QA (project `qa198`, 38 passed, 0 failed).
- 1.3 (2026-11-01) — TASK-191: TC-015.2 gains the owner-URL guard tests, TC-015.1 the Celery worker and beat UID evidence, TC-015.3 the owner/runtime role rule (`DATABASE_URL` and `DATABASE_OWNER_URL` differ in user and password). Content change, returned to `in_review`.
- 1.4 (2026-11-01) — TASK-191 round 2 (QA finding 1): TC-015.2 checks the owner credential by value (infra render and started-stack `/proc/1/environ`), no `env_file`, TCP healthcheck. Stays `in_review`.
- 1.5 (2026-11-01) — TASK-196: TC-015.3 gains the SSE-key rule (separate setting, 32 bytes, refused when equal to the field key or a retired key) and `infra/tests/test_compose_secrets.py` guards `OBJECT_STORE_SSE_KEY` in the preflight and keeps it out of every Python service; AC 5 mapped. Content change, returned to `in_review`.

- 1.6 (2026-11-02) — Status `approved`: approved by the human's decision of 2026-11-02 (CR-004 D-10: TASK-196 accepted with the QA round-2 text fix, no QA re-review).
- 1.7 (2026-11-08) — TASK-202: the PRB-056 tests in `backend/tests/test_env_example.py` are named in TC-015.4 (TASK-193 QA). They check that the template loads and that `CORS_ORIGINS` takes the empty, JSON and comma-separated forms; they do not validate each origin (a non-list string such as `*` or `null` is read as one origin; harmless while `cors_origins` is only logged and no `CORSMiddleware` is installed, to be validated before CORS is wired). Content change, `in_review`.
- 1.7 (2026-11-08) — QA review of TASK-202 (round 2): `approved` (status only; content unchanged).
