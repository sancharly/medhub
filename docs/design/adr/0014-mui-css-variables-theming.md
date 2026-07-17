# ADR-0014: MUI CSS-variables theming with native colorSchemes for light/dark

## Status

Accepted

## Context

SR-037 requires a single centralized design-token foundation for the whole frontend; SR-038 requires equivalent light and dark modes built from the same token structure with WCAG 2.1 AA contrast; SR-039 requires a chrome-visible toggle, OS-preference default, and client-side persistence. The frontend is a React 18 + Vite SPA using MUI v9 with Emotion (ADR-0003), with an existing single-mode theme in `frontend/src/core/theme/`. The restyle must be frontend-only (no backend/API change) and must not alter workflow behavior. Concrete token values (palettes, typography, radii, shadows, verified contrast ratios) are specified in design record ADD-001.

## Decision

Implement theming with **MUI v9's native CSS-variables + color-schemes mechanism**, keeping the existing stack (no Tailwind/shadcn migration):

- One `createTheme({ cssVariables: { colorSchemeSelector: "data" }, colorSchemes: { light: {...}, dark: {...} }, ... })` in `frontend/src/core/theme/theme.ts` is the **single token definition** (palette per scheme; shared typography, spacing, shape, shadows, component styleOverrides). Tokens are emitted as CSS variables scoped by a `data-*` color-scheme attribute on `<html>`.
- Global visual identity is applied through `theme.components` styleOverrides so screens consume tokens implicitly; screens reference `theme.palette.*` / `theme.vars.*` only, never raw values.
- Mode control via MUI `useColorScheme()`: `defaultMode: "system"` (follows `prefers-color-scheme` until an explicit choice), explicit choices persisted by MUI in `localStorage` (client-side only, no PHI).
- Flash-of-wrong-theme prevented by an inline pre-hydration script in `frontend/index.html` that sets the color-scheme attribute and a matching background color before the bundle loads (SPA equivalent of `InitColorSchemeScript`).
- Fonts self-hosted via Fontsource variable packages bundled by Vite (Manrope for headings, Inter for body/data) — no external CDN dependency.

## Consequences

### Positive

- Both modes are literally two value sets over one token structure — SR-038 AC-1 is enforced by the API shape, not by discipline.
- Switching modes swaps CSS variables via one attribute: instant, no reload, no React remount, no loss of in-progress input (SR-039 AC-2).
- System default + persistence come from MUI's maintained implementation instead of bespoke context/localStorage code.
- CSS variables make token usage inspectable in DevTools and testable (computed styles), aiding the visual-review and contrast verification SR-038 demands.
- No new dependencies beyond two Fontsource font packages.

### Negative

- `theme.palette` values become variable references in some code paths; tests or utilities that string-compare resolved colors may need `theme.colorSchemes.*` or `theme.vars.*` instead.
- Emotion styles that computed colors in JS (e.g. alpha() on palette values) need care with CSS-variable channels (`color-mix`/theme.vars pattern).
- The inline `index.html` script duplicates the storage-key/attribute convention and must stay in sync with the theme configuration (kept adjacent via a shared constant and covered by a test).

### Neutral

- Preference is per browser/device (localStorage) — accepted scope in SR-039.
- MUI default localStorage keys/attributes are used unless a collision appears; the constant lives in the theme module.

## Alternatives Considered

**Two separate `createTheme` objects + custom React context and manual localStorage.** The pre-v6 pattern. Rejected: duplicates the token structure (modes can drift, violating SR-038 AC-1), requires bespoke persistence/system-preference code MUI already provides, and re-renders the whole Emotion cache on switch.

**Hand-rolled CSS-variable sheet outside MUI.** Full control, framework-agnostic. Rejected: MUI components would need to be bridged to the custom variables piecemeal — exactly the partial-adoption inconsistency SR-037 forbids.

**Tailwind/shadcn design-token migration.** Rejected: replaces the working component layer (ADR-0003), massive regression surface for a restyle whose requirement is explicitly "no functional change".

## References

- Requirements: SR-037, SR-038, SR-039; UN-014, UN-015; NFR-003, NFR-009
- Related: ADR-0003 (frontend stack), ADD-001 (token values and contrast verification), TASK-149…TASK-153 (implementation)
