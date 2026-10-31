---
id: "TASK-184"
type: task
title: "Decide the smoke test's object-store port check from docker inspect"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-040"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-059"
    relation: relates_to
  - target: "TASK-177"
    relation: relates_to
  - target: "TASK-179"
    relation: relates_to
  - target: "TASK-182"
    relation: relates_to
tags: ["verification", "infrastructure", "network", "cr:CR-002", "issue:sancharly/medhub#33", "control:design"]
---

# TASK-184 — Decide the smoke test's object-store port check from docker inspect

- **Software item / unit:** verification tooling for SI-OBJSTORE `U-OBJ-Server` (ADD-025),
  deployment topology. The check is the started-stack part of TS-014 TC-014.6 (SR-040 AC 3 and
  AC 5), added by TASK-177. No product code changes.
- **Depends on:** TASK-177 (it added the check) and TASK-179 (the CI override used for the
  mutation run), as `relates_to` links. **TASK-182 depends on this task**: its fresh-host smoke
  run is repeated after this task is committed.
- **Branch:** `bug/minio-object-store`
- **Size:** XS (1 check in `infra/smoke-test.sh`; TS-014 TC-014.6; PRB-059)
- **Needs:** a Docker host with Compose 2.20.2 (the reference workstation) and a disposable
  `docker:dind` daemon with Compose v5.6.1 (the TASK-182 round 2 recipe).
- **Scope decision:** CR-002 D-9 (human, 2026-10-31, "Fix it in CR-002").

## Objective

Resolve PRB-059. The check "object-store publishes no host port" (`infra/smoke-test.sh:212-217`)
must give the same, correct answer on every Compose version: pass when the store has no host port
binding, and fail when it has one. Today it fails a correct stack on Compose v5.6.1, which prints
`:0` for an unpublished port, so the fresh-host run of TASK-182 ends at 25 of 26 and AC-16 cannot
be met.

The links follow TASK-177, which owns this check: the task `implements` SR-040 (AC 3 and AC 5, by
TC-014.6), and it `mitigates` RISK-012 and RISK-001, whose control rows for the network
restriction cite TC-014.6 as their verification. TASK-179's links (SR-022, SR-028, RISK-011) belong
to its SSE objective, not to the smoke-test carry-over it also fixed (PRB-055), so they are not
copied here. The RISK records are not edited: their control rows keep TASK-177 and TC-014.6, and
this task restores the verification on newer Compose versions without changing the control.

## Design decision

**Decide on the `docker inspect` evidence alone. Drop the `docker compose port` condition.**

- `docker inspect` reads the Engine API fields `.NetworkSettings.Ports` (actual bindings) and
  `.HostConfig.PortBindings` (requested bindings). They are the data Compose itself reads, and the
  Engine API is versioned. The `compose port` output is CLI presentation. It changed between
  Compose 2.20.2 (empty) and v5.6.1 (`:0`) with no documented contract, and could change again
  (for example `0.0.0.0:0` or `[::]:0`).
- The `compose port` condition adds no sensitivity. Compose derives it from the same Engine data,
  so it is not an independent signal, and any real mapping already puts a `HostPort` key in
  `docker inspect`. The rejected alternative, accepting an empty output or `:0`
  (`[ -z "${PUBLISHED#:0}" ]`), keeps a pattern match on that presentation string and fixes only
  the one format seen so far.
- The count matches the `HostPort` **key**, not its value. A mapping with an ephemeral host port
  (`ports: ["8333"]`) has `"HostPort":""` in `PortBindings` before the daemon assigns one, and it
  is still counted. `PortBindings` also records a requested mapping that the daemon could not
  bind, for example on an `internal`-only network.
- **What it gives up:** a second view through Compose. This is accepted for the reasons above.
- **Fail-safe:** if `docker inspect` fails (for example, no container id), the check fails and
  never passes. The current code would count 0 `HostPort` entries on empty output and pass.

## Implementation detail

