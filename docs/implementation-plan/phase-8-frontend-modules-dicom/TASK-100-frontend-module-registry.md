# TASK-100 — Frontend ModuleRegistry + FrontendModule interface + lazy chunk loading

- **Phase:** 8 — Frontend module system + DICOM viewer
- **Software item / unit:** SI-FE-MODREG / U-FEM-Registry
- **Implements:** SR-016 (AC-1 add module without editing existing modules; AC-2 enabled module presented in nav); ADR-0003, ADR-0005
- **Depends on:** TASK-080 (typed `ApiClient`), TASK-081 (app shell + `ShellServices` + router), TASK-082 (navigation) — must be merged first
- **Branch:** `enabler-story/fe-module-registry`
- **Status:** Not started

## Objective

Implement the **frontend half of the plugin mechanism** (SR-016): the `ModuleRegistry` that modules register a `FrontendModule` against, and the lazy code-split loading of each module's component via `React.lazy`. The registry is the single integration point so a new module is added by registering a `FrontendModule` — **no edits to existing modules or the shell** (SR-016.1). The DICOM viewer (TASK-102/103) is the first module registered against it. Nav gating against `GET /me/modules` is a separate, dependent unit (TASK-101).

## Interfaces to honor

Provides the `ModuleRegistry` and the `FrontendModule` interface **verbatim** from [12-interfaces.md](../../design/12-interfaces.md) §12.2 / api-design.md:

```ts
interface FrontendModule {
  moduleKey: string;
  navItem: NavItem;
  lazyComponent: () => Promise<{ default: React.ComponentType }>; // code-split chunk
}

interface ModuleRegistry {
  register(module: FrontendModule): void;
  list(): FrontendModule[];           // consumed by the shell nav gate (TASK-101)
  get(moduleKey: string): FrontendModule | undefined;
}
```

- `register(FrontendModule)` is the only way a module is added (SR-016.1); the shell renders `navItem` **only if** `moduleKey ∈ GET /me/modules` — that gate lives in TASK-101, not here. This unit does not itself call `/me/modules`.
- `lazyComponent` returns a dynamic `import()` so each module is a separate Vite chunk loaded on demand (ADR-0005, ADR-0003 code-splitting); the registry must not eagerly import module components.
- This unit touches **no PHI** and no module internals; it only stores registrations and exposes them.

## Implementation detail

- Files to create:
  - `frontend/src/modules/registry/types.ts` — `FrontendModule`, `NavItem`, `ModuleRegistry` interfaces (verbatim signatures above).
  - `frontend/src/modules/registry/ModuleRegistry.ts` — registry implementation: a map keyed by `moduleKey`; `register` rejects duplicate keys (dev-time error); `list`/`get` accessors.
  - `frontend/src/modules/registry/registerModules.ts` — the single composition point where built-in modules call `registry.register(...)`; the DICOM viewer registers its `FrontendModule` here (its `lazyComponent` is `() => import('../dicom-viewer/DicomViewerRoute')`, TASK-102). Adding a future module is one `register(...)` line here — no other file changes (SR-016.1).
  - `frontend/src/modules/registry/index.ts` — exports the singleton registry + types.
- Libraries: React 18 (`React.lazy`, `Suspense`), Vite dynamic `import()` for code-splitting, TypeScript.
- Lazy loading: the shell wraps a module route in `Suspense` with a fallback; `React.lazy(module.lazyComponent)` produces the component. Chunk-load failure shows a clear error surface (SR-027.3) and does not crash the shell.
- The registry is framework-pure (no network, no PHI); `GET /me/modules` enforcement is TASK-101.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit tests (Vitest), `frontend/src/modules/registry/ModuleRegistry.test.ts`:
  - `register(module)` then `get(key)`/`list()` return it (SR-016.1).
  - registering a duplicate `moduleKey` throws / is rejected (registry integrity).
  - `lazyComponent` is **not** invoked at registration time (no eager import) — asserts lazy semantics (ADR-0005).
- Component test (Vitest + RTL), `frontend/src/modules/registry/lazyLoad.test.tsx`:
  - a registered module's `lazyComponent` resolves under `Suspense` and renders its default export; a rejected import shows the error fallback, shell intact (SR-027.3).
- Composition test, `frontend/src/modules/registry/registerModules.test.ts`:
  - the DICOM viewer is registered with `moduleKey === 'dicom-viewer'` and a `navItem`; adding it required no edit to other modules (SR-016.1/AC-4 frontend side).
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] A `FrontendModule` matching the §12.2 interface verbatim can be registered via `ModuleRegistry.register` (SR-016.1).
- [ ] Adding a module is a single registration line; no existing module or shell file is edited (SR-016.1).
- [ ] Each module loads as a lazy code-split chunk via `React.lazy(lazyComponent)`; nothing is imported eagerly (ADR-0005, ADR-0003).
- [ ] `list()`/`get()` expose registrations for the nav gate (TASK-101) to consume.
- [ ] Chunk-load failure is handled with a clear error surface without crashing the shell (SR-027.3).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-016 → TASK-100 → tests)
