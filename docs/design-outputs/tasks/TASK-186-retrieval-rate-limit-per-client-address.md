---
id: "TASK-186"
type: task
title: "Rate-limit anonymized-data retrieval per originating client address"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-042"
    relation: implements
  - target: "SR-024"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "RISK-008"
    relation: mitigates
  - target: "PRB-029"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-185"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
tags: ["security", "cr:CR-004", "control:design"]
---

# TASK-186 — Rate-limit anonymized-data retrieval per originating client address

- **Software item / unit:** SI-API `U-API-RateLimit` (new, ADD-005).
- **PRB:** PRB-029. **CR:** CR-004.
- **Depends on:** TASK-185.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** S (`backend/app/api/routers/anonymized_data.py`; 1 test file; TS-016)
- **Design:** ADR-0019; ADR-0013 (5 attempts per 3600 s, unchanged, CR-004 A-4)

## Objective

SR-042 AC 4, AC 5: count per originating client address; the sixth attempt from one address in
the 3600-second window that starts at its first counted attempt gets 429 without the code being
evaluated; one client's attempts never count against another's. The PRB-029 Investigation also
found the counter non-atomic and its window sliding.

## Implementation detail

- Key: `rate:anonymized_retrieve:{client_address(request)}`; when the address is `None` (no
  peer at all), refuse with 429 rather than share an `"unknown"` bucket.
- Count atomically: `INCR`; when the result is 1, `EXPIRE key 3600` (`NX` semantics, so the
  window starts at the first counted attempt and is not extended); refuse when the result is
  greater than 5. The check runs before `svc.retrieve_anonymized` is called.
- Remove the now-unused `request.client.host` read (`anonymized_data.py:66`); TASK-185's static
  check then has no exceptions left.

## Tests (write first)

`backend/tests/api/test_anonymized_retrieve.py` (extend; `fakeredis`, ASGI transport with a set
peer and `X-Forwarded-For`, `TRUSTED_PROXIES` set to the peer):

- attempts 1..5 from client A are evaluated; the 6th → 429 and the retrieval service is not called;
- after A is limited, client B through the same proxy is evaluated (AC 5);
- the window does not slide: with time advanced 3599 s after the first attempt, still 429; at
  3601 s, evaluated again;
- a forged `X-Forwarded-For` from an untrusted peer counts against the peer, not the forged address;
- concurrency: 10 threads at once from one address → exactly 5 evaluated.

## Acceptance criteria

- [x] SR-042 AC 4: sixth attempt 429, code not evaluated, fixed window
      (`backend/tests/api/test_anonymized_retrieve.py`).
- [x] SR-042 AC 5: client B unaffected by client A (same file).

## Verification

```sh
cd backend && uv run pytest tests/api/test_anonymized_retrieve.py tests/core/test_client_address.py tests/api/test_client_address_middleware.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

Negative control: key on the peer again; the AC 5 test fails.

## Records

- **TS-016**: TC-016.4 (per-address limit, fixed window, refusal before evaluation), TC-016.5
  (two clients through one proxy), under TASK-185's version.
- **PRB-029**: `## Resolution`, `resolved`.

## Definition of Done

- [x] Backend suite passes; coverage ≥ 85 %.
- [x] TS-016 updated; PRB-029 `resolved`.
- [x] `traceability-check` shows no error for TASK-186, TS-016, SR-042, PRB-029.

## Implementation notes

- `backend/app/api/routers/anonymized_data.py`: `_check_rate_limit(address, r)` now takes the
  originating address from `client_address(request)` (TASK-185). `None` raises
  `RateLimitedError` before any Redis call. The count is one `MULTI/EXEC` pipeline of `INCR` and
  `EXPIRE key 3600 NX`; the attempt is refused when the `INCR` result is greater than 5. The
  check runs before `svc.retrieve_anonymized`. The `request.client.host` read is removed.
- Deviation from the task text: `EXPIRE ... NX` runs on every attempt inside the same transaction,
  not only when the result is 1. Same window semantics (NX never extends an existing expiry), and a
  key that ever lost its expiry is given one instead of staying counted for ever. Redis 7.4 (pinned
  in `infra/docker-compose.yml`) supports `NX`.
- `backend/tests/api/test_anonymized_retrieve.py`: the old mock-based
  `test_rate_limit_rejects_after_threshold` (asserted the `GET` read, which no longer exists) is
  replaced by `TestRetrievalRateLimitPerAddress` (fakeredis, ASGI peer set via `TestClient(client=...)`,
  `TRUSTED_PROXIES` set to the peer, `time.time` advanced for the window test).
