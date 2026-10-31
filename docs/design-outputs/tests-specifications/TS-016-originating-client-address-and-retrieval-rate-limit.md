---
id: "TS-016"
type: test-specification
title: "Originating client address and retrieval rate limit verification"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-042"
    relation: verifies
tags: ["level:unit", "level:integration", "class:B", "cr:CR-004"]
---

# TS-016 — Originating client address and retrieval rate limit verification

## Scope

Software requirement covered: SR-042. Version 1.0 (TASK-185) covers AC 1, AC 2 and AC 3, the
originating client address. Version 1.1 (TASK-186) adds TC-016.4 and TC-016.5 for AC 4 and AC 5 (the
retrieval rate limit). Software items under test: SI-API `U-API-ClientAddress`
(`backend/app/core/client_address.py`, ADD-005) and SI-DEPLOY `U-DEP-Compose`
(`infra/docker-compose.yml`, ADD-026). Levels: unit (TC-016.1, TC-016.2, TC-016.3), integration
(TC-016.2 middleware, TC-016.3 started stack, TC-016.4, TC-016.5 over the ASGI app with fakeredis), static check (TC-016.3 Compose).

## Preconditions and environment

Branch `fix/review-2026-07-security`. Backend Python 3.12 with the dependencies locked in
`backend/uv.lock`. The Compose static checks need Python 3 (standard library) and Docker Compose v2
(`docker compose config` needs no daemon). The started-stack part of TC-016.3 follows the rules of
TS-014: a Compose project of its own (`-p`), fresh volumes, a temporary `infra/.env` with generated
values (backed up and restored byte-identical), a live Docker daemon, and, when the host already
uses ports 80 and 443, a throwaway copy of the Compose file with other host ports. A throwaway probe
route that returns `request.client.host` and the originating address is added to the real
application through a scratchpad override (no repository file changes); the entrypoint keeps
`--forwarded-allow-ips=`.

## Test cases

