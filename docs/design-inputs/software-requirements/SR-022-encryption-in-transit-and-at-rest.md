---
id: SR-022
type: software-requirement
title: Encryption in transit and at rest
status: approved
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approval_note: self-approved at the ship-feature spec gate (sancharly/medhub#27)
links:
  - target: RR-003
    relation: satisfies
  - target: RISK-006
    relation: mitigates
  - target: RISK-007
    relation: mitigates
  - target: RISK-008
    relation: mitigates
  - target: RISK-010
    relation: mitigates
  - target: RISK-011
    relation: mitigates
  - target: RISK-012
    relation: mitigates
  - target: NFR-004
    relation: derives_from
  - target: NFR-007
    relation: derives_from
tags:
  - control:design
  - control:protective
---

## Summary

The system shall encrypt all data in transit using TLS and encrypt personal and health data at rest.

## Description

This requirement implements the encryption obligations shared by GDPR and cybersecurity. All client-server communication uses TLS. Personal and health data, including clinical entries and file attachments such as DICOM images, are encrypted at rest in storage. Encryption uses recognized, current algorithms and key management.

## Acceptance Criteria

1. All client-server traffic is transmitted over TLS; non-TLS access is not served.
2. Personal and health data, including clinical entries and attachments, are encrypted at rest using a recognized algorithm (e.g., AES-256).
3. Encryption keys are managed so that data is not recoverable without authorized key access.
4. The object store bucket that holds attachments has default encryption enabled by the deployment, so that an object is stored encrypted at rest whichever client or path wrote it, including a write that carries no encryption request.
5. The encryption of an attachment written through the application's object-storage client is verified against a real object store: the stored object reports server-side encryption AES256.
6. Every value encrypted by the application's field-level encryption carries an identifier of the key that encrypted it. With more than one key configured, a new value is encrypted under the configured current key, a value encrypted under any other configured key is still decrypted, and a value whose key identifier matches no configured key is refused with an error; it is never decrypted with a different key or returned as ciphertext.
7. Introducing the key identifier (AC 6) leaves no existing value unreadable: every value written before it is either migrated to the identified format or still decrypted, and a test against a database populated in the earlier format shows it.
8. The deployment guide describes a key rotation procedure (add a new current key, re-encrypt or keep reading old values, retire the old key). The procedure is rehearsed against a backup copy of a populated database and the result is recorded in a test report.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-004 "GDPR compliance" and NFR-007 "Cybersecurity".

## Risk Analysis

### Rationale

Encryption protects special-category health data and is required by GDPR and medical-device cybersecurity guidance.

### Potential Risks

- Security/compliance risk: unencrypted data in transit or at rest exposes health data and violates regulation.

### Control Measures

- Enforce TLS (SR-001) and storage-level encryption; verify configuration during security review and system testing.
- Default bucket encryption (AC 4) covers writes that bypass the application (RISK-012). AC 5 closes the gap that only a mocked call was tested (PRB-036).
- The key identifier (AC 6 to AC 8) lets a compromised or ageing key be replaced without orphaning stored values (RISK-011, RISK-007; PRB-004). A failed or partial rotation can make clinical values unreadable, so AC 7 and the rehearsal of AC 8 are the fail-safe.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-006, RISK-007, RISK-008, RISK-010, RISK-011 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-09-17) — Added `satisfies` link to RR-003 (regulatory requirements
  extracted from the NFRs with clause citations). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.3 (2026-10-21) — Tagged `control:design`, `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.4 (2026-10-30) — Content change, so the approval is cleared and the record returns to review (CR-002). Added AC 4 (default bucket encryption) and AC 5 (encryption verified against a real object store) and a `mitigates` link to RISK-012. Reason: the application requests encryption only on its own write path, so an object written by another path is stored unencrypted (PRB-043), and no test ever wrote to a real store (PRB-036).
- 1.5 (2026-10-31) — Content change, so the approval record is cleared and the record returns to review (CR-004, GitHub sancharly/medhub#27). Added AC 6 (key identifier in every field-level ciphertext, decryption under any configured key, unknown key refused), AC 7 (no existing value made unreadable) and AC 8 (documented and rehearsed rotation). Reason: the ciphertext envelope records no key, so a rotation cannot decrypt earlier values (PRB-004), and RR-003 requires a documented key lifecycle.
