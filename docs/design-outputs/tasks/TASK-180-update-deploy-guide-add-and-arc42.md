---
id: "TASK-180"
type: task
title: "Update the deployment guide, the ADD records and arc42 for the new object store"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-040"
    relation: implements
  - target: "SR-028"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "ADD-024"
    relation: relates_to
  - target: "ADD-025"
    relation: relates_to
  - target: "TASK-177"
    relation: relates_to
  - target: "TASK-178"
    relation: relates_to
  - target: "TASK-179"
    relation: relates_to
tags: ["documentation", "arc42", "cr:CR-002", "issue:sancharly/medhub#33", "control:information"]
---

# TASK-180 — Update the deployment guide, the ADD records and arc42 for the new object store

- **Software item / unit:** documentation of SI-OBJSTORE (ADD-025), SI-ATTACH (ADD-012) and
  SI-DEVINFRA (ADD-024). No code.
- **Depends on:** TASK-177, TASK-178 and TASK-179 (`relates_to`), so that every fact described
  is already in place
- **Branch:** `bug/minio-object-store`
- **Size:** M (6–8 documentation files, text only). The Document Writer may take the arc42 part.

## Objective

CR-002 AC-20. `infra/DEPLOY.md` and the ADD and arc42 sections that describe the object store
and the deployment topology must match AC-1 to AC-6 and the component chosen by ADR-0015. That
means no console, scripted bucket administration, key generation, the network and SeaweedFS. The
deployment guide is the "information for safety" side of RISK-012's controls.

## Implementation detail

- **`infra/DEPLOY.md`:**
  - remove step 5 (console URL and `mc` commands);
  - describe what `object-store-init` does and how to re-run it
    (`docker compose run --rm object-store-init`);
  - describe bucket administration with scripted S3 calls from the backend image. **See CR-002
    Q-6** on the AC-20 wording "with `mc`".
  - keep TASK-174's key-generation step and TASK-178's migration section;
  - add the `object-store` network, the component and its version, and the monthly advisory
    check (PLAN-002 as revised by TASK-172).
- **ADD-012** (version from TASK-175):
  - `U-ATT-Fetch` now verifies the stored checksum and refuses with an audit FAILURE (TASK-173);
  - ADR-0015 is named among the governing decisions.
- **ADD-024**:
  - bump the version and clear the approval record;
  - `U-INF-CIPipeline` gains the job `object-store-integration` and the CI override file;
  - Verification lists TC-008.8.
- **ADD-025**:
  - check the units against the implemented services;
  - check the SOUP links (SOUP-019, SOUP-036; none to SOUP-022 or SOUP-023);
  - keep it `in_review`.
- **arc42** (`docs/design/`, following the `arc42` skill):
  - `07-deployment-view.md`: the table row "MinIO (S3)" becomes the new component, plus the
    `object-store` network, the preflight and the initialiser. The operational notes cover keys,
    no console and migration;
  - `05-building-blocks.md`: SI-OBJSTORE and its three units;
  - `11-risks-and-technical-debt.md`: the MinIO debt is closed, and the replacement's advisory
    cadence is named;
  - `12-interfaces.md`, only if it names MinIO or the console.
  - Update the deployment diagram (`docs/specifications/diagram-deployment.puml`) under the
    `plantuml` skill.
- **ADR-0009**: under Status, add "Amended by ADR-0015 (self-hosted product)". The ADR index
  already lists ADR-0015.
- **`docs/templates/task.md`**: replace "MinIO (S3 / SSE-AES256)" in the stack list with the
  chosen component.

## Acceptance criteria

- [x] CR-002 **AC-20**: DEPLOY.md, ADD-012, ADD-024, ADD-025 and arc42 sections 05, 07 and 11 match
      AC-1..AC-6 and ADR-0015. `git grep -n -i "minio" docs/design infra/DEPLOY.md` returns only
      historical or migration mentions, each one deliberate.

## Verification

Inspection against the Compose file and the evidence of TASK-174..179, then `traceability-check`
for the ADD records. Render the PlantUML diagram once to check that it compiles.

## Definition of Done

- [x] Every listed file is updated. No narrative is copied into the ADD records.
- [x] `traceability-check` shows no error for ADD-012, ADD-024 and ADD-025.

## Verification results (document writer, 2026-10-30)

### Files changed

