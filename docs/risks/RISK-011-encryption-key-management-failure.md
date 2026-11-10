---
id: RISK-011
type: risk
title: Encryption or key management failure exposes or orphans clinical data
status: approved
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-10"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-10"
approval_note: approved by the human in chat at the close of CR-004
hazard: Encrypted clinical fields exposed in clear, or made permanently unreadable.
cause: The ciphertext envelope carries no key identifier or version → a key rotation cannot tell which key decrypts which row → old rows fail to decrypt (data lost) or rotation is avoided altogether (a compromised key stays in use). Separately, a misconfigured storage endpoint could store attachments without server-side encryption.
harm: Delayed care from lost history, or privacy harm from exposure.
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 2
acceptability: alarp
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
| Key identifier and version in the ciphertext envelope to make rotation safe | Design | PRB-004 resolution | TS-008 TC-008.9, TC-008.10 |
| Server-side encryption enforced on the object store, verified at bring-up | Protective | SR-022 AC 4 and AC 5, TASK-115; CR-002: TASK-175 (bucket default encryption set and read back at initialisation, fail closed), TASK-179 (end-to-end check against the real store in CI) | TR-001, TS-008: TC-008.6 (bucket default `AES256`, a plain put reported `AES256`, started stack, TASK-175 and TASK-176 QA reruns) and TC-008.8 (CI job `object-store-integration`, 4 tests, mutation-checked; local run of the job steps by QA, hosted run pending TASK-182) |
| Migration of existing objects and key material by a procedure rehearsed against a backup, comparing checksums before and after each write; the source never modified | Protective | SR-022, SR-013 AC 5; TASK-178 | TS-008 TC-008.7: unit tests with mutations; rehearsal on restored copies (3 copied, 3 of 3 API downloads match, 0 plaintext-marker hits in the new volume, source tree hash unchanged), TASK-178 QA round 2 |
| Documented key custody and rotation procedure | Information for safety | NFR-007, TASK-115 | none yet |
| Key identifier in the field envelope, bound as associated data; decryption under any configured key; unknown key refused (CR-004, ADR-0018) | Design | SR-022 AC 6, AC 7; TASK-193, TASK-194 | TS-008 TC-008.9, TC-008.10 |
| Documented rotation with a re-encryption command, rehearsed against a backup copy of a populated database (CR-004) | Protective | SR-022 AC 8; TASK-195 | TS-008 TC-008.11; rehearsal records in TASK-194 and TASK-195, collected for the next TR; TASK-202 repeated the rotation on a started stack (old key retired, `--check` exit 3 then `--apply` then `--check` exit 0, retired key removed, 5 of 5 entries and 10 of 10 attachments still readable) |
| Separate field-encryption and object-store SSE keys, refused when equal; attachments migrated to the new SSE key by a rehearsed copy (CR-004, CR-002 D-6 carried over) | Design | SR-041 AC 5; TASK-196 | TS-014 TC-014.7; TS-015 TC-015.3; rehearsal record in TASK-196 |
| Placeholder and wrong-length keys refused at start-up by the backend, the worker and the preflight (CR-004) | Protective | SR-041 AC 3; TASK-197 | TS-015 TC-015.3 |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. The exposure path is closed (PRB-004 resolved, rotation documented and rehearsed); the residual stays ALARP because of the loss path (PRB-057, open).

**Change analysis (CR-004, Risk stage, 2026-10-31).** CR-004 implements the two items this
residual has waited for: the key identifier (PRB-004) and an exercised rotation (the rehearsal of
SR-022 AC 8). It also separates the two keys (SR-041 AC 5), so one key's compromise or loss
reaches one store, not both.

**Expected residual, for the human to decide at verification:**

- the exposure path (a compromised key stays in use because rotation is unsafe) drops to
  probability 1 once TASK-193..196 are verified: **3 × 1 → acceptable** by the `risk_matrix`;
- the loss path (a lost key makes its data permanently unreadable) is unchanged by CR-004,
  because no backup and restore procedure covers the keys (PRB-057, open, outside CR-004).

So the record can be re-scored to 3 × 1 only if PRB-057 is resolved first or the human accepts the
loss path as a residual anomaly for development use; otherwise it stays **3 × 2 → alarp** with
the ALARP justification below. Scores are not changed now; TASK-202 re-scores from the evidence.

