---
id: "TASK-093"
type: task
title: "Appointments list/create/confirm/decline"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-010"
    relation: implements
  - target: "SR-011"
    relation: implements
  - target: "SR-035"
    relation: implements
  - target: "TASK-065"
    relation: relates_to
  - target: "TASK-083"
    relation: relates_to
tags: ["audit-verified", "phase:7-frontend-core-views"]
---

- **Phase:** 7 — Frontend core views
- **Software item / unit:** SI-FE-CORE / U-FEC-Appointments
- **Implements:** SR-010 (create doctor+patient+datetime), SR-011 (scoped visibility), SR-035 (notification visible in-app, confirmation state, patient-only confirm/decline); ADR-0003
- **Depends on:** TASK-065 (appointments API endpoints, SI-API), TASK-083 (auth/session UI + role context in shell) — must be merged first
- **Branch:** `feature/fe-appointments`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Build the **appointments** view: list appointments scoped to the caller (own for doctor/patient, all for admin — server-scoped per SR-011), create an appointment (admin or authorized user, SR-010), and let the **patient** confirm or decline (SR-035). The patient's list shows the in-app notification surface and each appointment's confirmation state (Pending/Confirmed/Declined). Confirm creates an appointment-scoped consent grant server-side (SR-036) — the UI triggers it but the grant logic is entirely backend; the unified consent view (TASK-094) reflects it.

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2) and `ShellServices`:

```ts
apiClient.listAppointments();                       // GET /appointments  (server-scoped, SR-011)
apiClient.createAppointment({ doctorId, patientId, scheduledAt });  // POST /appointments (SR-010)
apiClient.confirmAppointment(appointmentId);        // POST /appointments/{id}/confirm (patient only, SR-035.5)
apiClient.declineAppointment(appointmentId);        // POST /appointments/{id}/decline (patient only, SR-035.6/7)
// confirmation dialog for decline (destructive-ish) via ShellServices
shell.confirmDialog({...});
```

- Visibility is **server-scoped** (SR-011): the list returns only appointments the caller may see; the UI never widens. Admin sees scheduling fields but **no clinical data** (SR-010 AC-4, SR-009).
- Confirm/decline are exposed **only to the patient** in the UI; the server also enforces patient-only (SR-035.9). A doctor/admin sees the state read-only and **cannot** confirm/decline (no buttons, and server denies).
- The UI does **not** create/revoke consent grants directly — confirming an appointment causes the server to create the `APPOINTMENT:{id}` grant (SR-036.1); the UI just invalidates the consent query so TASK-094 reflects it.
- Cookie + CSRF via `ApiClient` (SR-031.3).

## Implementation detail

- Files to create:
  - `frontend/src/core/appointments/AppointmentsPage.tsx` — route `/appointments`; `useQuery(['appointments'])`.
  - `frontend/src/core/appointments/AppointmentList.tsx` — rows: doctor name, patient name, scheduled date/time, **confirmation state chip** (Pending/Confirmed/Declined) (SR-035.4/8).
  - `frontend/src/core/appointments/CreateAppointmentForm.tsx` — MUI form (doctor select, patient select, date/time); `useMutation` → `createAppointment`; available to admin and other authorized creators per role (SR-010.1/4).
  - `frontend/src/core/appointments/PatientActions.tsx` — for the **patient** only: Confirm button on Pending; Decline button on Pending or Confirmed (SR-035.5/6/7). Decline uses `ShellServices.confirmDialog` then `declineAppointment`; on success invalidate `['appointments']` and `['me','consents']` (so TASK-094 updates).
  - `frontend/src/core/appointments/index.ts` — route export.
- Libraries: React 18, TanStack Query, MUI (form, chips, dialog via ShellServices), React Router.
- In-app notification surface (SR-035.3): the patient's appointment list **is** the in-app notification view; a Pending appointment is visually highlighted and the appointment carries the doctor name + scheduled date/time + a path to the view (SR-035.2). The email channel is backend (SI-WORKER); the UI does not send email.
- Performance: list under the 3 s routine budget (SR-026.1, NFR-008) — single `GET /appointments`, paginated if large.
- Error cases: `400 /errors/validation-error` on create (missing doctor/patient/datetime, SR-010.2) → field errors; `403 /errors/forbidden` if a non-patient attempts confirm/decline (defense-in-depth; UI also hides the buttons) → error surface; state-transition `409 /errors/conflict` (e.g., confirm an already-declined appointment) → clear message.
- Edge cases / SR rules quoted:
  - SR-035.9: "The doctor cannot confirm or decline an appointment on the patient's behalf; only the patient … may perform confirmation or declination." — confirm/decline controls rendered for patient role only.
  - SR-035.7: "The patient can decline a previously Confirmed appointment, transitioning its state back to Declined." — Decline is available on Confirmed too.
  - SR-010.4 / SR-009: admin create/list shows scheduling fields only, never clinical data.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + RTL + MSW), `frontend/src/core/appointments/AppointmentsPage.test.tsx`:
  - patient role: list shows confirmation-state chips; a Pending appointment shows Confirm + Decline; Confirm → `POST /appointments/{id}/confirm` and list/consent queries invalidated (SR-035.4/5, SR-036 handoff).
  - patient declines a Confirmed appointment → confirm dialog shown, then `POST .../decline`; chip becomes Declined (SR-035.7).
  - doctor/admin role: confirmation state visible but **no** Confirm/Decline controls rendered (SR-035.9).
  - create form: missing doctor/patient/datetime → blocked / server `400` field errors (SR-010.2).
  - admin create: only scheduling fields, no clinical fields present (SR-010.4, SR-009).
  - list is server-scoped: component renders exactly the returned appointments, no widening (SR-011).
  - `409` on invalid transition → clear message; `403` on unauthorized confirm → error surface.
- Each test names the SR AC it verifies.

## Acceptance criteria

- [x] An authorized user can create an appointment with doctor + patient + date/time; missing fields are rejected (SR-010 AC-1/2).
- [x] Appointments are listed scoped to the caller (own / admin); unrelated users see none — server-scoped, UI never widens (SR-011).
- [x] Each appointment shows its confirmation state (Pending/Confirmed/Declined) to all participants (SR-035.4/8).
- [x] The patient — and only the patient — can confirm a Pending appointment and decline a Pending or Confirmed one; decline requires confirmation (SR-035.5/6/7/9, SR-027.2).
- [x] Confirming triggers the server-side appointment-consent grant; the UI invalidates the consent view so TASK-094 reflects it (SR-036 handoff; no client-side grant logic).
- [x] Admin create/list exposes no clinical data (SR-010.4, SR-009).

## Definition of Done

- [x] Lint + type-check pass (`eslint`/`tsc`)
- [x] Unit/component tests pass; coverage target met
- [x] Traceability matrix row updated (SR-010, SR-011, SR-035 → TASK-093 → tests)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
