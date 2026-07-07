---
id: "SR-036"
type: software-requirement
title: "Clinical data access grant on appointment confirmation"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "UN-013"
    relation: derives_from
  - target: "UN-005"
    relation: derives_from
  - target: "NFR-004"
    relation: derives_from
tags: []
---

## Summary

The system shall automatically grant the doctor associated with an appointment access to the patient's clinical data when the patient confirms that appointment, and shall not grant such access for unconfirmed or declined appointments.

## Description

Appointment confirmation (SR-035) is the patient's explicit consent event. When the patient confirms an appointment, the system records a clinical data access grant scoped to that specific appointment for the doctor named in it. This grant is independent of any other grants the doctor may hold for the same patient (e.g., a manual grant via SR-008 or a grant from a different appointment). Declining an appointment only removes the grant that was created by confirming that same appointment; it has no effect on any other grants the doctor may hold. A doctor's net access to the patient's clinical data is therefore the union of all active grants from all sources; declining one appointment removes only the contribution of that appointment's grant.

## Acceptance Criteria

1. When a patient confirms an appointment (SR-035 criterion 5), the system automatically creates a clinical data access grant for the doctor associated with that appointment, equivalent in scope to a manual grant via SR-008.
2. Following the grant, the doctor can access the patient's clinical data (subject to SR-006), without any additional manual action required from the patient.
3. While an appointment is in Pending or Declined state, this appointment creates no clinical data access grant for the doctor. The doctor's access to the patient's clinical data is determined solely by other active grants (e.g., manual grants via SR-008 or confirmations of other appointments). Specifically:
   - If the doctor had no access to the patient's clinical data before the appointment was created, and the patient declines or never confirms the appointment, the doctor still has no access.
   - If the doctor already had access through another grant before the appointment was created, and the patient declines or never confirms the appointment, that pre-existing access is unaffected.
4. Declining an appointment removes only the grant that was created by confirming that specific appointment. The effect on the doctor's access depends on the origin of that access:
   - **Case A — Doctor had no prior access before this appointment was confirmed:** Declining revokes the appointment-confirmation grant. The doctor's access returns to the state it was in before the confirmation, i.e., no access.
   - **Case B — Doctor already had access from another source (manual grant via SR-008 or confirmation of a different appointment) before this appointment was confirmed:** Declining revokes the appointment-confirmation grant. The doctor retains access through the other active grant(s); no change in the doctor's effective access.
   - **Case C — Patient had never confirmed this appointment (appointment is still Pending or was previously Declined):** Declining has no effect on access; no grant exists from this appointment to revoke.
5. The access grant created by appointment confirmation persists after the appointment date and time has passed; it remains in effect until the patient explicitly revokes it via SR-008 or the account is modified.
6. Each access grant and revocation triggered by appointment confirmation or declination is recorded in the audit log (per SR-023) with: patient identity, doctor identity, appointment identifier, trigger action (appointment confirmed / appointment declined), and timestamp.
7. The patient's clinical data access view (SR-008) reflects the grant created by appointment confirmation alongside any manually created grants, so the patient has a complete, unified view of who has access to their data.

## Origin Requirement

Derived from: User Need UN-013 "Patient notification and confirmation of scheduled appointments", User Need UN-005 "Patient ownership and control of their clinical data", and Non-Functional Requirement NFR-004 "GDPR compliance".

## Risk Analysis

### Rationale

A doctor requires access to the patient's clinical history to prepare for and conduct a meaningful clinical encounter. Appointment confirmation is the natural, patient-initiated consent event that authorizes this access. Tying access to the confirmation step — rather than to appointment creation — ensures that clinical data is shared only with the patient's explicit knowledge and action, satisfying GDPR's requirement for specific and unambiguous consent for the processing of health data.

### Potential Risks

- **Compliance (GDPR):** If access were granted on appointment creation rather than patient confirmation, clinical data could be accessed without an explicit patient consent event, violating GDPR Article 9 (processing of special-category data).
- **Privacy:** If the per-appointment grant is not correctly scoped, a declination could incorrectly revoke access the doctor legitimately holds through another grant, disrupting clinical care.
- **Safety:** If a doctor cannot access clinical data for a confirmed upcoming appointment due to a system error in grant creation, the encounter may be conducted without necessary patient history.
- **Implementation error:** Implementing declination as a blanket revocation of all the doctor's access to the patient (rather than removing only the appointment-specific grant) would incorrectly strip legitimately granted access. The system must track grants per source and revoke only the matching one.

### Control Measures

- Grant creation is triggered server-side by the confirmation event (criterion 1); it is not a client-initiated action and cannot be bypassed by the client.
- Declination removes only the grant from this specific appointment (criterion 4); the access-control layer evaluates all active grants per doctor–patient pair, so other grants are unaffected. This requires the access model to track grants by source (appointment ID or manual) rather than as a single binary flag.
- Audit logging (criterion 6) records every automated grant and revocation with the triggering appointment, providing a complete and auditable consent history.
- Unified access view (criterion 7) prevents the patient from having a fragmented picture of data-sharing consents across manual and appointment-driven grants.


## Revision History

Version 1.0 - Initial creation
Version 1.1 - Clarified per-appointment grant scoping and enumerated all three decline cases to remove ambiguity about effect on pre-existing access
