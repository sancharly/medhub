---
id: "TASK-138"
type: task
title: "PII scrubbing for worker and notification logs"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "NFR-004"
    relation: implements
  - target: "SR-023"
    relation: relates_to
  - target: "TASK-031"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium"]
---

- **Phase:** Review 2026-07 — backend security/robustness
- **Implements:** NFR-004 (GDPR)
- **Depends on:** —
- **Branch:** `fix/log-pii-scrub`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — finding E (Medium)

## Objective

Worker logs write user email addresses as structured-log fields, e.g.
`app/workers/email_tasks.py:170` `extra={"recipient": recipient_email, ...}`. `AuditService`
scrubbing only protects audit rows; the JSON stdout log stream (shipped to whatever log sink)
carries raw PII — a GDPR data-minimization violation and an uncontrolled PII copy outside the
retention/erasure machinery (SR-024 erasure cannot reach log archives).

## Implementation detail

- Sweep `app/workers/` and `app/` for `logger.*` calls carrying email/name/PII in message args or
  `extra` (`grep -rn "email\|recipient" backend/app --include='*.py' | grep logger` as a start).
- Replace with non-identifying keys (account id, dataset id) — ids are already the pattern used by
  the retention sweep logs.
- Add a logging filter in `core/logging.py` that redacts email-shaped values in `extra` fields as a
  safety net, mirroring the AuditService scrub regex.

## Acceptance criteria

- [ ] No log statement emits email addresses or names; account UUIDs are used instead.
- [ ] The redaction filter masks an email smuggled through `extra` (unit test).
- [ ] Existing worker tests pass.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Unit test for the redaction filter; grep-based CI check optional
- [ ] Traceability row updated (NFR-004 → TASK-138 → tests)