1. In `infra/smoke-test.sh`, section "Object-store network isolation", replace lines 212-217:
   - keep `STORE_ID=$(compose ps -q object-store)`;
   - capture `docker inspect "$STORE_ID" --format '{{json .NetworkSettings.Ports}} {{json .HostConfig.PortBindings}}'`
     and its exit status. A non-zero status or an empty `STORE_ID` is a FAIL with the message
     `docker inspect failed`;
   - pass only when the captured output has no `HostPort` key. Otherwise fail with the captured
     JSON in the message, so the operator sees the binding;
   - remove `PUBLISHED` and the `compose port` call. The check name stays
     "object-store publishes no host port", so the count of 26 is unchanged.
2. No other check changes. The static check "only reverse-proxy publishes external ports"
   (lines 66-79) stays as it is: it covers a `ports:` entry in the base Compose file.
3. **Unit test:** none. No test in `infra/tests/` exercises `infra/smoke-test.sh`
   (`grep -rn smoke infra/tests` finds nothing), and the decision is one shell condition. The
   mutation runs below are its evidence. If a reviewer wants a test, it belongs in a separate
   task that extracts the decision into a testable unit.
4. **TS-014** TC-014.6: in "Expected", replace "`docker compose port object-store 8333` is empty
   and `docker inspect` shows no `HostPort`" with "`docker inspect` of the store shows no
   `HostPort` key in `.NetworkSettings.Ports` or `.HostConfig.PortBindings`". Add a note citing
   PRB-059 and the mutation runs. TS-014 1.4 is `approved`, so bump it to 1.5, clear the approval
   record, and add a version-history entry, as TASK-176 and TASK-177 did.
5. **PRB-059** → `resolved` (1.1). Replace "Proposed resolution" with a `## Resolution` that names
   the change, the decision and its reason, and the reproducible verification below, and cites
   the commit as in PRB-055. Keep `## Investigation`.

## Acceptance criteria

- [x] PRB-059 fixed: on a correct started stack, `bash infra/smoke-test.sh` reports
      `26 passed, 0 failed` on Compose 2.20.2 (workstation) **and** on Compose v5.6.1 (dind).
- [x] Mutation sensitivity (SR-040 AC 3 and AC 5, TC-014.6): with a real `ports:` mapping on
      `object-store`, the check "object-store publishes no host port" fails on both Compose
      versions, and its message shows the `HostPort` binding. A failing `docker inspect` fails the
      check.
- [x] TS-014 1.5 (TC-014.6 updated) and PRB-059 `resolved` with `## Resolution`. CR-002 carries
      `resolves` → PRB-059 (D-9).

## Verification

Run every started-stack step in its own Compose project, with a temporary `infra/.env` made from
`infra/.env.example` (generated keys, `CORS_ORIGINS=[]`, PRB-056) in a `git archive` copy, as in
TASK-182. Back up the dev `infra/.env` and leave the dev project `infra` and its volumes untouched.
Remove each project with `down -v` at the end.

```sh
bash -n infra/smoke-test.sh
grep -n "compose port" infra/smoke-test.sh                       # expect no match
python3 infra/check_image_pins.py && python3 -m unittest discover -s infra/tests
```

| Run | Host | Stack | Expected |
|---|---|---|---|
| R1 | Workstation, Compose 2.20.2 | `-p medhub-t184` from `infra/docker-compose.yml` | `26 passed, 0 failed` |
| R2 | `docker:dind` (TASK-182 round 2 recipe: digest-pinned dind, `apk add bash curl python3 git`), Compose v5.6.1 | same | `26 passed, 0 failed`. Before the fix, the same stack gives 25/1 (PRB-059 reproduction) |
| M1 | both hosts | `-f infra/docker-compose.yml -f infra/compose.ci-object-store.yml` with `OBJECT_STORE_CI_PORT=18333` (a loopback `ports:` mapping on `object-store`, TASK-179) | "object-store publishes no host port" fails and its message shows `"HostPort":"18333"`. Record the totals; any other failing check is explained in the record |
| M2 | both hosts | base file plus a scratch override in the session scratchpad (not committed) that attaches `object-store` to a non-internal network and sets `ports: ["8333"]` (ephemeral host port) | the same check fails |
| M3 | either host | a scratch copy of the script (session scratchpad) with `STORE_ID` forced empty, on a started stack | FAIL `docker inspect failed`, never a pass |

