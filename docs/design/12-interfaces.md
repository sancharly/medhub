# 12 - Interfaces between Software Items

This section defines the interfaces between software items, as required by the software development plan. Two interface classes exist:

- **External interfaces** (system ↔ outside world) — specified in [`../specifications/api-design.md`](../specifications/api-design.md) (HTTP/JSON, OpenAPI 3.1) and section 03.
- **Internal interfaces** (item ↔ item, in-process) — specified here as method-level contracts. Items are Python packages; interfaces are abstract service classes injected via FastAPI DI. Frontend item interfaces are TypeScript module boundaries.

## 12.1 Internal backend interfaces

| Provider item | Interface                 | Consumers                                                            | Contract (key operations)                                                                                                                      |
|---------------|---------------------------|----------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| SI-AUTHZ      | `AuthorizationService`    | SI-API, SI-CLINICAL, SI-ATTACH, SI-APPT, SI-MOD-DICOM-BE, SI-MODHOST | `authorize(actor, action, resource) -> Decision` (raises on deny); `effective_access(doctor_id, patient_id) -> bool` (union of grants, SR-036) |
| SI-AUTHZ      | `ConsentService`          | SI-APPT, SI-API (consent endpoints)                                  | `grant(patient_id, doctor_id, source)`, `revoke(grant_id|source)`, `list_grants(patient_id)` (SR-008, SR-036)                                  |
| SI-AUTHZ      | `ModuleAccessGuard`       | SI-MODHOST, SI-API                                                   | `is_module_enabled(account_id, module_key) -> bool` (SR-015)                                                                                   |
| SI-AUTH       | `SessionService`          | SI-API, SI-IDENTITY (lifecycle), SI-WORKER                           | `create_session(account)`, `resolve(session_id) -> Session?`, `invalidate(session_id)`, `invalidate_all(account_id)` (SR-030, SR-034)          |
| SI-AUTH       | `PasswordService`         | SI-IDENTITY, SI-API                                                  | `validate_policy(account, password)`, `hash(password)`, `verify(hash, password)` (SR-025, SR-002)                                              |
| SI-AUDIT      | `AuditService`            | all security-relevant items                                          | `record(actor, action, target, outcome, ip)` append-only (SR-023)                                                                              |
| SI-CLINICAL   | `ClinicalDataService`     | SI-API, SI-MOD-DICOM-BE (via PlatformServices)                       | `list_entries(patient_id)`, `create_entry(...)` — all calls pre-authorized (SR-012, SR-006)                                                    |
| SI-ATTACH     | `AttachmentService`       | SI-API, SI-MOD-DICOM-BE, SI-CLINICAL                                 | `store(entry_id, file) -> Attachment`, `open(attachment_id) -> stream` (authorized) (SR-013)                                                   |
| SI-IDENTITY   | `AccountService`          | SI-API, SI-AUTH                                                      | `create(creator, data)`, `activate(token, password)`, `deactivate/reactivate/delete(account_id)`, `erase(account_id)` (SR-032/033/034/024)     |
| SI-GROUPS     | `GroupService`            | SI-API, SI-AUTHZ                                                     | `create_group`, `membership(...)`, `set_module_enabled(group_id, module_key, bool)`, `groups_of(account_id)` (SR-014, SR-015)                  |
| SI-APPT       | `AppointmentService`      | SI-API                                                               | `create(...)`, `confirm(id, patient)`, `decline(id, patient)`, `list_for(actor)` (SR-010, SR-035)                                              |
| SI-PERSIST    | repositories              | all data items                                                       | typed repository methods, parameterized queries (SR-031.1)                                                                                     |
| SI-WORKER     | task interface            | SI-IDENTITY, SI-APPT, SI-AUTH                                        | `send_activation_email(...)`, `send_appointment_notification(...)`, `propagate_session_kill(account_id)` (SR-033/035/034)                      |
| SI-MODHOST    | `PlatformServices` facade | all modules (SI-MOD-DICOM-BE, future)                                | bundles `authorization`, `clinical`, `attachments`, `audit` — the **only** way a module touches PHI (SR-016.3)                                 |
| SI-MODHOST    | `RouterRegistry`          | all modules                                                          | `mount(module_key, APIRouter)` under `/api/v1/modules/{key}` (SR-016)                                                                          |

### Module contract (provider: SI-MODHOST; implementer: each module)

```python
class ModuleManifest:
    module_key: str
    name: str
    version: str
    required_permissions: list[str]
    def register(self, registry: RouterRegistry, services: PlatformServices) -> None: ...
```

Invariants (verified in module integration tests):

- A module **must not** import another item's internals or access `SI-PERSIST` directly for core entities.
- All PHI access goes through `PlatformServices`, so SR-005 authorization and SR-023 audit always apply (SR-016.3).

## 12.2 Internal frontend interfaces

| Provider item   | Interface         | Consumers                       | Contract                                                                                               |
|-----------------|-------------------|---------------------------------|--------------------------------------------------------------------------------------------------------|
| SI-FE-APICLIENT | typed `ApiClient` | SI-FE-AUTH, SI-FE-CORE, modules | methods generated from OpenAPI; attaches session cookie + CSRF (SR-031.3)                              |
| SI-FE-MODREG    | `ModuleRegistry`  | SI-FE-SHELL, modules            | `register(FrontendModule)`; shell renders nav only if `moduleKey ∈ GET /me/modules` (SR-015, SR-016.2) |
| SI-FE-SHELL     | `ShellServices`   | SI-FE-CORE, modules             | navigation, confirmation dialog, error toast, layout slots (SR-027)                                    |

```ts
interface FrontendModule {
  moduleKey: string;
  navItem: NavItem;
  lazyComponent: () => Promise<{ default: React.ComponentType }>; // code-split chunk
}
```

## 12.3 Item dependency rules (enforced in review)

1. Data items (SI-CLINICAL, SI-ATTACH, SI-APPT, SI-IDENTITY, SI-GROUPS) **must** call `AuthorizationService` before returning protected data; they never re-implement access checks (SR-005, deny-by-default).
2. Security-relevant operations **must** call `AuditService` (SR-023).
3. Only SI-PERSIST talks to PostgreSQL; only SI-ATTACH talks to object storage; only SI-AUTH/SI-WORKER talk to Redis.
4. Modules depend **only** on `PlatformServices` / `ModuleRegistry` — never on other items directly (SR-016).
5. All cross-item interfaces are typed; the external contract is the OpenAPI document, expected to pass lint in CI (NFR-006).

> The machine-readable external contract (`/api/v1/openapi.json`) plus this section together constitute the "definition of interfaces between software items" output of the Architecture design activity.