- `backend/tests/api/test_client_address_middleware.py` (TASK-185 QA follow-up): `KNOWN_READS` is
  empty; the check now matches `.client` attribute reads (not `.client(` calls), `["client"]` and
  `.get("client"`, so it catches `request.client.host`, `request.client[0]`, `scope["client"]` and
  `scope.get("client")`. Two tests prove it on temporary files and that `boto3.client(...)` is ignored.
  `grep -rn "client.host" backend/app` finds nothing.
- No schema change: OpenAPI files are unchanged.

## Verification results

| AC | Test (`backend/tests/api/test_anonymized_retrieve.py`) |
|---|---|
| SR-042 AC 4 | `test_sixth_attempt_is_refused_and_not_evaluated`, `test_window_is_fixed_from_the_first_attempt`, `test_forged_header_from_untrusted_peer_counts_against_the_peer`, `test_missing_peer_is_refused_without_a_shared_bucket`, `test_concurrent_attempts_from_one_address_evaluate_exactly_five` |
| SR-042 AC 5 | `test_client_b_is_evaluated_after_client_a_is_limited` |

- `uv run pytest tests/api/test_anonymized_retrieve.py tests/core/test_client_address.py tests/api/test_client_address_middleware.py`: 44 passed.
- `uv run pytest --cov=app --cov-fail-under=85`: 638 passed, 4 skipped, coverage 91.77 %.
- `uv run ruff check .`, `uv run black --check .`, `uv run mypy app`: clean.
- Negative controls (source edited, then restored from a copy):
  1. key on `request.client.host`: `test_client_b_is_evaluated_after_client_a_is_limited` and
     `test_no_code_reads_the_tcp_peer_outside_client_address` fail;
  2. `EXPIRE` without `NX`: `test_window_is_fixed_from_the_first_attempt` fails;
  3. `GET`, compare, then `INCR` (non-atomic): `test_concurrent_attempts_from_one_address_evaluate_exactly_five` fails.

## QA review (QA engineer, 2026-10-31)

**Verdict: APPROVED.** No CRITICAL, HIGH or MEDIUM finding.

Judgements:

- **`EXPIRE key 3600 NX` on every attempt** (`anonymized_data.py:40`): same window as "EXPIRE
  only when INCR == 1". `INCR` creates the key with no expiry; `NX` sets one only then and never
  touches an existing one; `MULTI/EXEC` keeps the pair atomic. It also heals a key that lost its
  expiry. Pinned Redis is 7.4.12 (`infra/docker-compose.yml:116`, SOUP-021); `NX` needs ≥ 7.0.
  redis-py 8.0.0 (SOUP-013) has the `nx=` argument. Checked against the pinned image: the
  remaining TTL stayed at 100 s over six more attempts; a key with no expiry got 3600 s back.
- **Refused attempts still `INCR`:** this matches SR-042 AC 4. The window starts at the first
  counted attempt and refused attempts never extend it (`NX`), so the caller is released 3600 s
  after the first attempt. The counter going past 5 has no effect.
- **`None` address refused without Redis** (`anonymized_data.py:33`): this fails closed. ADR-0019
  gives `None` only when there is no request peer, which a deployed TCP request always has. A
  shared `"unknown"` bucket would bring back PRB-029. SR-042 says nothing on this case, so it
  conflicts with nothing.
