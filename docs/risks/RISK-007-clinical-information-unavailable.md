---
id: RISK-007
type: risk
title: Clinical information unavailable when needed
status: in_review
version: "1.22"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-26"
hazard: The application, its database, its object storage or its workers unavailable, or attachments unreadable.
cause: Single-host outage, database or object-store failure, exhausted connection pool from a session leak, a missing storage SDK (PRB-002), an encryption key rotation that makes old rows unreadable, upload scratch space full under concurrent large uploads (PRB-092), a crafted Deflated DICOM object inflated without bound in the API process, or an optional module (the DICOM viewer) absent from the deployed image → the clinician cannot open the record → they proceed without it or wait.
harm: Delayed care; decisions made without available history. No direct physical harm from the software itself.
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 2
acceptability: alarp
links:
  - target: SOUP-020
    relation: relates_to
  - target: SOUP-036
    relation: relates_to
  - target: SOUP-019
    relation: relates_to
  - target: SOUP-014
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
  - target: SOUP-015
    relation: relates_to
  - target: SOUP-037
    relation: relates_to
tags:
  - hazard:availability
  - class:B
---

# RISK-007 — Clinical information unavailable when needed

## Hazard

The application, its database, its object storage or its workers unavailable, or attachments unreadable.

## Sequence of events

Single-host outage, database or object-store failure, exhausted connection pool from a session leak, a missing storage SDK (PRB-002), an encryption key rotation that makes old rows unreadable, upload scratch space full under concurrent large uploads (PRB-092), a crafted Deflated DICOM object inflated without bound in the API process, or an optional module (the DICOM viewer) absent from the deployed image → the clinician cannot open the record → they proceed without it or wait.

Two DICOM causes are explicit since CR-008 (2026-11-25):

- **Module absent from an environment (PRB-048).** Until CR-008 the DICOM viewer module was installed
  nowhere, so its endpoint answered 404 in every environment and SR-017 was silently unavailable. A
  packaging change could do it again (a module dropped from the lock, a wheel built without its
  package, an import that fails at discovery, which logs and skips the module).
- **Unbounded inflation of a Deflated object (pydicom 3.0.2, SOUP-015).** pydicom inflates the whole
  data set of a Deflated Explicit VR Little Endian file in memory with no limit while reading it, even
  header-only. An object within the 150 MiB stored bound can inflate about 1000-fold, so one crafted
  object can exhaust the API container's memory and stop the worker that reads it. Two paths read it:
  the module's frame path (reachable once CR-008 installs the module) and the host's upload validation
  (`app/attachments/dicom_validation.py`, reachable today by any user who may upload an attachment;
  [PRB-094](../problem-reports/PRB-094-upload-validation-inflates-deflated-dicom-without-bound.md), major).
  Both are controlled in CR-008 by the same bounded inflation (rows below; D-B).

A stored file name that cannot be represented in an HTTP header makes the attachment undownloadable (PRB-063): the download answered 500 for any character outside Latin-1.

Since CR-002 the object store is SeaweedFS ([SOUP-036](../soup/SOUP-036-seaweedfs.md)), replacing
MinIO. Two object-store causes are explicit: an attachment whose stored bytes fail the checksum
check is refused rather than served (SR-013 AC 5), and a lost or changed `AT_REST_ENCRYPTION_KEY`
makes every stored object unreadable, because the store derives its only SSE key from it (SOUP-036
F-4).

An upload can fail when a temporary directory is full (PRB-092). The reverse proxy buffers the request body
in its client-body temporary directory and Starlette spools a file part above 1 MiB to a temporary file in the
API container (ADR-0021), so several concurrent maximum-size (150 MiB) uploads on a small disk exhaust the
space (about 300 MiB per upload where both directories share a disk). When the API container's directory is
full the upload answers 503 `upload-storage-unavailable` with `Retry-After: 30` and one ERROR log line, and
nothing is stored (TASK-232); before TASK-232 it answered a plain, unlogged 400. When the proxy's directory
is full nginx answers its own 500 and logs at `crit`. Other requests that need the directory may fail while
it is full.

## Hazardous situation

A clinician needs clinical information that the system cannot deliver.

## Harm

Delayed care; decisions made without available history. No direct physical harm from the software itself.

## Software items involved

SI-API, SI-PERSIST, SI-ATTACH, SI-WORKER, infrastructure (single-host Compose, ADR-0010).

## Initial risk

