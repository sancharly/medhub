---
id: "SR-035"
type: software-requirement
title: "Patient notification and confirmation of scheduled appointments"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "UN-013"
    relation: derives_from
  - target: "UN-007"
    relation: derives_from
tags: []
---

## Summary

The system shall notify the patient when an appointment is created for them, maintain a confirmation state on each appointment, and allow the patient to confirm or decline the appointment before it takes place.

## Description

When an appointment is created (per SR-010), it enters a **Pending** state. The patient associated with the appointment receives a notification immediately after creation. The patient can then view the appointment and take one of two actions: confirm attendance or decline. Confirming transitions the appointment to **Confirmed**; declining transitions it to **Declined**. The doctor and administrative personnel can see the current confirmation state. An appointment that has not been confirmed by the patient before its scheduled date and time is treated as unconfirmed and does not authorize clinical data access (see SR-036).

## Acceptance Criteria

1. Every appointment created via SR-010 is assigned an initial confirmation state of **Pending**.
2. Immediately after an appointment is created, the system sends a notification to the associated patient. The notification includes: the doctor's name, the scheduled date and time, and a direct link or path to the appointment view.
3. The notification is delivered as an in-application notification visible in the patient's appointment view. An additional email notification is sent to the patient's registered email address.
4. The patient's appointment view lists all their appointments with their current confirmation state (Pending, Confirmed, or Declined).
5. The patient can confirm a Pending appointment, transitioning its state to **Confirmed**.
6. The patient can decline a Pending appointment, transitioning its state to **Declined**.
7. The patient can decline a previously Confirmed appointment, transitioning its state back to **Declined**.
8. The doctor and administrative personnel associated with the appointment can view the current confirmation state of that appointment.
9. The doctor cannot confirm or decline an appointment on the patient's behalf; only the patient associated with the appointment may perform confirmation or declination.
10. Each confirmation and declination event is recorded in the audit log (per SR-023) with: patient identity, doctor identity, appointment identifier, action taken, and timestamp.

## Origin Requirement

Derived from: User Need UN-013 "Patient notification and confirmation of scheduled appointments" and User Need UN-007 "Appointment scheduling between doctors and patients".

## Risk Analysis

### Rationale

Without notification and an explicit confirmation step, patients may be unaware of appointments scheduled on their behalf and may unknowingly trigger clinical data access grants (SR-036). The confirmation workflow is the patient-facing consent action required before the appointment can proceed and before the associated doctor gains access to clinical records.

### Potential Risks

- **Privacy:** If the patient is not notified, they cannot exercise their consent rights before the appointment date.
- **Usability:** If the notification is not prominent or timely, patients may miss it and leave appointments in Pending state, preventing the doctor from accessing data needed for the encounter.
- **Safety:** A doctor expecting clinical data access for an upcoming confirmed appointment may not be aware if the patient has declined.

### Control Measures

- Dual-channel notification (in-app and email, criterion 3) reduces the chance of a missed notification due to platform access patterns.
- The confirmation state is visible to all appointment participants (criterion 8) so the doctor can see whether the patient has confirmed before the encounter.
- Only the patient can confirm or decline (criterion 9); this cannot be delegated to administrative personnel to ensure the consent action is unambiguously the patient's.
- Audit logging (criterion 10) creates a traceable record of each consent action.
