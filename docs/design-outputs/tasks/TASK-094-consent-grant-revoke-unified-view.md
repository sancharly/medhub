---
id: "TASK-094"
type: task
title: "Consent grant/revoke + unified view"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-008"
    relation: implements
  - target: "SR-036"
    relation: implements
  - target: "SR-027"
    relation: implements
  - target: "TASK-064"
    relation: relates_to
  - target: "TASK-083"
    relation: relates_to
tags: ["audit-verified", "phase:7-frontend-core-views"]
---

- **Phase:** 7 — Frontend core views
- **Software item / unit:** SI-FE-CORE / U-FEC-Consent
- **Implements:** SR-008 (AC-1/3 patient grants/revokes a doctor; revoke immediate + confirmation), SR-036.7 (unified view of manual + appointment-derived grants); SR-027.2 (confirm destructive action); ADR-0003
- **Depends on:** TASK-064 (consent API endpoints, SI-API), TASK-083 (auth/session UI + role context) — must be merged first
- **Branch:** `feature/fe-consent`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Build the patient's **consent** view: a single unified list of every active grant on the patient's clinical data — both **manual** grants (SR-008) and **appointment-derived** grants created by confirming appointments (SR-036) — and the controls to grant a named doctor manual access and to revoke any grant. Revocation takes effect immediately on the server (authorization reads live consent per request, SR-008.4) and requires explicit confirmation (SR-027.2, SR-008). This is the patient's complete, single picture of who can see their data (SR-036.7).

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2) and `ShellServices`:

```ts
apiClient.listMyConsents();                 // GET /me/consents — unified manual + appointment grants (SR-036.7)
apiClient.grantConsent({ doctorId });       // POST /consents — MANUAL grant (SR-008.1)
apiClient.revokeConsent(grantId);           // DELETE /consents/{id} — immediate (SR-008.3/4)
shell.confirmDialog({...});                 // required confirmation before revoke (SR-027.2)
```

- `GET /me/consents` returns the **union** of grants with their `source` (MANUAL or APPOINTMENT:{id}) — the UI displays both kinds in one list and labels the source (SR-036.7). The UI does not compute the union; the server does.
- Revoke maps to `DELETE /consents/{id}` for the specific grant; the UI must revoke **only the selected grant** (per-source model, SR-036.4) — it never issues a blanket revoke. For appointment-derived grants the patient may also decline the appointment (TASK-093); both paths deactivate only that grant.
- Cookie + CSRF via `ApiClient` (SR-031.3). This view is patient-only (own consents).

## Implementation detail

- Files to create:
  - `frontend/src/core/consent/ConsentPage.tsx` — route `/consents`; `useQuery(['me','consents'])`.
  - `frontend/src/core/consent/ConsentList.tsx` — unified list: doctor name, **source label** (Manual / From appointment on <date>), granted-at; a Revoke action per row (SR-036.7).
  - `frontend/src/core/consent/GrantConsentForm.tsx` — doctor select + Grant button; `useMutation` → `grantConsent`; invalidates `['me','consents']` (SR-008.1).
  - `frontend/src/core/consent/RevokeAction.tsx` — `ShellServices.confirmDialog` (states which doctor loses access) then `revokeConsent(grantId)`; on success invalidate `['me','consents']` (SR-008.3, SR-027.2).
  - `frontend/src/core/consent/index.ts` — route export.
- Libraries: React 18, TanStack Query, MUI (list, select, confirm dialog via ShellServices), React Router.
- Source labeling: each grant row shows whether it is manual or appointment-derived (and which appointment), so the patient understands why a doctor has access (SR-036.7). Appointment-derived grants can be revoked here as well as by declining the appointment (TASK-093) — both deactivate only that one grant.
- Immediacy (SR-008.4): after a successful revoke the UI invalidates the consent query and reflects removal at once; the server denies the doctor immediately because it reads live consent — the UI makes no caching promise that would mask this.
- Error cases: `400` on grant (e.g., already granted / unknown doctor) → field/message; `404` revoking a non-existent grant → refetch and message; `403` if a non-patient reaches the view → access denied.
- Edge cases / SR rules quoted:
  - SR-008 "Require confirmation for revoke (per NFR-009 via SR-027)" — revoke always goes through `confirmDialog`.
  - SR-036.7: "The patient's clinical data access view reflects the grant created by appointment confirmation alongside any manually created grants, so the patient has a complete, unified view of who has access to their data."
  - SR-036.4 (Case B): revoking/declining one source must not remove access held via another source — the UI revokes only the selected `grantId`.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + RTL + MSW), `frontend/src/core/consent/ConsentPage.test.tsx`:
  - MSW `GET /me/consents` returns one MANUAL and one APPOINTMENT grant → both rendered with correct source labels in one unified list (SR-036.7).
  - grant: select doctor, submit → `POST /consents`; list refetches and shows the new manual grant (SR-008.1).
  - revoke: click Revoke → confirm dialog appears; confirming issues `DELETE /consents/{id}` **for that grant only**; the other grant remains in the refetched list (SR-008.3, SR-036.4 Case B, SR-027.2).
  - revoke: cancelling the dialog issues **no** request (SR-027.2).
  - revoke an appointment-derived grant → only that grant removed; manual grant to the same doctor (if present) remains (SR-036.4).
  - `404`/`400` error paths → clear message, list reconciled.
- Each test names the SR AC it verifies.

## Acceptance criteria

- [x] The patient sees one unified list of all active grants, manual and appointment-derived, with the source labeled (SR-036.7).
- [x] The patient can grant a named doctor manual access; it appears in the list (SR-008 AC-1).
- [x] The patient can revoke any grant; revoke requires explicit confirmation and removes only the selected grant (SR-008 AC-3, SR-027.2, SR-036.4).
- [x] Revocation reflects immediately in the UI; the server enforces immediate denial (SR-008.4) — the UI adds no masking cache.
- [x] Cancelling the confirmation performs no state change (SR-027.2).

## Definition of Done

- [x] Lint + type-check pass (`eslint`/`tsc`)
- [x] Unit/component tests pass; coverage target met
- [x] Traceability matrix row updated (SR-008, SR-036.7 → TASK-094 → tests)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