**Verification and proposed residual (CR-004 Checkpoint F, TASK-202, 2026-11-08).** Checkpoint F evidence (TASK-202, 2026-11-08, HEAD 579aaaa plus TASK-202's small edits): backend 1547 passed, 6 skipped, coverage 94.51% (floor 85%); DICOM module 25 passed; frontend 315 passed; infra 110 passed; started stack (project `task202`, empty template, generated secrets): `infra/smoke-test.sh` 78 passed, 0 failed; `infra/log-secrets-check.sh` 38 passed, 0 failed. The exposure path is closed by evidence: the envelope carries the key id (TC-008.9, TC-008.10), a rotation was run on a started stack with attachments and nothing became unreadable, and the two keys are separate (TC-014.7, TC-015.3). The loss path is not: PRB-057 is `open` and no backup and restore procedure covers the keys. **Proposed residual: severity 3 × probability 2 → alarp** (derived from `risk_matrix`; unchanged). **Decision for the human:** 3 × 1 → acceptable is available only if you accept the loss path as a residual anomaly for development use, or PRB-057 is resolved first. Neither has happened, so this record does not propose it. The ALARP justification below was rewritten on 2026-11-08 from these facts; its re-evaluation trigger is PRB-057 resolved, or the first release. TASK-202's rotation changed the exposure path only.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

**What changed since the first justification.** The residual used to come from key rotation, which could not be done safely
until the ciphertext envelope carried a key identifier. That is no longer so. PRB-004 is `resolved`: every stored value starts
with `mh1:<key id>:`, the id is bound as associated data, and an unknown id is refused (TS-008 TC-008.9, TC-008.10).
Rotation is documented in `infra/DEPLOY.md` ("Field-encryption key rotation": a `pg_dump` first, a `--check` mode, `--apply`, a
way to roll back), it was rehearsed on a backup copy (TASK-195) and TASK-202 ran it on a started stack with attachments, with
nothing unreadable at any step. The field key and the object-store SSE key are separate, so one key's compromise or loss reaches
one store. The exposure path (a compromised key stays in use because rotation is unsafe) is therefore closed, and rotation is now
a procedure that can be run, not one that is withheld.

**What remains: the loss path.** No backup and restore procedure exists for the database, `object_store_data` or the
`AT_REST_ENCRYPTION_KEY` and `OBJECT_STORE_SSE_KEY` they depend on outside a rotation
([PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md), major, open). A lost or overwritten key, a disk loss or
a failed upgrade can still make records and attachments permanently unreadable. This is what keeps the probability at 2 and the
record at `alarp`.

**Why ALARP still holds.** (1) No release exists (CR-004 A-1) and only development data is stored (CR-002 Q-5), so no clinical
record depends on MedHub alone yet. (2) A lost or wrong key fails loudly, not silently: the key is required at start-up, a
stored value that names a key id that is not configured stops `db-migrate` (`--verify-key-ids`, its last step) and keeps the
backend down, and an undecryptable value is refused, never returned as wrong content. (3) The alternative, storing PHI
unencrypted, is unacceptable. The current state is the best practicable one pending PRB-057. 3 × 1 is not claimed, because that
needs the loss path closed or accepted by the human.

**Re-evaluate** when PRB-057 is resolved or at the first release, whichever comes first, and at every release.

## Risks introduced by controls

Rotation itself is a risky operation; it needs a rehearsed, documented procedure and a backup before each run.

The object-store SSE key adds the same exposure for attachments: rotating or losing
`AT_REST_ENCRYPTION_KEY` makes the stored objects unreadable (SOUP-036 F-4). No backup and restore
procedure covers `object_store_data` together with the key
([PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md), major, open; outside
CR-002), and `infra/DEPLOY.md` says so only in the migration section. The migration (TASK-178) moved
objects between stores under the same key; it was rehearsed and needs no new key.

CR-004 (2026-10-31): the controls are themselves operations that can make data unreadable,
which is this record's hazard:

- migration 0010 (field envelope): one transaction, rolls back on any value that does not
  decrypt, tested against a database in the old format, rehearsed on a backup copy;
- the re-encryption command: `--check` before a key is retired, read-back before commit, idempotent;
- the SSE key copy: source read only, checksums compared per object, rehearsed on a backup copy,
  the old volume kept until the API reads every attachment back.

Each is a CR-004 "ask first" step: none runs against a database or volume other than a copy until
the human approves. The operator now holds two keys (three during a rotation); `infra/DEPLOY.md`
documents generation and custody (TASK-195, TASK-196).

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
- 1.4 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.5 (2026-11-08) — CR-004 Checkpoint F (TASK-202): planned verification replaced by the tests that ran and the started-stack rotation; residual proposed from the evidence, 3 × 2 → alarp, unchanged (3 × 1 needs PRB-057 resolved or the human's acceptance of the loss path). Content change, so `in_review` and the approval record cleared.
- 1.6 (2026-11-08) — TASK-202 round 2 (QA finding 1): the ALARP justification and the residual paragraph rewritten from the current facts (PRB-004 resolved, rotation documented and rehearsed, loss path open under PRB-057); scores unchanged, 3 × 2 → alarp. `in_review`.
