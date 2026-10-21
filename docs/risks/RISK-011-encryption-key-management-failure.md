---
id: "RISK-011"
type: risk
title: "Encryption or key management failure exposes or orphans clinical data"
status: in_review
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
hazard: "Encrypted clinical fields exposed in clear, or made permanently unreadable."
cause: "The ciphertext envelope carries no key identifier or version → a key rotation cannot tell which key decrypts which row → old rows fail to decrypt (data lost) or rotation is avoided altogether (a compromised key stays in use). Separately, a misconfigured storage endpoint could store attachments without server-side encryption."
harm: "Delayed care from lost history, or privacy harm from exposure."
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 2
acceptability: alarp
links:
  - target: "SOUP-011"
    relation: relates_to
  - target: "SOUP-022"
    relation: relates_to
  - target: "SOUP-019"
    relation: relates_to
tags: ["hazard:privacy", "hazard:availability", "class:B"]
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

SI-PERSIST (`U-PER-Crypto`), SI-ATTACH (object storage SSE), SOUP: cryptography 49.0.0, MinIO.

## Initial risk

Severity 3 — Moderate (exposure, or data unreadable) — × probability 2 (Remote) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| AES-256-GCM field encryption at rest and TLS in transit | Design | SR-022, SR-001 | TR-001, TS-008, TS-011 |
| Key identifier and version in the ciphertext envelope to make rotation safe | Design | PRB-004 resolution | none yet |
| Server-side encryption enforced on the object store, verified at bring-up | Protective | SR-022, TASK-115 | TR-001, TS-008 |
| Documented key custody and rotation procedure | Information for safety | NFR-007, TASK-115 | none yet |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. Residual stays ALARP until the envelope carries a key identifier (PRB-004) and a rotation procedure has been exercised at least once.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Encryption at rest and in transit is in place; the residual comes from key rotation, which cannot be done safely until the ciphertext envelope carries a key identifier (PRB-004). Until then the mitigation is procedural — documented key custody and backups before any rotation. The alternative, storing PHI unencrypted, is unacceptable, so the current state is the best practicable one pending PRB-004.

## Risks introduced by controls

Rotation itself is a risky operation; it needs a rehearsed, documented procedure and a backup before each run.
