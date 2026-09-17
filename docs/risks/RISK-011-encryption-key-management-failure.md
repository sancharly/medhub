---
id: "RISK-011"
type: risk
title: "Encryption or key management failure exposes or orphans clinical data"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
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

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 3 — Moderate (exposure, or data unreadable) | 2 — Remote | 6 — ALARP (6) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| AES-256-GCM field encryption at rest and TLS in transit | Design | SR-022, SR-001 | TS (Review stage) |
| Key identifier and version in the ciphertext envelope to make rotation safe | Design | PRB-004 resolution | TS (Review stage) |
| Server-side encryption enforced on the object store, verified at bring-up | Protective | SR-022, TASK-115 | TR (Release stage) |
| Documented key custody and rotation procedure | Information for safety | NFR-007, TASK-115 | TR (Release stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 3 — Moderate (exposure, or data unreadable) | 2 — Remote | 6 — ALARP (6) | **pending human decision** | — |

Residual stays ALARP until the envelope carries a key identifier (PRB-004) and a rotation procedure has been exercised at least once.

## Risks introduced by controls

Rotation itself is a risky operation; it needs a rehearsed, documented procedure and a backup before each run.
