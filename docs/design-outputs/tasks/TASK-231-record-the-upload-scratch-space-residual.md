---
id: "TASK-231"
type: task
title: "Record the upload scratch-space residual in RISK-007 and the deployment guide"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-16"
updated: "2026-11-16"
links:
  - target: "SR-013"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-007"
    relation: relates_to
  - target: "PRB-092"
    relation: relates_to
  - target: "TASK-232"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
tags: ["cr:CR-007", "control:information", "deployment"]
---

# TASK-231 — Record the upload scratch-space residual in RISK-007 and the deployment guide

- **Software items:** SI-ATTACH upload (ADD-012; Starlette spooling, ADR-0021) and SI-DEPLOY
  `infra/DEPLOY.md` (ADD-026, `U-DEP-EnvTemplate`).
- **PRB:** PRB-092. **CR:** CR-007 (D-1: no capacity control, residual accepted by the human in MedTrace; D-7, D-8: failure handling by TASK-232, PRB-092 resolved by CR-007, sizing about 300 MiB).
- **Depends on:** TASK-232 (round 2 states what it built; committed in `99c208a`). Parallel with TASK-229 and TASK-230.
- **Branch:** `fix/cr-007-review-followups`.
- **Size:** S (`infra/DEPLOY.md`, `docs/risks/RISK-007-clinical-information-unavailable.md`,
  `docs/design/11-risks-and-technical-debt.md`, PRB-092). No code, Compose or test change.

## Objective

SR-013 AC 1 (upload up to 150 MiB) needs free disk in two places: the reverse proxy's client-body temporary
directory and the API container's temporary directory. After TASK-232 a full API directory answers a logged
503 `upload-storage-unavailable`; the capacity itself stays uncontrolled (D-1). The residual is recorded in
RISK-007 with two measures: the TASK-232 protective control and the DEPLOY.md information measure, which tells
the operator which directories, how much space (about 300 MiB per concurrent maximum-size upload where they
share a disk) and what a shortage looks like.

## Steps

