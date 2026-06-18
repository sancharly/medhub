# TASK-091 — Doctor patient list

- **Phase:** 7 — Frontend core views
- **Software item / unit:** SI-FE-CORE / U-FEC-Patients
- **Implements:** SR-006 (AC-1 list of authorized patients; AC-3 no unauthorized patients exposed); ADR-0003
- **Depends on:** TASK-080 (typed `ApiClient`), TASK-081 (app shell + routing), TASK-082 (navigation) — must be merged first
- **Branch:** `feature/fe-patients`
- **Status:** Not started

## Objective

Build the doctor's **patient list** view: the entry point from which a doctor navigates into a specific patient's clinical record (TASK-092). The list contains exactly the patients the doctor is authorized for — the server returns only authorized patients (deny-by-default, SR-005/SR-006), so the UI displays whatever the API returns and never widens it. Traces to SR-006 AC-1/AC-3.

## Interfaces to honor

Consumes the typed `ApiClient` ([12-interfaces.md](../../design/12-interfaces.md) §12.2) and `ShellServices`:

```ts
// list authorized patients — server scopes to the doctor's active grants (SR-006)
const patients = await apiClient.listAuthorizedPatients();   // generated from OpenAPI
// navigate into a patient (handled by ShellServices/router)
shell.navigate(`/patients/${patientId}/clinical-entries`);
```

- The patient list is **server-scoped** to the authenticated doctor's active consent grants (union of manual + appointment, SR-036). The frontend performs **no client-side authorization** (SR-031.5) — it must not filter or infer a wider set than the API returns and must not assume access to any patient id not in the response.
- Cookie + CSRF handled by `ApiClient` (SR-031.3).

> Note: the API source for the authorized-patient listing is the patients/clinical resource scoped to the doctor (api-design.md "Clinical records & attachments" / the doctor's scoped patient projection). If the backend exposes the listing under a specific path, this view binds to the generated client method for that path verbatim; it introduces no new endpoint.

## Implementation detail

- Files to create:
  - `frontend/src/core/patients/PatientListPage.tsx` — route component; `useQuery(['patients'])` → authorized patients.
  - `frontend/src/core/patients/PatientRow.tsx` — presentational row (name, surname, DOB) with a link into the clinical record.
  - `frontend/src/core/patients/index.ts` — route export; register `/patients` in the shell router (doctor-only nav; nav visibility is role-driven by the shell).
- Libraries: React 18, TanStack Query, MUI `DataGrid`/`List`, React Router.
- Empty state: a doctor with no authorized patients sees a clear empty message (not an error). Loading → skeleton. Error → `ShellServices` error toast with `detail` (SR-027.3).
- Pagination if the list is large (cursor/page per api-design.md conventions); bounds the listing under the ~500-entries-per-patient performance assumption (10-§normal-load) but patient counts are small — page size default reasonable.
- Clicking a patient navigates to that patient's clinical-entries route (TASK-092). The view itself reads **no clinical data**, only patient identity fields.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + RTL + MSW), `frontend/src/core/patients/PatientListPage.test.tsx`:
  - MSW returns 3 authorized patients → all 3 rendered with name/surname (SR-006 AC-1).
  - MSW returns empty list → empty-state message, no error (SR-006 AC-1 edge).
  - the component renders exactly the patients the API returned and performs no client-side widening/filtering (SR-006 AC-3, SR-031.5) — assert the rendered set equals the mocked set.
  - clicking a row navigates to `/patients/{id}/clinical-entries` (integration with router).
  - `500 problem+json` → error surface (SR-027.3).
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] A doctor can retrieve and view the list of patients they are authorized for (SR-006 AC-1).
- [ ] The view renders exactly the server-returned set; no client-side authorization or widening (SR-006 AC-3, SR-031.5).
- [ ] Selecting a patient navigates into that patient's clinical record (handoff to TASK-092).
- [ ] Empty, loading, and error states are handled with clear messaging (SR-027.3).
- [ ] Responsive layout, no horizontal scroll of primary content (SR-020).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-006 → TASK-091 → tests)
