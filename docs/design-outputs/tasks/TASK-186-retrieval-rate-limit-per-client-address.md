---
id: "TASK-186"
type: task
title: "Rate-limit anonymized-data retrieval per originating client address"
status: draft
version: "1.0"
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

- [ ] SR-042 AC 4: sixth attempt 429, code not evaluated, fixed window
      (`backend/tests/api/test_anonymized_retrieve.py`).
- [ ] SR-042 AC 5: client B unaffected by client A (same file).

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

- [ ] Backend suite passes; coverage ≥ 85 %.
- [ ] TS-016 updated; PRB-029 `resolved`.
- [ ] `traceability-check` shows no error for TASK-186, TS-016, SR-042, PRB-029.