- **Widened static check:** it catches `request.client.host`, `scope["client"]`,
  `request.client[0]`, `scope.get("client")` (spacing doesn't matter), tuple unpacking and
  multi-line chains. It ignores `boto3.client(...)`. `grep client.host / ["client"] /
  .get("client"` in `backend/app` finds only `core/client_address.py:89`. Gaps are in finding 1.
- **PRB-029 `resolved`:** valid. CR-004 has `resolves` PRB-029 and the Resolution gives a
  reproducible command that passes. Its wording is in finding 4.

Findings (all LOW, not blocking):

1. **[LOW] Static check misses `getattr` and exempts any file named `client_address.py`.** At
   `backend/tests/api/test_client_address_middleware.py:103` and `:117`,
   `getattr(request, "client")` is not matched. The exemption tests `path.name`, so any
   `client_address.py` in any package is exempt (probe: `sub/client_address.py` with
   `request.client.host` passes). Fix: compare `path.relative_to(app_dir) != Path("core/client_address.py")`
   and add `| getattr\(\s*\w+\s*,\s*['"]client['"]` to `_PEER_READS`, with a parametrised case.
   Pick it up in TASK-189 (static-check task) or TASK-201.
2. **[LOW] The Redis SOUP records don't name the rate-limit counter.** SOUP-021:26 and
   SOUP-013:26 list only the session store and Celery. The limit now relies on `INCR`,
   `MULTI/EXEC` and `EXPIRE ... NX` (Redis ≥ 7.0; redis-py `nx=`). Fix: add these to "Functional
   and performance requirements" in TASK-199, which already updates both records for
   `WATCH`/`MULTI` (CR-004 Plan, "SOUP touched").
3. **[LOW] RISK-008 has no control row for this task.** TASK-186 and the CR-004 Plan say it
   `mitigates` RISK-008, but the RISK-008 control table has no retrieval-rate-limit row (only
   RISK-007:86 has one). Fix: carried to TASK-202, which re-scores. RISK-008 not edited.
4. **[LOW] PRB-029 overstates the old window.** `PRB-029:37` and `:53` say a caller "who kept
   trying was never released". The old code raised before the pipeline, so refused attempts did
   not refresh the expiry, and the caller was released 3600 s after the fifth counted attempt.
   Fix: "the window ran from the last counted attempt (the fifth), not the first".
5. **[LOW] `test_missing_peer_is_refused_without_a_shared_bucket` proves less than its name.**
   At `backend/tests/api/test_anonymized_retrieve.py:167-173`, `retrieve.call_count == 0` is
   always true because the test calls `_check_rate_limit` directly. Fix: pass the fixture's
   `FakeRedis` and assert `r.keys("rate:*") == []` after the raise. The `"unknown"` mutation still
   fails it (see the negative controls below), so the behaviour is covered.

Carried from TASK-185's review (LOW 1): RISK-007's control row (`RISK-007:86` area) should also
name TASK-185 → carried to TASK-202. RISK-007 not edited.

Verification run (QA, 2026-10-31):

- `uv run pytest tests/api/test_anonymized_retrieve.py tests/core/test_client_address.py tests/api/test_client_address_middleware.py`: 44 passed.
- `uv run pytest --cov=app --cov-fail-under=85`: 638 passed, 4 skipped (`OBJECT_STORE_INTEGRATION`
  only), coverage 91.77 %.
- `uv run ruff check .`, `uv run black --check .`, `uv run mypy app`: clean.
- OpenAPI export compared with `backend/openapi/openapi.json`: identical; generated files untouched.
- Negative controls run through a scratchpad pytest plugin, with no source edits:
  (a) `client_address` replaced by the raw TCP peer: only
  `test_client_b_is_evaluated_after_client_a_is_limited` fails (1 failed, 8 passed);
  (b) `None` mapped to a shared `"unknown"` bucket: `test_missing_peer_is_refused_without_a_shared_bucket`
  fails.
- Real Redis probe (`redis:7.4.12-bookworm@sha256:b6b6e3dc…`): attempts →
  `[ok×5, 429, 429]`, counter 7, TTL not reset by `NX`; a `PERSIST`ed key got its expiry back.
- Traceability (throwaway checker, scope TASK-186, TS-016, PRB-029, SR-042, TASK-185, TASK-137,
  PRB-010, CR-004 and their neighbours, 405 records scanned): **0 errors**, 7 warnings (W5
  TASK-185→ADD-026 and ADD-005→SOUP-004/005 `in_review`; W1 SR-041, SR-043 no TS yet; W6 CR-002→SOUP-022/023
  obsolete). Re-run on TASK-186, TS-016 and PRB-029 after this approval: 0 errors, 3 warnings
  (the W5 above). SR-042 has no TR yet (W2, release scope).

## Checkpoint A result (QA engineer, 2026-10-31)

The CR-004 Plan does not say where checkpoint results go, so this one is recorded here.

**PASSED** (TASK-185, TASK-137, TASK-186):

- Backend suite green, coverage ≥ 85 %: 638 passed, 4 skipped, 91.77 %.
- A 403 through a trusted peer leaves an `AUTHZ_DENIED` row with the client address:
  `tests/audit/test_audit_client_address.py::test_authz_denied_row_records_client_address_through_trusted_peer`
  passed on a real database (4/4 in that file, including the forged-header and consent cases).
- Two clients through one proxy have separate buckets: `test_client_b_is_evaluated_after_client_a_is_limited`
  passed, and the peer-keyed negative control fails it.
- SR-042 AC 1–3 (TS-016 TC-016.1–3), AC 4–5 (TC-016.4–5) and SR-023 AC 6 (TS-009 TC-009.9) all
  have passing tests.
- PRB-010 `resolved` and PRB-029 `resolved`, each with a `resolves` link from CR-004.
  TASK-185, TASK-137 and TASK-186 are `approved`, and so are TS-016 and TS-009.
- `cd infra && python3 -m unittest discover -s tests`: 37 tests OK.

## Version history

- 1.1 (2026-10-31) — Implemented; handed to QA (`in_review`). Implementation notes and verification results added.
- 1.1 (2026-10-31) — QA review: APPROVED (`in_review → approved`); review and Checkpoint A result recorded.
