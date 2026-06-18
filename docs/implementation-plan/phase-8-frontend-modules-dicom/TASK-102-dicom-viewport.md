# TASK-102 — Cornerstone3D viewport

- **Phase:** 8 — Frontend module system + DICOM viewer
- **Software item / unit:** SI-MOD-DICOM-FE / U-DICOMFE-Viewport
- **Implements:** SR-017 (AC-1 open & display; AC-2 CT/MRI/X-ray; AC-3 slice ordering; AC-4 modality + VOI LUT scaling + default window/level; AC-5 enabled + authorized only), SR-026.3 (initial image < 10 s); ADR-0008, ADR-0005, ADR-0003
- **Depends on:** TASK-100 (`ModuleRegistry` / `FrontendModule`), TASK-073 (DICOM module backend byte endpoint) — must be merged first
- **Branch:** `feature/dicom-viewport`
- **Status:** Not started

## Objective

Implement the **DICOM viewer module frontend** — the first module and the safety-critical rendering function (NFR-005). It initializes Cornerstone3D, fetches DICOM bytes **only** from the authorized module endpoint, parses them, applies modality and VOI LUT for correct pixel scaling and a sensible **default window/level from the DICOM tags**, orders slices for volumetric series, and renders the **initial image within 10 s** (SR-026.3). It lives in `frontend/src/modules/dicom-viewer/` and registers a `FrontendModule` with the registry (TASK-100). Interactive controls are TASK-103. Rendering correctness is verified against reference images in system testing (TASK-111, SR-017 risk control).

## Interfaces to honor

Registers a `FrontendModule` (TASK-100, §12.2) and consumes the typed `ApiClient`:

```ts
// FrontendModule registered in registerModules.ts (TASK-100):
export const dicomViewerModule: FrontendModule = {
  moduleKey: 'dicom-viewer',
  navItem: { /* label, icon, path: '/modules/dicom-viewer' */ },
  lazyComponent: () => import('./DicomViewerRoute'),   // code-split chunk (ADR-0005)
};

// bytes — ONLY from the authorized module endpoint (never object storage / other APIs):
apiClient.getDicomStudyBytes(attachmentId);   // GET /api/v1/modules/dicom-viewer/studies/{attachmentId}
```

- The viewer obtains DICOM bytes **only** through `GET /api/v1/modules/dicom-viewer/studies/{attachmentId}` (api-design.md "Module endpoints", ADR-0008) — it must **not** read object storage directly or call any other attachment path. That endpoint enforces `ModuleAccessGuard` (enablement) then `AuthorizationService` (consent) server-side (runtime view 6.4, SR-017.5); a non-enabled or non-authorized user receives `403` and the viewer shows an access-denied surface, no image (SR-017 AC-5).
- The module touches PHI only via this authorized endpoint — consistent with the module-boundary invariant (SR-016.3) on the frontend side.
- Reached only when `dicom-viewer ∈ GET /me/modules` (nav gating, TASK-101); deep-link still gated client + server.

## Implementation detail

- Files to create (module package directory `frontend/src/modules/dicom-viewer/`):
  - `DicomViewerRoute.tsx` — `default` export (the `lazyComponent` target); reads `attachmentId` from route/query; renders `<DicomViewport>`; handles access-denied (`403`) and not-found (`404`) surfaces.
  - `csInit.ts` — one-time Cornerstone3D initialization: `@cornerstonejs/core` `init()`, register `@cornerstonejs/dicom-image-loader` (configure the WADO/local file loader for the bytes fetched from the module endpoint), set up the rendering engine. WebGL-backed (ADR-0008).
  - `DicomViewport.tsx` — creates a Cornerstone3D `RenderingEngine` + viewport (stack viewport for single/X-ray, volume viewport for volumetric CT/MRI), loads image ids derived from the fetched bytes, sets the camera/initial image, and renders. Applies **modality LUM/LUT and VOI LUT** (correct pixel scaling) and a **default window/level derived from the DICOM tags** (Window Center/Width, or computed default if absent) (SR-017 AC-4).
  - `imageIds.ts` — turns the fetched Part-10 bytes (and optional `?frame=`) into Cornerstone image ids; for a volumetric series, **orders slices** by ImagePositionPatient / InstanceNumber so the stack/volume is correctly ordered (SR-017 AC-3).
  - `modality.ts` — data-driven modality handling table (CT, MRI, X-ray in MVP scope, ADR-0008); a new modality is a table entry, not a re-architecture.
  - `index.ts` — exports `dicomViewerModule` (the `FrontendModule`).
  - `frontend/src/modules/registry/registerModules.ts` — add the single `registry.register(dicomViewerModule)` line (TASK-100; no other module edited, SR-016.1).
