# ADR-0019: The originating client address comes from one trusted-proxy rule in the application

## Status

Accepted (2026-10-31, CR-004 plan gate: the human approved the plan). Proposed earlier the
same day by the Software Architect role.

## Context

SR-042 AC 1 to AC 3 define the originating client address: the TCP peer, unless the peer is a
trusted proxy, in which case the right-most `X-Forwarded-For` entry that is not a trusted proxy.
An empty trusted-proxy setting trusts nothing. SR-023 AC 6 (audit source address) and SR-042 AC 4
and AC 5 (retrieval rate limit) both depend on it.

Today the application reads `request.client.host` (PRB-010, PRB-029), which is the reverse proxy
on a deployed stack. nginx already sets `X-Forwarded-For` (`infra/reverse-proxy/nginx.conf:35`).
Gunicorn's own forwarded-header handling trusts only `127.0.0.1` by default, which the proxy
container is not, so the header is ignored.

## Options

1. **Server-level:** set Gunicorn/Uvicorn `forwarded_allow_ips` to the proxy, and let Uvicorn
   rewrite `request.client`.
2. **Application-level:** a small ASGI middleware applies SR-042's rule with a `TRUSTED_PROXIES`
   setting and publishes the result for the request.
3. **Proxy-level:** have nginx overwrite `X-Forwarded-For` with `$remote_addr` and trust the
   header from anyone.

## Decision

Option 2.

- `app.core.client_address`: a pure ASGI middleware, mounted first, computes the address once per
  request from the scope's peer and `X-Forwarded-For`, using `TRUSTED_PROXIES` (comma-separated
  IP addresses or CIDR blocks, parsed with `ipaddress` at start-up; an invalid entry refuses
  start-up). It stores the result in `request.state.client_address` and in a `ContextVar`. Code
  outside a request (worker, scheduler) sees `None`.
- Every consumer reads that value: `AuditService.record` uses it when the caller passes no address
  (TASK-137), and the retrieval rate limit keys on it (TASK-186). No code reads
  `request.client.host` directly any more; a test fails if one does.
- The server's own forwarded-header handling stays off: Gunicorn is started with
  `--forwarded-allow-ips=` (empty) so `request.client` is always the TCP peer and the rule is
  applied exactly once.
- **Deployment.** The `medhub` network gets a fixed subnet and the reverse proxy a fixed address
  in it; `TRUSTED_PROXIES` is set to that one address in the Compose file (SR-042 AC 3). Trusting
  the whole subnet was rejected: every container on it (frontend, worker) could then forge an
  address.

Option 1 was rejected because its default (unset → `127.0.0.1`) differs from SR-042 AC 3 (empty
→ none), its behaviour is that of a SOUP item (SOUP-004, SOUP-005) we would have to verify per
version, and it cannot be unit-tested without a server. Option 3 was rejected because it makes
the header trusted from any peer that can reach the backend, contrary to AC 2.

## Consequences

### Positive

- One rule, one setting, one place to test, and a forged header from an untrusted peer is ignored
  (SR-042 AC 2).
- The audit trail and the rate limit always agree on who the caller is.

### Negative

- A wrong `TRUSTED_PROXIES` fails silently: every address becomes the proxy's again. Mitigated by
  a check on the started stack that an audit row's address is not the proxy's (SR-042 Control
  measures; TS-016).
- The fixed subnet can collide with a host network; DEPLOY.md says which two lines to change.

### Neutral

- IPv6 works through `ipaddress`; nothing in the deployment uses it today.

## References

- Requirements: SR-042 AC 1 to AC 5; SR-023 AC 6; RR-004; NFR-007
- Problem reports: PRB-010, PRB-029
- Risks: RISK-006, RISK-007
- SOUP: SOUP-004 (Uvicorn), SOUP-005 (Gunicorn), SOUP-024 (nginx)
- Related: ADR-0010, ADR-0013 (retrieval rate limit values unchanged, CR-004 A-4); ADD-005, ADD-026

## Notes

- **2026-11-08 (TASK-201, CR-004), no change to the decision:** the Negative consequence "DEPLOY.md says which two lines to change" is three lines in `infra/docker-compose.yml`, and the first is two settings of one block: the `medhub` network's `subnet` **and `ip_range`**, the proxy's `ipv4_address`, and the backend's `TRUSTED_PROXIES`. The `ip_range` was found on the started stack (TASK-185): without it Docker gave the proxy's fixed address to another container. Dynamic addresses come from `ip_range`, which excludes the proxy's address. `infra/DEPLOY.md`, "Trusted proxy and the Compose subnet", lists the three, and `infra/tests/test_compose_trusted_proxy.py` checks that they agree. [07 deployment view](../07-deployment-view.md) holds the narrative.
