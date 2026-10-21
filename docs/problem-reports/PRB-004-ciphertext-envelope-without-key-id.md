---
id: "PRB-004"
type: problem-report
title: "Ciphertext envelope carries no key identifier, so key rotation cannot be performed safely"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: major
links: []
tags: ["security", "hazard:availability"]
---

# PRB-004 — Ciphertext envelope carries no key identifier, so key rotation cannot be performed safely

## Observed

`app/db/crypto.py` writes the AES-GCM envelope with no key id or version prefix, so no row records which key encrypted it. A rotation therefore cannot decrypt pre-rotation rows. Separately, no PHI column currently uses `EncryptedString`, so the field-level encryption scope is undefined.

## Impact

SR-022 (encryption in transit and at rest) is only partly realized: either rotation is avoided — leaving a possibly compromised key in use — or it silently orphans existing rows.

## Safety evaluation

Contributes to RISK-011 (encryption or key-management failure) and RISK-007 (clinical information unavailable). No occurrence to date; no rotation has been attempted.

## Resolution

Not yet tracked by a task. Proposed: add a key-id/version prefix to the envelope with a migration path for existing rows, decide and document the field-level PHI scope, and rehearse a rotation with a backup. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Medium.
