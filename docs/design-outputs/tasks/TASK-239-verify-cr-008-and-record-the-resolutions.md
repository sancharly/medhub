---
id: "TASK-239"
type: task
title: "Verify CR-008 end to end, re-score the risks and record the PRB resolutions"
status: approved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-26"
links:
  - target: "SR-017"
    relation: implements
  - target: "RISK-003"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-008"
    relation: relates_to
  - target: "PRB-048"
    relation: relates_to
  - target: "PRB-046"
    relation: relates_to
  - target: "PRB-075"
    relation: relates_to
  - target: "PRB-094"
    relation: relates_to
  - target: "PRB-095"
    relation: relates_to
  - target: "SR-013"
    relation: implements
  - target: "TS-007"
    relation: relates_to
  - target: "TS-019"
    relation: relates_to
  - target: "TS-010"
    relation: relates_to
  - target: "TS-013"
    relation: relates_to
tags: ["cr:CR-008", "verification"]
---

# TASK-239 — Verify CR-008 end to end, re-score the risks and record the PRB resolutions

- **Role:** Software Developer (runs the verification), with the Software Architect role for the re-score.
- **CR:** CR-008 (Verification approach; IEC 62304 §8.2.3, §9.7).
- **Depends on:** TASK-233 to TASK-238 and TASK-240 all `approved` by QA. Last task.
- **Size:** M (records only; no code unless a defect is found, which becomes a PRB, never a silent fix).

## Objective

Execute CR-008's verification approach on the branch head, replace every "planned" in the RISK and TS
records with the executed result, re-score RISK-003 and RISK-007 from the evidence, and record the
resolutions of PRB-048, PRB-046 and PRB-094.

## Steps

1. **Suites** on the branch head (record the commit): backend with coverage, module suite, Ruff, Black,
   mypy; frontend test, lint, typecheck, build on Node 20+ (CI: 24.22.2); infra tests and pin check;
   Docker Build with the TASK-236 step.
2. **Clean checkout:** in a fresh clone of the branch, `cd backend && uv sync --frozen` and the
   entry-point command of CR-008 (prints `['dicom-viewer']`).
3. **Negative controls** (CR-008): step 2's command and the TASK-236 step on an image built at 396e9de
   (fail); module guard tests with the package uninstalled (fail); allow-list removed (TC-019.6 fails); the upload inflation check removed (TC-007.18 fails).
   Restore after each.