| ID | Verifies (SR / AC) | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-016.1 | SR-042 AC 1 | `backend/tests/core/test_client_address.py` (`cd backend && uv run pytest tests/core/test_client_address.py -v`): `test_trusted_peer_takes_the_forwarded_client`, `test_chain_with_both_proxies_trusted_gives_the_client`, `test_all_entries_trusted_gives_the_left_most`, `test_forged_leading_entry_is_ignored_right_most_untrusted_wins`, `test_cidr_entry_trusts_the_block`, `test_trusted_peer_without_header_gives_the_peer`, `test_ipv6_client_through_ipv6_proxy`, `test_ipv6_is_normalised_and_families_do_not_cross_match`, `test_malformed_entries_are_skipped`, `test_non_ip_peer_is_returned_untrusted`; `backend/tests/api/test_client_address_middleware.py`: `test_value_reaches_request_state_and_context_var`, `test_repeated_headers_are_combined_right_most_wins`, `test_context_var_is_reset_after_the_request`, `test_context_var_is_reset_when_the_application_raises` | From a trusted peer the address is the right-most `X-Forwarded-For` entry that is not a trusted proxy; if all are trusted, the left-most; a forged leading entry never wins; malformed entries are skipped; the value reaches `request.state` and the `ContextVar`, which is reset after the request | All listed tests pass |
| TC-016.2 | SR-042 AC 2 | `backend/tests/core/test_client_address.py`: `test_untrusted_peer_header_is_ignored`; `backend/tests/api/test_client_address_middleware.py`: `test_forged_header_from_untrusted_peer_is_ignored`. Negative control: trust the header from any peer (the `_is_trusted(peer_ip, trusted)` test removed): these tests and the two empty-setting tests fail | A header from a peer that is not a trusted proxy is ignored; the address is the peer's | All listed tests pass; the negative control fails four tests (TASK-185 "Verification results") |
| TC-016.3 | SR-042 AC 3 | Unit: `backend/tests/core/test_client_address.py`: `test_empty_setting_trusts_no_peer`, `test_no_peer_gives_none`, `test_invalid_setting_raises_naming_the_entry`, `test_invalid_entry_is_named`; `backend/tests/api/test_client_address_middleware.py`: `test_empty_setting_ignores_the_header_from_every_peer`, `test_setting_is_read_when_no_explicit_value_is_given`, `test_invalid_setting_refuses_start_up`, `test_no_code_reads_the_tcp_peer_outside_client_address`, `test_static_check_catches_every_form_of_peer_read`, `test_static_check_ignores_client_factories`. Static: `infra/tests/test_compose_trusted_proxy.py` (`cd infra && python3 -m unittest discover -s tests -p 'test_compose_trusted_proxy.py' -v`, or `python3 -m pytest tests/test_compose_trusted_proxy.py` where pytest is installed). Started stack: manual, steps in TASK-185 Verification | An empty setting trusts nothing; an invalid entry refuses start-up naming the entry; no code outside `client_address.py` reads the TCP peer (`.client`, `scope["client"]`, `scope.get("client")`), with no exceptions left (`KNOWN_READS` emptied by TASK-186); the `medhub` network has a fixed subnet and an `ip_range` that excludes the reverse proxy's fixed address; `TRUSTED_PROXIES` of the backend equals that one address and cannot be widened by `infra/.env` or the shell; Gunicorn is started with an empty `--forwarded-allow-ips=`. Started stack: `request.client.host` is the proxy's address, the originating address is the caller's (host and another container), a forged `X-Forwarded-For` through the proxy does not win, a direct request to the backend from an untrusted peer ignores the header, and with `TRUSTED_PROXIES` empty the address is the proxy's | Unit and static tests pass; started-stack results recorded in TASK-185 "Verification results" |
| TC-016.4 | SR-042 AC 4 | `backend/tests/api/test_anonymized_retrieve.py::TestRetrievalRateLimitPerAddress` (`cd backend && uv run pytest tests/api/test_anonymized_retrieve.py -v`): `test_sixth_attempt_is_refused_and_not_evaluated`, `test_window_is_fixed_from_the_first_attempt`, `test_forged_header_from_untrusted_peer_counts_against_the_peer`, `test_missing_peer_is_refused_without_a_shared_bucket`, `test_concurrent_attempts_from_one_address_evaluate_exactly_five`. Negative controls: non-atomic count fails the concurrency test; `EXPIRE` without `NX` fails the fixed-window test | Attempts 1..5 from one address are evaluated; the 6th is 429 and the retrieval service is not called; the window starts at the first counted attempt and is not extended (still 429 at 3599 s, evaluated at 3601 s); a forged `X-Forwarded-For` from an untrusted peer counts against the peer; no peer is refused; 10 simultaneous attempts evaluate exactly 5 | All listed tests pass; both negative controls fail the named test (TASK-186 "Verification results") |
| TC-016.5 | SR-042 AC 5 | `backend/tests/api/test_anonymized_retrieve.py::TestRetrievalRateLimitPerAddress::test_client_b_is_evaluated_after_client_a_is_limited`. Negative control: key the limit on the TCP peer: this test fails | After client A (through the trusted proxy) is limited, client B through the same proxy is evaluated (200, service called) | Test passes; the negative control fails it (TASK-186 "Verification results") |

## Acceptance criteria (class B unit level)

Unit acceptance (§5.5.3): `originating_address` is a pure function; a peer that is not an IP address
is returned unchanged and trusted for nothing; IPv4 and IPv6 entries never match a network of the
other family; the parser accepts addresses and CIDR blocks with surrounding spaces and empty
elements, and rejects any other entry with a `ValueError` naming it; the middleware resets the
`ContextVar` after the request even when the application raises.

## Version history

- 1.0 (2026-10-31): TASK-185. Created for SR-042 AC 1 to AC 3 (TC-016.1 to TC-016.3). TASK-186 adds
  TC-016.4 and TC-016.5.
- 1.0 (2026-10-31): QA review (TASK-185): `in_review → approved`.
- 1.1 (2026-10-31): TASK-186. TC-016.4 and TC-016.5 added (SR-042 AC 4, AC 5); TC-016.3 static check widened to every form of reading the TCP peer, with `KNOWN_READS` empty. Content changed after approval: `approved → in_review`.
- 1.1 (2026-10-31): QA review (TASK-186): `in_review → approved`.
