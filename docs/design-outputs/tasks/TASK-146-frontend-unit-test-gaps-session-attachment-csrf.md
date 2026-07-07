---
id: "TASK-146"
type: task
title: "Frontend unit-test gaps: session provider, attachment gating/upload, CSRF helper"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "NFR-006"
    relation: implements
  - target: "SR-030"
    relation: relates_to
  - target: "TASK-111"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium"]
---

- **Phase:** Review 2026-07 — verification
- **Implements:** NFR-006 (IEC 62304 verification coverage)
- **Depends on:** best done after TASK-143/144 (tests target their final shape); before TASK-111
- **Branch:** `test/frontend-gaps`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — finding T-unit (Medium)

## Objective

Security-relevant frontend units have zero tests: `SessionActivityProvider` (idle/expiry
orchestration — only `useIdleTimer` is tested), `AttachmentItem` (module-gated DICOM link),
`AttachmentUpload` + `client.uploadAttachment` (multipart path), and `api/csrf.ts` (`withCsrf`
header injection). These guard SR-030/SR-015/SR-031 behaviors and currently rely on manual testing
only.

## Implementation detail

Vitest + Testing Library + MSW, following existing co-located test conventions:

- `SessionActivityProvider.test.tsx` — warn dialog at threshold, extend resets deadline, expiry
  redirects to `/login?timeout=1`, query cache cleared on logout.
- `AttachmentItem.test.tsx` — viewer link present iff DICOM module in `["myModules"]`; non-DICOM
  attachments unaffected.
- Upload tests — success, 413/problem+json error surface, 401 path.
- `csrf.test.ts` — header set from cookie for mutating methods, absent cookie tolerated.

## Acceptance criteria

- [ ] All four areas covered with meaningful assertions (behavioral, not snapshot).
- [ ] Suite green in CI.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Coverage report shows the four modules exercised
- [ ] Traceability rows updated (tests linked to SR-030/SR-015/SR-031)
