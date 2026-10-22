---
id: RISK-012
type: risk
title: Object store compromised from the internal network or left unpatchable
status: in_review
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-22"
updated: "2026-10-22"
hazard: "Clinical attachments (including DICOM studies) in the object store can be read, replaced, planted or made unreadable without the object store's secret key, and the object store will never receive a security fix."
cause: "MinIO RELEASE.2025-09-07T16-13-09Z is the last community release and is no longer maintained (SOUP-022, PRB-042). It carries unfixed vulnerabilities (CVE-2026-41145, CVE-2026-40344, CVE-2026-113466, CVE-2026-34204), which MedHub's configuration exposes to every container on the `medhub` network (PRB-043) → an actor who gains a foothold on that network (a compromised container or the host) writes or takes over the store → attachments are disclosed, substituted, stored without encryption, or made permanently unreadable, and the backend serves the substituted content because it does not check the stored checksum on download."
harm: "Wrong or delayed diagnosis or treatment from a substituted or planted attachment or DICOM study (harms of RISK-002 and RISK-003); privacy harm from disclosure of attachments (RISK-001, RISK-011); delayed care from lost or unreadable attachments (RISK-007)."
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
- Deployment topology: `infra/docker-compose.yml`, services `minio` and `createbuckets`.
- SOUP: MinIO server [SOUP-022](../soup/SOUP-022-minio.md) and MinIO client
  [SOUP-023](../soup/SOUP-023-minio-client.md).

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

All measures are planned under the separate CR-002 (decided 2026-10-22). None is implemented yet.

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Replace the unmaintained object store with a maintained S3-compatible component, chosen by ADR | Design | PRB-042 (CR-002) | none yet |
| Interim: build the object-store image from the archived release binaries, after verifying their published checksums and signatures, so a fresh host can deploy the pinned release | Protective (availability, reproducibility) | PRB-042 (CR-002) | none yet |
| Disable the embedded console (remove `--console-address ":9001"` and the 9001 `expose`) | Design | PRB-043 (CR-002) | none yet |
| Refuse to start with the default or example credentials (`minioadmin`, `changeme`); require a non-default access key | Protective | PRB-043 (CR-002) | none yet |
| Set default bucket encryption (SSE-S3) in `createbuckets`, so any write is encrypted at rest | Protective | PRB-043 (CR-002) | none yet |
| Check the stored SHA-256 checksum on every download and fail loudly on mismatch | Protective | PRB-043 (CR-002) | none yet |
| Restrict the object store to a network that only the backend and `createbuckets` can reach | Design | PRB-043 (CR-002) | none yet |

## Residual risk

Severity 4 (unchanged: the controls reduce probability, not severity) × probability 2 (Remote) →
**alarp**, derived from `risk_matrix`. The residual equals the initial risk until CR-002 lands,
because no control is implemented or verified. Once the configuration hardening and the checksum
check are verified, the expected residual is probability 1. Severity 4 × probability 1 →
acceptable per `risk_matrix`. That is an estimate for CR-002 to confirm, not a score.

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
public network. Re-evaluate when CR-002 lands.

## Risks introduced by controls

- Checking the checksum on download rejects an attachment whose stored checksum is wrong. That is
  an availability effect (RISK-007), and it must fail with a clear error.
- Replacing the component means migrating the stored objects and their SSE key material. A
  migration error can orphan or expose attachments (RISK-011). CR-002 needs a rehearsed migration
  with a backup.
- Removing the console moves bucket administration to `mc` only. The procedure in
  `infra/DEPLOY.md` must be updated with it.
