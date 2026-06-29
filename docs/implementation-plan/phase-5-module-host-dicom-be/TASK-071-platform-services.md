# TASK-071 — PlatformServices facade (sole PHI path)

- **Phase:** 5 — Module host + DICOM backend
- **Software item / unit:** SI-MODHOST / U-MH-PlatformServices
- **Implements:** SR-016 (AC-3 modules obtain data only through platform's authorized interfaces), SR-005 (authorization choke point preserved), SR-023 (audit preserved); ADR-0005
- **Depends on:** TASK-070 (module discovery / contract), TASK-027 (`AuthorizationService` / API deps), TASK-044 (`ClinicalDataService`), TASK-046 (`AttachmentService.open`), TASK-014 (`AuthorizationService`/audit) — must be merged first
- **Branch:** `feature/platform-services`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Build the `PlatformServices` facade that is injected into every module's `register(...)` hook and is the **only** way a module touches PHI. By bundling `authorization`, `clinical`, `attachments`, and `audit`, all module data access necessarily passes the SR-005 authorization choke point and the SR-023 audit, even for future third-party modules. Traces to SR-016 AC-3, SR-005, SR-023.

## Interfaces to honor

Implements `PlatformServices` from [12-interfaces.md](../../design/12-interfaces.md) §12.1 / [api-design.md](../../specifications/api-design.md) **verbatim**:

```python
class PlatformServices:
    authorization: AuthorizationService   # authorize(actor, action, resource)
    clinical: ClinicalDataService         # read entries (authorized)
    attachments: AttachmentService        # fetch object bytes (authorized)
    audit: AuditService                   # append audit event
```

- This facade is the **sole** PHI path for modules (SR-016.3, §12.1 invariant). It exposes only the four bundled services; it must **not** expose repositories, the DB session, object-storage clients, or any other item's internals (§12.1 invariant: "a module must not access SI-PERSIST directly for core entities").
- The bundled services are the **same authorized instances** the core uses — the facade adds no bypass. `clinical.list_entries`, `attachments.open` already enforce `authorize(...)` internally (TASK-044/046), so a module calling them inherits deny-by-default (SR-005) and audit (SR-023) automatically.
- The facade carries the per-request actor context so a module's authorization decisions are made for the real caller, not the module.

## Implementation detail

- Files to create:
  - `backend/app/modules/platform_services.py` — `PlatformServices` dataclass/object bundling the four service instances; a factory `build_platform_services(...)` wired from FastAPI DI providers (TASK-027) so each is the authorized core instance.
  - `backend/app/api/deps.py` — a dependency that yields a request-scoped `PlatformServices` (current actor bound), consumed by module routers (TASK-072) (surgical addition).
- The facade is deliberately thin: no logic beyond holding references. Any "convenience" wrapper that re-fetches PHI without going through the authorized service is forbidden (would breach SR-016.3). Keep it minimal (CLAUDE.md §2).
- Module-boundary enforcement (verified in module integration tests, §12.1): a static/lint check or a test asserting the DICOM module imports nothing from `app.db`, `app.core.object_storage`, or other items' service modules — only from `app.modules.contract` / `platform_services`.
- Audit: no new events here; the facade ensures the underlying services audit. (`audit` is exposed so a module can record its own module-specific security-relevant events, SR-023.)
- Error cases: a module calling `clinical`/`attachments` for an unauthorized resource gets the same `403 /errors/forbidden` the core would raise — surfaced unchanged through the facade (SR-005 AC-4). No special-casing for modules.
- Edge cases: the facade is request-scoped (actor bound per request); it must not be a process-global that could leak one caller's authorization context into another's. Reusing it across requests is a bug the tests guard against.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/modules/test_platform_services.py`):
  - the facade exposes exactly `authorization`, `clinical`, `attachments`, `audit` and nothing else (SR-016.3 surface check).
  - `clinical.list_entries` via the facade for an **unauthorized** actor → `403`, no data, denied access audited (SR-005, SR-023) — proves the choke point holds through the facade.
  - `attachments.open` via the facade for an authorized actor → bytes returned and access audited (SR-013, SR-023).
  - the bundled instances are the same authorized core services (no bypass) (SR-016.3).
  - the facade is request-scoped: two requests with different actors get correctly-scoped authorization (no context bleed).
- Module-boundary test (`backend/tests/modules/test_module_boundary.py`): assert the DICOM module package (TASK-073) does not import `app.db.*`, object-storage clients, or other items' internals — only the contract/facade (§12.1 invariant, SR-016 AC-3).

## Acceptance criteria

- [x] `PlatformServices` bundles exactly `authorization`, `clinical`, `attachments`, `audit` per the §12.1 contract (SR-016.3).
- [x] It is the only PHI path exposed to modules; no repositories/DB session/object-storage client is reachable through it (SR-016.3 invariant).
- [x] PHI access through the facade enforces SR-005 authorization (deny-by-default) and SR-023 audit, identical to core access.
- [x] The facade is request-scoped with the correct per-request actor (no context bleed).
- [x] A module-boundary test proves the DICOM module accesses PHI only via the facade.

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + boundary tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (N/A — internal facade)
- [x] Audit events emitted for security-relevant actions (preserved via bundled services, SR-023)
- [x] Traceability matrix row updated (SR-016.3, SR-005, SR-023 → TASK-071 → tests)
- [x] Security review completed (PHI access boundary / authorization choke point — SR-031.6)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
