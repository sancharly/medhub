# ADR-0005: Backend plugins via Python entry points; frontend modules via dynamic registration + lazy chunks

## Status

Accepted

## Context

SR-016 requires a module/plugin mechanism through which new functionality is integrated **without modifying existing modules**, presented in the navigation/UI to authorized users, operating within a **defined access boundary** that obtains data **only through the platform's authorized interfaces**. SR-015 requires per-group enablement; UN-009/UN-010 require system-administrator control. The DICOM viewer (SR-017/SR-018) is the first module and must validate the mechanism. ADR-0001 fixes this as an **in-process** module mechanism (not separate services).

## Decision

Define a two-sided **Module Contract**:

**Backend (Python).** A module is a Python package that registers via a **`medhub.modules` entry point** (Python packaging entry points) exposing a `ModuleManifest`:

- `module_key` (stable identifier, e.g., `dicom-viewer`), `name`, `version`, `required_permissions`.
- A `register(router_registry, ...)` hook that mounts an APIRouter under `/api/v1/modules/{module_key}/...`.
- Modules **must not** import other modules' internals or touch the database directly for core entities. They access PHI only through injected **platform services** (`ClinicalDataService`, `AuthorizationService`, `AttachmentService`), so every data access passes the SR-005 authorization choke point — this *is* the "defined access boundary" (SR-016 AC-3).

**Frontend (TypeScript).** A module is an entry in a `ModuleRegistry` providing `{ moduleKey, navItem, lazyComponent }`. `lazyComponent` is a `React.lazy()` dynamic import, so each module is a separate code-split chunk loaded only when used. The shell renders a module's nav item only if the module is enabled for one of the user's groups (data from the backend `GET /api/v1/me/modules`).

**Enablement.** The core `ModuleRegistry` (DB-backed) records installed modules; `GroupModuleEnablement` records which groups have each module enabled (SR-015). The runtime `ModuleAccessGuard` (part of SR-005) denies any request to a module endpoint unless the module is enabled for one of the caller's groups (SR-015 AC-3/AC-4).

## Consequences

### Positive

- New module = new package + new registry entry; **zero edits to existing modules** (SR-016 AC-1).
- Forcing data access through platform services keeps the SR-005 authorization and SR-023 audit guarantees intact even for third-party modules (SR-016 AC-3).
- Frontend lazy chunks keep initial load light, helping SR-026 budgets and SR-020 mobile performance.
- Enablement is pure data (groups × modules), so the sysadmin UI (UN-009) is straightforward and auditable (SR-023 AC-4).

### Negative

- In-process modules share the runtime; a crashing module can affect the host (accepted per ADR-0001; mitigated by treating modules as trusted, reviewed code at MVP — no untrusted third-party sandboxing yet).
- The platform-service interface is a hard compatibility contract; changing it is a breaking change for modules (versioned via `ModuleManifest.version` and API `/v1`).

### Neutral

- "Plugin" is build/deploy-time installed (package present in the image) and **runtime-enabled** per group; it is not hot-loaded from arbitrary uploads (a deliberate security simplification for the MVP — see section 11 risks/technical debt in the Arc42 doc).

## Alternatives Considered

**Separately deployed microservice modules.** Rejected per ADR-0001 (consistency, audit, operational cost).

**Hot-loadable uploaded plugins (arbitrary code at runtime).** Rejected for the MVP: running untrusted uploaded code inside a PHI system is a severe security risk (NFR-007) with no requirement demanding it; SR-016 only requires adding modules without modifying existing ones, which package-level installation satisfies.

**Iframe/microfrontend isolation per module.** Rejected for the MVP as over-engineering; lazy-loaded React chunks with a typed registry meet SR-016 with far less complexity. Revisit if untrusted modules are ever allowed.

## References

- Requirements: UN-009, UN-010, SR-005, SR-015, SR-016, SR-017, SR-018, SR-023
- Related: ADR-0001, ADR-0006, ADR-0008
