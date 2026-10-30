---
id: CR-002
type: change-request
title: Secure or replace the MinIO object store
status: in_progress
version: "1.7"
author: Carlos Santiago Liceras
created: "2026-10-30"
updated: "2026-10-30"
branch: bug/minio-object-store
risk_impact: affects_controls
links:
  - target: PRB-043
    relation: resolves
  - target: PRB-042
    relation: resolves
  - target: PRB-036
    relation: resolves
  - target: PRB-039
    relation: resolves
  - target: PRB-052
    relation: resolves
  - target: PRB-055
    relation: resolves
  - target: PRB-007
    relation: relates_to
  - target: RISK-012
    relation: relates_to
  - target: RISK-010
    relation: relates_to
  - target: RISK-002
    relation: relates_to
  - target: RISK-003
    relation: relates_to
  - target: RISK-001
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: RISK-011
    relation: relates_to
  - target: SOUP-022
    relation: relates_to
  - target: SOUP-023
    relation: relates_to
  - target: SR-013
    relation: relates_to
  - target: SR-022
    relation: relates_to
  - target: SR-028
    relation: relates_to
  - target: SR-040
    relation: relates_to
  - target: CR-001
    relation: relates_to
  - target: CR-003
    relation: relates_to
  - target: PLAN-001
    relation: relates_to
  - target: PLAN-002
    relation: relates_to
  - target: TASK-172
    relation: relates_to
  - target: TASK-173
    relation: relates_to
  - target: TASK-174
    relation: relates_to
  - target: TASK-175
    relation: relates_to
  - target: TASK-176
    relation: relates_to
  - target: TASK-177
    relation: relates_to
  - target: TASK-178
    relation: relates_to
  - target: TASK-179
    relation: relates_to
  - target: TASK-180
    relation: relates_to
  - target: TASK-181
    relation: relates_to
  - target: TASK-182
    relation: relates_to
  - target: TASK-183
    relation: relates_to
  - target: RISK-006
    relation: relates_to
  - target: SR-023
    relation: relates_to
  - target: ADD-025
    relation: relates_to
tags:
  - soup
  - security
  - object-store
  - configuration-management
  - class:B
  - release-blocker
  - issue:sancharly/medhub#33
---

# CR-002 — Secure or replace the MinIO object store

## Reason

The first SOUP anomaly-list review (CR-001, TASK-154, 2026-10-22) found that the MinIO server and
client (SOUP-022, SOUP-023) are no longer distributed or maintained, and that four published
vulnerabilities with no community fix are exposed by MedHub's own object-store configuration.
The human decided on 2026-10-22 to handle the controls in this CR and to make no release before it
(CR-001 D-4; [RISK-012](../risks/RISK-012-object-store-compromised-or-unpatchable.md)). RISK-012
is 4 × 2 → alarp and is "not justified for a release". PRB-043 is `critical` and blocks the
PLAN-001 release gate.

- **PRB-043** (critical): CVE-2026-41145, CVE-2026-40344, CVE-2026-113466 and CVE-2026-34204 let an
  actor with a foothold on the `medhub` network write, take over, or break the store. The
  configuration gives them their full reach: an enabled console on `:9001`, both ports exposed to
  every container, the example access key `minioadmin`, no default bucket encryption, and a stored
  SHA-256 checksum that no download checks, so a substituted object is served as the original.
- **PRB-042** (major): the pinned images cannot be pulled from any registry, so a fresh or amd64
  host cannot build or start the stack (§5.8.5, CR-001 AC-5), and the component will never receive
  a security fix (§6.1 f).
- **PRB-036** (minor): attachment encryption (SR-022, RISK-001) is verified only against a mocked
  `put_object`; no test writes to a real store.
- **PRB-039** (minor): `createbuckets` starts before the store accepts connections, fails silently
  and still exits 0, so a fresh volume gets no bucket.
- **PRB-052** (major, added by D-7): audit events that record a failure are rolled back with the
  error response (`get_db` rolls back on any exception), so denials, failed logins, failed
  activations and refused DICOM reads leave no audit row (SR-023, RISK-006). TASK-173 worked around
  it for one event with a `durable` flag that commits the whole request session.

One CR bundles them, as CR-001 and CR-003 did: they come from the same review, share RISK-012 and
the SOUP-022/023 records, and share one verification run (a fresh-host stack start, the pin check,
the smoke test, both suites and `traceability-check`).

Source: GitHub issue sancharly/medhub#33.

## Scope

### In scope

