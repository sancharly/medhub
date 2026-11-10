---
id: "TASK-185"
type: task
title: "Determine the originating client address with one trusted-proxy rule"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-042"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "RISK-006"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "PRB-010"
    relation: relates_to
  - target: "PRB-029"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
tags: ["security", "audit", "cr:CR-004", "control:protective"]
---

# TASK-185 — Determine the originating client address with one trusted-proxy rule

- **Software item / unit:** SI-API `U-API-ClientAddress` (new, ADD-005); SI-DEPLOY `U-DEP-Compose` (ADD-026).
- **PRB:** PRB-010, PRB-029 (both need this rule). **CR:** CR-004.
- **Depends on:** none. **Gate** for TASK-137 and TASK-186.
- **Branch:** `fix/review-2026-07-security`. One commit per QA-approved task, with its records.
- **Size:** M (new `backend/app/core/client_address.py`; `main.py`, `config.py`,
  `infra/docker-compose.yml`, `backend/entrypoint.sh`; 2 test files; TS-016)
- **Needs:** a Docker host for the started-stack check.
- **Design:** [ADR-0019](../../design/adr/0019-originating-client-address-trusted-proxy-rule.md)

## Objective

SR-042 AC 1 to AC 3: the address is the TCP peer unless the peer is a trusted proxy, then the
right-most `X-Forwarded-For` entry that is not a trusted proxy; a header from an untrusted peer is
ignored; the trusted proxies are a setting, empty means none, and the deployment sets it to the
reverse proxy.

## Implementation detail

1. `backend/app/core/client_address.py`:
   - `parse_trusted_proxies(value: str) -> tuple[IPv4Network | IPv6Network, ...]` (comma-separated
     addresses or CIDRs; an invalid entry raises `ValueError` naming the entry);
   - `originating_address(peer: str | None, xff: str | None, trusted) -> str | None` (the rule,
     pure function; malformed `X-Forwarded-For` entries are skipped, never trusted);
   - `ClientAddressMiddleware` (pure ASGI, not `BaseHTTPMiddleware`): sets
     `scope["state"]["client_address"]` and a module-level `ContextVar[str | None]`, resets it
     after the request;
   - `current_client_address() -> str | None` and `client_address(request) -> str | None`.
2. `backend/app/core/config.py`: `trusted_proxies: str = ""`, validated at start-up with
   `parse_trusted_proxies`.
3. `backend/app/main.py`: mount the middleware outermost.
4. `backend/entrypoint.sh`: Gunicorn `--forwarded-allow-ips=` (empty) so the server never
   rewrites the peer; confirm on the started stack that `request.client.host` is the proxy's.
5. `infra/docker-compose.yml`: the `medhub` network gets `ipam` with a fixed subnet; the
   `reverse-proxy` gets a fixed `ipv4_address`; `backend` gets `TRUSTED_PROXIES` set to that address
   (in `environment:`, so `.env` cannot widen it by accident). DEPLOY.md: how to change the subnet.
6. A test (below) fails when code under `backend/app` reads `request.client.host` outside
   `client_address.py`. TASK-137 and TASK-186 remove the current reads; until then the test
   lists them as known exceptions, and TASK-186 empties the list.

## Tests (write first)

- `backend/tests/core/test_client_address.py` (unit, the pure function and the parser):
  untrusted peer with header → peer; trusted peer, `XFF: client` → client; chain
  `client, proxy2` with both proxies trusted → client; all entries trusted → the left-most;
  forged `XFF: 1.2.3.4, client` through the trusted proxy → `client` (right-most untrusted);
  empty setting → peer always; malformed entries; IPv6; invalid setting → `ValueError`.
- `backend/tests/api/test_client_address_middleware.py` (ASGI, `httpx` transport with a set
  client address): the value reaches `request.state` and the `ContextVar`; it is reset after the
  request; the no-`client.host` static check.
- Started stack (smoke): through the proxy, a request's recorded address (TASK-137's audit row,
  or a debug log of the middleware until then) is the caller's, not the proxy's address.

## Acceptance criteria

- [x] SR-042 AC 1: right-most untrusted entry from a trusted peer (`backend/tests/core/test_client_address.py`).
- [x] SR-042 AC 2: header from an untrusted peer ignored (same file, and the middleware test).
- [x] SR-042 AC 3: empty setting trusts nothing; the Compose file sets the proxy's fixed address
      (`backend/tests/core/test_client_address.py`, `infra/tests/test_compose_trusted_proxy.py`).

## Verification

```sh
cd backend && uv run pytest tests/core/test_client_address.py tests/api/test_client_address_middleware.py -v
cd infra && python3 -m pytest tests/test_compose_trusted_proxy.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
infra/smoke-test.sh      # on a started stack
```

Negative control: trust the header from any peer; the AC 2 tests fail.

## Records

- **TS-016** (new, `verifies` SR-042): TC-016.1 (rule), TC-016.2 (untrusted header ignored),
  TC-016.3 (setting, Compose value, started-stack check). TASK-186 adds TC-016.4..5.
- **SOUP-005** (Gunicorn), **SOUP-004** (Uvicorn): record that MedHub relies on the forwarded
  header handling being **off**; `in_review`.