- `infra/DEPLOY.md`: step 5 rewritten ("Check the object store": the three services, re-running
  `docker compose -f infra/docker-compose.yml run --rm object-store-init`, bucket administration
  with a boto3 snippet run in the backend container, the `object-store` network, the component and
  its pin, the monthly advisory check); key-handling note for `AT_REST_ENCRYPTION_KEY`; start-up
  order note in step 3; Data Residency note names `object_store_data`; "Migrating from MinIO"
  carry-overs (below). TASK-174's key generation and TASK-178's migration section are kept.
- ADD-012 1.3 (`U-ATT-Fetch` checksum check; ADR-0015 named), ADD-024 1.2 (job
  `object-store-integration`, override file, TC-008.8; `approved` returned to `in_review`, approval
  record cleared), ADD-025 1.2 (units and SOUP links checked, port 8333, TC-008.6 and TC-008.8).
- arc42: `05-building-blocks.md` (SI-OBJSTORE and its three units; `U-ATT-Fetch`; SI-DEVINFRA note),
  `07-deployment-view.md` (new row, preflight and initialiser rows, network and start-up order,
  operational notes on keys, no console, component currency and migration), `11-risks-and-technical-debt.md`
  (risk row with the monthly cadence; "Closed technical debt" for MinIO), `02-architecture-constraints.md`
  and `04-solution-strategy.md` (MinIO wording). `12-interfaces.md` does not name MinIO or the
  console: unchanged.
- Diagrams: `docs/specifications/diagram-deployment.puml` (preflight, initialiser, object store,
  `object-store` network note), `diagram-building-blocks.puml` and `diagram-context.puml` (labels).
  All three compile (`plantuml -checkonly`); the deployment diagram was rendered once.
- ADR-0009: Status gains "Amended by ADR-0015 (self-hosted product)". ADR-0015: dated amendment
  notes (below). `docs/templates/task.md`: stack list names SeaweedFS 4.51.

### Carry-overs from earlier QA reviews

1. Step 5 and the Data Residency note: rewritten for SeaweedFS and `object-store-init`. Done.
2. Migration commands: the `L="docker compose ..."; $L ...` variable is now a shell function
   `legacy()`, which works in bash and zsh; `docker stop $(docker ps -q ...)` is now
   `docker ps -q ... | xargs -r docker stop`, with a note that `-r` is a GNU option, that macOS
   (BSD) `xargs` accepts it as a no-op and does nothing on empty input, so the line is portable.
   Checked on this macOS host (`printf '' | xargs -r echo` prints nothing, exit 0) and in zsh.
3. ADR-0015: the "Decision (recommended, pending ...)" heading is now "Decision" with a dated
   amendment note, and the "Internal ports" Negative bullet has a dated amendment (loopback only
   under `weed server`; only 8333 and 18333 listen on the container address). Original text kept.
