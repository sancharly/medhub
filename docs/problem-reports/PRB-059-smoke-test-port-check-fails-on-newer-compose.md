---
id: "PRB-059"
type: problem-report
title: "The smoke test reports a published port on Docker Compose 5.x for an unpublished one"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
criticality: minor
links: []
tags: ["infrastructure", "verification", "cr:CR-002"]
---

# PRB-059 — The smoke test reports a published port on Docker Compose 5.x for an unpublished one

## Observed

On a fresh `docker:dind` daemon (Docker 29.9.2, Compose v5.6.1, linux/amd64 images), CR-002 TASK-182
ran `bash infra/smoke-test.sh` against the started stack and got `25 passed, 1 failed`. The failing
check is "object-store publishes no host port": `published: ':0', HostPort entries: 0`. On the
reference workstation (Compose v2.20.2) the same script passes 26 of 26.

## Impact

The check gives a false failure on a host with a recent Compose, so an operator or a CI job on such
a host cannot reach "N passed, 0 failed" for a correct stack. The check does not hide a real
exposure: it does not detect a published port wrongly on either version. Verification only.

## Investigation

`infra/smoke-test.sh:212-217` sets `PUBLISHED=$(compose port object-store 8333 2>/dev/null || true)`
and passes only when `PUBLISHED` is empty and no `HostPort` entry exists. Compose v2.20.2 prints
nothing for a container port that is not published (the script passes there). Compose v5.6.1 prints `:0`
and exits 0, so `-z "$PUBLISHED"` is false. The second condition is the reliable one: on the same
stack `docker inspect` gives `.NetworkSettings.Ports` with every value `null` and
`.HostConfig.PortBindings` equal to `{}`, so there is no host binding. The assumption that broke is
that an empty `compose port` output means "unpublished" on every Compose version.

## Safety evaluation

No data, safety-related function or clinical decision is affected. The product is unchanged. The
fault is in a verification script and fails safe (a false failure, never a false pass). No
released version exists, so no notification is needed. Hence `minor`.

## Resolution

`infra/smoke-test.sh` (section "Object-store network isolation") no longer calls `docker compose port`
(the `PUBLISHED` variable is removed). The check "object-store publishes no host port" (name and the
total of 26 checks unchanged) passes only when `docker inspect` of the store container
(`{{json .NetworkSettings.Ports}} {{json .HostConfig.PortBindings}}`) succeeds and contains no
`HostPort` key. It fails with `docker inspect failed` when the container id is empty or the inspect
fails (the old code would count 0 entries on empty output and pass), and fails with the captured JSON
when a binding exists. Fixed in the commit that carries TASK-184 on `bug/minio-object-store`; verify
with `git log -1 --format=%h -- infra/smoke-test.sh`.

Why this approach: the `compose port` text is CLI presentation that changed between Compose 2.20.2
(empty) and v5.6.1 (`:0`) with no documented contract, and Compose derives it from the same Engine data
that `docker inspect` returns, so it adds no independent signal. Matching the `HostPort` key (not its
value) also counts an ephemeral mapping, whose `PortBindings` entry has an empty or `0` `HostPort`.
The rejected alternative, `[ -z "${PUBLISHED#:0}" ]`, keeps a pattern match on a presentation string.

Verification (reproducible, TASK-184 "Verification results"): stack in its own project (`git archive` copy,
temporary `infra/.env` with generated keys and `CORS_ORIGINS=[]`, PRB-056),
`bash infra/smoke-test.sh`. Before the change on a fresh `docker:dind` (Compose v5.6.1, amd64): 25 passed,
1 failed (`published: ':0'`). After: `26 passed, 0 failed` on the workstation (Compose v2.20.2) and on
dind (v5.6.1). Mutations (loopback `ports:` from `compose.ci-object-store.yml`, an ephemeral
`ports: ["8333"]`, and a forced empty container id) each fail the check on the hosts run, with the
binding or `docker inspect failed` in the message. The stacks were removed with `down -v`; the dev
`infra/.env` and volumes were unchanged.

## Source

Software developer, CR-002 TASK-182 (2026-10-31).