Severity 3 — Moderate (care delayed) — × probability 2 (Remote) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Documented backup, monitoring and deployment procedure | Protective | SR-028, TASK-115 | TR-001, TS-013. **Backup part not met:** no backup and restore procedure exists for `postgres_data` or `object_store_data` with its key ([PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md), major, open, found 2026-10-30 by CR-002 TASK-180) |
| Performance budgets so routine operations stay usable | Design | SR-026 | TS-018 TC-018.3 and TC-018.12: 20-client load test through the proxy, 0 × 5xx, p95 at most 1.05 s for every operation (GET /me 0.281 s, create clinical entry 0.371 s); build budget 160.44 kB gzip of 165 in the production image build on Node 24.22.2 (TC-018.10; 160.06 kB on the host's Node 18.17.1); passed 2026-11-15 on the branch head (TASK-226). AC 3 (DICOM first image) is not measurable: the viewer is not installed and NumPy is missing (TC-018.11, PRB-048, PRB-046) |
| Worker retries with backoff and no silent enqueue failures | Protective | TASK-141 | TS-004 TC-004.5 (sweep retries at most 3 times, `backend/tests/workers/test_retention_tasks.py`), TS-017 TC-017.6 to TC-017.8 and TS-003 TC-003.7 (enqueue logging, TASK-207); passed 2026-11-15 on the branch head (TASK-226), backend 1743 passed |
| No blocking IO on the event loop, with thread-pool and connection-pool sizes set together: 20 concurrent mixed clients on one API worker get no 5xx and the SR-026 AC 1 and AC 2 budgets hold; a slow call for one request does not delay unrelated ones (CR-006, PRB-009, PRB-072) | Design | SR-026 AC 5; TASK-136 (final load test TASK-226) | TS-018 TC-018.1 (static test), TC-018.2 (slow call isolation), TC-018.4 (pool settings and start-up invariant); TC-018.3 (20-client load test), final run 2026-11-15 (TASK-226) through nginx with the deployed 20 / 20 / 20 / 10 values: 29 601 requests, 0 × 5xx, 0 transport errors, 0 worker kills, 0 `QueuePool limit` lines (before, on `8028685`: 210 transport errors and 10 worker kills in 456 requests). Residual: about threads + connections concurrent requests per worker, beyond that 500s after the pool timeout ([PRB-081](../problem-reports/PRB-081-requests-beyond-threads-plus-db-connections-fail-with-500.md), minor, open) |
| Attachment upload and download in bounded chunks; an over-limit upload refused after at most the limit plus one chunk; the download checksum kept by a first chunked pass before the streaming pass (CR-006, PRB-008, D-6) | Design | SR-013 AC 6, AC 5; SR-026 AC 5; TASK-135 (upload), TASK-217 (download) | TS-007 TC-007.12 (over-limit upload refused within limit plus one chunk), TC-007.13 (memory-bounded two-pass download, conditional second read, second-pass mismatch aborts), TC-007.6 to TC-007.8 unchanged; passed 2026-11-15 on the branch head (TASK-226). System level, TC-007.16 on a started stack through nginx: 100 MiB and 150 MiB uploaded and downloaded with equal SHA-256 (150 MiB download 2.83 s, two reads), 151 MiB refused with a problem response, a replaced object answers 502 with a FAILURE audit row (the first-pass checksum path, no second read); real SeaweedFS 4.51 conditional-read tests 4 passed (the second read's `If-Match`, `test_replaced_object_is_refused_with_object_changed`) |
| DICOM stored-size and declared-decoded-size bounds checked before decoding, so one study cannot exhaust the API process (CR-006, PRB-006, D-2) | Protective | SR-017 AC 6; TASK-218 | TS-019 TC-019.1 to TC-019.4 (`backend/modules/dicom_viewer/tests/test_size_bounds.py`; `pixel_array` stubbed because NumPy is absent, PRB-048) |
| Data-access cost does not grow with the data: indexes on the lookups of SR-026 AC 6 (migration 0011, four; migration 0012, attachments by clinical entry and active consents by doctor, D-29), constant queries for `groups_of`, one-row activation check (CR-006, PRB-021, PRB-024, PRB-022 regression) | Design | SR-026 AC 6; TASK-219 (0011 indexes, activation), TASK-220 (`groups_of`, 0012 indexes) | TS-018 TC-018.5 to TC-018.8 (`test_migration_0011_indexes.py`, `test_migration_0012_indexes.py`: upgrade and downgrade empty and populated, `EXPLAIN` uses the index and the negative controls scan), TC-018.6 (activation reads one row), TS-005 TC-005.4 (`groups_of` constant query count); passed 2026-11-15 on the branch head (TASK-226). Started stack, empty database: migrations 0011 and 0012 applied in 1.7 s and 1.6 s wall time including the process start (0001 to 0010 in 1.9 s), no error |
| Retention sweep isolates a failing dataset, releases every session it opens and retries at most 3 times, so it cannot exhaust the connection pool (CR-006, PRB-012) | Protective | SR-024 AC 5; TASK-141 | TS-004 TC-004.5 (`test_sweep_failing_dataset_closes_every_session`, `test_sweep_retries_at_most_three_times_then_logs_count`, `test_sweep_dataset_failing_once_then_succeeding_is_erased`, `test_sweep_never_deletes_before_deadline_across_retries`) and TC-004.7 (real PostgreSQL lock); passed 2026-11-15 on the branch head (TASK-226) |
| A route chunk that fails to load (route-level code splitting) shows a clear message with a retry, never a blank route (CR-006 change-analysis cause 11, PRB-020) | Protective | SR-027 AC 3, SR-026 AC 7; TASK-145 | TS-012 TC-012.6 (failed chunk shows the message, Retry imports it again and the page renders; negative control without the rebuild fails); TS-018 TC-018.10 (initial payload 159.93 kB gzip, within 165 kB) |
| Object storage SDK declared as a required runtime dependency and verified in CI | Design | TASK-157 (CR-001, resolves PRB-002) | TS-007 TC-007.5, TS-013 TC-013.8 |
| Key identifier in the ciphertext envelope so rotation cannot orphan rows | Design | SR-022, PRB-004 resolution | TR-001, TS-008 |
| Bucket initialisation ordered after the store is healthy and fail-fast: the backend does not start on a missing or misconfigured bucket (CR-002, PRB-039) | Protective | SR-040 AC 4; TASK-175 (re-run on SeaweedFS by TASK-176) | TS-014 TC-014.4: initialiser starts only after `object-store` is healthy (`docker events` order); an unreachable store gives exit 1 and `backend` stays `Created`; idempotent re-run (TASK-175 and TASK-176 QA reruns) |
| Checksum refusal fails with a clear error, never with partial or wrong content (CR-002) | Protective | SR-013 AC 5; TASK-173 | TS-007 TC-007.6, TC-007.8: 502 `application/problem+json` naming only the attachment id, no object bytes, committed FAILURE audit row; TC-007.7: an unmodified object is served (TASK-173 QA rerun) |
| Field values converted to the identified envelope in one transaction that rolls back if any value does not decrypt; tested against a database populated in the old format; an unknown key id is refused, never decrypted with another key (CR-004, ADR-0018) | Protective | SR-022 AC 6, AC 7; TASK-193, TASK-194 | TS-008 TC-008.9, TC-008.10 (real database populated in the old format) |
| Rotation by a re-encryption command with a `--check` mode, rehearsed on a backup copy before use (CR-004) | Protective | SR-022 AC 8; TASK-195 | TS-008 TC-008.11; rehearsal records in TASK-195; TASK-202 repeated it on a started stack with attachments (5 values converted from `k1` to `k2`, `--check` exit 0, 5 of 5 entries and 10 of 10 attachments readable and matching after each step) |
| Attachments moved to the separate SSE key by a copy with checksum comparison, source read only, rehearsed on a backup copy (CR-004) | Protective | SR-041 AC 5; TASK-196 | TS-014 TC-014.7; rehearsal record in TASK-196; TASK-202: the bucket held 10 objects for 10 attachments before the rotation, after it and after the retired key was removed |
| File names encoded per RFC 6266/5987 with an ASCII fallback; the header is built in one place | Design | SR-013 AC 3; TASK-204 | TS-007 TC-007.9 |
| A file name is refused above 255 UTF-8 bytes at upload, and the `Content-Disposition` value is bounded (about 1 KB) for any stored name, so a long name cannot make the download fail at the proxy (CR-004, PRB-069) | Design | SR-013 AC 1, AC 3; TASK-206 | TS-007 TC-007.11 |
| Dispatch does not wait on a result store (`task_ignore_result`): a Celery `.delay()` with Redis unreachable ends within 5 s instead of about 20 s inside the request's open transaction (CR-004, TASK-206 QA finding 1) | Design | TASK-207 | TS-003 TC-003.7 |
| Retrieval rate limit per originating client address, so one caller cannot block retrieval for all (CR-004, PRB-029) | Design | SR-042 AC 4, AC 5; TASK-186 (keys on the originating address that TASK-185 provides; without it every caller would share the proxy's bucket) | TS-016 TC-016.4, TC-016.5; a missing peer is refused without touching any `rate:*` key |
| A write is acknowledged only after it is committed: the request transaction ends before the response is sent, so an immediate read finds the write and a failed commit is a 5xx the user sees, not a lost acknowledged write; a streamed download no longer holds a connection during the transfer (CR-006 D-27, PRB-080, ADR-0023) | Design | SR-012 AC 5; TASK-227 | TS-007 TC-007.14 (`backend/tests/db/test_request_commit_order.py`: success only after commit, a failed commit is a 5xx) and TC-007.15 (`test_download_audit_order.py`: audit rows committed before the first body chunk); passed 2026-11-15 on the branch head (TASK-226). The 20-client run (TC-018.3, which writes and reads back under load) showed no 5xx and no pool wait |
| Spool failure on upload detected, logged at ERROR (HTTP method, route template, errno; no path, file name or clinical data) and answered 503 `application/problem+json` `upload-storage-unavailable` with `Retry-After: 30`; nothing stored; a malformed body stays 400 (CR-007 D-7, PRB-092, ADR-0021) | Protective | SR-013 AC 1, SR-027 AC 3; TASK-232 | TS-007 TC-007.17 (`backend/tests/api/test_attachments_router.py::TestUploadScratchSpaceFailure`, 4 tests, fail on `4eeef74`); TS-011 TC-011.7 (the upload form shows the 503 detail) |
| Deployment guide names both temporary directories (the API container's `/tmp` unless `TMPDIR` is set, the proxy's nginx client-body directory), sizes them at about 300 MiB free per concurrent maximum-size upload where they share a disk, tells the operator to monitor the free space and states the failure behaviour (CR-007 D-1, D-7, D-8, PRB-092) | Information | SR-013 AC 1; TASK-231 | Review of `infra/DEPLOY.md` (TASK-231 QA); no automated test: information for safety |
| DICOM viewer module installed from the lock in every environment (uv workspace member, non-editable in the image, ADR-0024), with the entry point proven discovered in the CI test environment and in the production image, which fails the build otherwise; the started stack answers 401, not 404, on the module route (CR-008 D-1, D-6, D-7, PRB-048) | Protective | SR-017 AC 7; TASK-233, TASK-236 | TS-010 TC-010.8 (guard test in the module suite; passed 2026-11-26; negative control run that day: package uninstalled and the three guard tests fail, reinstalled and they pass); TS-013 TC-013.15 (the image check, `backend/scripts/check_image_modules.py`, now also asserts `discover_modules()` returns `dicom-viewer`): exit 0 in an image built from the branch, exit 1 on the pre-TASK-233 image `infra-backend:latest` and on a stand-in install whose entry-point target is `dicom_viewer.manifest:nope`; the hosted Docker Build job: verified on hosted CI after push (pending); TS-010 TC-010.9 (smoke test 401): `[PASS]` on a started stack, 2026-11-26 |
| Deflated objects inflated on the frame path with a bounded decompressor before pydicom reads them: an inflated data set above `dicom_max_decoded_bytes` (1 GiB) is refused with the AC 6 problem `dicom_decoded_size_exceeded`, holding at most the bound plus one chunk in memory (CR-008, SOUP-015 review 2026-11-25) | Protective | SR-017 AC 6, AC 10; TASK-234 | TS-019 TC-019.7 (a deflate bomb under 1 MiB stored is refused without inflating it in full; a valid deflated object decodes), passed 2026-11-26 (TASK-239) |
| Deflated DICOM uploads inflated with the same bounded helper (`app.modules.dicom_support`) before upload validation reads them: an inflated data set above `dicom_max_decoded_bytes` (1 GiB) is refused with a 400 problem `dicom_decoded_size_exceeded` and nothing is stored; other syntaxes unchanged (CR-008 D-B, PRB-094) | Protective | SR-013 AC 6; TASK-240 | TS-007 TC-007.18 (bomb refused without full inflation, nothing stored; valid deflated upload accepted), passed 2026-11-26 (TASK-239); negative control: inflation check removed and two tests fail, restored and they pass; started stack 2026-11-26: a 1 044 152-byte Deflated upload inflating above 1 GiB answered 400 `dicom_decoded_size_exceeded` in 1.8 s, the backend container stayed at 152 to 153 MiB (idle 152 MiB), no worker restart, no attachment row; a small valid Deflated upload was accepted and downloaded byte-identical |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. Single-host Compose with no high availability is a deliberate MVP decision (arc42 §11, ADR-0010); the residual therefore stays ALARP and needs an explicit human acceptance for each release, with the argument that MedHub is not the only route to the information.

**Change analysis (CR-004, Risk stage, 2026-10-31).** CR-004 both strengthens and threatens
this record. Strengthened: the "key rotation makes old rows unreadable" cause gets its design
control (the row above that names PRB-004 is realised by TASK-193..195), and the shared
rate-limit bucket goes (PRB-029). Threatened, by the change itself: the field migration, the
rotation and the SSE key separation can each make clinical values or attachments unreadable, and
the runtime-role grants can make a statement fail. Each has a fail-safe control above and is an
"ask first" step of CR-004. **Expected residual: 3 × 2 → alarp, unchanged**, set by the
single-host decision (ADR-0010) and PRB-057 as before. Confirmed at verification (TASK-202).

**Verification and proposed residual (CR-004 Checkpoint F, TASK-202, 2026-11-08).** Checkpoint F evidence (TASK-202, 2026-11-08, HEAD 579aaaa plus TASK-202's small edits): backend 1547 passed, 6 skipped, coverage 94.51% (floor 85%); DICOM module 25 passed; frontend 315 passed; infra 110 passed; started stack (project `task202`, empty template, generated secrets): `infra/smoke-test.sh` 78 passed, 0 failed; `infra/log-secrets-check.sh` 38 passed, 0 failed. The migration, the rotation and the SSE-key copy each have a test that ran and a started-stack repetition (rotation with attachments, bucket object count unchanged). The celery worker and beat run (smoke test, PRB-061 resolved), and the retention sweep is in the beat schedule. Right after `docker compose up -d --build` replaced the backend, one sign-in got 502 and the same request succeeded seconds later: the stack was not ready yet, which DEPLOY.md should say (a note for the human, not a defect measured). **Proposed residual: severity 3 × probability 2 → alarp** (derived from `risk_matrix`; unchanged). Not lowered: PRB-057 (no backup and restore, `major`, open) is untouched by CR-004. PRB-072 (twenty parallel writes answer 502 and kill the single API worker, `major`, open) and PRB-075 (the backend does not start when a module with group enablement rows is uninstalled or its manifest is rejected, `major`, open) are two further availability causes found during CR-004; both are known anomalies outside it. They are consistent with 3 × 2 but argue against lowering it, and PRB-072 must be re-evaluated at the first release.

**Change analysis (CR-006, Risk stage, 2026-11-13).** CR-006 removes several availability
causes: whole-object buffering of attachments (PRB-008), an unbounded DICOM decode (PRB-006),
blocking IO on the event loop of every authenticated request (PRB-009, the likely mechanism of
PRB-072), data-access cost that grows with the data (PRB-021, PRB-024) and the session leak of the
retention sweep, which is the "exhausted connection pool from a session leak" cause above
(PRB-012). It also introduces causes of its own, each with a control in the CR: the size bounds
refuse a study above 150 MiB; the two-pass download doubles object-store reads for a large study
(measured against SR-026 AC 3); a thread pool sized above the connection pools makes requests
queue and time out (pool sizes set together, verified by the SR-026 AC 5 load test); the index
migration blocks writes to four tables while it runs (ask first, tested on a populated database);
a lazy route chunk that fails to load leaves a route blank (error boundary with retry). **Expected
residual: 3 × 2 → alarp, unchanged**, set by the single-host decision (ADR-0010) and PRB-057, both
outside CR-006. Re-scored from the evidence at the CR-006 verification checkpoint (TASK-226, 2026-11-15): every CR-006 control row above now cites an executed test; the 20-client run through the proxy had 0 × 5xx, p95 at most 1.05 s and no worker kill, so PRB-072's failure (8 clients pass, 16 and 20 fail) is gone and PRB-072 is resolved by TASK-136 (CR-006 D-1, D-26); the 150 MiB download takes 2.83 s with two reads. The residual is still set by the single-host decision (ADR-0010), PRB-057 (no backup procedure) and PRB-081 (about threads + connections concurrent requests, beyond that 500s), none touched by CR-006; **3 × 2 → alarp, unchanged**, and not 3 × 1.

**Change analysis (CR-007, 2026-11-16, PRB-092).** The temporary directories in which an uploaded file is held
(the proxy's client-body directory and, above 1 MiB, Starlette's spool in the API container, ADR-0021) are
neither limited nor checked, so concurrent maximum-size uploads can fill them. Before TASK-232 a full API
directory made FastAPI answer a plain 400 "There was an error parsing the body" that the API did not log, so
the operator could not tell it from a bad request. CR-007 adds no capacity control (D-1): the cause is
accepted as a residual. It adds two measures: the protective one (TASK-232, D-7) makes the failure logged,
visible to the user as a 503 with a retry instruction, and leaves nothing stored; the information one
(TASK-231, `infra/DEPLOY.md`) names both directories, the sizing (about 300 MiB per concurrent maximum-size
upload where they share a disk) and the free space to monitor. A full proxy directory is still nginx's own
500 with a `crit` log line. The harm stays a delayed upload that the user can repeat: no stored record is
changed or lost. **Residual: 3 × 2 → alarp, unchanged.** The protective measure does not lower the
probability that the space runs out; it makes the failure detectable and recoverable, which supports the
ALARP argument but is not scored as a reduction. The cause needs several concurrent maximum-size uploads
on a host with little temporary space; ADR-0010 and PRB-057 still set the residual. The TC-018.3 load test
uploads 1 MiB files and does not exercise this cause. Acceptance is the human's, in MedTrace.

**Change analysis (CR-008, Risk stage, 2026-11-25; §7.4).** CR-008 installs the DICOM module in every
environment and makes its frame path decode (PRB-048, PRB-046). Effects on this record:

- *Removed cause.* SR-017 is no longer unavailable by construction: the module is installed from the
  lock and its discovery is checked in CI and in the image build (protective row above). The
  whole-object path serves any stored study (SR-017 AC 8).
- *Added causes, each controlled in the CR.* The frame path becomes reachable, so pydicom's unbounded
  inflation of Deflated objects becomes reachable through it: bounded inflation before pydicom reads
  the object (row above). A study in a syntax outside D-3 (a) gets no server-decoded frame
  (`dicom_transfer_syntax_unsupported`); the whole object stays available, so this is a refusal, not
  unavailability of the study. A NumPy or module import failure at start-up is logged and the module
  skipped; the core API still starts (discovery isolates per-module errors, `discovery.py`), and the
  image-build check fails first.
- *Start-up now runs the module registry sync* at every start, which it skipped while no module was
  discovered. PRB-075 (start-up fails when a module with enablement rows disappears) **stays
  unreachable**: it needs a second discovered module while one with rows is absent; with `dicom-viewer`
  the only module, uninstalling it or a rejected manifest leaves none discovered and the sync is skipped
  (PRB-075 Investigation). It becomes reachable with the first second module; not fixed here (CR-008 out
  of scope).
- *Upload-path inflation (PRB-094), taken into CR-008 (D-B, 2026-11-25).* Upload validation inflated
  Deflated uploads without bound; reachable today by an authenticated user allowed to upload, with a
  worker killed and uploads and reads delayed, no data lost. Controlled by TASK-240 (row above). A
  legitimate Deflated upload within the bound is still inflated in full by pydicom, up to about 1 GiB per
  request, the same peak the frame path accepts (Q-2); several concurrent ones on a small host can still
  exhaust memory, which is consistent with probability 2.

**Expected residual: 3 × 2 → alarp, unchanged** (`risk_matrix` row 3, column 2), still set by the
single-host decision (ADR-0010), PRB-057 and PRB-081. Bringing PRB-094 under control removes a cause but
does not lower the probability, which those three set. Accepted by the human on 2026-11-25 with its ALARP
argument (CR-008 D-B; recorded, the MedTrace approval of this record confirms it); re-scored from the evidence at the CR-008
verification task (TASK-239, 2026-11-26, branch head 5bd10e7 plus the task's working-tree changes): the
controls above are shown by tests, negative controls and a started stack (see the rows). The started
stack also shows that PRB-075 stays unreachable with one module: the registry sync ran at start-up with
`dicom-viewer` the only module and the registry listed it. The drivers of the residual are
unchanged: ADR-0010 (single host), PRB-057 and PRB-081 still set the probability, and a legitimate Deflated
upload within the bound is still inflated in full. **Re-scored: 3 × 2 → alarp, unchanged**; initial 3 × 2
unchanged. No change of residual, so the human's acceptance of 2026-11-25 stands as given; the record stays
`in_review` for the MedTrace approval. Hosted CI (the Docker Build job and the full workflow) is verified
after the push and is not claimed here.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Single-host deployment without high availability is a documented MVP decision (ADR-0010, arc42 §11): the product is containerized so HA can be added without redesign. Unavailability delays access but does not corrupt or misattribute information, and the institution's own systems remain available.

**Permanent loss is not covered yet.** A disk loss, a failed upgrade or a lost
`AT_REST_ENCRYPTION_KEY` can lose records and attachments for good, not only delay access, because
no backup and restore procedure exists for `postgres_data`, `object_store_data` and the key
([PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md), major, open). The
backup part of the first control row is therefore unmet. The `alarp` residual still holds until
then because no release exists and only development data is stored (CR-002 Q-5), so no clinical
record depends on MedHub alone yet. The benefit of shipping the MVP outweighs this residual for the
initial deployment scale only once PRB-057 is resolved or explicitly accepted. **Re-evaluate** when
PRB-057 is resolved or at the first release, whichever comes first; the residual must be
re-accepted at every release.

## Risks introduced by controls

The CR-002 controls of RISK-012 add availability effects to this record, by design:

- The checksum check refuses an attachment whose stored bytes do not match (502). The clinician
  gets a clear error instead of wrong content; the event is audited. Recorded as a control row
  above.
- The credential preflight (TASK-174) and the fail-fast initialiser (TASK-175) stop a deployment
  with a weak key, an unreachable store or a failed bucket set-up. Deployment-time only, with a
  message naming the setting or the step.
- The object store's SSE key is `AT_REST_ENCRYPTION_KEY`; losing or changing it makes the
  attachments unreadable (SOUP-036 F-4). Key handling is RISK-011's; the missing backup and restore
  procedure for the volume and its key is PRB-057.

CR-004 (2026-10-31), availability effects introduced by its controls:

- Start-up refused on a missing, placeholder or invalid secret, on identical field and SSE keys,
  or on an invalid `TRUSTED_PROXIES` entry (deployment time, message names the setting).
- `db-migrate` must complete before the backend and worker start; a failed migration keeps them
  down (fail closed, like the bucket initialiser).
- A table without grants makes the runtime role's statement fail until the next `db-migrate`
  run; `app.db.roles` re-applies grants after every migration (ADR-0017).
- The fixed `medhub` subnet (TASK-185) could overlap a network Docker allocated for `object-store` and stop the start (PRB-076, resolved in TASK-202 round 2: the subnet is now `10.77.77.0/24`, outside Docker's default pools).
- The frontend now listens on 8080; a proxy still pointing at 80 serves nothing. The smoke test
  checks the page through the proxy.

CR-006 (2026-11-13), availability effects introduced by its controls:

- A DICOM study above 150 MiB stored or 1 GiB decoded, and an attachment above 150 MiB, is refused
  with an RFC 7807 error naming the limit (SR-017 AC 6, SR-013).
- The two-pass download reads each object twice from the store; a large study takes longer to
  start (SR-026 AC 3, measured in the load test).
- Moving the dependencies off the event loop puts every authenticated request on a thread; the
  thread pool and the database and Redis pools are sized together, or requests queue on the pool.
- Migration 0011 blocks writes to the appointment, consent, clinical-entry and attachment tables
  while the indexes build (deployment time, ask first).
- An erasure request fails with a retryable error when its retrieval-code e-mail cannot be queued
  (D-5): the erasure is delayed, not lost (RISK-008).
- A lazy route chunk that fails to load shows an error with a retry instead of the view.

CR-008 (2026-11-25), availability effects introduced by its controls:

- A production image that does not discover the module fails the Docker Build job, so a packaging
  defect stops a deployment instead of shipping without the module.
- `?frame=N` on a study in an unsupported syntax, or on a Deflated object that inflates above 1 GiB, is
  refused with an RFC 7807 400 naming the syntax or the limit; the whole object stays downloadable.
- The module's build backend (hatchling, pinned) is fetched at image build time; an unreachable package
  index fails the build, as it already does for every locked wheel.

## Version history

- 1.2 (2026-10-21) — Approved (self-approved, 2026-10-21).
- 1.3 (2026-10-22) — CR-001 (TASK-157, PRB-002), change analysis §7.4: the control "Object storage
  dependency declared and verified at startup" is realized as "declared as a required runtime
  dependency and verified in CI" (`boto3` in `[project] dependencies`; the instantiation test
  TS-007 TC-007.5; the production-image import check TS-013 TC-013.8). It is not a check at
  application start. Assessed as equivalent for the cause it targets, a missing SDK, because the
  shipped image is built only from the frozen lock (`uv sync --frozen --no-dev`). Table row updated
  with the implementer and the verification evidence. Scores, `acceptability` and the other
  sections unchanged; residual stays 3 × 2, `alarp`, set by the single-host decision (ADR-0010).
  Approval record cleared; the owner's acceptance is the approval of this version.
- 1.4 (2026-10-30) — CR-002 TASK-181, §7.4 change analysis (CR-002 AC-14), by the Software
  Architect role. Content change, so the approval record is cleared and the record returns to
  review.
  - `cause` and Sequence of events: "MinIO failure" becomes "object-store failure"; the checksum
    refusal and the SSE key loss (SOUP-036 F-4) are named as object-store causes.
  - Link `relates_to` SOUP-022 (obsolete) replaced by SOUP-036 (CR-002 AC-12).
  - Control rows added: bucket initialisation ordered and fail-fast (SR-040 AC 4, TASK-175, TS-014
    TC-014.4) and checksum refusal with a clear error (SR-013 AC 5, TASK-173, TS-007).
  - The backup row records that its backup part is not met (PRB-057).
  - Risks introduced by controls: the CR-002 availability effects listed.
  - Not re-scored: severity 3 × probability 2 → `alarp`, set by the single-host decision
    (ADR-0010). Acceptance is the human's, through approval of this version.
- 1.5 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.6 (2026-11-06) — CR-004 TASK-204 (PRB-063), §7.4 change analysis: cause "a stored file name that cannot be represented in an HTTP header makes the attachment undownloadable" added to the sequence of events, and one control row (RFC 6266/5987 file names, one header builder; TS-007 TC-007.9). Residual unchanged (3 × 2, `alarp`); this cause was never part of the scored estimate. Content change, so the approval record is cleared and the record returns to review.
- 1.7 (2026-11-07) — TASK-206 (PRB-069): one control row, bounded attachment names and header (TS-007 TC-007.11). Residual unchanged.
- 1.8 (2026-11-07) — TASK-207 (TASK-206 QA finding 1): one control row, dispatch does not wait on a result store (TS-003 TC-003.7). Residual unchanged.
- 1.9 (2026-11-08) — CR-004 Checkpoint F (TASK-202): planned verification replaced by the tests that ran and the started-stack repetition; the retrieval-limit row names TASK-185; PRB-072 and PRB-075 recorded; residual proposed from the evidence, 3 × 2 → alarp, unchanged. Content change; `in_review`.
- 1.10 (2026-11-08) — TASK-202 round 2: PRB-076 (the fixed `medhub` subnet could overlap the `object-store` network and stop the start) found in QA and fixed by moving the subnet outside Docker's default pools; recorded in the CR-004 availability effects below. Scores unchanged. `in_review`.
- 1.11 (2026-11-13) — CR-006 Risk stage, §7.4 change analysis (Software Architect role). Five control rows added (no blocking IO with pool sizing, SR-026 AC 5; bounded attachment IO, SR-013 AC 6; DICOM bounds, SR-017 AC 6; data-access cost, SR-026 AC 6; retention sweep session release and retries, SR-024 AC 5), each with its planned verification and its TASK left to the Plan stage; the budget and worker-retry rows annotated; expected residual stated; "Risks introduced by controls" extended for CR-006. Scores unchanged (3 × 2 → alarp). Content change, so the approval record (approved 2026-11-10 in chat) is cleared and the record returns to review.
- 1.12 (2026-11-13) — CR-006 Plan gate (D-22, D-23): the CR-006 rows name their tasks (TASK-135 and TASK-217 bounded attachment IO; TASK-218 DICOM bounds; TASK-219 and TASK-220 data-access cost; TASK-136 and TASK-141 unchanged, "at Plan stage" removed); one control row added for a failed lazy route chunk (cause 11; SR-027 AC 3, SR-026 AC 7; TASK-145). Scores unchanged. Content change, so the approval record is cleared and the record returns to review.
- 1.13 (2026-11-13) — TASK-136 round 2: the TASK-136 control row names PRB-072 and TS-018 (TC-018.1 to TC-018.4) and the residual limit (PRB-081). Scores unchanged. Content change, so the approval record is cleared and the record returns to review.
- 1.14 (2026-11-13) — CR-006 D-27 (PRB-080), §7.4 change analysis (Software Architect role): control row added for the request commit before the response (SR-012 AC 5, TASK-227). PRB-081 stays out of scope (D-27); TASK-227 removes only its streaming contribution. Scores unchanged (3 × 2 → alarp; the residual is set by ADR-0010 and PRB-057). Content change, so the approval record is cleared and the record returns to review.
- 1.15 (2026-11-13) — CR-006 D-29 (Software Architect role): the data-access-cost row names migration 0012 (TASK-220) for the two lookups the code issues that 0011 did not index (TASK-219 QA finding 1). Scores unchanged. Content change; the record stays in review (no approval record to clear).
- 1.16 (2026-11-14) — TASK-145: the failed-route-chunk control row cites its verification (TS-012 TC-012.6, TS-018 TC-018.10). Scores unchanged. Content change, so the approval record is cleared and the record returns to review.
- 1.17 (2026-11-14) — TASK-225 (Document Writer): the Verify column of the DICOM-bounds row names TS-019 TC-019.1 to TC-019.4 (TASK-218) instead of "none yet (planned: TS-010 or a new TS)"; the decode is stubbed (PRB-048). Scores unchanged. Stays `in_review`.
- 1.18 (2026-11-15) — TASK-226 (CR-006 verification): every remaining "none yet" row of the CR-006 controls replaced by the executed tests, the load-test result and the migration timings, all dated 2026-11-15; re-scored from that evidence, 3 × 2 → alarp, unchanged. Content change, so the record stays `in_review` for the owner's acceptance.
- 1.19 (2026-11-15) — TASK-226 round 2 (QA M-2, L-1): the stack 502 named as the first-pass checksum path; AC 7 evidence is the production image build, 160.44 kB. Scores unchanged (3 × 2 → alarp). Stays `in_review`.
- 1.20 (2026-11-16) — CR-007 TASK-231 (PRB-092): upload scratch space added as a cause, with a protective control row (TASK-232: logged 503, nothing stored) and an information row (`infra/DEPLOY.md`: both directories, about 300 MiB per concurrent maximum-size upload, monitor free space), and a residual paragraph; no capacity control (D-1). Round 2 restates the failure behaviour (round 1 wrongly said "a loud 5xx"; it was an unlogged 400 before TASK-232). Scores unchanged (3 × 2 → alarp). Content change, so the approval record is cleared and the record returns to review.
  Same version, after the Plan gate (D-B): the upload-path cause is PRB-094 and is controlled by TASK-240 (row added, SR-013 AC 6, TC-007.18 planned); residual unchanged (3 × 2 → alarp), accepted in chat, recorded; stays `in_review` for the MedTrace approval.
- 1.21 (2026-11-25) — CR-008 Risk stage, §7.4 change analysis (Software Architect role). `cause` and Sequence of events: the module absent from an environment (PRB-048) and pydicom's unbounded inflation of Deflated objects (frame path and upload validation). Two control rows added (module installed and its discovery checked in CI and the image, SR-017 AC 7, TASK-233 and TASK-236; bounded inflation on the frame path, SR-017 AC 6, TASK-234), each with planned verification. PRB-075 assessed: still unreachable with one module. Upload-validation inflation recorded as a known uncontrolled cause outside CR-008. Links `relates_to` SOUP-015 and SOUP-037. Expected residual stated; "Risks introduced by controls" extended. Scores unchanged (3 × 2 → alarp). Content change, so the approval record is cleared and the record returns to review.
- 1.22 (2026-11-26) — TASK-239 (CR-008 verification, Software Architect role): the "planned" verification of the three CR-008 rows replaced by the executed tests, negative controls and started-stack results of 2026-11-26; hosted CI recorded as pending; re-scored from the evidence, 3 × 2 → alarp, unchanged. Content change, so the record stays `in_review` for the owner's acceptance.