- **ADD-005** 1.1, **ADD-026** 1.0: confirm the unit text.

## Definition of Done

- [x] Backend and infra tests pass; coverage ≥ 85 %; started-stack check recorded.
- [x] TS-016 `in_review`; SOUP-004/005 `in_review`.
- [x] `traceability-check` shows no error for TASK-185, TS-016, SR-042.

## Implementation notes (Software Developer role, 2026-10-31)

- `backend/app/core/client_address.py`: `parse_trusted_proxies`, `originating_address`,
  `ClientAddressMiddleware` (pure ASGI; HTTP and WebSocket scopes; sets `scope["state"]` and the
  `ContextVar`, reset in `finally`), `current_client_address`, `client_address`. The trusted set is
  read lazily from `get_settings().trusted_proxies` on the first request (settings are not available
  at import time, when `app = create_app()` runs) and cached per setting value; tests may pass `trusted=`.
- `config.py`: `trusted_proxies: str = ""` with a `field_validator` calling `parse_trusted_proxies`,
  so an invalid entry makes `Settings()` fail (start-up refused, the lifespan calls `get_settings()`).
  `infra/.env.example` gets an empty `TRUSTED_PROXIES=` (the settings-coverage test requires it).
- `main.py`: middleware added last, so it is outermost. `entrypoint.sh`: `--forwarded-allow-ips=`.
- `docker-compose.yml`: `medhub` subnet `172.28.77.0/24` with `ip_range: 172.28.77.128/25`;
  `reverse-proxy` at `172.28.77.2`; `backend` `environment: TRUSTED_PROXIES: 172.28.77.2`.
  DEPLOY.md: section "Trusted proxy and the Compose subnet".
- Records: TS-016 1.0 (new), SOUP-004 and SOUP-005 1.2, ADD-026 1.1, all `in_review`. ADD-005 1.1
  unit text (`U-API-ClientAddress`) matches the implementation; no change.

### Deviations from the task text

1. `ip_range` added to the network (not in the task). Found on the started stack: with only a fixed
   `ipv4_address` for the proxy, Docker handed `172.28.77.2` to the frontend container, because
   `backend` depends on services that start before the proxy, and the proxy failed to start
   (`Address already in use`). Dynamic addresses now come from `172.28.77.128/25`, the proxy's
   address is outside it, and `test_compose_trusted_proxy.py` checks that. ADD-026 updated.
2. The infra test is run with `python3 -m unittest discover -s tests` because `pytest` is not
   installed for the system `python3`; the file is also valid for pytest.
3. The started-stack check used a throwaway probe route (scratchpad override, no repository file)
   instead of a debug log in the middleware, because the JSON log formatter has no extra fields and
   the level is INFO; TASK-137's audit row will give the permanent evidence.
4. The Compose file has no change for the CI override (`compose.ci-object-store.yml` does not touch `medhub`).

## Verification results (Software Developer role, 2026-10-31)

- `cd backend && uv run pytest tests/core/test_client_address.py tests/api/test_client_address_middleware.py -v`:
  27 passed.
- `cd infra && python3 -m unittest discover -s tests -v`: 37 passed (5 new in
  `test_compose_trusted_proxy.py`, 32 existing).
- `cd backend && uv run pytest --cov=app --cov-fail-under=85`: 618 passed, 4 skipped, coverage 91.65 %.
  `uv run ruff check .`, `uv run black --check .` and `uv run mypy app`: clean.
- Negative control: removing the trusted-peer test from `originating_address` (header trusted from
  any peer) fails 4 tests (`test_untrusted_peer_header_is_ignored`, `test_empty_setting_trusts_no_peer`,
  `test_forged_header_from_untrusted_peer_is_ignored`,
  `test_empty_setting_ignores_the_header_from_every_peer`); restored, 27 pass.
- Started stack (project `task185`, fresh volumes, temporary `infra/.env` restored byte-identical,
  host ports remapped to 127.0.0.1:18080/18443 because 80/443 were in use, probe route returning
  `request.client.host` and the originating address; `infra/.env` set `TRUSTED_PROXIES=0.0.0.0/0` to
  show it does not widen the setting):
  - proxy at `172.28.77.2`, other containers from `172.28.77.129`;
  - from the host, with and without a forged `X-Forwarded-For: 1.2.3.4`: peer `172.28.77.2`,
    address `172.28.77.128` (the Docker Desktop NAT source), not the proxy's, forged value ignored;
  - from the frontend container (`172.28.77.130`) with `X-Forwarded-For: 1.2.3.4, 5.6.7.8`: address
    `172.28.77.130`;
  - direct to the backend from the frontend container with a forged header: peer and address both
    `172.28.77.130` (untrusted peer, AC 2);
  - with `TRUSTED_PROXIES` empty: address `172.28.77.2`, the proxy's (the silent failure mode).
  `infra/smoke-test.sh` was not run on the full stack as it targets the default project; the
  object-store checks are unchanged by this task.

## QA review (QA engineer, 2026-10-31)

