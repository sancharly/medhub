---
id: SR-040
type: software-requirement
title: Object store deployment hardening and initialisation
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-30"
updated: "2026-10-30"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-30"
approved_digest: 86b9564217db819f3a270fa813b485c5f023b33adcce39fd8530bbaf880f2cf7
approval_note: self-approved
links:
  - target: RR-003
    relation: satisfies
  - target: NFR-007
    relation: derives_from
  - target: UN-008
    relation: derives_from
  - target: RISK-012
    relation: mitigates
  - target: RISK-001
    relation: mitigates
  - target: RISK-007
    relation: mitigates
tags:
  - control:design
  - control:protective
  - issue:sancharly/medhub#33
---

## Summary

The deployment shall expose the object store that holds clinical attachments only to the backend, with no administrative console, with non-default credentials, and shall create and configure its bucket reliably before the application depends on it.

## Description

This requirement implements the security-of-processing obligations (RR-003, NFR-007) for the component that stores every attachment and DICOM study. The object store sits behind the backend; no clinician, administrator or other service needs to reach it directly. Anyone who can reach it with an access key can write to it, so the deployment reduces who can reach it, what it exposes and what a guessable credential grants (§5.2.2 e security, j IT-network aspects, h installation). The deployment includes the Compose topology, its environment template and the deployment guide. It does not cover the other credentials and defaults of the deployment (PRB-007, GitHub #27).

## Acceptance Criteria

1. The object store exposes no administrative console: no console listener is started, and no console port is reachable from any container or from the host.
2. The object store and its bucket initialiser refuse to start when the access key or the secret key is unset, empty or equal to a known default value (including `minioadmin` and `changeme`), and report which setting was rejected. The environment template and the deployment guide contain no such default value and describe how to generate the keys.
3. The object store is reachable only from the backend and the bucket initialiser. A connection to it from any other service of the deployment is refused, and it publishes no port to the host.
4. The bucket initialiser starts only after the object store reports that it accepts requests. If creating or configuring the bucket fails, the initialiser exits with a non-zero status and the stack does not report the backend as started.
5. The verification of AC 1 to AC 4 runs against the deployment definition and a started stack, not against documentation alone.

## Origin Requirement

Derived from: Regulatory Requirement RR-003 "Security of processing: encryption and access control", Non-Functional Requirement NFR-007 "Cybersecurity" and User Need UN-008 "Recording clinical entries for a patient" (attachments must be stored safely and be there when needed).

## Risk Analysis

### Rationale

Known, unfixable vulnerabilities of the object store (PRB-043) become exploitable only because of its configuration: an enabled console, a guessable access key and reach from every container (RISK-012). Reducing the reach, the exposed surface and the credential guessability lowers the probability of the hazard. The bucket initialisation race (PRB-039) is an availability defect with the same configuration root.

### Potential Risks

- Security risk: an actor with a foothold on the deployment network writes to, takes over or reads the object store (RISK-012, RISK-001).
- Availability risk: a bucket that was never created makes attachments unavailable at first use (RISK-007); an overly strict start-up refusal can stop a legitimate deployment with a clear message, which is the intended failure mode.

### Control Measures

- Remove the console, refuse default credentials, restrict the network, order and check the bucket initialisation (AC 1 to AC 4). A configuration test and a started-stack check verify them (AC 5).
- These controls lower the probability of RISK-012 only; they do not remove the vulnerabilities of the component (PRB-042, ADR of CR-002).

## Version history

- 1.0 (2026-10-30) — Created for CR-002 (PRB-043, PRB-039).
