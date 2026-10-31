---
id: RISK-011
type: risk
title: Encryption or key management failure exposes or orphans clinical data
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-31"
hazard: Encrypted clinical fields exposed in clear, or made permanently unreadable.
cause: The ciphertext envelope carries no key identifier or version → a key rotation cannot tell which key decrypts which row → old rows fail to decrypt (data lost) or rotation is avoided altogether (a compromised key stays in use). Separately, a misconfigured storage endpoint could store attachments without server-side encryption.
harm: Delayed care from lost history, or privacy harm from exposure.
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 2
acceptability: alarp
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approved_digest: 4e7dc41b849b34b77a13f4d212275feada131884544f08f0d8afb5f36b169196
approval_note: self-approved
links:
  - target: SOUP-011
    relation: relates_to
  - target: SOUP-036
    relation: relates_to
  - target: SOUP-019
    relation: relates_to
tags:
  - hazard:privacy
  - hazard:availability
  - class:B
---

# RISK-011 — Encryption or key management failure exposes or orphans clinical data

## Hazard

Encrypted clinical fields exposed in clear, or made permanently unreadable.

## Sequence of events

The ciphertext envelope carries no key identifier or version → a key rotation cannot tell which key decrypts which row → old rows fail to decrypt (data lost) or rotation is avoided altogether (a compromised key stays in use). Separately, a misconfigured storage endpoint could store attachments without server-side encryption.

## Hazardous situation

Clinical data is either unreadable to legitimate users or readable to someone with stolen storage access.

## Harm

Delayed care from lost history, or privacy harm from exposure.

## Software items involved

SI-PERSIST (`U-PER-Crypto`), SI-ATTACH (object storage SSE), SI-OBJSTORE (the object store and its
initialiser, ADD-025). SOUP: cryptography (SOUP-011), the object store (SOUP-036, SeaweedFS since
CR-002), boto3 (SOUP-019); versions in the SOUP records.

The object store derives its only SSE key from `AT_REST_ENCRYPTION_KEY`, the same key that feeds
field encryption. This reuse is carried over from the former store unchanged (CR-002 Q-3 and Q-7,
decision D-6); key separation is tracked on PRB-007. Losing or changing that key makes every stored
object unreadable as well as every encrypted field: a different key on the same volume gives
`InternalError` (SOUP-036 F-4, TASK-172, rerun by QA).

## Initial risk

Severity 3 — Moderate (exposure, or data unreadable) — × probability 2 (Remote) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| AES-256-GCM field encryption at rest and TLS in transit | Design | SR-022, SR-001 | TR-001, TS-008 (incl. TC-008.5), TS-011 |
| Key identifier and version in the ciphertext envelope to make rotation safe | Design | PRB-004 resolution | none yet |
| Server-side encryption enforced on the object store, verified at bring-up | Protective | SR-022 AC 4 and AC 5, TASK-115; CR-002: TASK-175 (bucket default encryption set and read back at initialisation, fail closed), TASK-179 (end-to-end check against the real store in CI) | TR-001, TS-008: TC-008.6 (bucket default `AES256`, a plain put reported `AES256`, started stack, TASK-175 and TASK-176 QA reruns) and TC-008.8 (CI job `object-store-integration`, 4 tests, mutation-checked; local run of the job steps by QA, hosted run pending TASK-182) |
| Migration of existing objects and key material by a procedure rehearsed against a backup, comparing checksums before and after each write; the source never modified | Protective | SR-022, SR-013 AC 5; TASK-178 | TS-008 TC-008.7: unit tests with mutations; rehearsal on restored copies (3 copied, 3 of 3 API downloads match, 0 plaintext-marker hits in the new volume, source tree hash unchanged), TASK-178 QA round 2 |
| Documented key custody and rotation procedure | Information for safety | NFR-007, TASK-115 | none yet |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. Residual stays ALARP until the envelope carries a key identifier (PRB-004) and a rotation procedure has been exercised at least once.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Encryption at rest and in transit is in place; the residual comes from key rotation, which cannot be done safely until the ciphertext envelope carries a key identifier (PRB-004). Until then the mitigation is procedural — documented key custody, and no rotation is performed.

**The backup part of that mitigation is not in place.** No backup and restore procedure exists for
the database, `object_store_data` or the `AT_REST_ENCRYPTION_KEY` they depend on
([PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md), major, open). The
`alarp` residual still holds until then because no rotation can be run safely anyway (PRB-004), so
none is performed; no release exists and only development data is stored (CR-002 Q-5); and the
key is required at start-up, so a lost key fails loudly rather than silently. The alternative,
storing PHI unencrypted, is unacceptable, so the current state is the best practicable one pending
PRB-004 and PRB-057. **Re-evaluate** when PRB-057 is resolved or at the first release, whichever
comes first.

## Risks introduced by controls

Rotation itself is a risky operation; it needs a rehearsed, documented procedure and a backup before each run.

The object-store SSE key adds the same exposure for attachments: rotating or losing
`AT_REST_ENCRYPTION_KEY` makes the stored objects unreadable (SOUP-036 F-4). No backup and restore
procedure covers `object_store_data` together with the key
([PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md), major, open; outside
CR-002), and `infra/DEPLOY.md` says so only in the migration section. The migration (TASK-178) moved
objects between stores under the same key; it was rehearsed and needs no new key.

## Version history

- 1.2 (2026-10-29) — CR-003 (TASK-163, D-5), §7.4 change analysis for the cryptography upgrade
  49.0.0 → 50.0.2 (SOUP-011). Content change, so the approval record is cleared and the record
  returns to review.
  - "Software items involved" named cryptography 49.0.0. It now names the SOUP records (SOUP-011,
    SOUP-022) instead of a version, so it does not go stale at the next upgrade.
  - The AES-256-GCM control row gains TS-008 TC-008.5 as verification: the known-answer test shows
    that a field value encrypted under 49.0.0 still decrypts under the locked version, which is the
    "old rows fail to decrypt" harm of this record.
  - Scores are not changed: severity 3 × probability 2 → alarp, as derived from `risk_matrix`.
- 1.3 (2026-10-30) — CR-002 TASK-181, §7.4 change analysis (CR-002 AC-14), by the Software
  Architect role. Content change, so the approval record is cleared and the record returns to
  review.
  - Link `relates_to` SOUP-022 (obsolete) replaced by SOUP-036 (CR-002 AC-12).
  - The SSE row gains SR-022 AC 4 and AC 5, TASK-175 and TASK-179, and TS-008 TC-008.6 and TC-008.8.
  - New row for the rehearsed migration (TASK-178, TS-008 TC-008.7).
  - "Software items involved" no longer names MinIO; it names the object-store records and notes
    the carried-over key reuse (Q-3, Q-7, PRB-007) and the SSE key loss (SOUP-036 F-4).
  - Risks introduced by controls: the object-store key exposure and PRB-057 added.
  - Not re-scored: severity 3 × probability 2 → `alarp`, as derived from `risk_matrix`; the
    residual is still set by PRB-004 (no key identifier) and the unexercised rotation. Acceptance
    is the human's, through approval of this version.