4. ADD-024 records the job and the CI-only override. Done.
5. Smoke-test counts: no document under `docs/design`, `infra/DEPLOY.md`, ADD records or the
   templates claims 17/17. The remaining "17 passed" and "17/17" hits are historical task and PRB
   results (CR-001, CR-003, TASK-160..168, TASK-175, SOUP-003) and CR-002 AC-wording ("17/17 at
   least"), which this task does not edit (CR-002 belongs to another workstream). Current count: 26
   (TASK-179, PRB-055).

### Commands

| Command | Result |
|---|---|
| `python3 -m unittest discover -s infra/tests` | 32 tests, OK (includes the DEPLOY.md default-credential check) |
| `python3 infra/check_image_pins.py` | exit 0 |
| `git grep -n -i minio docs/design infra/DEPLOY.md` | only ADR-0009, ADR-0010, ADR-0015 and ADR index (historical decisions), arc42 07 and 11 (migration and closed debt), DEPLOY.md "Migrating from MinIO" and "Rollback" |
| `docker compose --env-file <temp> -f infra/docker-compose.yml config --services` | lists `object-store-preflight`, `object-store`, `object-store-init`, `backend` and the rest: the service names in DEPLOY.md exist |
| DEPLOY.md boto3 snippet | compiles; not run against a live store (no stack started here) |

`traceability-check` and markdownlint were not run (the tool is not installed here); the ADD
records keep `in_review` with no approval fields.

## QA review, round 1 (QA engineer, 2026-10-30): CHANGES REQUESTED

Checked CR-002 AC-20 (as reworded by Q-6/D-6) against the committed implementation
(`infra/docker-compose.yml`, `infra/compose.ci-object-store.yml`,
`infra/migration/compose.minio-legacy.yml`, `infra/.env.example`, `infra/smoke-test.sh`,
`.github/workflows/ci.yml`, `backend/app/core/object_store_init.py`, `backend/app/db/crypto.py`).
No console, the initialiser, scripted S3 administration, the network and SeaweedFS all match. The
ADR amendments are dated and keep the original text, the diagrams compile, and
`traceability-check` shows 0 errors. One HIGH blocks approval: the key-generation guidance for
`AT_REST_ENCRYPTION_KEY`, which this task makes the store's SSE key.

### Findings

- **[HIGH] `AT_REST_ENCRYPTION_KEY` is documented with the wrong format and has no generation
  command** (`infra/DEPLOY.md:19`, `infra/DEPLOY.md:25-41`, `infra/.env.example:48-50`).
  - What the docs say: "exactly 32 bytes".
  - What the code requires: `backend/app/db/crypto.py:27-42` base64-decodes the value and needs
    exactly 32 decoded bytes. Results, checked with the same decode:
    - 32 ASCII characters decode to 24 bytes and are refused;
    - the `.env.example` placeholder is not valid base64;
    - `openssl rand -hex 32` decodes to 48 bytes and is refused;
    - `openssl rand -base64 32` decodes to 32 bytes and is accepted.
  - Why it fails late: the check runs only on the first field encrypt or decrypt, not at start-up.
    A key that follows the guide therefore starts the stack, and SeaweedFS accepts any string
    (HKDF). Attachments are then encrypted under that key. The first clinical entry fails, and
    the operator's fix (a new key) is what the new paragraph at `DEPLOY.md:39-41` says makes the
    stored objects unreadable.
  - Scope: AC-20 requires "key generation", and RISK-012's information control depends on this
    guidance, so it is in scope.
  - Fix:
    - In "Generate the object-store keys", add `openssl rand -base64 32   # AT_REST_ENCRYPTION_KEY
      (base64 of 32 random bytes; the backend refuses any other length)`, and say that it must
      be set before the first start, because it cannot be changed later on a populated store.
    - Change `DEPLOY.md:19` to "base64 of 32 random bytes".
    - Make the same change to the comment at `.env.example:49` (comment text only).
- **[LOW] Data Residency note names only the `medhub` network as "internal"**
  (`infra/DEPLOY.md:167`). The attachment bytes travel on `object-store`, and `medhub` is not
  `internal: true`. Fix: "outside the stack's Docker networks (`medhub`, and `object-store`,
  which is internal)".
- **[LOW] "keeps the whole stack down" overstates the effect** (`infra/DEPLOY.md:75-78`).
  PostgreSQL, Redis, the frontend and the Celery worker still start. Only the backend, and with
  it the proxy, stay down, and `up -d` exits non-zero. Fix: "keeps the backend and the reverse
  proxy down (`up` reports that a dependency failed)".
- **[LOW] ADD-012's new "Version history" lists only 1.3**
  (`docs/design-outputs/architecture/ADD-012-attachment-service.md`, end of file). TASK-175 made
  1.1 and TASK-176 made 1.2. That already broke CR-002's "bump once per CR" rule, and this task
  continues it. Fix: add the 1.1 (TASK-175: approval cleared, SOUP-023 link removed) and 1.2
  (TASK-176) entries. Keeping 1.3 is acceptable once the history explains it.
- **[LOW] ADD-024 `U-INF-CIPipeline` carries design rationale that belongs in arc42**
  (`ADD-024-development-and-verification-infrastructure.md:43-51`). The sentences "because
  Docker cannot publish a port…" and "writes throwaway credentials… `down -v`" repeat the
  rationale in `07-deployment-view.md` and in the override file's comment. Fix: keep the job
  name, project, files and marker, and point to arc42 07 for the reason.
- **[LOW] The arc42 07 backup TODO has no reference** (`docs/design/07-deployment-view.md`,
  Operational notes, "Backups"). Fix: once the PRB under ruling (c) exists, cite it in the TODO.

### Rulings on the writer's reported inconsistencies

