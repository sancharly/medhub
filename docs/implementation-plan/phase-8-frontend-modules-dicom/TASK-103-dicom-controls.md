# TASK-103 — DICOM viewer controls

- **Phase:** 8 — Frontend module system + DICOM viewer
- **Software item / unit:** SI-MOD-DICOM-FE / U-DICOMFE-Controls
- **Implements:** SR-018 (AC-1 window level/contrast; AC-2 zoom in/out; AC-3 pan; AC-4 slice navigation for volumetric studies; AC-5 consistent across browsers); ADR-0008
- **Depends on:** TASK-102 (Cornerstone3D viewport + rendering engine) — must be merged first
- **Branch:** `feature/dicom-controls`
- **Status:** Not started

## Objective

Add the **interactive controls** to the DICOM viewer (TASK-102): window level/contrast adjustment, zoom in/out, pan, and slice navigation for volumetric multi-slice studies. Controls use Cornerstone3D's built-in tools (`@cornerstonejs/tools`, ADR-0008) so each updates the displayed image consistently and predictably (SR-018). Slice navigation must show the correct slice for the indicated index — a safety-relevant correctness property (SR-018 risk analysis), verified in system testing (TASK-111).

## Interfaces to honor

Operates on the Cornerstone3D viewport created in TASK-102; adds tools via `@cornerstonejs/tools`:

```ts
// @cornerstonejs/tools: WindowLevelTool, ZoomTool, PanTool, StackScrollTool (slice nav)
// bound to mouse/touch + on-screen control affordances; act on the TASK-102 viewport/toolGroup
```

- Controls act **only** on the already-loaded, already-authorized image data from TASK-102 — they perform no new byte fetch and no PHI access beyond what the viewport already holds (the authorized bytes from the module endpoint). No new API calls.
- Controls must behave consistently across the four supported browsers (SR-018 AC-5, SR-019); WebGL-backed, standards-based (ADR-0008, §8.8).

## Implementation detail

- Files to create / modify (within `frontend/src/modules/dicom-viewer/`):
  - `tools.ts` — register and configure the Cornerstone3D tool group for the viewport: `WindowLevelTool` (level/contrast, SR-018.1), `ZoomTool` (SR-018.2), `PanTool` (SR-018.3), `StackScrollTool` / volume slice scroll (SR-018.4); bind primary/secondary mouse, wheel, and touch gestures.
  - `ViewerControls.tsx` — on-screen MUI control bar: window/level presets + sliders, zoom in/out buttons, pan toggle, and a slice scrubber + prev/next for volumetric studies (showing current slice index / total). Wired to the tool group so on-screen controls and direct interaction stay in sync.
  - `DicomViewport.tsx` (modify, TASK-102) — attach the tool group from `tools.ts` to the viewport; render `<ViewerControls>`. Slice controls render **only** for volumetric (multi-slice) series; single-image/X-ray hides slice navigation.
- Libraries (exact): `@cornerstonejs/tools` (with `@cornerstonejs/core` from TASK-102), React 18, MUI controls.
- Consistency (SR-018 AC-1–4): each control updates the displayed image predictably; window/level changes re-render with the new VOI; zoom/pan adjust the camera; slice nav changes the displayed slice. Slice index shown to the user must match the slice rendered (safety, SR-018 risk control).
- Cross-browser (SR-018 AC-5, SR-019): no browser-proprietary input APIs; verified in the cross-browser system-test pass (TASK-111).
- Edge cases / SR rules quoted:
  - SR-018.4: "For a volumetric multi-slice study, the user can navigate forward and backward through slices, and the displayed slice changes accordingly." — prev/next + scrubber, bounded at first/last slice.
  - SR-018 risk control: "Verify each control's behavior … including slice-index correctness." — covered by TASK-111 system tests against expected output.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + RTL, Cornerstone3D tools mocked at the tool-group boundary), `frontend/src/modules/dicom-viewer/ViewerControls.test.tsx`:
  - window/level slider/preset change invokes the `WindowLevelTool` / viewport VOI update (SR-018.1).
  - zoom in / zoom out buttons invoke the zoom action with the expected direction (SR-018.2).
  - pan toggle activates the `PanTool` (SR-018.3).
  - volumetric series: next/prev and scrubber change the active slice index and the index display updates; bounded at first/last (SR-018.4).
  - single-image/X-ray: slice navigation controls are **not** rendered (SR-018.4 scope).
  - controls perform **no** API/byte fetch (operate on loaded data only).
- Slice-index correctness (displayed slice == indicated index) and cross-browser consistency (SR-018 AC-5) are verified as **system tests** in TASK-111 (Safari/Firefox/Chrome/Edge), per the SR-018 risk control.
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] The user can adjust window level/contrast and the image updates accordingly (SR-018.1).
- [ ] The user can zoom in and out (SR-018.2) and pan when zoomed (SR-018.3).
- [ ] For volumetric studies the user can navigate forward/backward through slices and the displayed slice changes; index display matches the rendered slice (SR-018.4).
- [ ] Slice navigation is shown only for multi-slice series; single images hide it (SR-018.4 scope).
- [ ] Controls perform no new byte/API fetch; they act on the loaded, authorized data only.
- [ ] Controls behave consistently across Safari/Firefox/Chrome/Edge (SR-018 AC-5) — verified in TASK-111.

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Slice-index correctness + cross-browser consistency scheduled in the system-test matrix (TASK-111, SR-018)
- [ ] Traceability matrix row updated (SR-018 → TASK-103 → tests)
