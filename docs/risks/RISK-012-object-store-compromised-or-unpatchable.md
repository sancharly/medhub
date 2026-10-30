---
id: RISK-012
type: risk
title: Object store compromised from the internal network or left unpatchable
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-22"
updated: "2026-10-30"
hazard: Clinical attachments (including DICOM studies) in the object store can be read, replaced, planted or made unreadable without the object store's secret key, or the object store stops receiving security fixes (as first raised in 1.0, for MinIO, which would never receive one).
cause: The object-store component carries a vulnerability with no deployed fix, or the deployment exposes the store beyond its intended clients (as first raised in 1.0, MinIO RELEASE.2025-09-07T16-13-09Z, unmaintained, with CVE-2026-41145, CVE-2026-40344, CVE-2026-113466 and CVE-2026-34204 exposed to every container on the `medhub` network, SOUP-022, PRB-042, PRB-043; replaced by SeaweedFS, SOUP-036, under CR-002) → an actor with a foothold that reaches the store writes to it or takes it over → attachments are disclosed, substituted, stored without encryption or made permanently unreadable, and a substituted object is served unless the stored checksum is checked on download.
harm: Wrong or delayed diagnosis or treatment from a substituted or planted attachment or DICOM study (harms of RISK-002 and RISK-003); privacy harm from disclosure of attachments (RISK-001, RISK-011); delayed care from lost or unreadable attachments (RISK-007).
severity_initial: 4
probability_initial: 2
severity_residual: 4
probability_residual: 1
acceptability: acceptable
links:
  - target: SOUP-036
    relation: relates_to
  - target: PRB-042
    relation: relates_to
  - target: PRB-043
    relation: relates_to
tags:
  - hazard:security
  - hazard:data-integrity
  - hazard:soup
  - class:B
---

# RISK-012 — Object store compromised from the internal network or left unpatchable

Raised by TASK-154 (first SOUP anomaly-list review, CR-001 AC-12) on 2026-10-22. The evidence is
in the "Anomaly list review" sections of [SOUP-022](../soup/SOUP-022-minio.md) and
[SOUP-023](../soup/SOUP-023-minio-client.md). The human decided on 2026-10-22 that this hazard is a
new record rather than a re-score of RISK-002 and RISK-003. The controls are made by a separate
CR-002, and no release happens before it.

## Hazard

Clinical attachments in the object store, DICOM studies included, can be read, replaced, planted
or made unreadable without the object store's secret key. The object store will never receive a
security fix.

## Sequence of events

1. MinIO community edition is source-only since 2025-10-15, unmaintained since 2026-02-12 and
   archived since April 2026. Its fixes ship only in the proprietary AIStor line (PRB-042). The
   pinned `RELEASE.2025-09-07T16-13-09Z` therefore keeps every vulnerability found after it.
2. Four of them are hazard-relevant in MedHub's configuration (PRB-043):
   - CVE-2026-41145 and CVE-2026-40344: an object write with no valid signature, needing only an
     access key. MedHub's example access key is the default `minioadmin`.
   - CVE-2026-113466: takeover of the embedded console, which MedHub enables on `:9001`.
   - CVE-2026-34204: SSE metadata injection that makes an object permanently unreadable.
3. Ports 9000 and 9001 are reachable from every container on the `medhub` network. An actor with a
   foothold there (a compromised container, or the host) can write to the store or take it over.
4. A planted or substituted object carries no SSE request, and the bucket has no default
   encryption. The backend stores a SHA-256 checksum per attachment at upload but does not check
   it on download. MedHub therefore serves the substituted content as the original.

## Hazardous situation

A clinician opens an attachment or DICOM study that is not the one stored for that patient. Or
the attachment is unreadable when needed. Or the attachments have been copied out by an
unauthorized party.

## Harm

- Wrong or delayed diagnosis or treatment based on a substituted or planted attachment or study.
  These are the harms of [RISK-002](RISK-002-clinical-data-misattribution.md) and
  [RISK-003](RISK-003-incorrect-dicom-rendering.md).
- Privacy harm from disclosure of attachments: [RISK-001](RISK-001-unauthorized-clinical-data-disclosure.md)
  and [RISK-011](RISK-011-encryption-key-management-failure.md).
