# TASK-092 — Clinical entries view/create + attachment upload

- **Phase:** 7 — Frontend core views
- **Software item / unit:** SI-FE-CORE / U-FEC-ClinicalEntries
- **Implements:** SR-012 (AC-1/2/3 create entry, required fields, author from session), SR-013 (AC-1/3 attach files incl. DICOM, retrieve attachments); SR-006/SR-007 (read scope, inherited from server); ADR-0003, ADR-0008
- **Depends on:** TASK-091 (doctor patient list — entry point), TASK-066 (clinical-entries + attachments API endpoints, SI-API) — must be merged first
- **Branch:** `feature/fe-clinical-entries`
- **Status:** Not started

## Objective

Build the **clinical record** view for a patient: list the patient's clinical entries in reverse-chronological order, let a doctor create a new entry (required fields), and upload one or more attachments (including DICOM) to an entry. Patients see their own record read-only (SR-007); doctors see/create on authorized patients (SR-006, SR-012). Attribution (authoring doctor) is **server-derived from the session** and never sent by the client (SR-012.3). DICOM attachments here are the data the viewer module opens (TASK-102, via the module byte endpoint).

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2) and `ShellServices`:

```ts
// list (authz server-side, SR-006/007)
apiClient.listClinicalEntries(patientId);                 // GET /patients/{id}/clinical-entries
// create — body carries date/time, description; NOT the author (server sets it, SR-012.3)
apiClient.createClinicalEntry(patientId, { occurredAt, description });  // POST /patients/{id}/clinical-entries
// attach a file to an entry (multipart)
apiClient.uploadAttachment(entryId, file);                // POST /clinical-entries/{id}/attachments
// download/open an attachment (authorized stream)
apiClient.getAttachmentUrl(attachmentId);                 // GET /attachments/{id}
```

- The create request body **must not** include an `author`/`doctorId` field — authorship comes from the authenticated session server-side (SR-012.3). The UI shows the author returned by the server, read-only.
- All four calls are server-authorized (SR-005); the UI relies on the server for scope and never assumes access (SR-031.5). Cookie + CSRF via `ApiClient`; multipart upload is also CSRF-protected (SR-031.3).
- DICOM bytes for viewing are **not** fetched here — the viewer module fetches via `GET /api/v1/modules/dicom-viewer/studies/{attachmentId}` (TASK-102). This view only links an attachment to the viewer when it is a DICOM object and the module is enabled.

## Implementation detail

- Files to create:
  - `frontend/src/core/clinical/ClinicalEntriesPage.tsx` — route `/patients/:patientId/clinical-entries`; `useQuery(['clinicalEntries', patientId])` for the list.
  - `frontend/src/core/clinical/ClinicalEntryList.tsx` — reverse-chronological list (date/time, author, description, attachments).
  - `frontend/src/core/clinical/CreateEntryForm.tsx` — MUI form (date/time picker, description textarea); `useMutation` → `createClinicalEntry`; invalidates `['clinicalEntries', patientId]` on success. Doctor-only (form hidden for patient role; server still authoritative).
  - `frontend/src/core/clinical/AttachmentUpload.tsx` — file input (multiple), `useMutation` → `uploadAttachment`; progress UI; accepts DICOM and other formats (SR-013.1). Upload time is excluded from the 3 s budget (SR-026.2).
  - `frontend/src/core/clinical/AttachmentItem.tsx` — per-attachment row; download/open link; if DICOM and the viewer module is enabled (from `GET /me/modules`, TASK-101), an "Open in viewer" action routes to the DICOM module route with the `attachmentId`.
  - `frontend/src/core/clinical/index.ts` — route export.
- Libraries: React 18, TanStack Query (`useQuery`/`useMutation`), MUI (form controls, list, file input), React Router.
- Validation (client convenience only; server authoritative, SR-031.5): description non-empty, date/time present. Server `400 /errors/validation-error` field errors are mapped onto the form fields (SR-027.3).
- Error cases: `403 /errors/forbidden` (not authorized to patient) → the route should not normally be reachable, but render an access-denied surface, no data; `400` → field-level errors; upload failure → retry affordance.
- Edge cases / SR rules quoted:
  - SR-012 AC-2: "records date/time, patient, authoring doctor, and a description; the system rejects an entry missing any of these" — client requires date/time + description; patient is the route param; author is server-set.
  - SR-012 AC-3: "authoring doctor is set from the authenticated user and cannot be spoofed by the client" — no author field in the request.
  - SR-013 AC-1: "attach one or more files … including DICOM image files" — multi-file upload, DICOM accepted.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + RTL + MSW), `frontend/src/core/clinical/ClinicalEntriesPage.test.tsx`:
  - MSW returns entries → list renders date/time, author, description in reverse-chronological order (SR-012 AC-4, SR-006/007).
  - create form: submit with date/time + description → `POST /patients/{id}/clinical-entries` issued; **assert the request body contains no author/doctorId** (SR-012 AC-3); list refetches (SR-012 AC-1).
  - create form: empty description / missing date-time → client blocks submit and/or server `400` field errors mapped to fields (SR-012 AC-2, SR-027.3).
  - attachment upload: select two files (one DICOM) → two `POST /clinical-entries/{id}/attachments` requests; DICOM accepted (SR-013 AC-1).
  - DICOM attachment with viewer module enabled → "Open in viewer" action present and routes with `attachmentId`; with module disabled → action absent (handoff to TASK-101/102).
  - patient role: create form not rendered; list still visible (SR-007 read-only).
  - `403` → access-denied surface, no data leaked.
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] A doctor can create a clinical entry on an authorized patient with date/time + description; the request carries no client-supplied author (SR-012 AC-1/2/3).
- [ ] A saved entry appears in the patient's history list (SR-012 AC-4).
- [ ] A doctor can upload one or more attachments, including DICOM, to an entry (SR-013 AC-1).
- [ ] An authorized user can open/download an attachment; DICOM attachments offer "Open in viewer" only when the module is enabled (SR-013 AC-3, SR-015/016 gating via TASK-101).
- [ ] Patients see their own record read-only; doctors see/create only on authorized patients — scope enforced server-side, UI never widens (SR-006/007, SR-031.5).
- [ ] Validation and error states show clear, actionable, field-level messages (SR-027.3).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-012, SR-013 → TASK-092 → tests)