**Verdict: APPROVED.** TASK-185 → `approved`; TS-016 1.0 → `approved`. SOUP-004 1.2, SOUP-005 1.2
and ADD-026 1.1 stay `in_review` for the human (their approval record was removed because their
content changed; this is expected and is not a finding). SR-042, ADR-0019, RISK-006 and RISK-007
are not edited.

Security logic (checked against the code, not the summary):

- Right-most-untrusted rule (`backend/app/core/client_address.py:50-63`): the peer is used unless
  it parses as an IP inside a trusted network; then the `X-Forwarded-For` entries are walked from
  the right, malformed entries dropped, and the first untrusted one wins (left-most if all are
  trusted). Repeated headers are joined in arrival order. nginx appends `$remote_addr`
  (`infra/reverse-proxy/nginx.conf:35`), so the right-most entry is what the proxy saw.
- Empty setting trusts nothing: `parse_trusted_proxies("")` is `()`, and `_is_trusted` is then
  always false.
- Invalid setting refuses start-up: `Settings` field validator (`backend/app/core/config.py:69-73`);
  probe: `TRUSTED_PROXIES="10.0.0.2, bogus"` → `ValidationError` naming `'bogus'`. Strict
  `ip_network` also rejects host bits (`10.0.0.1/24`).
- Server handling off: with Gunicorn 26.0.0, `--forwarded-allow-ips=` parses to `[]`, and Uvicorn
  0.49.0's `ProxyHeadersMiddleware(trusted_hosts=[])` trusts neither `127.0.0.1` nor
  `172.28.77.2` (probe). SOUP-004/005 record this reliance correctly.
- Real application: probe on `create_app()` shows `ClientAddressMiddleware` is the outermost user
  middleware and publishes the rule's result in `request.state` and the `ContextVar`.
- Compose: `TRUSTED_PROXIES` in `environment:` wins over `env_file: .env` and the shell (the infra
  test covers both); the worker reads `.env` only, whose template value is empty.

Risk-control claims: RISK-006's control row (protective, SR-042 AC 1 to AC 3, TASK-185) is
implemented and tested (TC-016.1..3). RISK-007's control is the per-client rate limit (TASK-186);
TASK-185 supplies the address it keys on, implemented and tested here. OpenAPI contract unaffected
(fresh export identical to `backend/openapi/openapi.json`).

Deviations: (1) `ip_range` accepted: it is a refinement of ADR-0019's "fixed subnet and fixed
address", needed to keep the address free, recorded in ADD-026 1.1, DEPLOY.md and
`test_compose_trusted_proxy.py`. ADR-0019 needs no new decision; see observation 2. (2)
`python3 -m unittest` accepted; TS-016 TC-016.3 names both runners (the Verification block above
still says `pytest`, which is harmless). (3) Probe instead of a debug log accepted for this task;
TASK-137's audit row and TASK-202 give the permanent started-stack evidence.

Observations (LOW, not blocking):

1. RISK-007's control table (`docs/risks/RISK-007-clinical-information-unavailable.md:86`) lists
   only TASK-186, while TASK-185 `mitigates` RISK-007. Fix at TASK-186 or TASK-201: name TASK-185
   in that row as the address prerequisite (human-owned record).
2. ADR-0019 Consequences (`docs/design/adr/0019-originating-client-address-trusted-proxy-rule.md:67`)
   says "DEPLOY.md says which two lines to change"; DEPLOY.md now lists three (subnet and
   `ip_range`, the proxy address, `TRUSTED_PROXIES`). Fix in TASK-201: an editorial note in the
   ADR naming `ip_range`.
3. The static check (`backend/tests/api/test_client_address_middleware.py:111`) matches only
   `.client.host`; a read of `scope["client"]` or `request.client[0]` would pass. Consider widening
   the pattern when TASK-186 empties `KNOWN_READS`.
4. Local development (`README.md:14`, `uvicorn app.main:app`) keeps Uvicorn's default proxy
   handling (trusts `127.0.0.1`). Not a deployment path; no action unless dev audits matter.

Verification run by QA:

- `uv run pytest tests/core/test_client_address.py tests/api/test_client_address_middleware.py`: 27 passed.
- `uv run pytest --cov=app --cov-fail-under=85`: 618 passed, 4 skipped, coverage 91.65 %.
- `uv run ruff check .`, `uv run black --check .`, `uv run mypy app`: clean.
- `cd infra && python3 -m unittest discover -s tests`: 37 passed.
- Negative control (scratchpad plugin, no source edit): `_is_trusted` always true → 6 of 27 fail,
  including both AC 2 tests and both empty-setting tests.
- `traceability-check` (fallback parser; TASK-185, TS-016, SOUP-004, SOUP-005, ADD-026, SR-042):
  0 errors. Warnings: ADD-026, SOUP-004 and SOUP-005 `in_review` (W5 from this approved task to
  ADD-026, expected); SR-042 has no TR yet (W2, release scope); `risk_control_unverified` for
  TASK-185 until a TR exists.

## Version history

- 1.1 (2026-10-31) — Implemented; handed to QA (`in_review`). Implementation notes and
  verification results added.
- 1.1 (2026-10-31) — QA review: APPROVED (`in_review → approved`); review recorded.