- (a) `ADD-004-soup-list.md` (MinIO and `mc` `:latest`, boto3 "not declared"): **out of scope,
  no PRB.**
  - ADD-004 has been `obsolete` since 2026-10-21. Its banner says that the content is kept
    unchanged and that SOUP-001..035 superseded it.
  - Every row is frozen at 2026-09-17, so nginx, Redis and PostgreSQL are also shown floating.
  - AC-12 concerns the SOUP records (SOUP-022, SOUP-023, SOUP-036), and they are correct.
  - Optional: one sentence in the banner, the way TASK-166 added the openapi-fetch correction:
    "MinIO and mc were retired by CR-002 (SOUP-022, SOUP-023 obsolete; SOUP-036 SeaweedFS)".
- (b) Key format: **the docs are wrong, not CI** (HIGH above).
  - CI's `openssl rand -hex 32` feeds only `WEED_S3_SSE_KEY` (any string, HKDF). The
    `object-store-integration` job never runs field encryption.
  - Optional, outside this docs task: generate the key with `openssl rand -base64 32` in the CI
    job so that it uses the deployed format. LOW, no PRB.
- (c) No backup or restore procedure for `object_store_data`: **out of scope for CR-002.**
  - The gap predates the CR: DEPLOY.md has no backup procedure for PostgreSQL either.
  - ADR-0010:37 and arc42 11 ("backups + monitoring documented") claim a procedure that does not
    exist.
  - Raise a PRB with criticality **major**. It covers a backup and restore procedure for
    `postgres_data` and `object_store_data`, together with `AT_REST_ENCRYPTION_KEY`, and the
    untrue "documented" claims (UN-008 durability).
- (d) `@startuml deployment` header: **established project convention, observation only.**
  - All 9 diagrams in `docs/specifications/` use a named `@startuml`.
  - The same diagram colours the documented system `#lightblue`. The new preflight and
    initialiser elements are uncoloured, which matches the house style but not their siblings.
  - No PRB. If wanted, a separate documentation-hygiene change can fix all nine.
- (e) ADR-0010 names MinIO: **historical, leave as is, no PRB.**
  - The decision (single-host Compose) is unchanged.
  - ADR-0015 amends ADR-0009, not ADR-0010.
  - ADRs are not rewritten.

### Verification run (QA)

| Check | Result |
|---|---|
| `python3 -m unittest discover -s infra/tests` | 32 tests OK |
| `python3 infra/check_image_pins.py` | exit 0 |
| `plantuml -checkonly` on deployment, building-blocks, context | exit 0 each |
| `git grep -n -i minio docs/design infra/DEPLOY.md` | only ADR history and index, arc42 07 migration and 11 closed debt, and the DEPLOY "Migrating from MinIO"/"Rollback" sections |
| Scratch stack `-p qa180` (temporary `infra/.env` from `.env.example`, `CORS_ORIGINS=[]`, `POSTGRES_PASSWORD`; dev `.env` backed up and restored, `shasum -c` OK and `cmp` identical), `up -d --build postgres redis object-store-init backend` | preflight exit 0, store healthy, init exit 0, backend started |
| DEPLOY boto3 snippet, verbatim with `-p qa180` | `[{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}, 'BucketKeyEnabled': False}]`, `0 objects`, rc 0 |
| `docker compose … run --rm object-store-init` (re-run) | `object-store init ok: bucket medhub private, AES256`, rc 0 |
| `docker network inspect qa180_object-store` | `Internal=true`; members: object-store and backend (init exited) |
| `down -v` of `qa180` | volume list identical to before; no `qa180` containers left |
| `printf '' \| xargs -r echo` (macOS) | no output, exit 0 |
| zsh: `legacy()` passes arguments as separate words | yes |
| `traceability-check` (fallback parser), scope TASK-180, ADD-012, ADD-024, ADD-025 | 0 errors, 0 warnings |
| `traceability-check`, whole project | 0 errors; 43 warnings (W5 23, W6 11, W2 5, W1 3, W7 1); gated: 1 `soup_without_risk`. Approving this task will add the expected W5 warnings to the `in_review` ADDs |

## Round 2 (document writer, 2026-10-30): QA findings fixed