The smoke script reads only the base file, so in M1 and M2 the static `ports:` check still passes,
and the started-stack check alone has to catch the mapping. Record each run with
`docker compose version`, the result line and the failing message. Then:

```sh
git diff --stat                     # only infra/smoke-test.sh and the records listed above
```

## Definition of Done

- [x] R1, R2 and M1..M3 recorded below, with the Compose version of each host.
- [x] TS-014 1.5 and PRB-059 1.1 updated. `traceability-check` shows no error for TASK-184,
      TS-014, PRB-059, SR-040 and CR-002.
- [x] After this task is committed, TASK-182 repeats its fresh-host smoke run with the repository
      script (round 3) and expects `26 passed, 0 failed`.

## Verification results (Software Developer role, 2026-10-31)

Change: `infra/smoke-test.sh`, section "Object-store network isolation": `PUBLISHED` and the
`compose port` call removed; `STORE_ID=$(compose ps -q object-store)` kept; the check passes only when
`docker inspect "$STORE_ID" --format '{{json .NetworkSettings.Ports}} {{json .HostConfig.PortBindings}}'`
succeeds (and `STORE_ID` is not empty) and its output has no `HostPort`. An empty id or failed inspect gives
`docker inspect failed`; a binding gives `published: <captured JSON>`. Name and total (26) unchanged.
TS-014 1.5 (TC-014.6, status `in_review` pending QA) and PRB-059 1.1 `resolved` updated. No unit test
(step 3 of the task); the runs below are the evidence.

Static: `bash -n infra/smoke-test.sh` exit 0; `grep -n "compose port" infra/smoke-test.sh` no match;
`python3 infra/check_image_pins.py` exit 0 and `python3 -m unittest discover -s infra/tests` 32 tests OK
(workstation and dind).

Method. The tree is `git archive $(git stash create)` (commit `0716ce7`, HEAD `7351bfb` plus this working tree)
extracted in the session scratchpad, with a temporary `infra/.env` (generated keys, generated
`POSTGRES_PASSWORD` also in `DATABASE_URL`, `CORS_ORIGINS=[]` for PRB-056) and a self-signed certificate.
Project `medhub-t184` (workstation) and `medhub-t184` inside disposable dind daemons. The repository script
in the archive has the same sha1 (`cf0d9b45...`) as the working tree. Dev `infra/.env` sha1 `714c7630...` and
the creation times of `infra_minio_data`, `infra_postgres_data`, `infra_redis_data` (all
`2026-06-20T17:29:26Z`) identical before and after.

| Run | Host | Command / setup | Result |
|---|---|---|---|
| R1 | Workstation, Docker Compose v2.20.2-desktop.1, arm64 | `COMPOSE_PROJECT_NAME=medhub-t184 docker compose -f docker-compose.yml build --no-cache --pull`, `up -d`, wait 40 s, `bash infra/smoke-test.sh` | `=== Results: 26 passed, 0 failed ===` |
| R2 before | dind (`docker@sha256:cb160a57...`, arm64 entry of `docker:dind`; Docker 29.9.2, Compose v5.6.1, empty daemon), `DOCKER_DEFAULT_PLATFORM=linux/amd64`, `apk add bash curl python3 git`; build `--no-cache --pull` 5 m 24 s, `up -d` | same stack, script from HEAD (`git show HEAD:infra/smoke-test.sh`) | `[FAIL] object-store publishes no host port: published: ':0', HostPort entries: 0`; `25 passed, 1 failed` (PRB-059 reproduced) |
| R2 after | same stack | repository script with the fix | `=== Results: 26 passed, 0 failed ===` |
| M1 workstation | `-f docker-compose.yml -f compose.ci-object-store.yml`, `OBJECT_STORE_CI_PORT=18333`; inspect `{"8333/tcp":[{"HostIp":"127.0.0.1","HostPort":"18333"}]}` | smoke | only failure: `object-store publishes no host port: published: {...,"8333/tcp":[{"HostIp":"127.0.0.1","HostPort":"18333"}],...} {"8333/tcp":[{"HostIp":"127.0.0.1","HostPort":"18333"}]}`; `25 passed, 1 failed` |
| M1 dind (v5.6.1) | same | smoke | same single failure with `"HostPort":"18333"`; `25 passed, 1 failed` |
| M2 workstation | scratch override (`/work`-side `m2.yml`, not committed): `object-store` on a new bridge network `m2-pub`, `ports: ["8333"]`; `PortBindings` `[{"HostIp":"0.0.0.0","HostPort":"0"}]`, actual `63967` | smoke | `FAIL object-store publishes no host port: published: {...63967...} {...HostPort":"0"...}`; `25 passed, 1 failed` |
| M2 dind (v5.6.1) | same override; `PortBindings` `[{"HostIp":"","HostPort":""}]` (the key counts although empty), actual `32768` | smoke | same check fails; `25 passed, 1 failed` |
| M3 workstation | scratch copy of the script with `STORE_ID=""` (one-line diff) on the started stack | smoke | `[FAIL] object-store publishes no host port: docker inspect failed`; `25 passed, 1 failed` |
| M3 dind | same | smoke | same failure; `25 passed, 1 failed` |