1. **`infra/DEPLOY.md`** ("Attachment size"): both directories (the API container's `/tmp` unless `TMPDIR` is
   set; the proxy's nginx client-body directory, `/var/cache/nginx/client_temp` in the pinned image); the
   sizing rule (about 300 MiB free per concurrent maximum-size upload where they share a disk, about 150 MiB in
   each otherwise); monitor the free space; the failure behaviour (503 `application/problem+json`
   `upload-storage-unavailable`, `Retry-After: 30`, one ERROR log line with method, route template and errno,
   nothing stored, the user can retry; a malformed body stays 400; a full proxy directory is nginx's own 500
   logged at `crit`).
2. **RISK-007** (approved 1.19 → 1.20; `in_review`; approval fields removed):
   - cause and Sequence of events: the scratch-space step, with both directories and the 503.
   - Risk control measures: a Protective row for TASK-232 (SR-013 AC 1, SR-027 AC 3; TS-007 TC-007.17,
     TS-011 TC-011.7) and an Information row for the DEPLOY.md note (SR-013 AC 1; TASK-231).
   - Residual risk: CR-007 paragraph without the "loud 5xx" premise; 3 × 2 → `alarp`, unchanged; the
     protective measure makes the failure visible and recoverable but is not scored as a reduction.
   - Version-history line.
3. **`docs/design/11-risks-and-technical-debt.md`:** the "Upload scratch space" row states both
   directories, the logged 503, the capacity residual accepted in RISK-007 and the DEPLOY.md measure.
4. **PRB-092** (1.1 → 1.2): Impact, Investigation and Safety evaluation corrected for the behaviour before
   TASK-232 (an unlogged 400); "Open decision for a human" replaced by the CR-007 decisions; Resolution covers
   TASK-232 and the sizing. Status stays `open`; QA sets `resolved` once it confirms (CR-007 D-8).

## Verification

- Review: the DEPLOY.md note matches the code (`ATTACHMENT_MAX_BYTES=157286400`; Starlette spools above
  1 MiB, ADR-0021; `attachments.py:34-68`, `errors.py:163-179`; `nginx.conf:75-89` sets no
  `client_body_temp_path`) and the TASK-232 tests (TC-007.17, TC-011.7).
- RISK-007: scores unchanged and `acceptability` equal to what `risk_matrix` derives for 3 × 2; the new rows'
  "Implemented by" name TASK-231 and TASK-232, which link `mitigates` RISK-007 (TASK-232 is checked by QA).
- `traceability-check` on RISK-007, PRB-092, TASK-231, CR-007: 0 errors.

## Acceptance criteria

- [x] SR-013 AC 1 residual: the deployment guide states where uploads are held (both directories), how much
  space to provide and what happens when it runs out.
- [x] RISK-007 lists the cause, the TASK-232 protective control, the information measure and the residual,
  `in_review` for the human's acceptance, scores unchanged.

## Definition of Done

- [x] DEPLOY.md, RISK-007, section 11 and PRB-092 consistent with the code and with each other;
  `traceability-check` no error for these records (run by QA)

## QA review — round 1 (2026-11-16): CHANGES REQUESTED

Probe of the real app (`create_app()`, FastAPI 0.138.0, Starlette 1.3.1, `TestClient`, Starlette's
`SpooledTemporaryFile.rollover` patched to raise `OSError(ENOSPC)`, 2 MiB file part, auth and service
overridden): the upload answers **HTTP 400** `application/json` `{"detail":"There was an error parsing the body"}`,
and `AttachmentService.store` is never called. The same with a bare FastAPI app. Throwaway test, removed after
the run; no repository file changed.

- **R1-1 [HIGH] The stated failure behaviour is wrong: a full scratch directory answers 400, not 5xx.**
  `backend/.venv/lib/python3.12/site-packages/fastapi/routing.py:420-465`: `await request.form()` runs inside a
  `try` whose `except Exception` raises `HTTPException(400, "There was an error parsing the body")`, so the
  `OSError` never reaches the generic 500 handler (`backend/app/api/errors.py:206-221`), which is also the only
  place that logs it (`logger.exception`). For the operator the failure is a 400 indistinguishable in the nginx
  access log from a bad request, with no API error log; for the user it is a client error ("Bad Request",
  `frontend/src/api/client.ts:67-80`, not a problem+json) that does not invite a retry. The "5xx" claim (and
  "fails loudly") is in: `infra/DEPLOY.md` "Attachment size" (line 238); RISK-007 Sequence of events paragraph
  (line 52-56), the new control row (line 102) and the CR-007 residual paragraph (lines 134-141);
  `docs/design/11-risks-and-technical-debt.md` "Upload scratch space" row; PRB-092 Resolution; and, upstream,
  PRB-092 Impact/Safety evaluation ("server error", "a 5xx") and CR-007 Scope/Change analysis. "Nothing is
  stored" is correct (the handler body never runs).
  → Correct every occurrence to what the code does: the upload is refused with HTTP 400 "There was an error
  parsing the body" (not the API's problem+json), nothing is stored, the API logs no error, and the operator
  sees it only as a 400 in the access log and as low free space in the directory; tell the operator to monitor
  that free space. Bump PRB-092 (Impact, Safety evaluation: the failure is visible to the user but not loud to
  the operator) in the same change; ask the orchestrator to correct CR-007's "5xx" wording. Re-state the RISK-007
  residual argument without "loud (5xx)"; whether 3 × 2 still holds is the human's decision, so put the corrected
  failure mode in front of them. Mapping the parse `OSError` to a logged 5xx is a code control (`backend/app`
  change, CR-007 "Ask first"), so it goes back to the human, not into this task.
- **R1-2 [MEDIUM] The sizing rule ignores the reverse proxy's own body buffer.** `infra/reverse-proxy/nginx.conf:75-89`
  (`location /api/`) sets `client_max_body_size 151m` and leaves `proxy_request_buffering` and
  `client_body_buffer_size` at their defaults, so nginx writes every upload body above the buffer to its
  client-body temporary directory in the reverse-proxy container and keeps it until the request ends, while the
  API spools its own copy. A deployment sized at "about 150 MiB per concurrent upload" for the API container
  alone can still fail in the proxy (nginx answers 500 and logs at `crit`). On one host both usually sit on the
  Docker data root, so the peak is about two copies per concurrent maximum-size upload.
  → In the DEPLOY.md note, name both directories (the API container's `/tmp` unless `TMPDIR` is set, and the
  reverse-proxy container's nginx client-body temporary directory) and size for about 300 MiB free per
  concurrent maximum-size upload where they share a disk; carry the same in RISK-007, section 11 and PRB-092
  (or, if the human prefers, raise a separate PRB for the proxy buffer and reference it).
- **R1-3 [LOW] PRB-092 still says "Open decision for a human"** (Safety evaluation) although D-1/D-4 decided it.
  → Replace with a pointer to CR-007 D-1 and D-4 in the 1.2 bump.
- **R1-4 [LOW] Implementation record: "A DB failure deletes the object"** overstates
  `backend/app/attachments/service.py:126-132`: the delete is best effort (`except Exception: pass`). Not in any
  deliverable text. → Say "attempts to delete the object".

Verified correct: Starlette 1.3.1 `formparsers.py:147` `spool_max_size = 1024 * 1024` and `:230`
`SpooledTemporaryFile(max_size=...)`; `backend/app/core/config.py:82` `attachment_max_bytes = 157286400` and
`infra/docker-compose.yml:95`; the route takes `file: UploadFile` (`attachments.py:50`) so the parse precedes
the handler and the object-store put (`service.py:111`) and DB add (`service.py:125`); no `TMPDIR`, `tmpfs`,
spool or free-space check in `backend/app` or Compose (so the stdlib `tempfile` default `/tmp` applies).
RISK-007: approved 1.19 → 1.20 `in_review`, all four approval fields removed, version line present; cause added
in frontmatter and Sequence of events; new row type Information, implemented by SR-013 AC 1 and TASK-231
(`mitigates` RISK-007); scores 3/2/3/2 unchanged and `alarp` matches `docs/medtrace.yml` for 3 × 2; ALARP
justification section present. PRB-092 stays `open` (D-4). `traceability-check` (CR-007, TASK-231, RISK-007,
PRB-092, SR-013): 0 errors, 1 warning (W5 SR-013 `approved` → RISK-007 `in_review`, expected until the human
accepts RISK-007). markdownlint-cli2 (defaults, MD013 off as the repo has no config): no new finding against
`HEAD` in the five files.

## QA review — round 2 (2026-11-16): APPROVED

R1-1 to R1-4 closed against the code and CR-007 1.3 ("What TASK-231 round 2 must state", D-7, D-8):

- **R1-1 closed.** The round 1 probe re-run on `HEAD` `99c208a` (real `create_app()`, `rollover` raising
  `OSError(ENOSPC)`, 2 MiB part) answers 503 `application/problem+json` `upload-storage-unavailable`,
  `Retry-After: 30`, the TASK-232 detail, `store` never called. DEPLOY.md, RISK-007 (sequence of events,
  Protective and Information rows, residual paragraph), section 11 and PRB-092 state that behaviour; the plain
  400 appears only as the behaviour before TASK-232. Citations checked: `attachments.py:34-68`, `:105`;
  `errors.py:163-179`; TS-007 TC-007.17 (4 tests) and TS-011 TC-011.7 exist as cited.
- **R1-2 closed, and the writer's inferences tested.** `nginx -V` of the pinned `nginx:1.31.8-alpine`:
  `--http-client-body-temp-path=/var/cache/nginx/client_temp`. Same image with a 2 MiB `tmpfs` on
  `/var/cache/nginx` and the `/api/` limits: a 5 MB POST answers **500** and logs
  `[crit] ... pwrite() "/var/cache/nginx/client_temp/0000000001" failed (28: No space left on device)`;
  a 3-byte POST is proxied (502, no upstream). Compose mounts nothing there (`docker-compose.yml:48-50`) and sets
  no `TMPDIR`/`tmpfs` for the backend. The shared disk is stated conditionally ("where they share a disk"),
  with the 150 MiB-each alternative: acceptable as written.
- **R1-3 closed:** PRB-092 Safety evaluation points to D-1, D-7, D-8. **R1-4 closed:** "attempts to delete".
- RISK-007 1.20 `in_review`, approval fields absent; scores 3/2/3/2, `alarp` as `risk_matrix` derives for
  3 × 2; the Protective row is not scored as a reduction (reasoning given); ALARP justification present. Stays
  `in_review` for the human.

Carried, not blocking:

- **R2-1 [LOW]** "`/tmp` unless `TMPDIR` is set" (DEPLOY.md, RISK-007, section 11, PRB-092) simplifies Python's
  `tempfile.gettempdir()`, which also reads `TEMP` and `TMP`. Neither is set in the repository, so the
  deployed answer is `/tmp`. → Tighten the wording only if an operator sets one of them.

Verification: `trace.py docs CR-007,TASK-231,TASK-232,RISK-007,PRB-092,SR-013,SR-027`: 475 records, 0 errors,
5 warnings, all W5 (`approved` → `in_review`: SR-013/TASK-232 → RISK-007, TASK-232 → TASK-231 (cleared by this
approval), TASK-232 → SOUP-002/SOUP-003, outside this task). markdownlint-cli2 0.18.1 (MD013 off, no repo
config) on DEPLOY.md, RISK-007, section 11, PRB-092, TASK-231 and CR-007: no new finding against `HEAD`.
PRB-092 set `resolved` (1.3) with the QA confirmation (CR-007 D-8); CR-007 plan row updated.

## Version history

- 1.0 (2026-11-16) — Created at the CR-007 Plan stage (Software Architect role), D-1 (PRB-092 residual accepted, no code control). `draft`.
- 1.1 (2026-11-16) — Implemented (Document Writer role). `in_review`.
- 1.1 (2026-11-16, QA) — Round 1 CHANGES REQUESTED (R1-1 HIGH, R1-2 MEDIUM, R1-3/R1-4 LOW). Status `draft`.
- 1.2 (2026-11-16) — Round 2 (Document Writer role) after TASK-232: R1-1 to R1-4 addressed; Objective, Steps, Verification and acceptance criteria restated. `in_review`.
- 1.2 (2026-11-16, QA) — Round 2 APPROVED; R2-1 LOW carried. Status `approved`.

## Implementation record

Round 2 (replaces the round 1 record). Verified in code before writing:

- Spool threshold: Starlette 1.3.1 `backend/.venv/lib/python3.12/site-packages/starlette/formparsers.py:147`
  (`spool_max_size = 1024 * 1024`) and `:230`; the directory is Python's `tempfile` default (`TMPDIR`, else
  `/tmp`; stdlib behavior, inferred, not set in the repository: no `TMPDIR` or `tmpfs` in `infra/docker-compose.yml`).
- Maximum: `backend/app/core/config.py:82` (`attachment_max_bytes = 157286400`), `infra/docker-compose.yml:95`;
  the service checks it at `backend/app/attachments/service.py:75-82`.
- Nothing stored on a spool failure: the route takes `file: UploadFile` (`backend/app/api/routers/attachments.py:105`),
  so the multipart parse runs before the handler body; the object-store put (`service.py:111`) and the DB add
  (`service.py:125`) come after. If the DB add fails the service attempts to delete the object, best effort
  (`service.py:126-132`, `except Exception: pass`).
- Failure behaviour (TASK-232, commit `99c208a`): `attachments.py:34-68` (`_SpoolFailureRoute`) maps a 400 with
  an `OSError` cause to `UploadStorageUnavailableProblem` (`backend/app/api/errors.py:163-179`: status 503,
  `type_slug = "upload-storage-unavailable"`, `Retry-After: 30`), after `logger.error` with the method, the route
  template and the errno name (`attachments.py:55-62`); no path, file name or form data. Tests: TS-007 TC-007.17
  and TS-011 TC-011.7 (read, not re-run by this role). Before TASK-232 the answer was a plain 400 and no log (QA R1-1).
- Proxy directory (R1-2): `infra/reverse-proxy/nginx.conf:75-89` sets `client_max_body_size 151m` and leaves
  `proxy_request_buffering`, `client_body_buffer_size` and `client_body_temp_path` at their defaults;
  `infra/docker-compose.yml:44` pins `nginx:1.31.8-alpine`, whose build uses
  `--http-client-body-temp-path=/var/cache/nginx/client_temp` (from `nginx -V` of that image run locally); no
  volume or `tmpfs` is mounted there (`docker-compose.yml:48-50`). nginx's own 500 and `crit` log on a full
  directory is nginx behavior, inferred from the nginx documentation and QA R1-2, not tested here.
- The 300 MiB figure is one copy in each directory per concurrent maximum-size upload (CR-007 D-8); that both
  share a disk on one host (the Docker data root) is inferred, not set in this repository.

Changes (round 2):

- `infra/DEPLOY.md` "Attachment size": both directories, sizing (300 MiB shared, 150 MiB each otherwise),
  monitor the free space, the 503 behavior and the proxy's own 500.
- RISK-007 1.20, `in_review`: sequence of events, Protective row (TASK-232), Information row (DEPLOY.md), CR-007
  residual paragraph restated without "loud (5xx)", version line. Scores unchanged (3 × 2, `alarp`).
- `docs/design/11-risks-and-technical-debt.md`: "Upload scratch space" row.
- PRB-092 1.2: Impact, Investigation, Safety evaluation, Resolution; "Open decision for a human" replaced; stays
  `open` for QA to set `resolved` (CR-007 D-8).

Open: the human accepts the residual in MedTrace (RISK-007). `traceability-check` was not run by this role; the
QA stage runs it.
