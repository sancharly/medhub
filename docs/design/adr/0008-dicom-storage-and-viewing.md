# ADR-0008: DICOM stored as objects; viewing via Cornerstone3D in the browser

## Status

Accepted

## Context

The DICOM viewer is the first module and the proof of the plugin system (SR-016, SR-017, SR-018, UN-011). It must open CT/MRI/X-ray, render with correct pixel scaling, sensible default window/level and correct slice ordering for volumetric series (SR-017), and provide window/level, zoom, pan and slice navigation (SR-018). Rendering correctness is **safety-critical** (NFR-005, SR-017 risk analysis). Initial image must appear within 10 s for a typical study (SR-026 AC-3). Files arrive as clinical-entry attachments (SR-013) and must be access-controlled (SR-005) and encrypted at rest (SR-013 AC-4, SR-022). It must work across the four target browsers (SR-019).

## Decision

**Storage:** DICOM files are stored as encrypted objects in object storage (ADR-0009), referenced by `Attachment` metadata rows in PostgreSQL (ADR-0004). The backend never stores pixel data in the DB.

**Serving:** The backend exposes authorized, time-limited access to DICOM objects. For the MVP it streams DICOM Part-10 files (and, where beneficial, frames) through an authorized endpoint that enforces SR-005 on every request; the viewer fetches via the platform attachment interface, not directly from storage.

**Viewing:** Rendering is done **client-side in the browser** with **Cornerstone3D** (`@cornerstonejs/core`, `@cornerstonejs/tools`, `@cornerstonejs/dicom-image-loader`). Cornerstone3D parses DICOM, applies modality/VOI LUT for correct scaling and default window/level (SR-017 AC-4), orders slices for volumetric series (SR-017 AC-3), and provides built-in tools for window/level, zoom, pan and slice scroll (SR-018) using WebGL.

## Consequences

### Positive

- Cornerstone3D is the vetted, widely-used engine behind OHIF; using it (rather than hand-rolling rendering) directly addresses the safety/correctness risk in SR-017 and provides the exact SR-018 controls out of the box.
- Client-side WebGL rendering offloads pixel work from the Python backend (mitigating ADR-0002's CPU concern) and helps meet the 10 s budget (SR-026) since only bytes transit the network.
- Standards-based WebGL works on all four target browsers (SR-019); known Safari caveats are part of the cross-browser test pass.
- Access stays enforced: the viewer obtains bytes only through the authorized attachment endpoint (SR-005, SR-016 AC-3).

### Negative

- "Correct rendering" must be verified against reference images during system testing (SR-017 risk control) — Cornerstone3D reduces but does not remove this verification obligation (medical-device viewing function, NFR-005).
- Large volumetric studies stream many bytes to the client; mitigated by progressive/lazy slice loading and the 10 s budget being "initial rendered image", not full study.
- No server-side rendering fallback in the MVP (a browser without WebGL cannot view) — acceptable given the four modern target browsers all support WebGL.

### Neutral

- A full PACS/DICOMweb (WADO-RS/QIDO-RS) backend is **not** adopted for the MVP; the authorized attachment endpoint suffices. Migrating to DICOMweb later is additive and Cornerstone3D already speaks it.

## Alternatives Considered

**Server-side rendering (render to PNG on the backend).** Rejected: pushes heavy pixel processing onto the Python backend (latency, SR-026 risk), loses interactive client-side window/level performance, and is a worse fit for the controls in SR-018.

**Full PACS + DICOMweb server (e.g., Orthanc/dcm4chee).** Rejected for the MVP as over-engineering: introduces a second heavyweight data system and regulated surface; no requirement needs PACS interoperability yet. The model is kept compatible so this is a future, additive option.

**Hand-rolled WebGL/canvas renderer.** Rejected: re-implementing modality/VOI LUTs and volumetric ordering is exactly the safety risk SR-017 warns about; using a vetted library is the responsible choice.

## References

- Requirements: UN-011, SR-005, SR-013, SR-016, SR-017, SR-018, SR-019, SR-022, SR-026; NFR-005
- Related: ADR-0003, ADR-0005, ADR-0009