In M1 and M2 the static "only reverse-proxy publishes external ports" check still passes (the script reads
only the base file), so the started-stack check alone caught the mapping. Cleanup: workstation project
removed with `down -v` (all override files named so the extra networks went too), the five `medhub-t184-*`
images I built removed with `docker rmi`, no container or volume of `t184` remains; the dind containers
removed with `docker rm -f -v`. No prune, nothing else removed.

TASK-182 round 3 (the fresh-host repetition after this change) is recorded in TASK-182. Not committed.

## QA review (QA engineer, 2026-10-31)

**Verdict: APPROVED.** TASK-184 and TS-014 1.5 → `approved`. PRB-059 stays `resolved` (it is closed in the REL
commit). CR-002 1.9 stays `in_progress`. RISK-012 and RISK-001 are not edited. Approving this task adds two W5
warnings, because those RISKs are `in_review`. This is expected.

Logic (`infra/smoke-test.sh:211-218`):
- An empty `STORE_ID` or a non-zero `docker inspect` gives FAIL `docker inspect failed`. The exit status is
  the one of the command substitution in the assignment, so the fail-safe holds.
- Several store containers (a newline in the id) also make the inspect fail. That is also fail-safe.
- Matching the `HostPort` key also catches an ephemeral mapping (`"HostPort":""` or `"0"`).
- No `compose port` call remains.

Findings: none.

QA reruns, on a scratch tree from `git archive $(git stash create)` with the smoke script at sha1 `cf0d9b45...`,
the same as the working tree. They used project `qa184`, a temporary `infra/.env` (generated keys, `POSTGRES_PASSWORD`,
`CORS_ORIGINS=[]`) and a self-signed certificate, on the workstation (Docker Compose v2.20.2-desktop.1):
- `bash -n` passes. There is no `compose port` match.
- `check_image_pins.py` exits 0. `unittest discover -s infra/tests` passes.
- R1 (build with the layer cache, then `up -d`): `26 passed, 0 failed`.
- M1, a recreated `object-store` with `compose.ci-object-store.yml` and `OBJECT_STORE_CI_PORT=18334`: only
  "object-store publishes no host port" fails, with `"HostPort":"18334"` in the message. Result `25 passed, 1 failed`.
- M3 variant, a scratch copy with `STORE_ID=deadbeef0000` (a bogus id, so the inspect itself fails): FAIL
  `docker inspect failed`, `25 passed, 1 failed`.
- After the store was restored, the result was 26/26 again.
- The dind R2 and M2 runs were not repeated. The developer's records are consistent with the reproduced runs.

Cleanup: `down -v --remove-orphans` with both files (the `qa184_ci-publish` network included), and the five
`qa184-*` images removed. The temporary `.env` was deleted. The dev `infra/.env` (sha1 `714c7630...`) and the
`infra_*_data` creation times are unchanged.

`traceability-check` (QA fallback parser, whole project, 380 records): **0 errors**, 97 warnings before
these approvals. No error and no gated finding names TASK-184, TS-014, PRB-059, SR-040 or CR-002.

DoD item 3: TASK-182 round 3 ran before the commit, on a tree whose script has the same sha1 as the one this
task commits. QA accepts that as the repetition.
