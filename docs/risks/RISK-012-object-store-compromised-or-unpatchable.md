---
id: RISK-012
type: risk
title: Object store compromised from the internal network or left unpatchable
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-22"
updated: "2026-10-30"
hazard: Clinical attachments (including DICOM studies) in the object store can be read, replaced, planted or made unreadable without the object store's secret key, and the object store will never receive a security fix.
cause: MinIO RELEASE.2025-09-07T16-13-09Z is the last community release and is no longer maintained (SOUP-022, PRB-042). It carries unfixed vulnerabilities (CVE-2026-41145, CVE-2026-40344, CVE-2026-113466, CVE-2026-34204), which MedHub's configuration exposes to every container on the `medhub` network (PRB-043) → an actor who gains a foothold on that network (a compromised container or the host) writes or takes over the store → attachments are disclosed, substituted, stored without encryption, or made permanently unreadable, and the backend serves the substituted content because it does not check the stored checksum on download.
harm: Wrong or delayed diagnosis or treatment from a substituted or planted attachment or DICOM study (harms of RISK-002 and RISK-003); privacy harm from disclosure of attachments (RISK-001, RISK-011); delayed care from lost or unreadable attachments (RISK-007).
severity_initial: 4
probability_initial: 2
severity_residual: 4
probability_residual: 2
acceptability: alarp
links:
  - target: SOUP-022
    relation: relates_to
  - target: SOUP-023
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
- Deployment topology: `infra/docker-compose.yml`, services `minio` and `createbuckets`. Under
  CR-002 they become SI-OBJSTORE
  ([ADD-025](../design-outputs/architecture/ADD-025-object-store-deployment.md)): the
  `object-store-preflight`, `object-store` and `object-store-init` services.
- SOUP: MinIO server [SOUP-022](../soup/SOUP-022-minio.md) and MinIO client
  [SOUP-023](../soup/SOUP-023-minio-client.md). Under ADR-0015 (b) both become `obsolete`, and
  SeaweedFS gets a new record (SOUP-036, TASK-172). TASK-181 moves this record's `relates_to` links
  to it (CR-002 AC-12).

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

The controls are planned under CR-002, and none is implemented yet. The component choice
(replace or interim) is [ADR-0015](../design/adr/0015-object-store-component-after-minio.md),
which stays `Proposed` until the human answers CR-002 Q-1. The table follows the ADR's
recommended option (b), replacement by SeaweedFS. Rows that change under another option say so.
"Verified by" names the test specification and case that each task adds or extends. TS-014 is new
and `verifies` SR-040. The test report entry is written at release.

| Measure | Type | Implemented by (SR, TASK) | Verified by (TS/TR) |
|---|---|---|---|
| Replace the unmaintained object store with a maintained S3-compatible component, chosen by ADR (option b) | Design | SR-028 AC-7, SR-022; TASK-172 (contract spike, SOUP-036 review), TASK-176 (server swap) | TS-013 (pull and build on a fresh daemon, pin check); TS-008 (SSE against the real store, TASK-179); SOUP-036 anomaly review |
| Interim: build the image from the archived release binaries after verifying their checksums and signatures. **Only under ADR-0015 option (c) or (d)**; not planned under (b) | Protective (availability, reproducibility) | SR-028 AC-7; TASK-176 in its option-(c) form | TS-013 (tampered-binary negative test, CR-002 AC-10) |
| Disable the embedded console or admin UI and every unused listener | Design | SR-040 AC 1; TASK-176 | TS-014 (Compose assertion; connection refused on the former console port from the backend and the host) |
| Refuse to start with an unset, empty or default credential, or a secret key shorter than 16 characters (CR-002 Q-2) | Protective | SR-040 AC 2; TASK-174 | TS-014 (four preflight cases; Compose and template assertions) |
| Set default bucket encryption (SSE-S3) at initialisation, so any write is encrypted at rest | Protective | SR-022 AC 4, SR-040 AC 4; TASK-175 | TS-008 (bucket configuration read back; plain upload reported `AES256`); TS-014 (initialiser failure exits) |
| Check the stored SHA-256 checksum on every download, and refuse and audit a mismatch | Protective | SR-013 AC 5; TASK-173 | TS-007 (substituted object refused with an audit FAILURE event; unmodified object served; DICOM covered) |
| Restrict the object store to a network that only the backend and the initialiser join | Design | SR-040 AC 3; TASK-177 | TS-014 (connection refused from proxy, frontend, postgres, redis and worker; backend round trip) |
| Verify encryption end to end against a real object store on every pull request (PRB-036) | Protective | SR-022 AC 5; TASK-179 | TS-008 (CI job `object-store-integration`) |
| Migrate existing objects and key material by a procedure rehearsed against a backup | Protective | SR-022, SR-013; TASK-178 | Rehearsal record in TASK-178 (before and after checksums, pre-change object decrypts) |