1. **Configuration hardening (PRB-043).**
   - Remove the MinIO console: drop `--console-address ":9001"` and the `9001` `expose`.
   - Refuse to start with a missing, empty or default object-store access key or secret key
     (`minioadmin`, `changeme`). Remove the default values from `infra/.env.example` and document
     how to generate the keys in `infra/DEPLOY.md`. Only the object-store credentials are in scope
     here. The other insecure defaults of the Compose file stay with PRB-007 (GitHub #27).
   - Set default bucket encryption (SSE-S3) at bucket initialisation, so that any write is
     encrypted at rest whichever path made it.
   - Put the object store on a network that only `backend` and the bucket initialiser join.
2. **Checksum on download (PRB-043; new control for RISK-002 and RISK-003).** Verify the stored
   SHA-256 checksum on every attachment and DICOM download. On a mismatch: serve nothing, return
   an error and record an audit event.
3. **Component decision (PRB-042).** An ADR decides how the unmaintained component is dealt with
   and the decision is implemented. The architect decides (Q-1). The options are:
   - **Replace** it with a maintained S3-compatible server (for example the AIStor Free licence,
     or another one), including the migration of existing objects and key material (RISK-011); or
   - **Interim:** build the server and client images from the archived release binaries after
     verifying their published SHA-256 checksums and signatures, and pin the result; or
   - a combination of both (interim now, replacement later), if the ADR gives the reason.
   Whatever the choice, a fresh or amd64 host can build and start the stack (CR-001 AC-5 holds).
4. **Bucket initialisation (PRB-039).** Give the object store a healthcheck, make the bucket
   initialiser wait for `service_healthy`, and make the initialiser fail (non-zero exit) when a
   command fails. The initialiser must set no `exit 0` over a failure.
5. **End-to-end encryption verification (PRB-036).** An automated check writes an object through
   `ObjectStorageClient` to a real object store and asserts that the stored object reports
   `ServerSideEncryption: AES256`. It is recorded against SR-022.
6. **SOUP (§8.1.2, §7.1.2).** Update SOUP-022 and SOUP-023, or set them `obsolete` when the
   component is replaced. A replacement gets its own `soup` record with an exact version and a
   dated, sourced anomaly-list review. Update PLAN-002 monitoring if the replacement changes it.
7. **Risk (§7.4).** Run the change analysis. Complete RISK-012's control table with the implementing
   tasks (each `mitigates` RISK-012) and the verification, and re-score the residual risk from the
   evidence. Re-evaluate the MinIO path (path 2) of RISK-010. Consider RISK-001, RISK-002,
   RISK-003, RISK-007 and RISK-011 (including the risks the controls introduce, listed in
   RISK-012).
8. **Records and documents.** Requirements as in "Requirements decision". Tasks, test
   specifications and a test report entry for each AC. `infra/DEPLOY.md` (bucket administration
   through the initialiser and scripted S3 calls only, key generation, no console) and the ADD and arc42 sections that describe the
   object store and the deployment topology are updated to the new state.
9. **Audit persistence (PRB-052, added by D-7).** `AuditService` commits every audit event that
   records a failure or a refusal on its own short-lived transaction, so it persists whatever the
   request's outcome ([ADR-0016](../design/adr/0016-failure-audit-events-on-own-transaction.md)).
   TASK-173's `durable` flag is removed. Real-database tests cover each affected path. The two
   other LOW findings of TASK-173's QA review are fixed with it: the 502 responses declare their
   problem body, and the integrity message no longer reloads the attachment.

### Requirements decision

The Specify stage decided which requirement records change. All stay `in_review`; the human
approves them.

- **SR-013 (attachments), revised to 1.3:** new AC 5 states the checksum check on download. It also
  gains `mitigates` links to RISK-003 and RISK-012. SR-013 already realizes UN-008 and mitigates
  RISK-002, and the check is a behavior of the attachment download, so no new SR is needed.
- **SR-022 (encryption at rest), revised to 1.4:** new AC 4 (default bucket encryption, whichever
  path wrote the object) and AC 5 (encryption verified against a real object store, PRB-036). It
  gains a `mitigates` link to RISK-012. The AC 2 obligation was already there, but nothing required
  the store itself to enforce it.
- **SR-028 (traceable development records, §5.8.5), revised to 1.6:** new AC-7 requires that every
  pinned image can be obtained on a host with no cached images. AC-5 and AC-6 require pinning and a
  reviewed version, but not that the pinned reference can be fetched, which is the gap PRB-042
  exposes.
- **SR-040 (object store deployment hardening and initialisation), new:** console absent,
  non-default credentials enforced at start-up, network reach limited to the backend and the bucket
  initialiser, and reliable bucket initialisation. No existing SR covers the deployment topology of
  the object store. It satisfies RR-003 and derives from NFR-007 and UN-008, and mitigates RISK-012,
  RISK-001 and RISK-007.
- **SR-023 (audit logging), unchanged (D-7):** AC 1 already requires failed authentication
  attempts to be recorded, and AC 2 requires access to clinical data to be recorded. A row that is
  rolled back is not recorded, so PRB-052 is a failure to meet SR-023, not a gap in it. TS-009
  gains the real-database test cases (TASK-183).
- **No UN, NFR or RR is created or amended.** RR-003, RR-008, RR-010 and NFR-007 already state the
  obligations.
- **§5.2.2 checklist:** e (security), h (installation), j (IT-network) are covered by SR-040;
  b/g (data integrity of stored objects) by SR-013 AC 5; a, c, d, f, i, k, l: not applicable or
  unchanged. The checksum failure shows the user an error rather than a new alarm (d).

### Out of scope

- The other insecure Compose defaults and the root-user container (PRB-007, GitHub #27). The
  object-store credentials are the only part of PRB-007 resolved here; PRB-007 stays open and
  gets a note.
- Pinning GitHub Actions by SHA and other CI tooling (PRB-034).
- DICOM viewer deployment (PRB-048) and DICOM decompression limits (PRB-006). The checksum check
  covers the core download that the viewer will use.
- Per-user or per-attachment encryption keys, or client-side encryption of attachments. Server-side
  encryption stays the at-rest control (SR-022).
- Changing the database, the Redis service or any other SOUP item.
- Re-scoring RISK-002 or RISK-003. The new control is recorded in RISK-012 (human decision,
  2026-10-22).
- Changing a PRB to `closed`, or an SR to `approved`. Only the human approves.

### Boundaries

- **Ask first:** accepting the licence terms of a proprietary replacement (AIStor Free or another);
  any change that makes existing stored objects unreadable; any change to `AT_REST_ENCRYPTION_KEY`
  handling beyond MinIO's own credentials (Q-3).
- **Never:** store the access key or the secret key in the repository; leave an object-store
  default credential in any file; set a record `approved`; edit an `approved` record without
  bumping its version and clearing its approval record.

### Risk impact (§7.4)

Preliminary classification: **`affects_controls`**. The change adds and strengthens controls of
RISK-012 and replaces or rebuilds the SOUP that the at-rest control (SR-022, RISK-011) runs on.
It adds one effect that needs a rehearsed fail-safe: an attachment whose stored object fails the
checksum is refused (RISK-007, listed in RISK-012). The software safety class does not change. The
Risk stage confirms or revises this. The items to analyse:

| Change | Items touched | Records that consider them |
|---|---|---|
| Console, credentials, network, default encryption, initialisation | Deployment topology (`infra/docker-compose.yml` `minio`, `createbuckets`, `.env.example`, `DEPLOY.md`) | RISK-012, RISK-001, RISK-011, RISK-007 |
| Checksum on download | SI-ATTACH (`backend/app/attachments/service.py`, `backend/app/core/object_storage.py`), audit log | RISK-012, RISK-002, RISK-003, RISK-007, RISK-006 |
| Component replaced or rebuilt | SOUP-022, SOUP-023 (or successors), image build, SSE key material and stored objects | RISK-012, RISK-010, RISK-011, RISK-007 |

#### Change analysis (Risk stage, 2026-10-30)

The Software Architect role ran this analysis. The scales and matrix are `docs/medtrace.yml`
(5 × 5 `risk_matrix`) and PLAN-005. It follows ADR-0015's recommended option (b), replacement by
SeaweedFS. Where option (a) or (c) changes a result, the table says so.

- **Records consulted:** RISK-001, 002, 003, 006, 007, 010, 011, 012; SR-013, 022, 028, 040;
  ADD-012, ADD-024; SOUP-019, 022, 023; TS-007, TS-008, TS-013; PRB-036, 039, 042, 043, 007;
  ADR-0009, ADR-0010.
- **Code read:** `backend/app/core/object_storage.py`, `backend/app/attachments/service.py`,
  the two callers of `AttachmentService.open` (the attachments router and the DICOM viewer
  router), `infra/docker-compose.yml`, `infra/.env.example`, `infra/smoke-test.sh` and
  `.github/workflows/ci.yml`.
- **Upstream sources:** listed in ADR-0015, all checked on 2026-10-30.

**Conclusion.** The classification `affects_controls` is confirmed.

- **No new hazard. Class B is unchanged.** Every harm any change can reach is already in RISK-012,
  RISK-007 or RISK-011, at severity 4 at most. Class B covers severity 4 (`medtrace.yml`
  classification rationale).
- **The controls strengthened are RISK-012's** (all rows), plus the SR-022 at-rest control of
  RISK-011 and RISK-001's access reach.
- **One new effect is introduced:** the checksum refusal, an availability effect under RISK-007.
  It fails with a clear error and is audited.
- **One new SOUP risk is introduced:** the replacement's larger surface and high advisory rate,
  recorded in RISK-012 1.1. RISK-010 path 1 picks it up once the item is on the list.

| Change (task) | Software items / SOUP | §7.4.1 hazard contribution | §7.4.2 controls affected | §7.4.3 verification |
|---|---|---|---|---|
| Spike and SOUP-036 review (TASK-172) | SOUP-036 (new) | None by itself. Its findings are inputs to this stage ("Escalations") | RISK-010 review control, re-implemented for the new item | SOUP-036 review; TS-013 |
| Checksum on download (TASK-173) | SI-ATTACH `U-ATT-Fetch` (ADD-012); SI-AUDIT | A substituted object is no longer served. That removes RISK-012's integrity path to the harms of RISK-002 and RISK-003. New effect: an object that fails the check is refused (RISK-007, severity 3, already scored). The comparison runs over bytes already in memory, so performance is unchanged (SR-026) | RISK-012 (new protective row). RISK-002 and RISK-003: not re-scored (out of scope, human decision 2026-10-22). RISK-006: a FAILURE event is added, nothing removed | TS-007 TC-007.6..8, with a mutation check |
| Credential preflight; default strings removed (TASK-174) | SI-OBJSTORE `U-OBJ-Preflight` (ADD-025); test fixtures; CI | A weak key stops start-up with a named message. That is an availability effect by design, at deployment time only. No runtime path changes | RISK-012 and RISK-001 (strengthened) | TS-014 TC-014.1..3 |
| Python initialiser with SSE-S3 default; `mc` retired (TASK-175) | `U-OBJ-Init`; SOUP-019 (unchanged version); SOUP-023 → obsolete | A failed initialisation now keeps the backend down instead of failing silently (PRB-039), which removes RISK-007's "no bucket at first use". With bucket default encryption, an object written without an SSE request is still encrypted (RISK-011, RISK-012) | RISK-012, RISK-011 (SSE control now enforced by the store), RISK-007 (strengthened) | TS-014 TC-014.4; TS-008 TC-008.6 |
| Server replaced by SeaweedFS 4.51 (TASK-176) | `U-OBJ-Server`; SOUP-022 → obsolete; SOUP-036 | The four PRB-043 CVEs leave with the MinIO code. Introduced: a different SSE implementation (verified by AC-4 and AC-7 on every PR), a larger surface with internal ports, and rolling releases (RISK-012 1.1, "risks introduced by controls"). No change in severity. **Under (c):** the CVEs stay, and only availability is restored | RISK-012 (design row), RISK-010 path 2 (gains a fix path), RISK-011 (SSE now runs on a new SOUP item), RISK-007 (obtainable on any host) | TS-013 TC-013.10; TS-014 TC-014.5; TS-008 |
| Network isolation (TASK-177) | Deployment topology | Reach is cut from five containers. The backend is unaffected (CR-002 A-2, confirmed by the task). No new hazard | RISK-012 and RISK-001 (strengthened) | TS-014 TC-014.6 |
| Migration rehearsal (TASK-178) | Tooling (`backend/scripts/`), both stores | A migration error can orphan or expose objects (RISK-011, RISK-007). The control is a rehearsal on backups with checksum comparison, and the source is never modified. Q-5: development data only | RISK-011 (new protective row in TASK-181) | Rehearsal record; TS-007 path through the API |
| SSE end-to-end in CI (TASK-179) | `ObjectStorageClient`; SI-DEVINFRA CI | Verification only. It closes PRB-036's gap, and urllib3/botocore changes are now caught end to end | RISK-011, RISK-012 (verification of the SSE control) | TS-008 TC-008.8 |
| Documents (TASK-180) | DEPLOY.md, ADD, arc42 | Information for safety: bucket administration without a console, key generation, migration | RISK-012 (information) | Inspection |

**Re-evaluation of RISK-010 path 2 (AC-14).** At this stage path 2 stays at probability 2, so
RISK-010 is 3 × 2 → `alarp`. No control is in place yet, and RISK-010 is therefore **not edited
now**. The expected outcome, for TASK-181 to confirm with evidence:

- under option (b) or (a), the store is maintained and patchable, so path 2 gets a fix path →
  3 × 1 → acceptable. RISK-010 as a whole is then 3 × 1 if path 1 also holds;
- under option (c), path 2 stays 3 × 2 → `alarp`, and the record must say why.

**Results per record (AC-14):**

- **RISK-012**: revised to 1.1 now (`in_review`). The control table is mapped to SRs, tasks and
  the planned verification. The residual is **not** re-scored: pending verification (TASK-181).
- **RISK-010**: unchanged now. Path 2 is re-evaluated by TASK-181 (above).
- **RISK-001**: affected (its reach shrinks: SR-040 `mitigates` RISK-001). Not re-scored.
  TASK-181 adds the control row with evidence.
- **RISK-002, RISK-003**: affected only through RISK-012's checksum control. Not re-scored and not
  edited (Out of scope; the human decided 2026-10-22).
- **RISK-007**: affected (the initialisation is fixed; the checksum refusal is a new availability
  effect; its body names MinIO and it links SOUP-022). Not re-scored. TASK-181 updates the body,
  the links and the control rows.
- **RISK-011**: affected (SSE control enforced by the store and verified end to end; key material
  migrated; it links SOUP-022). Not re-scored. TASK-181 updates it.

*Re-evaluated by TASK-181 (2026-10-30) from the verification evidence of TASK-172..180:*

- **RISK-012** (1.1, `in_review`): re-scored from 4 × 2 → `alarp` to **4 × 1 → `acceptable`** (row 4, column 1). Every control row names its implementing TASK, its commit and the test case that passed. The interim row was removed under option (b). The 4 × 1 is **conditional on TASK-182**: the hosted `object-store-integration` run and the amd64 fresh-host run must pass, otherwise the score is reopened. It also rests on PLAN-002 1.2 (the monthly check).
- **RISK-010** (1.5, `in_review`): path 2 re-scored from 3 × 2 → `alarp` to **3 × 1 → `acceptable`**. A maintained store is deployed at a pinned digest, and its review found a fix path. The 3 × 1 is **conditional on the approval of PLAN-002 1.2** (the monthly check for items with rolling releases). Without it, path 2 stays 3 × 2 → `alarp`.
- **RISK-001** (1.2, `in_review`): not re-scored (2 × 2 → `acceptable`). Adds the control row "object store reachable only by the backend, no console, non-default credentials" (SR-040; TASK-174, TASK-177; TS-014).
- **RISK-007** (1.4, `in_review`): not re-scored (3 × 2 → `alarp`). "MinIO failure" now reads "object-store failure"; the link is now SOUP-036. Two rows added: the fail-fast bucket initialisation (TS-014 TC-014.4) and the checksum refusal with a clear error (TS-007 TC-007.6..8). The backup part of the backup row is unmet (PRB-057). The ALARP justification is re-evaluated when PRB-057 is resolved, or at the first release.
- **RISK-011** (1.3, `in_review`): not re-scored (3 × 2 → `alarp`). The SSE row gains TASK-175, TASK-179, TS-008 TC-008.6 and TC-008.8. A migration row is added (TASK-178, TS-008 TC-008.7). The link is now SOUP-036. The key reuse is carried over (Q-3, Q-7, PRB-007). The key-loss path (F-4) has no backup (PRB-057). The ALARP justification is re-evaluated when PRB-057 is resolved, or at the first release.
- **RISK-002, RISK-003**: not edited and not re-scored (Out of scope, D-2). Their bodies name no replaced item: a grep finds no MinIO, SOUP-022 or SOUP-023.

**For the human to accept** (risk acceptability is a human decision):

1. RISK-012 1.1 at 4 × 1 → `acceptable`. This replaces the development-only acceptance of 4 × 2 (D-6). It is conditional on TASK-182's hosted CI run and fresh-host run.
2. RISK-010 1.5 at 3 × 1 → `acceptable`, together with the approval of PLAN-002 1.2 and SOUP-036 1.2.
3. RISK-001 1.2, RISK-007 1.4 and RISK-011 1.3: content changes, scores unchanged.
4. **PRB-057 as a release-gate condition.** Before the first release, either PRB-057 is resolved, or it is listed under "Known residual anomalies" in the REL record, with RISK-007 and RISK-011 re-accepted against it.
5. **How the release treats PRB-043.** PRB-043 (`critical`) is `resolved` under AC-19. It still counts as open for the `iec62304-sdlc` release gate and MedTrace E10 until it is `closed`. Decision: it is closed in the release-record (REL) commit, after the release test report (TR) confirms the resolution.

**Escalations.** None at the Risk stage. TASK-172 adds any hazard-relevant finding of the SOUP-036
review here as a RISK, and any MedHub-affecting defect as a PRB. TASK-181 checks that the list is
complete.

*Added by TASK-172 (2026-10-30).* The SOUP-036 review found no hazard-relevant advisory against
4.51, so **no new RISK** was raised. Its configuration findings F-1..F-5 (unauthenticated
filer, master and volume ports in `weed mini`; S3 gRPC port; telemetry default; SSE key loss; admin
listeners) are inputs to RISK-012, to be scored by TASK-181, and to TASK-176 and TASK-177. One
defect candidate, **P-1 (minor)**: the base OS package `fuse` 2.9.9 of the pinned image is in
Alpine v3.24 `community`, whose support ends 2026-11-01 (PLAN-002 end-of-support rule; not
exercised by MedHub; remedy is the reviewed digest change under the PLAN-002 1.2 monthly rule).
The human raised it as [PRB-051](../problem-reports/PRB-051-seaweedfs-image-fuse-from-alpine-community-end-of-support.md)
on 2026-10-30. It stays outside this CR's scope.

*Checked by TASK-181 (2026-10-30).* The list is complete. **No new RISK was raised**: the SOUP-036 review found no hazard-relevant advisory against 4.51, and each configuration finding is either closed by a verified control or recorded in an existing RISK:

- **F-1** (in `weed mini` the filer, master and volume ports answer unauthenticated requests on the network): avoided by design. `weed server` binds master, volume and filer to 127.0.0.1 (TASK-176, TS-014 TC-014.1 and TC-014.5). Only the backend and the initialiser can reach the store (TASK-177, TS-014 TC-014.6). A substituted object is refused on download (TASK-173, TS-007 TC-007.6..8). It is a residual reason in RISK-012.
- **F-2** (the S3 gRPC port 18333 stays on a non-loopback address): limited to the internal `object-store` network (TASK-177, TS-014 TC-014.6; QA probe: it times out from `medhub`). Its IAM-cache RPCs accept only local peers. It is a residual reason in RISK-012 and is watched in the monthly review.
- **F-3** (telemetry on by default): switched off with `-master.telemetry=false`, asserted by TS-014 TC-014.1. The `object-store` network is `internal: true` and has no egress (TASK-177 QA).
- **F-4** (the SSE key is the only key, so losing it loses the data): recorded in RISK-011 1.3 and RISK-007 1.4, and as a risk introduced by the controls in RISK-012. Key separation is tracked on PRB-007. The missing backup and restore of the volume with its key is PRB-057. Verified by TASK-172's run with a different key (`InternalError`, rerun by QA).
- **F-5** (admin listeners and a key file in `weed mini`): no action. Neither occurs under `weed server` (TASK-172; TS-014 TC-014.5 shows no admin listener).

Problem reports raised during CR-002:

- PRB-051 (fuse from Alpine `community`, minor): `open`, outside this CR.
- PRB-052 (FAILURE audit events rolled back, major): in scope by D-7, resolved by TASK-183.
- PRB-053 (raw-SQL guard test, minor): `open`, outside this CR.
- PRB-054 (test-data seeder in the runtime image, minor): `open`, outside this CR.
- PRB-055 (smoke test requires `minio_data`, minor): `resolved` by TASK-179.
- PRB-056 (empty `CORS_ORIGINS` in `.env.example`, minor): `open`, outside this CR.
- PRB-057 (no backup and restore procedure, major): `open`, outside this CR. It is a release-gate condition (see "For the human to accept").

*Added for PRB-052 (D-7, 2026-10-30, Software Architect role).* `risk_impact` stays
`affects_controls`. No new hazard, and class B is unchanged: PRB-052 is a new **cause** of the
existing RISK-006 hazard (severity 2), not a new harm.

| Change (task) | Software items / SOUP | §7.4.1 hazard contribution | §7.4.2 controls affected | §7.4.3 verification |
|---|---|---|---|---|
| Failure audit events on their own transaction; `durable` removed; 502 problem body (TASK-183) | SI-AUDIT `U-AUD-Writer` (ADD-013); SI-ATTACH `U-ATT-Fetch`; DICOM viewer route; SOUP-008 (SQLAlchemy, unchanged version) | Removes the cause "audit row rolled back with the failed request" from RISK-006 for `AUTHZ_DENIED`, `LOGIN_FAILURE`, `ACCOUNT_LOCKOUT` (found at this stage, not in PRB-052), `ACTIVATION_FAILED`, the `DICOM_STUDY_READ` FAILURE and the `ATTACHMENT_ACCESS` FAILURE. Introduced: a second pooled connection per failure event (pool pressure on a login burst, which the lockout bounds; it fails with an error and does not drop the row). A business write can no longer be committed by an audit call (TASK-173 LOW 1) | RISK-006 (new design control row; residual pending verification). RISK-012: its AC-5 audit evidence now has a general mechanism, and its scores are not affected | TS-009 TC-009.4..8 (real DB, mutation check); TS-007 TC-007.6 rerun without `durable` |

- **RISK-006**: revised to 1.2 (`in_review`). New cause and control. Scores unchanged, and the
  residual is pending verification by TASK-183 (until then the failure-evidence path is 2 × 3,
  `alarp`).
- **For the human to accept:** RISK-006 1.2, that is, the new cause, the control plan, and the
  interim 2 × 3 `alarp` for the failure-evidence path, accepted for development only (no release
  exists) until TASK-183 is approved; then 2 × 2 `acceptable` is confirmed from its evidence.

## Acceptance criteria

Configuration hardening (PRB-043, SR-040)

- **AC-1 (console, SR-040 AC 1):** In the deployed object-store service there is no console
  listener, command-line console option or console port. On a started stack, a connection to the
  former console port from the backend container and from the host is refused.
- **AC-2 (credentials, SR-040 AC 2):** `infra/.env.example`, `infra/docker-compose.yml` and
  `infra/DEPLOY.md` contain none of the strings `minioadmin` and `changeme` as an object-store
  credential. With the access key or secret key unset, empty, or set to a known default, the object
  store and its bucket initialiser do not start and the message names the rejected setting. A test
  covers each of the four cases. `infra/DEPLOY.md` documents how to generate the keys.
- **AC-3 (network, SR-040 AC 3):** The object store joins a network that only the backend and the
  bucket initialiser join, and publishes no host port. On a started stack, a connection to the
  object store from the reverse proxy, the frontend, PostgreSQL, Redis and the Celery worker
  containers is refused, and the backend can read and write an attachment.
- **AC-4 (default encryption, SR-022 AC 4):** After the bucket initialiser has run on a fresh
  volume, the bucket's default encryption configuration is SSE-S3, and an object written with a
  plain upload that carries no encryption request is reported as encrypted (`AES256`).
- **AC-5 (checksum on download, SR-013 AC 5):** A test replaces the stored object of an attachment
  and requests the download. The content is not returned, the client gets an error response, and
  the audit log gains an event with outcome FAILURE for that attachment and actor. A second test
  shows that an unmodified attachment downloads with the same bytes, and a third that a DICOM
  attachment is covered too. The tests fail when the check is removed.
- **AC-6 (initialisation, SR-040 AC 4):** The bucket initialiser starts only after the object store
  healthcheck passes. A test or run against an unreachable store or a failing command shows the
  initialiser exiting non-zero. On a fresh volume, `docker compose up -d` creates the bucket
  without manual steps.

Verification of encryption (PRB-036)

- **AC-7 (SSE end to end, SR-022 AC 5):** An automated check writes an object through
  `ObjectStorageClient.put_object` to a real object store and asserts `ServerSideEncryption:
  AES256` on the stored object, and a read through `get_object` returns the original bytes. The
  check runs in CI on every pull request, or, if Q-4 is answered otherwise, as a documented step
  of `infra/smoke-test.sh`. It is listed in a test specification that `verifies` SR-022.

Component decision (PRB-042)

- **AC-8 (ADR):** An ADR in `docs/design/adr/` records the object-store decision. It states the
  options considered, the choice (replace, interim, or both), SSE-S3 support, the licence, image
  availability and digest pinning, the migration of existing objects and key material (for a
  replacement), the consequences for RISK-010 path 2, and PLAN-002 monitoring. Q-1 is answered in
  it.
- **AC-9 (obtainable):** On a host with no cached images (a fresh Docker daemon or builder cache,
  not the reference workstation) and on amd64, `docker compose -f infra/docker-compose.yml build`
  and `docker compose up -d` succeed from registries and version-controlled sources only (SR-028
  AC-7).
- **AC-10 (verified source):** If any image is built from archived or downloaded binaries, the
  build verifies the published SHA-256 checksum and the signature of each binary and fails on a
  mismatch. A negative test with a tampered binary shows the failure. If no image is built this way,
  the AC is met by the ADR stating so.
- **AC-11 (migration):** If the store is replaced, existing objects and key material are migrated
  by a procedure that has been rehearsed against a backup. After it, every attachment downloads
  with a matching checksum (AC-5), and an object written before the change decrypts. If the store
  is not replaced, the ADR says that no migration is needed.

SOUP, risk and requirements records

- **AC-12 (SOUP):** SOUP-022 and SOUP-023 are each either updated or `obsolete`. An updated record
  has `soup_version` equal to the deployed build and a dated review of the anomaly list that cites
  its source. A replacement has a new `soup` record with manufacturer, exact version, relied-on
  requirements and the same review, and is linked from the architecture element that uses it. No
  non-`obsolete` record keeps a `relates_to` link to an `obsolete` SOUP record, other than the
  tasks and records that retire it. `python3 infra/check_image_pins.py` exits 0 (SR-028 AC-5, AC-6).
- **AC-13 (RISK-012):** Every control row of RISK-012's table names an implementing TASK that
  `mitigates` RISK-012 and a verification (a TS or TR). The residual severity and probability are
  re-scored from that evidence, `acceptability` follows the `risk_matrix`, the ALARP section and the
  "risks introduced by controls" section are updated, and the record returns to `in_review`.
- **AC-14 (RISK-010 and the others):** The MinIO path (path 2) of RISK-010 is re-evaluated
  against the outcome: a score of 3 × 1 only if a maintained, patchable object store is deployed
  (otherwise the record states why path 2 stays). The change analysis names RISK-001, RISK-002,
  RISK-003, RISK-007 and RISK-011, with the result for each. No record is re-scored without
  evidence.
- **AC-15 (requirements):** SR-040 exists; SR-013, SR-022 and SR-028 are revised as in "Requirements
  decision"; all four are `in_review` or later and each is `verifies`-linked from a test
  specification whose test cases cover each of its new acceptance criteria.

Verification and release

- **AC-16 (fresh-host run):** On the branch head, on a host with no cached images, the stack
  builds and starts from the registry, `python3 infra/check_image_pins.py` exits 0, and
  `infra/smoke-test.sh` reports every check passing (17/17 today; a check added by this CR counts
  as well). The run is recorded with the host's architecture.
- **AC-17 (suites and CI):** Every job in `.github/workflows/ci.yml` passes on the branch head, and
  the full backend and frontend suites pass locally.
- **AC-18 (traceability):** `traceability-check` over the project reports 0 errors.
- **AC-19 (problem reports):** PRB-043, PRB-042, PRB-036, PRB-039 and PRB-052 are `resolved`, each with a
  completed `## Investigation` and `## Resolution` and an incoming `resolves` link from this CR.
  PRB-043 no longer blocks the PLAN-001 release gate. None is set `closed` (that needs a release).
  PRB-007 stays `open` and gets a note that its object-store credentials are resolved by this CR.
- **AC-20 (documents):** `infra/DEPLOY.md` and the ADD and arc42 sections that describe the object
  store and deployment topology match AC-1 to AC-6: no console, bucket administration through the initialiser and
  scripted S3 calls,
  key generation, the network, and the component chosen by the ADR.

Audit persistence (PRB-052, SR-023; added by D-7)

- **AC-21 (failure events persist, SR-023 AC 1 and AC 2):** For each of `AUTHZ_DENIED` (403),
  `LOGIN_FAILURE` (401; unknown email, locked account, and wrong password), `ACCOUNT_LOCKOUT` (401,
  on the threshold failure), `ACTIVATION_FAILED` (401), the `DICOM_STUDY_READ` FAILURE (403) and
  the `ATTACHMENT_ACCESS` FAILURE (502), a test sends the request through the application with the
  real `get_db` against a real PostgreSQL database, receives the error status, and then finds the
  event's row (action, outcome, and actor or target) in `audit_log` from a separate session. With
  every event written back into the request transaction (the old behaviour), these tests fail.
  The mutation result is recorded.
- **AC-22 (one mechanism, no partial commit):** `AuditService.record` has no `durable` parameter,
  `AuditRepository` has no method that commits the request session, and no file under
  `backend/app` or `backend/modules` contains `durable=`. A real-database test shows that when a
  request adds a business row, records a FAILURE event and then ends in an error, the business row
  is absent and the FAILURE row is present.
- **AC-23 (502 problem body):** In the regenerated `backend/openapi/openapi.json` and
  `frontend/src/api/generated/openapi.ts`, the 502 responses of `GET /attachments/{attachment_id}`
  and the DICOM viewer `GET /studies/{attachment_id}` declare `application/problem+json` with the
  `ProblemDetail` schema, and a contract test asserts it.

## Verification approach

IEC 62304 §8.2.1 (change approval), §8.2.3 (verification of changes) and §7.4.3 (verification of
risk-control measures after a change).

- **Configuration (AC-1, AC-2, AC-3, AC-6):** a test that parses the Compose file and the
  environment template for the console option, ports, networks, credentials and dependency
  condition. Negative start-up tests for the four credential cases. On a started stack, connection
  checks from each container against the object store (the smoke test is extended or a new check
  added; `infra/tests/` is the existing home for infrastructure tests).
- **Encryption (AC-4, AC-7):** a check against the real store, the same store that serves
  AC-5. It reads the bucket's encryption configuration and the stored object's metadata.
- **Checksum (AC-5):** backend unit and integration tests with a substituted object, including the
  audit event and an unmodified control case. Negative tests must fail when the check is removed.
- **Supply (AC-9, AC-10, AC-16):** a build and start on a host or runner with no cached images; for
  a binary-based build, a negative test with a corrupted binary or checksum.
- **Migration (AC-11):** a rehearsal against a backup of a populated volume, with before and after
  checksums.
- **Records (AC-8, AC-12..AC-15, AC-18, AC-19):** `traceability-check`, and human approval of the
  ADR, the SOUP records, RISK-012, RISK-010 and the SRs.
- **Audit persistence (AC-21, AC-22, AC-23):** real-database API tests per path (testcontainers
  PostgreSQL, the real `get_db`), an atomicity test, a mutation run, and a contract test for the
  502 body. All are recorded in TS-009 and TS-007.
- **Regression (AC-17):** the full CI pipeline on the branch head, including the TS-007
  attachment tests.

Results go into the next test report (TR) for the release.

## Assumptions

- **A-1:** No release exists (`docs/releases/` is absent), so no released version in use is
  affected and no notification is needed (§9.3). The human decided on 2026-10-22 that no release
  is made before this CR.
- **A-2:** Only `backend` uses the object store at runtime (`ObjectStorageClient` is used by the
  attachments router, service and `app/api/deps.py`). The Celery worker does not, so the network
  of AC-3 can exclude it. TASK design confirms this.
- **A-3:** All reads of stored objects, DICOM included, go through
  `AttachmentService.open` and `ObjectStorageClient.get_object`. The `checksum` column is
  `NOT NULL`, so every attachment has a checksum to compare.
- **A-4:** The data in `minio_data` is development and test data only. A migration needs a backup
  anyway (RISK-012, "risks introduced by controls"). If a populated volume holds real data, Q-5
  applies.
- **A-5:** Default bucket encryption (SSE-S3) and `MINIO_KMS_SECRET_KEY` keep working together as
  they do now for the backend's own `AES256` writes. A replacement must support SSE-S3 (AC-8).
- **A-6:** This CR's status is `open` at handoff. The change-request status set has no
  `in_review`, so the human's approval of the Specify gate is recorded as a decision in this
  record, as in CR-001 and CR-003.
- **A-7:** The 12-month support horizon of CR-003 applies to a replacement as a selection
  criterion (PLAN-002), but a pinned, obtainable image is the minimum.

## Open questions

Each carries a recommended answer. None is decided here.

- **Q-1 (PRB-042, for the architect and the human):** Replace the component (AIStor Free licence
  or another maintained S3-compatible server), keep MinIO through the interim verified build, or
  do the interim now and the replacement later? *The Product Owner does not decide.* Constraints
  the ADR must weigh: (a) the interim build restores reproducibility but no security fixes, so
  RISK-010 path 2 stays at probability 2 and the expected 3 × 1 is reached only by a maintained
  store; (b) a replacement may carry a proprietary licence the human must accept (Boundaries); (c)
  a self-built image needs a registry MedHub controls, or the build must run on the fresh host;
  (d) SSE-S3 support and migration of objects and key material (AC-11). *Recommended: the
  architect evaluates at least one maintained replacement and the interim, and gives the human the
  comparison. A replacement is the only option that satisfies the intent of PRB-042 (maintenance).*
- **Q-2 (credential policy):** What counts as a rejected key (AC-2)? *Recommended: empty, a known
  default (`minioadmin`, `changeme`), or a secret key shorter than 16 characters. The access key
  must differ from the defaults.* The architect may set the exact rule.
- **Q-3 (`AT_REST_ENCRYPTION_KEY`):** `infra/.env.example` ships `change-me-to-a-random-32-byte-key!`
  and the Compose file passes it as `MINIO_KMS_SECRET_KEY`, the root of the SSE key material.
  Does it belong in this CR or stay with PRB-007? *Recommended: leave it with PRB-007 (GitHub
  #27), unless the ADR's choice makes the object store's key handling part of the replacement.*
- **Q-4 (SSE check, AC-7):** A CI integration job with the object store as a service container, or
  a smoke-test step? *Recommended: CI service container if the chosen image can be pulled in CI
  (it also then proves AC-9 in CI); the smoke step otherwise.* It depends on Q-1.
- **Q-5 (existing data):** Does any `minio_data` volume outside development hold real attachments?
  *Recommended: no (A-4); the human confirms.*

**Added at the Plan stage (2026-10-30), for the human:**

- **Q-6 (AC-20 and scope item 8 wording):** AC-20 asks for "bucket administration with `mc`" in
  `infra/DEPLOY.md`. ADR-0015 D2 retires `mc` (SOUP-023 → `obsolete`): the bucket is administered
  by `object-store-init` and scripted S3 calls from the backend image. *Recommended: reword AC-20
  and scope item 8 to "bucket administration through the initialiser and scripted S3 calls, no
  console". The alternative is to keep `mc` as an operator tool, which would keep an archived,
  unmaintained SOUP item.*
- **Q-7 (key reuse, follow-up to Q-3):** `AT_REST_ENCRYPTION_KEY` feeds both SI-PERSIST field
  encryption and the object store's SSE key, as it did with MinIO. This CR carries that over
  (Q-3). *Recommended: record it on PRB-007 (#27) as a separate key-separation item, rather than
  widen this CR.*

- **Q-8 (PRB-052 notification, §9.3; for the human; added by D-7):** PRB-052's safety evaluation
  leaves open whether users must be notified that failure events were not kept. *Recommended: no
  notification.* No release exists (`docs/releases/` is absent, no git tag; A-1), so no
  installation relies on the audit trail. No patient harm follows (PRB-052, safety evaluation). PRB-052's
  sentence "All released versions with the audit trail are affected" should be corrected at
  resolution to "no released version". Revisit this only if a non-development installation
  exists.

## Decisions

- **D-1 (human, 2026-10-22, from PRB-042, PRB-043 and RISK-012):** the controls are made in this
  CR, separate from CR-001. No release is made before it. PRB-043 is `critical` and blocks the
  PLAN-001 release gate until it is `resolved`.
- **D-2 (human, 2026-10-22):** the hazard is its own record, RISK-012, not a re-score of
  RISK-002 and RISK-003.
- **D-3 (Specify, 2026-10-30):** requirements are revised and added as in "Requirements decision",
  and left `in_review`.
- **D-4 (human, Specify gate, 2026-10-30):** the spec is approved. Q-2..Q-5 are answered with
  the recommendations:
  - Q-2: a key is rejected when it is empty, a known default (`minioadmin`, `changeme` and the
    like), or a secret key shorter than 16 characters;
  - Q-3: `AT_REST_ENCRYPTION_KEY` stays with PRB-007;
  - Q-4: a CI job if the chosen image can be pulled in CI, otherwise a smoke-test step;
  - Q-5: no `minio_data` volume outside development holds real data.

  **Q-1 is open:** the human decides on [ADR-0015](../design/adr/0015-object-store-component-after-minio.md),
  which recommends option (b), SeaweedFS.
- **D-5 (Plan stage, 2026-10-30, Software Architect role; becomes binding with the human's
  approval of the plan):**
  - the architect settled Q-2's exact rule: the known-default set is `minioadmin`, `changeme`,
    `admin`, `password`, `secret` (case-insensitive), applied to both keys, and the 16-character
    minimum applies to the secret key (ADR-0015 D3);
  - Q-4 is realised as the CI job `object-store-integration`, which starts the store with the
    Compose file plus a CI-only override, because a GitHub Actions service container cannot take
    the server's command line (TASK-179).
- **D-6 (human, Plan gate, 2026-10-30):** the plan (TASK-172..182, checkpoints A–C, ADD-025) and
  the RISK-012 1.1 control plan are approved; the residual stays 4 × 2 (`alarp`), accepted for
  development only, until TASK-181 re-scores it. The open questions are answered:
  - Q-1: option (b), replace MinIO with SeaweedFS 4.51. ADR-0015 is Accepted;
  - Q-6: AC-20 and scope item 8 are reworded to "bucket administration through the initialiser
    and scripted S3 calls, no console"; `mc` (SOUP-023) is retired;
  - Q-7: the shared `AT_REST_ENCRYPTION_KEY` is carried over; key separation is tracked on PRB-007
    (#27).

- **D-7 (human, in chat, 2026-10-30):** PRB-052 is added to CR-002's scope ("Add to CR-002").
  The Software Architect role amended the CR: scope item 9, AC-21..AC-23, PRB-052 added to AC-19,
  the change analysis for RISK-006 (RISK-006 1.2 `in_review`), TASK-183, and
  [ADR-0016](../design/adr/0016-failure-audit-events-on-own-transaction.md) (`Proposed`). SR-023
  is unchanged. Q-8 is open. The amendment becomes binding with the human's approval of TASK-183,
  ADR-0016 and RISK-006 1.2.

- **D-8 (human, in chat, 2026-10-30):** the PRB-052 amendment is approved ("Approve amendment"):
  AC-21..AC-23, TASK-183, ADR-0016 (now Accepted) and RISK-006 1.2's control plan, with its
  residual pending verification by TASK-183. Q-8 is answered with the recommendation: no
  notification is needed for PRB-052 (no release exists).

## Implementation plan

The plan is the TASK records below. Under the overlay there is no `docs/plans/<feature>.md`.
It follows ADR-0015's recommended option (b). **Nothing starts until the human has approved the
plan. TASK-173 and TASK-174 can start once the plan is approved. The others wait for the Q-1
answer: TASK-175 needs ADR-0015 D2, which holds under every option but is accepted with the
ADR.**

- All tasks are on `bug/minio-object-store`, with one commit per QA-approved task, carrying its
  records.
- An `approved` record that more than one task changes gets its version bumped and its approval
  record cleared once in this CR, by the first task that changes it. Later tasks keep that
  version and add to its history entry (CR-001, CR-003). Here that applies to ADD-012:
  TASK-175 bumps it, and TASK-176 and TASK-180 add to it.
- New records: ADD-025 (Plan stage), TS-014 (TASK-174), SOUP-036 (TASK-172), TASK-183 (D-7).

| Order | Task | CR-002 AC | SR | Depends on | Size | Docker host / network |
|---|---|---|---|---|---|---|
| 1 | [TASK-172](../design-outputs/tasks/TASK-172-confirm-seaweedfs-meets-object-store-contract.md) Confirm SeaweedFS meets the object-store contract and review its anomaly list | AC-8 (evidence), AC-10, AC-12 (SOUP-036) | SR-022, SR-028 | Q-1 answered (ADR-0015 Accepted). **Gate** for TASK-176..179 | M | Docker host. Network (Docker Hub, GitHub, OSV, NVD) |
| 2 | [TASK-173](../design-outputs/tasks/TASK-173-verify-stored-checksum-on-download.md) Verify the stored checksum on every attachment download | AC-5, AC-15 (SR-013) | SR-013 | none (independent of Q-1) | M | None, apart from the real-database tests |
| 3 | [TASK-174](../design-outputs/tasks/TASK-174-refuse-weak-object-store-credentials.md) Refuse default or weak object-store credentials at start-up | AC-2, AC-15 (SR-040) | SR-040 | none (independent of Q-1) | M | Docker host |
| 4 | [TASK-175](../design-outputs/tasks/TASK-175-initialise-bucket-with-default-encryption.md) Initialise the bucket from the backend image with default encryption, and retire `mc` | AC-4, AC-6, AC-12 (SOUP-023), AC-19 (PRB-039) | SR-040, SR-022 | TASK-174 | M | Reference workstation (cached MinIO image) |
| 4a | [TASK-183](../design-outputs/tasks/TASK-183-commit-failure-audit-events-independently.md) Commit failure audit events independently of the request transaction (added by D-7) | AC-21, AC-22, AC-23, AC-19 (PRB-052) | SR-023 | TASK-173. Independent of TASK-172, TASK-174..179 and of Q-1; start after TASK-174 is committed | M | Docker host (testcontainers) |
| — | **Checkpoint A**, after tasks 2–4a | AC-17 (interim) | — | — | — | Docker host |
| 5 | [TASK-176](../design-outputs/tasks/TASK-176-replace-minio-server-with-seaweedfs.md) Replace the MinIO server with SeaweedFS pinned by tag and digest | AC-1, AC-9 (local), AC-4/AC-6 (re-run), AC-12 (SOUP-022, pins), AC-19 (PRB-042) | SR-028, SR-022, SR-040 | TASK-172, TASK-175 | M | Docker host plus an empty `docker:dind` daemon. Network |
| 6 | [TASK-177](../design-outputs/tasks/TASK-177-restrict-object-store-network.md) Restrict the object store to the backend and the bucket initialiser | AC-3 | SR-040 | TASK-176 | S | Docker host |
| 7 | [TASK-178](../design-outputs/tasks/TASK-178-migrate-objects-to-new-store.md) Migrate existing objects and key material, rehearsed against a backup | AC-11 | SR-022, SR-013 | TASK-176 (TASK-173 for the API check) | M | Reference workstation (cached MinIO image, populated `minio_data`) |
| 8 | [TASK-179](../design-outputs/tasks/TASK-179-check-sse-end-to-end-in-ci.md) Check encryption end to end against the real store in CI | AC-7, AC-4 (CI), AC-9 (CI), AC-15 (SR-022), AC-19 (PRB-036) | SR-022, SR-028 | TASK-175, TASK-177 | S | Network (CI on the branch head). Docker host for the local run |
| — | **Checkpoint B**, after tasks 5–8 | AC-9, AC-16, AC-17 (interim) | — | — | — | Docker host. Network |
| 9 | [TASK-180](../design-outputs/tasks/TASK-180-update-deploy-guide-add-and-arc42.md) Update the deployment guide, the ADD records and arc42 | AC-20 | SR-040, SR-028 | TASK-177, TASK-178, TASK-179 | M (docs only) | none |
| 10 | [TASK-181](../design-outputs/tasks/TASK-181-rescore-object-store-risks-from-evidence.md) Re-score RISK-012 and re-evaluate the related risks from the evidence | AC-13, AC-14, AC-12 (risk links), AC-19 (PRB-043, PRB-007) | SR-040, SR-013, SR-022 | TASK-172..179 | S | none |
| 11 | [TASK-182](../design-outputs/tasks/TASK-182-verify-cr-002-end-to-end.md) Verify CR-002 end to end on a host with no cached images (Checkpoint C) | AC-9, AC-12, AC-15..AC-19 | SR-028, SR-040 | all above | S | Empty Docker daemon, amd64. Network (CI) |

**Parallel work.**

- TASK-183 shares no source file with TASK-174..179 and can run in parallel with them. It edits
  `backend/app/attachments/service.py` after TASK-173 and nothing else in the plan edits that file.
- TASK-172, TASK-173 and TASK-174 share no file and can run in parallel. TASK-173 and TASK-174
  can start before the Q-1 answer.
- TASK-175 and TASK-176 both edit the object-store block of `infra/docker-compose.yml`, so they
  are sequential.
- TASK-177 and TASK-178 can run in parallel after TASK-176. They touch different files, except
  that TASK-178 removes the `minio_data` declaration, so commit TASK-177 first.
- The Document Writer may take the arc42 part of TASK-180.

**Checkpoint A (after TASK-173..175 and TASK-183, still on MinIO, reference workstation).**

- The backend suite passes (coverage ≥ 85 %), the frontend suite passes, and all CI jobs are green.
- `python3 infra/check_image_pins.py` exits 0, and the infrastructure tests pass.
- On a fresh Compose project, the stack starts, the bucket has `AES256` default encryption, a
  weak key stops the preflight, and a substituted attachment is refused.
- `infra/smoke-test.sh` passes (17/17 at least).
- A denied attachment read (403) leaves an `AUTHZ_DENIED` row in `audit_log` (TASK-183).

**Checkpoint B (after TASK-176..179).**

- On an empty daemon (amd64), the stack pulls, builds and starts. Smoke passes N/N, including the
  network checks.
- The `object-store-integration` job and every other CI job are green.
- The migration rehearsal is recorded.

Every runtime change of this CR is then in place. Tasks 9–11 change records only.

**Checkpoint C** is TASK-182.

### Tasks that change under another Q-1 answer

| Answer | TASK-172 | TASK-176 | TASK-178 | Others |
|---|---|---|---|---|
| (a) AIStor Free | AIStor contract spike. The licence is accepted by the human first (Boundaries); SOUP-036 "MinIO AIStor" | AIStor image plus a host-mounted licence file (never in git) and DEPLOY.md licence steps | In-place volume upgrade rehearsal | none |
| (c) Interim | Binary-verification design (minisign key source, pinned base image) | Build from archived binaries with SHA-256 and minisign checks, plus a tampered-binary negative test (AC-10). SOUP-022 updated, not obsolete | Dropped (AC-11 met by ADR-0015) | TASK-181 keeps RISK-010 path 2 at 3 × 2. TASK-180 describes the interim build |
| (d) Interim, then replacement | As (c) | As (c) | As (c) | A follow-up CR repeats (a) or (b) |

TASK-173, 174, 175, 177, 179, 180, 182 and 183 are the same under every answer.

### AC coverage

| AC | Task(s) |
|---|---|
| AC-1 | TASK-176 |
| AC-2 | TASK-174 |
| AC-3 | TASK-177 |
| AC-4 | TASK-175 (MinIO), TASK-176 (re-run), TASK-179 (CI) |
| AC-5 | TASK-173; TASK-178 uses it |
| AC-6 | TASK-175; TASK-176 (re-run) |
| AC-7 | TASK-179 |
| AC-8 | ADR-0015 (Plan stage; Q-1 answered by the human); TASK-172 (evidence) |
| AC-9 | TASK-176 (local), TASK-179 (CI), TASK-182 |
| AC-10 | ADR-0015 states that no image is built from binaries; TASK-172 confirms. Under (c): TASK-176 |
| AC-11 | TASK-178. Under (c): ADR-0015 |
| AC-12 | TASK-172 (SOUP-036), TASK-175 (SOUP-023), TASK-176 (SOUP-022, pin check), TASK-181 (risk links), TASK-182 (check) |
| AC-13 | Risk stage (RISK-012 1.1, control mapping); TASK-181 (re-score) |
| AC-14 | Risk stage (change analysis above); TASK-181 |
| AC-15 | TASK-173 (TS-007), TASK-174..177 (TS-014), TASK-175 and TASK-179 (TS-008), TASK-176 (TS-013); TASK-182 (check) |
| AC-16 | TASK-182 (Checkpoint B in the interim) |
| AC-17 | every task (its suites); Checkpoints A and B; TASK-182 |
| AC-18 | every task (scoped); TASK-182 (project) |
| AC-19 | TASK-175 (PRB-039), TASK-176 (PRB-042), TASK-179 (PRB-036), TASK-181 (PRB-043, PRB-007), TASK-183 (PRB-052), TASK-182 (check) |
| AC-20 | TASK-180 (see Q-6) |
| AC-21 | TASK-183; TASK-182 (suite run) |
| AC-22 | TASK-183 |
| AC-23 | TASK-183; `openapi-lint` CI job (AC-17) |

Every AC-1..AC-23 maps to at least one task.

### Plan risks

| Risk | Impact | Mitigation |
|---|---|---|
| SeaweedFS fails part of the contract: `HeadObject` does not report `AES256`, the bucket encryption API differs, or boto3 default checksums are rejected | Option (b) is not viable | TASK-172 is first and is a gate. On a no-go, report to the human with option (a) or (c); TASK-173 and TASK-174 are unaffected |
| A new SeaweedFS release or advisory lands during the CR (releases every few days) | The pinned digest is behind a fix | TASK-172 re-resolves the version. SOUP-036 records the review date. The PLAN-002 monthly check (TASK-172) catches later ones |
| Internal SeaweedFS ports (master, volume, filer, gRPC) are unauthenticated | Anyone on the store network can bypass S3 auth | Only the backend and the initialiser share the network (TASK-177). TASK-172 binds what it can to loopback and lists the rest. Accepted residual reasoning goes in RISK-012 (TASK-181) |
| The FAILURE audit row is rolled back with the failed request | AC-5 audit evidence is missing | TASK-173 follows the authorization-denied pattern and tests that the row persists. *Realised as PRB-052 (app-wide); fixed by TASK-183 (D-7)* |
| Independent audit rows commit outside test-held transactions (TASK-183) | Real-database tests leak rows into each other; flaky counts | Each persistence test deletes its own `audit_log` rows; DICOM tests run in their own session (TASK-173 QA) |
| The fresh-host check deletes the only copy of the MinIO image | Migration and rollback become impossible | No pruning on the reference workstation; the fresh host is a disposable `docker:dind` or a CI runner (TASK-176, TASK-182) |
| A port cannot be published from an `internal` network | The CI job cannot reach the store | The CI override adds a CI-only network (TASK-177, TASK-179) |
| No Docker daemon on the workstation (seen 2026-10-29) | Started-stack checks cannot run | Use the reference workstation with Docker Desktop running. CI covers AC-7 and the AC-9 CI part |
| PLAN-002 cadence change or licence acceptance (option a) is not approved | TASK-172 or TASK-176 is blocked | Both are named human decisions in this plan |

## Version history

- 1.0 (2026-10-30) — Created at the Specify stage (GitHub issue sancharly/medhub#33).
- 1.1 (2026-10-30) — Risk and Plan stages (Software Architect role).
  - D-4 records the human's Specify-gate approval and the answers to Q-2..Q-5. Q-1 is left to the
    human on ADR-0015 (`Proposed`, recommending option (b), SeaweedFS). D-5 records the architect's
    exact Q-2 rule and the CI form of Q-4.
  - "Change analysis (Risk stage, 2026-10-30)" added: `affects_controls` confirmed, no new hazard,
    class B unchanged. RISK-012 revised to 1.1 (`in_review`) with the control mapping; residual not
    re-scored (pending TASK-181). RISK-010 and the other risks are analysed and left unedited until
    the evidence exists.
  - New Q-6 (AC-20 wording on `mc`) and Q-7 (key reuse, for PRB-007).
  - Implementation plan TASK-172..182 with checkpoints A–C, the alternative-option table, AC
    coverage and plan risks. ADD-025 (SI-OBJSTORE) created `in_review`. `relates_to` links to the
    tasks and ADD-025 added. Status stays `open`.
- 1.2 (2026-10-30) — Plan gate: D-6 records the human's approval of the plan and the answers to
  Q-1 (SeaweedFS, ADR-0015 Accepted), Q-6 (AC-20 and scope item 8 reworded) and Q-7 (key
  separation on PRB-007).
- 1.3 (2026-10-30) — TASK-172 result: SeaweedFS 4.51 confirmed against the object-store contract
  (go). "Escalations" updated: no new RISK, five configuration findings as inputs to RISK-012,
  one PRB candidate (P-1). The deployment command changes from `weed mini` to `weed server`
  (ADR-0015, "Spike result"). SOUP-036 created and PLAN-002 1.2 proposed, both `in_review`.
- 1.4 (2026-10-30) — Status `open → in_progress`: the plan was approved at the Plan gate (D-6)
  and Build started with TASK-172 (approved by QA).
- 1.5 (2026-10-30) — PRB candidate P-1 raised by the human as PRB-051 (minor, outside this CR).
- 1.6 (2026-10-30) — D-7: PRB-052 added to scope (`resolves` link, Reason, scope item 9). New
  AC-21..AC-23, with PRB-052 added to AC-19. "Requirements decision": SR-023 is unchanged. Change
  analysis for PRB-052: RISK-006 1.2 `in_review`, with the residual pending verification. TASK-183
  (order 4a, before Checkpoint A) and ADR-0016 (`Proposed`). New Q-8 (notification). AC coverage,
  Checkpoint A, parallel work and plan risks updated.
- 1.7 (2026-10-30) — D-8: the human approved the PRB-052 amendment (AC-21..23, TASK-183,
  ADR-0016 Accepted, RISK-006 1.2 control plan) and answered Q-8 (no notification). TASK-181
  results added to "Escalations" (F-1..F-5, no new RISK, PRBs raised during CR-002) and
  "Results per record (AC-14)"; "For the human to accept" replaced, including PRB-057 as a
  release-gate condition and PRB-043 closed in the REL commit. Also carries `resolves` → PRB-055
  (committed earlier with TASK-179) and TC-008.8 for the CI SSE row.
