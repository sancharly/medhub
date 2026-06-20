# ADR-0003: TypeScript + React (Vite) responsive SPA

## Status

Accepted

## Context

The product is browser-delivered with no client install (UN-001, SR-001), must work on the current stable Safari, Firefox, Chrome and Edge (NFR-001, SR-019), must be responsive across phone/tablet/desktop (NFR-003, SR-020), must be usable with minimal training (NFR-009, SR-027), and must host pluggable feature modules in its navigation/UI (SR-016). The first module, the DICOM viewer (SR-017/SR-018), requires a mature in-browser medical-imaging library. The frontend will necessarily be a JS/TS framework (the stakeholder's Python preference applies to the backend).

## Decision

Build a **single-page application in TypeScript using React 18**, bundled with **Vite**. Use **React Router** for navigation, **TanStack Query** for server-state/data fetching, and a **component library with accessible, responsive primitives (MUI)** to accelerate consistent, responsive, usable UI (SR-020, SR-027). Frontend feature modules are registered dynamically and loaded as lazy code-split chunks (see ADR-0005). The DICOM viewer module uses **Cornerstone3D** (see ADR-0008).

TypeScript is mandatory (no plain JS) so the SPA shares typed contracts with the backend's OpenAPI schema via generated client types.

## Consequences

### Positive

- React + Cornerstone3D is the de-facto stack for web DICOM viewers; the OHIF viewer is built on it — directly de-risks SR-017/SR-018.
- Vite gives fast builds and native ES-module code-splitting, enabling per-module lazy chunks for the plugin mechanism (SR-016, ADR-0005).
- TypeScript end-to-end types from the OpenAPI contract reduce interface-mismatch defects across the SR-005 authorization boundary and all API calls (NFR-006 traceability of interfaces).
- Large ecosystem of accessible, responsive components supports NFR-003/NFR-009 with less bespoke code.
- Standards-based (ES2020, fetch, Web Workers, WebGL) → cross-browser by default (SR-019); avoids browser-proprietary APIs.

### Negative

- SPA adds a build/deploy step and a second language to the codebase (TS alongside Python).
- Client-side rendering means access control must never be enforced in the client alone — explicitly mandated server-side (SR-031 AC-5); the SPA only hides UI it isn't authorized to show.
- WebGL DICOM rendering must be verified per-browser (SR-019) including Safari quirks.

### Neutral

- Requires a documented browser support matrix and cross-browser test pass each release (SR-019 AC-3).

## Alternatives Considered

**Angular.** Strong, opinionated, good for large teams and regulated apps. Rejected: heavier learning curve for a small team and weaker alignment with the Cornerstone3D/OHIF imaging ecosystem, which is React-centric.

**Vue.** Viable and approachable. Rejected: smaller medical-imaging ecosystem; Cornerstone3D integration examples are predominantly React.

**Server-rendered HTML (e.g., Django templates / HTMX).** Would reduce JS surface and unify on Python, but cannot host the interactive WebGL DICOM viewer (SR-018) as a first-class module and complicates the rich, responsive, module-driven UI. Rejected.

## References

- Requirements: UN-001, SR-001, SR-016, SR-017, SR-018, SR-019, SR-020, SR-027, SR-031; NFR-001, NFR-003, NFR-009
- Related: ADR-0005 (module mechanism), ADR-0008 (DICOM viewing)