- Delayed care from lost or unreadable attachments: [RISK-007](RISK-007-clinical-information-unavailable.md).

## Software items involved

- SI-ATTACH (`backend/app/attachments/service.py`, `backend/app/core/object_storage.py`): stores,
  serves and downloads every attachment, DICOM studies included.
- The DICOM viewer item would serve the same objects, but it is not deployed today: it is
  installed in no environment
  ([PRB-048](../problem-reports/PRB-048-dicom-viewer-module-not-installed.md)). Substituted DICOM
  studies reach clinicians through the core download and, once PRB-048 is resolved, the viewer.
- Deployment topology: `infra/docker-compose.yml`. The former `minio` and `createbuckets`
  services are SI-OBJSTORE since CR-002
  ([ADD-025](../design-outputs/architecture/ADD-025-object-store-deployment.md)): the
  `object-store-preflight`, `object-store` and `object-store-init` services.
- SOUP: SeaweedFS [SOUP-036](../soup/SOUP-036-seaweedfs.md) (4.51, pinned by digest) since
  TASK-176. The MinIO server [SOUP-022](../soup/SOUP-022-minio.md) and client
  [SOUP-023](../soup/SOUP-023-minio-client.md) are `obsolete` (TASK-176, TASK-175); this record
  links SOUP-036 (TASK-181, CR-002 AC-12).

## Initial risk

**Severity 4.** The worst harm is a wrong diagnosis or treatment from a substituted DICOM study or
attachment, the same severity as RISK-002 and RISK-003. Following the
[PLAN-005](../plans/PLAN-005-risk-management-plan.md) software convention, P1 (the vulnerability
being present and exploitable) is taken as 1. The vulnerabilities are known, public and will
never be fixed in this item.

**Probability 2 (Remote).** This is P2, the probability that the hazardous situation leads to
harm. Every path needs network reach to `minio:9000` or `:9001`. Neither port is published to the
host, and nginx does not proxy them, so an attacker must first compromise a container on the
`medhub` network or the host. A substitution must also be targeted to an object a clinician later
relies on.

Severity 4 × probability 2 → **alarp**, derived from `risk_matrix` in `docs/medtrace.yml`
(row 4, column 2).


## Risk control measures