1. **[HIGH] fixed.** `infra/DEPLOY.md`: `openssl rand -base64 32   # AT_REST_ENCRYPTION_KEY` added to
   "Generate the object-store keys", with the rule that it is base64 of exactly 32 bytes (the backend
   refuses other lengths, but only at the first field encryption), that 32 ASCII characters and
   `openssl rand -hex 32` are wrong, and that it must be set before the first start because it
   cannot be changed on a populated store. The `.env` checklist line says "base64 of 32 random
   bytes". `infra/.env.example`: comment text only, no value changed.
2. **[LOW] fixed.** Data Residency note names `medhub` and `object-store`, and says only
   `object-store` is `internal: true`.
3. **[LOW] fixed.** Step 3 now says the backend and the reverse proxy stay down, `up` exits
   non-zero, and PostgreSQL, Redis, the frontend and the worker still start.
4. **[LOW] fixed.** ADD-012 version history has 1.1 (TASK-175) and 1.2 (TASK-176) before 1.3.
5. **[LOW] fixed.** ADD-024 `U-INF-CIPipeline`: the override rationale and credential detail are
   removed; it names the job, project, files and marker and points to arc42 07.
6. **[LOW] fixed.** arc42 07 "Backups" cites PRB-057 instead of the TODO.
7. **Optional, done.** ADD-004 obsolete banner: one sentence on MinIO and `mc` (CR-002); rows unchanged.

Not done (outside this docs task, per QA): generating the CI key with `openssl rand -base64 32`.

Re-run: `python3 -m unittest discover -s infra/tests` and `python3 infra/check_image_pins.py` (results in
the handoff report). No diagram touched.

## QA review, round 2 (QA engineer, 2026-10-30): APPROVED

All six round-1 findings are closed.

- **HIGH `AT_REST_ENCRYPTION_KEY` (closed).**
  - DEPLOY "Generate the object-store keys" gives `openssl rand -base64 32`, names the two wrong
    formats, says the key is checked only at the first field encryption, and requires it to be set
    before the first start.
  - Step 1 and the `.env.example` comment say "base64 of 32 random bytes". The `.env.example`
    value is unchanged.
  - Checked against `app.db.crypto` itself (`encrypt`/`decrypt` with `get_settings` patched),
    using the scratchpad script `qa180/keychk.py`. Results:
    - `openssl rand -base64 32`: accepted, round trip OK.
    - `openssl rand -hex 32`: refused, "got 48".
    - 32 ASCII characters: refused, "got 24".
- **LOW Data Residency (closed).** It names both networks; only `object-store` is
  `internal: true`.
- **LOW step 3 (closed).** It says the backend and the proxy stay down, `up` exits non-zero, and
  the other services start.
- **LOW ADD-012 history (closed).** It has 1.1 (TASK-175), 1.2 (TASK-176) and 1.3.
- **LOW ADD-024 (closed).** `U-INF-CIPipeline` is trimmed and points to arc42 07.
- **LOW arc42 07 Backups (closed).** It cites PRB-057, committed in b776d60. The relative link
  resolves.
- **ADD-004 banner (optional item done).** It has one sentence on CR-002; the rows are unchanged.

### Not blocking (recorded)

- ADD-024 says the reason for the override is in arc42 07. The 07 bullet says what the override
  adds, but not why: Docker cannot publish a port from a container that sits only on internal
  networks. That reason is in the override file's comment. Fix: one clause in 07, at the next
  edit of that section.
- `soup_without_risk` for SOUP-036 (no inbound link from a RISK) is TASK-181's scope (CR-002 AC-12,
  risk links). It is not a TASK-180 gap.

### Verification run (QA, round 2)

| Check | Result |
|---|---|
| `python3 -m unittest discover -s infra/tests` | 32 tests OK |
| `python3 infra/check_image_pins.py` | exit 0 |
| `plantuml -checkonly` on the three diagrams | exit 0 each |
| `traceability-check` (fallback parser), scope TASK-180, ADD-004, ADD-012, ADD-024, ADD-025, PRB-057 | 0 errors; 1 warning: ADD-004 W6 to obsolete ADD-002 (both obsolete, pre-existing) |
| `traceability-check`, whole project | 0 errors; 43 warnings (W5 23, W6 11, W2 5, W1 3, W7 1); gated: `soup_without_risk` SOUP-036 (TASK-181) |

ADD-012, ADD-024 and ADD-025 stay `in_review` for the human's approval. This approval adds the
expected W5 links from TASK-180 to them.