## Residual risk

Severity 4 (unchanged: the controls reduce probability, not severity) × probability 2 (Remote) →
**alarp**, derived from `risk_matrix`. The scores are **not re-scored at the CR-002 Risk stage**:
no control is implemented or verified yet. Re-scoring is **pending verification** and is done by
TASK-181 from the evidence of TASK-172..179.

Expected outcome, for CR-002 to confirm with that evidence. This is an estimate, not a score:

- Under ADR-0015 option (b) or (a): the unfixable CVEs leave with the MinIO code. Reach is
  limited to the backend and the initialiser, which hold the credentials anyway. The console is
  gone. A substituted object is refused, not served. Probability 1 → 4 × 1 → acceptable.
- Under option (c): the CVEs stay, and the same configuration controls and the checksum limit
  reach and detect substitution. Probability 1 is plausible but rests on configuration alone.
  TASK-181 must argue it explicitly or keep probability 2.

**Input for RISK-010 (handled by TASK-159, not here).** RISK-010 assumes that an anomaly review can
be followed by a patch. For MinIO it cannot: no fixed community version exists or will exist. The
anomaly review found that RISK-010's residual probability 1 does not hold for the MinIO path and
proposes probability 2 for that path (severity 3 × probability 2 → alarp) until PRB-042 is
resolved.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Not yet justified. The residual is ALARP only because no control is in place yet. Further
reduction is practicable: the controls above are known and planned. The human decided on
2026-10-22 that the controls go to CR-002 and that no release is made before CR-002. The current
state is accepted for development only, never for a release. Until then the common precondition
holds: the store is reachable only from the internal `medhub` network, not from the host or the
public network. Re-evaluate when CR-002 lands. CR-002 TASK-181 rewrites this section from the
verified evidence. If the residual is acceptable, the section is replaced by a statement that no
ALARP justification is needed.

## Risks introduced by controls

- Checking the checksum on download rejects an attachment whose stored checksum is wrong. That is
  an availability effect (RISK-007). It must fail with a clear error and an audit event, never
  with partial content (TASK-173).
- Replacing the component means migrating the stored objects and their SSE key material. A
  migration error can orphan or expose attachments (RISK-011). TASK-178 rehearses the migration
  with a backup, compares every object's checksum, and retires the MinIO key material only after
  the comparison passes.
- Removing the console moves bucket administration to scripted S3 calls (`object-store-init`)
  and the procedure in `infra/DEPLOY.md` (TASK-180).
- The credential preflight stops a deployment whose keys are weak. That is the intended failure
  mode, with a message that names the setting (TASK-174).
- **New under option (b): a larger attack surface with a high advisory rate.** SeaweedFS had 25
  GitHub advisories in 2026, 9 of them critical. Each was fixed in a release, and none affects
  4.51 (ADR-0015). The all-in-one server also opens internal master, volume and filer ports.
  - The controls are the network restriction (TASK-177), unused listeners switched off
    (TASK-176), and a monthly advisory check proposed for PLAN-002 (TASK-172).
  - Fixes ship only in the latest release, so staying patchable needs digest updates at the
    PLAN-002 cadence. That is RISK-010 path 1, which TASK-181 re-evaluates.
- `AT_REST_ENCRYPTION_KEY` feeds both field encryption and the object-store SSE key, as it did
  with MinIO. The change carries this over and adds nothing. Its handling stays with PRB-007
  (CR-002 Q-3).

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