ADR-0015 option (b) was chosen (CR-002 D-6, 2026-10-30): MinIO is replaced by SeaweedFS 4.51
([SOUP-036](../soup/SOUP-036-seaweedfs.md)). Every row is implemented, and each
implementing TASK is `approved` by QA and links `mitigates` RISK-012. Every row is verified, with
two qualifications: the CI row (end-to-end encryption on every pull request) is verified by QA's
run of the job steps, and its hosted CI run is pending (TASK-182); the monthly-advisory-check row
rests on PLAN-002 1.2, which is `in_review`. "Verified by" names the test
specification and case and the recorded run that passed; the test report entry is written at
release (TR, PLAN-001). The interim row of version 1.1 ("build the image from the archived release
binaries", option (c) or (d) only) was not adopted under option (b) and is removed.

| Measure | Type | Implemented by (SR, TASK) | Verified by (TS/TR) |
|---|---|---|---|
| Replace the unmaintained object store with a maintained S3-compatible component, pinned by tag and digest (option b) | Design | SR-028 AC-7, SR-022; TASK-172 (contract run, SOUP-036 review, commit `68fc68b`), TASK-176 (server swap, commit `9d3b395`) | TS-014 TC-014.1 (no `minio` service or `minio/*` image remains; `object-store` is `chrislusf/seaweedfs:4.51` by digest); TS-013 TC-013.10 (fresh `docker:dind` daemon, empty image store: build and `up` exit 0, TASK-176 AC-9 local and PRB-042 Resolution); `infra/check_image_pins.py` exit 0; TASK-172 contract run 9 PASS / 0 FAIL, rerun by QA. Hosted amd64 run: TASK-182 |
| Disable the console or admin UI and every unused listener; internal ports on loopback | Design | SR-040 AC 1; TASK-176 | TS-014 TC-014.1 and TC-014.5: `netstat` in the store shows only 8333 and 18333 off loopback; from `backend`, 9001, 9000, 9333, 19333, 8080, 18080, 8888, 18888, 7333, 12535, 8181, 9101 and the other probed ports give `ConnectionRefusedError`; from the host nothing is reachable (`docker port` empty). QA rerun, TASK-176 QA review |
| Refuse to start with an unset, empty or default credential, or a secret key shorter than 16 characters | Protective | SR-040 AC 2; TASK-174 (commit `8c46bcc`) | TS-014 TC-014.1..3: unit tests; started stack, each weak case (including a shell override with the defaults) gives preflight exit 1 and the store stays `Created`; good keys exit 0. QA round 2 rerun |
| Set default bucket encryption (SSE-S3) at initialisation, so any write is encrypted at rest; fail closed if it cannot be set | Protective | SR-022 AC 4, SR-040 AC 4; TASK-175 (commit `684ee7b`), re-run on SeaweedFS by TASK-176 | TS-008 TC-008.6 and TS-014 TC-014.4: `get_bucket_encryption` → `AES256`; a plain `put_object` is reported `AES256`; a plaintext marker is not found in `/data`; an unreachable store keeps `backend` `Created`. QA reruns in TASK-175 and TASK-176 |
| Check the stored SHA-256 checksum on every download; refuse (502) and audit a mismatch | Protective | SR-013 AC 5; TASK-173 (commit `0e01b2a`) | TS-007 TC-007.6..8: substituted object refused with 502 and a committed FAILURE audit row (real PostgreSQL); unmodified object served; DICOM route covered. Mutation: comparison removed → 4 tests fail (QA rerun). Also exercised through the API in the TASK-178 rehearsal |
| Restrict the object store to an internal network that only the backend and the initialiser join | Design | SR-040 AC 3; TASK-177 (commit `d4cdba0`) | TS-014 TC-014.6: network `object-store` `internal: true`, members `backend` and `object-store`; from reverse-proxy, frontend, postgres, redis and celery-worker the store name does not resolve and its IP times out on 8333, **18333**, 9333, 8888 and 8080 (QA probe); smoke test 27/27 with positive controls and mutations M1..M3 |
| Verify encryption end to end against the real object store on every pull request (PRB-036) | Protective | SR-022 AC 5; TASK-179 (commit `aa2fd61`) | TS-008 TC-008.8, CI job `object-store-integration`: job steps run unchanged by QA, 4 passed; the no-default-bucket test fails when `ServerSideEncryption` is removed. Hosted-runner run pending (TASK-182) |
| Migrate existing objects and key material by a procedure rehearsed against a backup | Protective | SR-022, SR-013 AC 5; TASK-178 (commit `db0b480`) | TS-008 TC-008.7: unit tests with mutations; rehearsal on restored copies: 3 copied, 3 of 3 API downloads match their checksum, 0 plaintext-marker hits, source volume tree hash identical, legacy MinIO only on a read-only copy (QA round 2) |
| Monthly advisory check of the store, with a fix adopted by a reviewed digest change by the next check | Protective | SR-028 AC-6; TASK-172 (commit `68fc68b`; SOUP-036 review, PLAN-002 1.2 "Items with rolling releases") | SOUP-036 anomaly review 2026-10-30 (GitHub advisories, NVD, OSV Go module, `stdlib`, Alpine packages), spot-checked by QA; TS-013 TC-013.9. PLAN-002 1.2 is `in_review` |
| Information for safety: bucket administration without a console, key generation, migration, network | Information | SR-040, SR-028; TASK-180 (commit `d2b557a`) | Inspection: TASK-180 QA review round 2 (`infra/DEPLOY.md`, ADD-012, ADD-024, ADD-025, arc42 07) |

## Residual risk

**Severity 4** (unchanged: the controls reduce probability, not severity; the worst harm is still a
wrong diagnosis or treatment from a substituted study) × **probability 1 (Improbable)** →
**acceptable**, derived from `risk_matrix` in `docs/medtrace.yml` (row 4, column 1). Re-scored on
2026-10-30 by TASK-181 from the evidence in the table, not from the 1.1 estimate.

Why probability 1, path by path of the 1.1 sequence of events:

1. **Unfixable component defects (step 1–2).** The four MinIO CVEs of PRB-043 leave with the MinIO
   code: no `minio` service or image remains (TC-014.1), and SOUP-022 and SOUP-023 are `obsolete`.
   The replacement is maintained: its 2026-10-30 review found no advisory affecting 4.51 (newest
   affected range ≤ 4.45), the repository is active, and fixes ship in the latest release.
2. **Reach (step 3).** The store is reachable only by the backend and the initialiser (TC-014.6),
   which hold the store credentials and the database credentials anyway. The internal SeaweedFS
   ports (master, volume, filer) are bound to loopback (TC-014.5), which closes the
   unauthenticated-filer bypass of SOUP-036 F-1. The S3 gRPC port 18333 cannot be bound to
   loopback, but it is reachable only from the `object-store` network (TASK-177 QA probe: it
   times out from `medhub`), and its IAM-cache RPCs accept only local peers (SOUP-036 F-2). No
   port is published to the host. An attacker now needs a foothold in the backend, the
   initialiser or the host, and from there already holds every key: that compromise is not a
   weakness of the object store.
3. **No console and no default credentials.** No console or admin listener exists (TC-014.5). A
   default, empty or short key stops the deployment before the store starts (TC-014.2). A wrong
   secret key gets 403 (TASK-172 contract item 7).
4. **Unencrypted writes and substitution (step 4).** Default bucket encryption means any write is
   encrypted at rest, whatever path made it (TC-008.6, TC-008.8). A substituted or planted object
   is refused with a 502 and audited, never served (TC-007.6..8). Substitution that is not detected
   would require changing the attachment's checksum in PostgreSQL as well, which is outside the
   store's reach.
5. **Unreadable objects.** CVE-2026-34204 leaves with MinIO. The remaining unreadability cause is
   loss or change of the SSE key (SOUP-036 F-4), which this record hands to RISK-011 and RISK-007
   (below).

The residual rests on these conditions, which the human's acceptance must include:

- **SeaweedFS advisory rate and monitoring.** 25 advisories in 2026, 9 critical; fixes ship only in
  the latest release. Probability 1 holds while the store is checked **monthly** and a fix for a
  hazard-relevant advisory is adopted by the next check (SOUP-036 "Monitoring", next check due
  2026-11-30). That rule is PLAN-002 1.2, still `in_review`. Between two checks a new advisory can
  stay deployed for up to two months; during that window the reach limits above still apply,
  which is why the probability stays at 1. `docs/medtrace.yml` (365 days) does not enforce the
  monthly cadence: it is a process rule.
- **Evidence still pending at release.** The hosted CI run of TC-008.8 and the fresh amd64 run
  (AC-9, AC-16) are TASK-182's. They confirm reproducibility and the CI gate; the encryption
  control itself is already verified on started stacks (TC-008.6, TASK-176 AC-4). If either fails,
  this re-score is reopened.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Not needed: the residual 4 × 1 is `acceptable` under `risk_matrix`. The ALARP state of 1.0 and 1.1
(accepted for development only, 2026-10-22 and D-6) ends when the human approves this version.

## Risks introduced by controls

- **Checksum refusal (TASK-173) → RISK-007.** An attachment whose stored bytes do not match its
  checksum is refused with a 502 problem response, never served partly. This is an availability
  effect: the clinician gets a clear error instead of wrong content. It is audited with a committed
  FAILURE event (TC-007.6). RISK-007 1.4 records it as a control row.
- **Fail-fast start-up (TASK-174, TASK-175) → RISK-007.** A weak key, an unreachable store or a
  failed bucket initialisation keeps the backend down with a message naming the setting or the
  step. Deployment-time availability effect by design.
- **SSE key handling (SOUP-036 F-4) → RISK-011, RISK-007.** The store derives its only key from
  `AT_REST_ENCRYPTION_KEY`; a different key on the same volume makes every object unreadable
  (`InternalError`, TASK-172, rerun by QA). Losing or changing the key loses the attachments. The
  key is shared with field encryption, carried over from MinIO (CR-002 Q-3, Q-7; key separation
  tracked on PRB-007). No backup and restore procedure covers the volume together with the key
  ([PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md), major, open, outside
  CR-002).
- **Rolling releases and a high advisory rate → RISK-010.** SeaweedFS has no maintained release
  line; staying patchable needs digest updates at the PLAN-002 1.2 monthly cadence. RISK-010 1.5
  re-evaluates its paths with this item.
- **18333 stays on a non-loopback address.** Reachable only from the internal `object-store`
  network, and its RPCs accept only local peers (SOUP-036 F-2). No exploit test was run; the
  monthly review watches this service class (GHSA-5fx4-c9qp-36jc, ≤ 4.45).
- **Base OS package from an ending repository.** `fuse` 2.9.9 comes from Alpine v3.24
  `community`, support ending 2026-11-01; MedHub does not exercise it
  ([PRB-051](../problem-reports/PRB-051-seaweedfs-image-fuse-from-alpine-community-end-of-support.md),
  minor, open). Remedy: the reviewed digest change of the monthly rule.
- **Failure audit commit (TASK-173, TASK-183).** The `ATTACHMENT_ACCESS` FAILURE row of a refused
  download is committed by `AuditService` on its own short-lived transaction (ADR-0016, TASK-183),
  which replaced TASK-173's `durable=True` session commit; no business write is committed with it.
  Verified by TS-007 TC-007.6 and TS-009 TC-009.4..8. It does not change this record's scores; the
  pool cause it introduces is in RISK-006.
- **Migration (TASK-178).** A migration error could orphan or expose objects (RISK-011). Controlled
  by the rehearsal on backups with checksum comparison before and after each write; the source is
  never modified. CR-002 Q-5: only development data existed.
- **Upstream integrity issue #8908** (`CopyObject` / multipart finalise returning different bytes,
  open, reported against 4.18). MedHub uses single `PutObject` only, and the download checksum
  would refuse such an object. Watched in the monthly review.
