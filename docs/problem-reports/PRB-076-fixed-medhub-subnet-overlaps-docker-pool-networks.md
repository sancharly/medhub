---
id: "PRB-076"
type: problem-report
title: "The stack can fail to start because the fixed medhub subnet overlaps a network Docker picks for another Compose network"
status: resolved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-08"
updated: "2026-11-08"
criticality: major
links: []
tags: ["deployment", "hazard:availability", "found-in:TASK-202-qa"]
---

# PRB-076 — The stack can fail to start because the fixed `medhub` subnet overlaps a network Docker picks for another Compose network

## Observed

Found in TASK-202's QA review (finding 3), on a first `up` of a fresh Compose project. Compose created the
`object-store` network first, and Docker gave it `172.28.0.0/16` from its default address pool. Creating the
`medhub` network, which TASK-185 pinned to `172.28.77.0/24`, then failed with `failed to create network
<project>_medhub: Error response from daemon: cannot create network … conflicts with network …: networks have
overlapping IPv4`. No container started. Removing the network and running `up` again worked, because Docker moved
on to `172.29.0.0/16`. The developer reproduced it in TASK-202 round 2 by creating a network on `172.28.0.0/16`
first, with the committed Compose file: `up` exited 1.

## Impact

Availability at deployment time: the stack does not start (RISK-007), with an error that does not name the cause.
It depends on which subnet Docker hands out first, so it can pass on one host and fail on another, or fail after
another Compose project or network has taken `172.28.0.0/16`. No data is disclosed or altered.

## Investigation

Docker allocates the subnet of every network without an explicit one from its default pools, `172.17.0.0/16` to
`172.31.0.0/16` and then `192.168.0.0/16`, in order. A subnet pinned inside a pool therefore collides with whichever
automatic network reaches it first. CR-004 introduced the pin (TASK-185, ADR-0019: the backend trusts one fixed
proxy address). DEPLOY.md covered only a collision with a host network.

## Safety evaluation

Failure to start is loud and nothing is changed, so no wrong clinical information is shown. Criticality **major**: a
default installation can fail on the first `up`, and the message does not say why. Contributes to RISK-007. No release
exists (CR-004 A-1), so no notification is needed. The human sets the final criticality.

## Resolution

Fixed in TASK-202 round 2 (CR-004 D-20). Two options were weighed:

1. Give `object-store` an explicit subnet next to `medhub` in the same pool: only removes the collision between the
   two networks of this project. Any other Compose project, or any network Docker creates earlier, can still take
   `172.28.0.0/16` before this project's `medhub` and fail the same way.
2. Move `medhub` outside Docker's default pools. Automatic allocation never draws from outside them, so no
   automatically allocated network, in this project or another, can overlap it.

Option 2 was taken: `medhub` is now `10.77.77.0/24` (`ip_range` `10.77.77.128/25`, proxy `10.77.77.2`,
`TRUSTED_PROXIES` `10.77.77.2`), and `object-store` stays automatic. TASK-185's guarantees are unchanged: one fixed
proxy address, dynamic addresses from the `ip_range` that excludes it, the backend trusting that address only.
`infra/tests/test_compose_trusted_proxy.py` gains two tests (the subnet lies outside `172.16.0.0/12` and
`192.168.0.0/16`; nothing pins `object-store`) and its three earlier tests still pass. `infra/DEPLOY.md` "Trusted
proxy and the Compose subnet" gives the symptom, the upgrade step (`down`, no `-v`, so Compose recreates the
network) and the recovery (find the subnets in use, change the three lines). arc42 07 and 12 name the new values.

Started-stack proof (scratch project `task202`): with a network on `172.28.0.0/16` created first, the committed
Compose file failed (`up` exit 1, "networks have overlapping IPv4"); the new file started (exit 0), with `medhub` on
`10.77.77.0/24` and `object-store` on `172.30.0.0/16`; `infra/smoke-test.sh` 78 passed, 0 failed; a login attempt
through the proxy with a forged `X-Forwarded-For: 1.2.3.4` wrote a `LOGIN_FAILURE` row whose address was the Docker
Desktop gateway `10.77.77.128`, neither the proxy's `10.77.77.2` nor the forged value (0 rows with either).
A host or VPN that already uses `10.77.77.0/24`, or a daemon configured with `default-address-pools` including it,
can still collide; DEPLOY.md says how to pick another range.

## Source

TASK-202 QA review 1, finding 3; orchestrator decision D-20.

## Version history

- 1.0 (2026-11-08) — Created and resolved in TASK-202 round 2 (Software Developer role). The CR-004 `resolves` link is in place.