- Libraries (exact): `@cornerstonejs/core`, `@cornerstonejs/dicom-image-loader` (and `@cornerstonejs/tools` is wired in TASK-103 for controls); React 18 `Suspense`/lazy; TanStack Query for the byte fetch.
- Performance (SR-026.3, NFR-008, §8.9): fetch bytes for the **first slice/image first** and render it before loading the full volume — "initial rendered image < 10 s" is first-image, not full study (10-§normal-load, typical CT/MRI ~150–300 slices ~50–150 MB). Remaining slices load progressively in the background. Heavy volumetric load is deferred so initial interaction stays responsive.
- Correct rendering (safety, SR-017 AC-4): rely on Cornerstone3D's vetted modality/VOI LUT pipeline (ADR-0008) rather than hand-rolled scaling; default window/level taken from DICOM tags. Correctness is verified against reference CT/MRI/X-ray images in the system-test matrix (TASK-111).
- Error cases: `403` (not enabled or not authorized) → access-denied surface, no bytes rendered (SR-017 AC-5); `404` (unknown attachment) → not-found; non-DICOM/parse failure → clear error (SR-027.3); WebGL-incapable browser is out of the supported set (SR-019, runtime view 6.4) — show a clear unsupported-browser message.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + RTL + MSW, Cornerstone3D mocked at the rendering-engine boundary), `frontend/src/modules/dicom-viewer/DicomViewport.test.tsx`:
  - given mocked bytes for a single image, the viewport initializes Cornerstone3D and renders an image; **assert bytes are fetched only from `/api/v1/modules/dicom-viewer/studies/{attachmentId}`** and from no other path (SR-017 AC-1, SR-016.3, ADR-0008).
  - default window/level is taken from the DICOM Window Center/Width tags (or computed default when absent) and modality/VOI LUT applied (SR-017 AC-4) — assert the values passed to the viewport API.
  - a multi-slice series is ordered by position/instance number before display (SR-017 AC-3) — assert image-id ordering.
  - `403` response → access-denied surface, no image, no further byte requests (SR-017 AC-5).
  - `404` / non-DICOM bytes → not-found / parse-error surface (SR-027.3).
  - CT, MRI, and X-ray sample fixtures each render via the modality table (SR-017 AC-2).
- Module registration test: `dicomViewerModule.moduleKey === 'dicom-viewer'`, `lazyComponent` is a dynamic import (not eager), registered without editing other modules (SR-016.1).
- Reference-image rendering correctness (CT/MRI/X-ray vs. known reference) is performed as a **system test** in TASK-111 (SR-017 risk control), not a unit test.
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] The viewer opens and displays a valid DICOM image (SR-017 AC-1) for CT, MRI, and X-ray (SR-017 AC-2).
- [ ] Multi-slice volumetric series are loaded and ordered correctly (SR-017 AC-3).
- [ ] Modality + VOI LUT scaling and a default window/level derived from the DICOM tags are applied (SR-017 AC-4).
- [ ] Bytes are fetched **only** from `GET /api/v1/modules/dicom-viewer/studies/{attachmentId}`; no direct storage/other-path access (SR-016.3, ADR-0008).
- [ ] Only an enabled + authorized user can open an image; `403` yields an access-denied surface, no image (SR-017 AC-5, runtime view 6.4).
- [ ] The initial rendered image appears within 10 s for a typical study; remaining slices load progressively (SR-026.3) — budget verified in TASK-112.
- [ ] The viewer is a registered `FrontendModule` lazy chunk, added without editing other modules (SR-016.1, ADR-0005).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Reference-image rendering correctness scheduled in the system-test matrix (TASK-111, SR-017)
- [ ] Traceability matrix row updated (SR-017, SR-026.3 → TASK-102 → tests)