- **No console.** Bucket administration is the initialiser and scripted S3 calls, documented in
  `infra/DEPLOY.md` (TASK-180).

## Version history

- 1.0 (2026-10-22): created by TASK-154 (CR-001); approved 2026-10-23 (self-approved).
- 1.1 (2026-10-30): CR-002 Risk stage (Software Architect role). Content change, so the approval
  record is cleared and the record returns to review.
  - The control table maps each measure to its SR (SR-040, SR-013 AC 5, SR-022 AC 4 and AC 5,
    SR-028 AC-7), its planned task (TASK-172..179) and its planned verification (TS-007, TS-008,
    TS-013, new TS-014).
  - Two rows added: end-to-end SSE verification (PRB-036) and the rehearsed migration.
  - The interim row is marked as applying only under ADR-0015 option (c) or (d).
  - The residual is not re-scored. It stays 4 × 2 → `alarp`, pending verification (TASK-181).
  - Risks introduced by controls: the preflight, the replacement's attack surface and advisory
    rate, and the carried-over key reuse added.
  - Acceptance is the human's, through approval of this version.
  - **Extended by TASK-181 (2026-10-30, Software Architect role), §7.3 and §7.4.3, from the
    verification evidence of TASK-172..180 (all QA-approved):**
    - every control row names its implementing TASK and commit and the TS/TC and recorded run
      that passed; the interim row is removed (option (b) chosen, D-6); rows added for the monthly
      advisory check (TASK-172, PLAN-002 1.2) and for information for safety (TASK-180);
    - `probability_residual` re-scored 2 → 1; severity stays 4; `acceptability` `acceptable`
      (`risk_matrix` row 4, column 1). The reasons per path and the conditions (PLAN-002 1.2
      monthly check, TASK-182 hosted and fresh-host runs) are in "Residual risk";
    - ALARP justification replaced by a statement that none is needed;
    - risks introduced by controls rewritten from the evidence (checksum 502 → RISK-007, SSE key
      loss F-4 → RISK-011 and PRB-057, advisory rate → RISK-010, 18333, PRB-051, durable audit
      commit → TASK-183, upstream #8908);
    - `relates_to` SOUP-022 and SOUP-023 (obsolete) replaced by SOUP-036 (CR-002 AC-12);
    - status stays `in_review`, no approval record: acceptance is the human's.
    - After QA approval of TASK-181 (L-3, L-4): the table preamble names the two qualified rows
      (hosted CI run pending, PLAN-002 1.2 `in_review`), the TASK-172 rows cite `68fc68b`, and
      `hazard` and `cause` are generic, with the MinIO chain marked as first raised in 1.0.
  - **Corrected by the QA review of TASK-183 (2026-10-30):** the "durable audit commit" item under
    risks introduced by controls now describes ADR-0016's independent transaction, since TASK-183
    removed `durable=True`. Text only; scores and status unchanged.