4. **Started stack** (`docker compose -f infra/docker-compose.yml up -d --build`, throwaway secrets as in
   DEPLOY.md), `bash infra/smoke-test.sh` (0 failed, includes TC-010.9's 401). Then as a system
   administrator enable `dicom-viewer` for a group, as a doctor of that group with access to a patient:
   upload a real uncompressed multi-frame DICOM (generated with the TASK-234 fixtures helper and written to
   a file), `GET /studies/{id}` (200 `application/dicom`, SHA-256 equal to the upload), `?frame=0` and the
   last frame (200 `application/octet-stream`, bytes equal to the known values, time recorded),
   `?frame=<frames>` (400), a JPEG Baseline object `?frame=0` (400 `dicom_transfer_syntax_unsupported`);
   a user without the module enabled gets 403. Upload path (PRB-094, TC-007.18 at system level): upload
   a small valid Deflated DICOM (accepted, downloaded byte-identical) and a deflate bomb under 1 MiB stored
   that inflates above 1 GiB (400 `dicom_decoded_size_exceeded`; the backend container's memory, from
   `docker stats --no-stream`, stays within a few hundred MiB of its idle value and no worker restarts in
   `docker compose logs backend`; no attachment row). This is **TC-019.5, backend frame part**; the "first
   rendered image within 10 s" part stays deferred to #29 (SR-026 AC 3; CR-006 D-35, CR-007 D-2).
5. **Records:**
   - TS-019, TS-010, TS-013, TS-007: verification results dated, TC-019.5 backend part executed.
   - RISK-003 (1.6 → 1.7) and RISK-007 (1.21 → 1.22), Software Architect role: each CR-008 row's
     "planned" replaced by the executed test and date; re-score from the evidence (expected unchanged: 4 × 2
     and 3 × 2, alarp); stay `in_review` for the human's acceptance.
   - PRB-048, PRB-046 and PRB-094: a `## Resolution` section each (PRB-094 replaces its "Not fixed yet" text) (what changed, by which TASKs, the evidence with
     commit and date, the negative controls), status `open` → `resolved` (the CR-008 `resolves` links
     exist). Not `closed`: the human closes in MedTrace after the merge.
   - PRB-075: a dated note — with `dicom-viewer` installed the registry sync runs at every start; the
     failure stays unreachable with one module (RISK-007 1.21). Status unchanged.
   - SOUP-037 and SOUP-015: confirm `soup_version` equals `backend/uv.lock`; anomaly review stays
     2026-11-25 unless a new release appeared, in which case review it.
   - CR-008: verification summary; status stays `in_progress` (never `closed` by an agent).
6. `traceability-check` on every CR-008 record (CR, SR-017, RISK-003, RISK-007, SOUP-015, SOUP-037,
   ADD-012, ADD-014, ADD-015, ADD-021, ADD-022, TASK-233 to TASK-240, TS-005, TS-007, TS-010, TS-013, TS-019,
   PRB-046, PRB-048, PRB-094):
   0 errors.

## Verification

The steps are the verification. Pass: every suite green; each negative control fails as expected and
passes when restored; the started-stack results as listed; `traceability-check` 0 errors.

## Acceptance criteria

- [x] CR-008's verification approach executed on the branch head, every result dated with the commit
  (SR-017 AC 6 to AC 11, SR-013 AC 6; TC-019.5 backend part, TC-010.9, TC-013.15, TC-007.18).
  Locally; the hosted Docker Build job is pending (after push), and the smoke test reached 75 passed,
  1 failed (PRB-096, older and outside CR-008; QA review round 1, QA-1).
- [x] RISK-003 and RISK-007 re-scored from the evidence and left `in_review`; PRB-048, PRB-046 and
  PRB-094 `resolved` with their Resolution sections.

## Definition of Done

- [x] Records updated; `traceability-check` 0 errors; any defect found raised as a PRB

## Implementation record (Software Developer, 2026-11-26)

Run on branch `bug/dicom-module-install`, head `5bd10e7` plus this task's uncommitted working-tree changes
(the orchestrator commits after QA). Python 3.12.15 (uv, `backend/.venv`), Node 20.19.0 via nvm, Docker Desktop (Compose 2.x).

**Code and test changes made in this task** (carried items; none changes product behaviour):

- PRB-095 (CR-008 D-D): `_dicom` in `backend/modules/dicom_viewer/tests/test_size_bounds.py` uses the fixed `SOP_INSTANCE_UID` of `fixtures.py`. 3000 builds of `_padded_to(MAX_STORED, 8192, 8192, 8)`: 0 mismatches; the same loop with a random UID: 54 mismatches (1.8 %).
- TASK-236 QA R1-1: `backend/scripts/check_image_modules.py` also asserts `[m.module_key for m in discover_modules()] == ["dicom-viewer"]` (it puts `<app>` on `sys.path` first). A stand-in `uv sync --frozen --no-dev --no-editable` install with the entry-point target `dicom_viewer.manifest:nope`: the name-only version passes, the new one exits 1 (`discover_modules() loaded [], expected ['dicom-viewer']`); the unmodified stand-in exits 0.
- TASK-236 QA R1-2: TASK-236 1.2 and TS-013 1.8 cite QA's run on the pre-TASK-233 image `infra-backend:latest` instead of `HEAD` 396e9de. R1-3: TS-010 1.8 (Levels, started-stack precondition). R1-4: `infra/smoke-test.sh` check 9b uses the fixed UUID `00000000-0000-4000-8000-000000000000` (no `python3` needed, never empty); `bash -n` passes.
- TASK-240 QA-2: `backend/tests/attachments/test_dicom_validation.py` asserts the Modality, PatientID and StudyDate values (`CT`, `P-0001`, `20261126`, written into the built objects by a small helper) instead of the key sets. QA-1 (MEDIUM) was already corrected in TASK-240 1.2 ("Corrected at commit per QA-1").
- TASK-238 QA-1: TS-019 TC-019.13 and `test_trailing_pixel_data_under_one_frame_is_ignored_a_whole_frame_refused` (2 and 30 extra bytes give the exact frame, 32 gives `dicom_decode_failed`), fixture `build_trailing_pixel_data`. QA-2: `docs/design/07-deployment-view.md` lists `alembic.ini`. QA-3: `infra/DEPLOY.md` reads "Being in the image does not enable it". QA-4: ADD-021 1.5. QA-5: ADD-015 1.5 and `docs/design/05-building-blocks.md` name `validate_dicom_content_type`. QA-6: `docs/design/12-interfaces.md` adds the `401`/`403`/`404` row and says what the table lists.

**Step 1, suites** (all pass; hosted CI not run):

| Suite | Result |
|---|---|
| Module suite, `pytest --import-mode=importlib modules/dicom_viewer/tests` | 84 passed |
| `tests/modules` (separate call) | 119 passed |
| Backend, full, `--cov=app --cov-fail-under=85` (`TESTCONTAINERS_RYUK_DISABLED=true`) | 1775 passed, 10 skipped; coverage 95.24 % |
| Ruff check, Black --check, `mypy app` (138 files), `mypy modules/dicom_viewer/dicom_viewer` (4 files) | clean |
| OpenAPI export vs `backend/openapi/openapi.json` | identical |
| Frontend (Node 20.19.0): `npm run test -- --run`, lint, typecheck, build | 412 passed (41 files); lint 0, typecheck 0; build within the 165 kB bundle budget |
| `python3 -m unittest discover -s infra/tests` | 178 passed |

**Step 2, clean checkout.** Fresh clone of the branch (head 5bd10e7), `cd backend && uv sync --frozen --python 3.12`, then the CR-008 command prints `['dicom-viewer']`. (Without `--python 3.12` `uv` picked the host's Python 3.15 and failed to build `psycopg2-binary`; the repository has no `.python-version`. CI pins 3.12.)

**Step 3, negative controls** (each restored; the working tree matches before and after):

| Control | Result |
|---|---|
| Image check on the pre-TASK-233 image `infra-backend:latest` | exit 1, six `FAIL:` lines. (The image of 396e9de itself was not built: QA's run on this image is the cited evidence; hosted CI never builds 396e9de) |
| Package uninstalled (`uv pip uninstall medhub-dicom-viewer`) | the three TS-010 TC-010.8 tests fail; `uv sync --frozen` restores them to passing; the rest of the module suite cannot import |
| Allow-list removed from `_check_transfer_syntax` | the TC-019.6 tests fail (`dicom_decode_failed` instead of `dicom_transfer_syntax_unsupported`); restored, 17 pass |
| Upload inflation check removed from `validate_dicom` | two bomb tests of TC-007.18 fail; restored, 14 pass |
| Entry-point target `:nope` on a stand-in venv | image check exits 1 (new assertion) |

**Step 4, started stack.** Docker pulls did not stall: every image was local or cached. A scratch Compose project `tcheck` beside the user's running `infra` dev stack (not touched): a copy of `infra/docker-compose.yml` with absolute build contexts, subnet 10.78.78.0/24, the proxy published on `127.0.0.1:18443`, `frontend` using the local image `infra-frontend:latest` (no npm download), throwaway secrets generated for this run (never printed or kept), backend built from the working tree. The `tcheck` project was removed with `down -v --rmi local` afterwards (volumes, networks and images; no `tcheck` volume or image remains), and its secrets and test accounts deleted.

- `entry_points(group='medhub.modules')` in the backend container is `['dicom-viewer']`; `check_image_modules.py /app` exits 0 there.
- `bash smoke-test.sh` (a copy with `https://localhost` changed to the published port): 75 passed, 1 failed. That is 76 checks, not the 79 of a stack with every service built: the scratch project ran `frontend` from `image: infra-frontend:latest` without `build:`, so section 11 skipped its three frontend non-root checks (SR-041). After PRB-096 was fixed (TASK-241) the run with the frontend built reads 79 passed, 0 failed. Check 9b: `[PASS] unauthenticated GET /modules/dicom-viewer/studies/<uuid> returns 401` (TC-010.9). The one failure, `'backend' stores and reads back an object: TypeError: ObjectStorageClient.put_object() missing 1 required positional argument: 'content_type'`, is an older defect of the smoke test itself, raised as PRB-096 (not CR-008). "0 failed" was therefore not reached.
- Flow (accounts created by a seed script in the backend container, everything else over HTTPS through the proxy): sysadmin created a group and enabled `dicom-viewer`; before enabling, a doctor in the group got 403; the patient granted consent to the doctor; the doctor created a clinical entry and uploaded:
  - a 4-frame 16-bit uncompressed object (33 264 bytes): `GET /studies/{id}` 200 `application/dicom`, SHA-256 equal to the upload; `?frame=0` and `?frame=3` 200 `application/octet-stream`, 8192 bytes equal to the known values (78 ms, 16 ms); `?frame=4` 400 "Frame 4 out of range; this DICOM has 4 frames.";
  - a JPEG Baseline object: `?frame=0` 400 `dicom_transfer_syntax_unsupported`; whole-object GET byte-identical;
  - a second doctor, not in the group: 403 "Module 'dicom-viewer' is not enabled for your account.";
  - a small valid Deflated object: accepted, downloaded byte-identical;
  - a deflate bomb of 1 044 152 bytes stored (under 1 MiB) inflating above 1 GiB: 400 `dicom_decoded_size_exceeded` in 1.8 s; backend memory 152.1 MiB idle, 153.1 MiB during and after (`docker stats`); `RestartCount` 0, `OOMKilled` false, one "Booting worker" line (the start); the entry's attachments are the three accepted ones, none for the bomb.
- TC-019.5 backend frame part: executed. The "first rendered image within 10 s" part stays open for #29.

**Step 5, records.** TS-019 1.7, TS-010 1.8, TS-013 1.8, TS-007 1.15 (each `in_review`, results dated); RISK-003 1.7 and RISK-007 1.22 re-scored and `in_review`; PRB-048, PRB-046, PRB-094 and PRB-095 `resolved` with Resolution sections; PRB-075 dated note, status unchanged; PRB-096 created (`open`, outside CR-008); CR-008 1.4 verification summary, status `in_progress`; TASK-236 1.2 `in_review`; ADD-015 and ADD-021 1.5 `in_review`.

- **Re-score.** RISK-003: 4 × 2 → alarp, unchanged (initial 4 × 3 unchanged). RISK-007: 3 × 2 → alarp, unchanged (initial 3 × 2 unchanged). No residual changes, so no new human decision is needed beyond the MedTrace approval already awaited.
- **SOUP.** SOUP-037 `soup_version` 2.5.5 and SOUP-015 `soup_version` 3.0.2 equal `backend/uv.lock`; PyPI's latest releases on 2026-11-26 are numpy 2.5.5 and pydicom 3.0.2, so the anomaly review of 2026-11-25 stands. The records are not changed.

**Step 6, traceability-check** (fallback parser, E1 to E9 over all 488 records, scope: CR-008, SR-017, SR-013, RISK-003, RISK-007, SOUP-015, SOUP-037, ADD-012, ADD-014, ADD-015, ADD-021, ADD-022, TASK-233 to TASK-240, TS-005, TS-007, TS-010, TS-013, TS-019, PRB-046, PRB-048, PRB-075, PRB-094, PRB-095, PRB-096): **0 errors**. Warnings in scope: 1 W6 (CR-008 links the obsolete ADD-004) and 36 W5 (approved TASKs and SR-013 link records now `in_review` pending the human's approval); no SOUP, risk or `risk_not_acceptable` finding. PRB-048, PRB-046, PRB-094 and PRB-095 each have an incoming `resolves` link from CR-008. MedTrace's own Verify view was not run here.

**Open / pending.**
- Hosted CI: the Docker Build job (including the TASK-236 image check) and the full workflow run only after the human approves a push. Verified on hosted CI after push; not claimed.
- TC-019.5 "first rendered image within 10 s" and the viewer: #29.
- "0 failed" on the smoke test: blocked by PRB-096.
- The image of `HEAD` 396e9de was not built (see step 3).

## Carried from TASK-236 (QA, 2026-11-25)

TASK-236 was approved with these open findings (details in TASK-236 "QA review — round 1"):

- R1-1 [MEDIUM] `backend/scripts/check_image_modules.py` compares entry-point names only; an entry point with the
  right name and a wrong value passes. Add a `discover_modules()` (or `ep.load().module_key`) assertion, or record
  the human's decision to rely on TC-010.8 and smoke 9b.
- R1-2 [LOW] TASK-236 and TS-013 TC-013.15 say the `HEAD` 396e9de negative run is "to be verified on hosted CI";
  hosted CI never builds 396e9de. Cite QA's run on the pre-TASK-233 image `infra-backend:latest` (exit 1) instead.
- R1-3 [LOW] TS-010: add "system (TC-010.9)" to Levels and the started-stack precondition (`curl`, `python3`).
- R1-4 [LOW] `infra/smoke-test.sh:175`: an empty `STUDY_ID` (no `python3`) requests `/studies/` and reports "module
  route not mounted". Check it is non-empty or use a fixed UUID.
- Hosted CI: record the Docker Build job's result for the new step on the pushed commit (TC-013.15).

## QA review — round 1 (2026-11-26): APPROVED

Reviewed on head 5bd10e7 plus the working tree. Re-run by QA, each its own call: module suite
(`--import-mode=importlib`) 84 passed, run 6 times; `tests/modules` 119 passed; full backend with coverage
1775 passed, 10 skipped, 95.24 % (`TESTCONTAINERS_RYUK_DISABLED=true`); Ruff check clean, `ruff format --check`
and Black `--check` clean on the five changed Python files; `mypy app` 138 files and `mypy` of the module 4 files
clean; OpenAPI export identical; frontend on Node 20.19.0 412 passed (41 files), lint 0, typecheck 0, build within
budget (160.44 of 165 kB gzip); `infra/tests` 178 passed; `bash -n infra/smoke-test.sh` 0.

- PRB-095: 3000 base builds with the fixed UID give one encoded length (376 bytes), and 30 full builds at
  `MAX_STORED` give 0 mismatches. Control with a random UID per build: 69 mismatches in 3000 (2.3 %). The
  fix is deterministic by construction.
- Image check, in the real image `medhub-backend:ci` (`57e3d35a9b47`), run as CI runs it (no environment) with
  the new script mounted: exit 0. With the entry point rewritten to `dicom_viewer.manifest:nope` inside the
  container, the old script exits 0 and the new one exits 1 (`discover_modules() loaded []`). On
  `infra-backend:latest` it exits 1 with six `FAIL:` lines. This goes further than the developer's stand-in venv.
- Negative controls re-run with pytest mutation plugins (the working tree was not edited): with the allow-list
  emptied, 11 module tests fail, including TC-019.6 (`dicom_decode_failed` instead of
  `dicom_transfer_syntax_unsupported`). With `check_inflated_size` stubbed, the two TC-007.18 bomb tests fail.
  With `patient_id` and `study_date` swapped in `validate_dicom`, the new value assertions fail. `_with_metadata`
  keeps the Deflated transfer syntax.
- PRB-096 predates CR-008. The smoke lines are unchanged since d4cdba0 (TASK-177, 2026-10-30). `put_object` became
  `(key, fileobj, size, content_type)` in 3bdd7ee (TASK-135, 2026-11-13 15:05). The last "0 failed" runs were
  TASK-215 and TASK-216 (f645979 and a5fd91a, 2026-11-13 00:21 and 00:58), before that commit, and no smoke run is
  recorded for CR-006 or CR-007. CR-008 changes neither `object_storage.py` nor that section: `git diff 396e9de`
  on the smoke script adds only check 9b. The suggested call binds to the current signature.
- All four PRB `resolved` transitions have an incoming CR-008 `resolves` link, cite evidence that can be
  re-run, and mark hosted CI as pending. RISK-003 is 4 × 2 and RISK-007 is 3 × 2, both alarp, matching
  `risk_matrix`, and both are left `in_review`. Every re-scored row cites an executed test. TASK-238 QA-1
  to QA-6 and TASK-236 R1-1 to R1-4 are done as described: the check order was checked against `router.py`,
  and `alembic.ini` against `backend/Dockerfile`. `soup_version` of SOUP-015 and SOUP-037 equals `uv.lock`.
- `traceability-check` (fallback parser, all 488 records): 0 errors. There were 139 warnings before these status
  changes (129 W5 from records awaiting the human, 9 W6 obsolete targets, W1 SR-018) and 129 after. All of
  them are pre-existing or come from approvals still awaited in MedTrace.

Findings (none blocking):

- **QA-1 [LOW] Step 4 "0 failed" not met.** Smoke 75 passed, 1 failed. The failure is PRB-096: older than
  CR-008, not caused by it, and raised as a PRB as the DoD requires. The object-store path it covers was used in
  the same run (uploads stored and downloaded byte-identical), and the CR-008 check 9b passed. Accepted as
  evidence for CR-008. Whether PRB-096 is taken into CR-008 (a two-line fix in `infra/smoke-test.sh`, with a
  smoke re-run) or left to a later CR is the human's decision. Record it as D-E if it is taken in.
- **QA-2 [LOW] Smoke count not explained.** The stack as shipped gives 78 checks at CR-005 plus check 9b, so 79.
  This run had 76. The scratch project ran `frontend` from `image: infra-frontend:latest`, without `build:`,
  so section 11 skipped its three frontend checks (Config.User, PID 1 and `id -u` non-root, SR-041). Add one
  sentence saying so in this record and in TS-010 TC-010.9.
- **QA-3 [LOW] `TS-010` TC-010.9 cell.** "passes in TASK-236 Executed 2026-11-26" needs a full stop before
  "Executed".
- **QA-4 [LOW] `TS-019` scope.** "Levels: unit and integration" leaves out system level, although TC-019.5 now
  records a system-level run. TS-010 had the same gap, fixed under R1-3. Add "system (TC-019.5)".
- **QA-5 [LOW] PRB-096 Investigation.** Add the timing evidence above: the last 0-failed runs came before 3bdd7ee,
  and CR-006 and CR-007 recorded no smoke runs. The suggested fix also needs `import io` in the snippet.

For information (release, not this task): PRB-043 and PRB-071 are `critical` and `resolved` but not `closed`,
so they block a release until the human closes them. The 33 SOUP anomaly reviews date from 2026-10-22 to
2026-11-25, all within 365 days. SR-017 and SR-013 AC 6 are verified by executed TS cases, but no `test-report`
reaches them yet (TR-001 and TR-002 date from 2026-10-21), so a release needs a new TR.

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
- 1.1 (2026-11-25) — CR-008 D-B: depends on TASK-240; also verifies and resolves PRB-094 (TC-007.18, started-stack upload of a deflate bomb); `implements` SR-013 added. `draft`.
- 1.2 (2026-11-26) — D-D: PRB-095 added to the task's links. Implemented (Software Developer role): verification executed, records updated, carried QA items closed. `in_review`.
- 1.2 (2026-11-26, QA) — QA review round 1: APPROVED with LOW QA-1 to QA-5; acceptance criteria and DoD ticked. `approved`.
- 1.3 (2026-11-26) — TASK-239 QA-2: the 76 versus 79 smoke count explained; the later 79-passed, 0-failed run noted (TASK-241). Content change on an approved record, so the status returns to `in_review`.
- 1.3 (2026-11-26, QA) — QA review of TASK-241 (round 1): the 1.3 edit is the QA-2 sentence only; QA-1 to QA-5 closed (QA-1 by D-E and TASK-241). `approved` (status only; content unchanged).
