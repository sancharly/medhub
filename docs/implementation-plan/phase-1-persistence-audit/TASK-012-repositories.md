# TASK-012 — Typed repositories

- **Phase:** 1 — Persistence & audit
- **Software item / unit:** SI-PERSIST / U-PER-Repos
- **Implements:** SR-031
- **Depends on:** TASK-011 (must be merged first)
- **Branch:** `feature/persist-repositories`
- **Status:** Not started

## Objective

Provide typed repository classes that are the **only** way other items read/write core entities, using SQLAlchemy 2.x ORM constructs exclusively (parameterized queries) so no string-concatenated SQL exists anywhere (SR-031.1). Repositories encapsulate persistence behind typed method signatures, keeping the SQL-injection attack surface closed and giving higher items a stable, mockable boundary.

## Interfaces to honor

- Provides the `repositories` interface listed in [12-interfaces.md](../../design/12-interfaces.md) (provider SI-PERSIST): "typed repository methods, parameterized queries (SR-031.1)", consumed by all data items.
- Per dependency rule 12.3.3, **only SI-PERSIST talks to PostgreSQL** — all DB access for core entities goes through these repositories; other items never construct SQL or open sessions ad hoc.
- Must **not** embed authorization decisions (that is SI-AUTHZ via `AuthorizationService`), business rules, or audit calls — repositories are persistence-only. Must **not** expose any raw-SQL or string-interpolation method.

## Implementation detail

- Files to create under `backend/app/db/repositories/`:
  - `base.py` — `Repository[ModelT]` generic with typed CRUD primitives (`get`, `list`, `add`, `delete`) built only from SQLAlchemy `select()`/ORM expressions (no `text()` with interpolation; if `text()` is ever needed it must use bound parameters).
  - One repository per aggregate, with explicit typed methods used by later phases:
    - `account_repo.py` — `get_by_id`, `get_by_email`, `list`, `add`; email lookups parameterized (supports SR-003/SR-032 uniqueness reads).
    - `appointment_repo.py` — `get`, `add`, `list_for_doctor`, `list_for_patient` (SR-010/SR-011 scoping support — scoping decision stays in higher layers).
    - `clinical_repo.py`, `attachment_repo.py`, `consent_repo.py`, `group_repo.py`, `module_repo.py`, `audit_repo.py` (insert-only; consumed by TASK-014), `anonymized_dataset_repo.py`.
  - `session.py` — SQLAlchemy `Session`/engine factory reading `database_url` from `Settings` (TASK-003); a FastAPI-style dependency provider for request-scoped sessions (transaction per request).
- Libraries (exact stack): SQLAlchemy 2.x. ORM-only; typed with `Mapped`/generics for `mypy --strict`.
- Config keys: `database_url` (via `Settings`).
- Error cases: not-found returns `None` (caller maps to `404 /errors/not-found`); integrity violations (unique/FK) propagate to be mapped by the API layer (e.g. `409 /errors/conflict`). Repositories raise no HTTP errors.

## Tests (write first — TDD, CLAUDE.md §4)

- `backend/tests/db/test_repositories.py` (ephemeral PostgreSQL):
  - CRUD round-trips per repository (add → get → list → delete) return correctly typed objects.
  - `account_repo.get_by_email` with an adversarial input containing SQL metacharacters (e.g. `"x' OR '1'='1"`) returns no spurious rows — demonstrates parameterization (SR-031.1).
  - List/scoping methods return only matching rows (e.g. `list_for_doctor` excludes other doctors' appointments).
- `backend/tests/db/test_no_raw_sql.py`: a static guard (grep/AST over `backend/app`) asserting there is **no string-concatenated/f-string SQL** and any `text()` usage binds parameters (SR-031.1 "no string-concatenated SQL present").
- Each test references SR-031.1.

## Acceptance criteria

Distilled from SR-031:

- [ ] All entity persistence goes through typed repositories using SQLAlchemy ORM/parameterized queries; no string-concatenated SQL anywhere in the codebase (SR-031.1).
- [ ] Repository methods are fully typed and pass `mypy --strict`.
- [ ] Adversarial input to lookup methods cannot alter query logic (parameterization verified by test).
- [ ] Repositories contain no authorization, business, or audit logic (clean persistence boundary).
- [ ] Sessions/transactions are request-scoped via a DI provider; only SI-PERSIST opens DB sessions for core entities (rule 12.3.3).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy --strict`)
- [ ] Unit/integration tests pass; coverage target met; no-raw-SQL guard green
- [ ] OpenAPI regenerated and re-linted (N/A)
- [ ] Audit events emitted for security-relevant actions (N/A — persistence layer; audit writer is TASK-014)
- [ ] Traceability matrix row updated (SR-031 → TASK-012 → repository/no-raw-SQL tests)
- [ ] Security review completed (N/A here; the auth/session SR-031.6 review gate applies to later auth tasks)
