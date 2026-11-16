---
id: SR-024
type: software-requirement
title: Personal data erasure
status: approved
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-11-13"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-13"
approved_digest: 44897412bc474e7868b5a9b4096618171e61caddbe984e0bd23947fa26ad0e31
approval_note: self-approved
links:
  - target: RR-002
    relation: satisfies
  - target: RR-005
    relation: satisfies
  - target: RISK-002
    relation: mitigates
  - target: RISK-008
    relation: mitigates
  - target: RISK-007
    relation: mitigates
  - target: NFR-004
    relation: derives_from
tags:
  - control:design
  - control:protective
---

## Summary

The system shall support erasure or anonymization of a data subject's personal data upon a lawful request.

## Description

This requirement implements the GDPR right to erasure. On a lawful request, an authorized operator can remove or irreversibly anonymize a data subject's personal data, subject to any overriding legal retention obligations for clinical records. The operation is recorded for accountability.

## Acceptance Criteria

1. An authorized operator can initiate erasure or anonymization of a specified data subject's personal data.
2. After completion, the subject's personal identifying data is no longer retrievable through the application.
3. The erasure/anonymization action is recorded in the audit log with actor and timestamp.
4. Records subject to mandatory clinical retention are handled per a documented retention policy rather than silently deleted.
5. The scheduled retention sweep isolates a failure to the dataset on which it occurs, releases every database session it opens, and retries after a transient failure at most 3 times, so an expired dataset is erased by a later run or retry and is never skipped silently. The number of failed datasets is logged without personal data (SR-043).
6. An erasure request whose verification or retrieval-code e-mail cannot be enqueued fails and is rolled back as a whole: no partial erasure is left behind and the request never reports success. The requester receives an error response and may retry.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-004 "GDPR compliance".

## Risk Analysis

### Rationale

The right to erasure is a core GDPR data-subject right; the platform must be able to honor it.

### Potential Risks

- Compliance risk: inability to erase personal data violates GDPR.
- Safety/legal risk: erasing clinically/legally required records could breach retention law.

### Control Measures

- Provide an erasure/anonymization operation gated to authorized operators; reconcile with a documented retention policy; record in audit log (SR-023).
- Assumption: detailed retention policy is defined with regulatory/legal input post-MVP; MVP provides the technical capability and policy hook.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-002, RISK-008 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-09-17) — Added `satisfies` link to RR-002, RR-005 (regulatory requirements
  extracted from the NFRs with clause citations). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.3 (2026-10-21) — Tagged `control:design`, `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.4 (2026-11-13) — Content change, so the approval is cleared and the record returns to review (CR-006, GitHub sancharly/medhub#28). Added AC 5 (retention sweep failure isolation, session release and retry). Reason: the sweep leaked a database session per failing dataset and never retried, so expired data stayed unerased after a transient error (PRB-012; RISK-007, RISK-008).
- 1.5 (2026-11-13) — Content change, so the approval is cleared and the record returns to review (CR-006 Risk gate R-2, R-3). Added AC 6 (an erasure request whose e-mail cannot be enqueued fails as a whole, decision D-5; RISK-008) and the `mitigates` link to RISK-007 (R-3).
