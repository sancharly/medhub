# TASK-115 — Deploy/run documentation + first-sysadmin bootstrap

- **Phase:** 9 — Integration, system testing, compliance hardening
- **Software item / unit:** (process / operational) — operator-facing build, install, deploy, and seed procedure
- **Implements:** the software-development-plan **Coding activities** output "Build, installation, and deployment instructions (README.md, INSTRUCTIONS.md, INSTALL.md, DEPLOY.md)"; supports NFR-006 (version-controlled lifecycle outputs); first-sysadmin bootstrap closes the SR-032 chicken-and-egg (every account is created by authorized personnel — the first sysadmin needs a seed path)
- **Depends on:** TASK-004 (Docker Compose topology + reverse proxy — the deployable stack the docs describe) must be merged first; references TASK-003 (config/secrets) for env keys, TASK-030/032 (account create + activation) for the seed semantics
- **Branch:** `enabler-story/deploy-docs-bootstrap`
- **Status:** Not started

## Objective

Produce the operator-facing **README / INSTALL / DEPLOY** documentation and a **first-sysadmin bootstrap/seed procedure** so a fresh deployment can be built, run, and brought into a usable initial state via Docker Compose. The MVP runs as a single-host Docker Compose stack behind a TLS reverse proxy (ADR-0010, TASK-004); these are the controlled build/installation/deployment instructions the development plan's Coding activity requires (NFR-006). Because every account is created by authorized personnel (SR-032), a fresh system has no one to create the first administrator — this task provides the **bootstrap seed** that creates the initial sysadmin securely, after which all further accounts use the normal create→activate flow.

## Interfaces to honor

- Describes the deployment topology realized in TASK-004 / [07-deployment-view.md](../../design/07-deployment-view.md): reverse proxy terminates TLS with HTTP→HTTPS redirect + HSTS; SPA + API reachable only through it; Postgres/Redis/MinIO/Celery on the internal network (SR-001, SR-022).
- Consumes the `Settings` contract and `infra/.env.example` keys from TASK-003 (`database_url`, `redis_url`, `object_store_*`, `smtp_*`, signing/crypto keys) — secrets are env-injected at deploy time, never committed (NFR-007, §8.11).
- The bootstrap creates the first sysadmin **through the same account/password mechanisms** (`AccountService`, Argon2id `PasswordService`, policy-compliant credential) — it must not introduce a parallel, weaker credential path or a hard-coded password.
- Documents that **hosting region / data residency is a deploy-time operator choice** (ADR-0010, §8.11): no region is pinned and no non-EU-only managed service is required, so the operator can host EU-only for GDPR residency.

This task must **not**: modify the dev plan, README task index/template, or requirement files beyond authoring the operator docs; embed real secrets or a default/hard-coded admin password in any committed file; create a bootstrap that bypasses the password policy or audit (SR-025, SR-023); add application endpoints.

## Implementation detail

- Files to create / modify:
  - `README.md` (root) — project overview, prerequisites (Docker + Compose), quick-start to bring up the stack, link to INSTALL/DEPLOY; states the supported-browser matrix (SR-019) and that data residency is an operator choice (ADR-0010). (Augments, does not restructure, any existing README content.)
  - `INSTALL.md` — local/dev install: clone, copy `infra/.env.example` → `.env` and fill required secrets, generate dev self-signed certs, `docker compose up`, run migrations (Alembic), verify health endpoint.
  - `DEPLOY.md` (or `infra/DEPLOY.md`) — production-style deploy: env/secret provisioning, TLS cert provisioning at the proxy, encrypted DB volume + MinIO SSE confirmation (SR-022), backup/restore notes for Postgres + object store, upgrade/migration procedure, and the EU-only residency note (ADR-0010).
  - `infra/bootstrap_sysadmin.py` (or a documented one-shot Compose command / management entry point) — the **first-sysadmin seed**: creates exactly one initial sysadmin via `AccountService` with a policy-compliant password supplied **at runtime** (prompt or env-injected secret, never committed), audited via `AuditService` (SR-023); idempotent/refuses to run if any sysadmin already exists (so it cannot be used to silently add admins later); documents that all subsequent accounts use the normal create→activation-email flow (SR-032, SR-033).
  - Document the bootstrap procedure in INSTALL/DEPLOY: when to run it, how the credential is supplied securely, and the idempotency guarantee.
- Tooling: Docker Compose (ADR-0010, TASK-004); Alembic for migrations; the existing `AccountService`/`PasswordService` for the seed (no parallel path).
- Operational notes carried from §07 / TASK-004: backend served by gunicorn+uvicorn; proxy is the only host-port-publishing service; internal traffic stays on the Docker network.
- Error cases documented: missing required env → backend fails fast (TASK-003 behaviour); bootstrap run on a system that already has a sysadmin → refuses and exits non-zero; cert/TLS misconfiguration → proxy serves redirect only, never plain-HTTP PHI (SR-001.2).

## Tests (write first — TDD, CLAUDE.md §4)

- Bootstrap test (`backend/tests/integration/test_bootstrap_sysadmin.py`):
  - on an empty system, the seed creates exactly one **sysadmin** with the supplied policy-compliant password and records an audit event (SR-032, SR-025, SR-023);
  - a non-policy-compliant password is rejected (SR-025);
  - running the seed again when a sysadmin exists is a no-op/refusal (idempotent; cannot mint extra admins);
  - the seeded sysadmin can log in and the normal create→activation flow works for subsequent accounts (SR-032/033).
- Docs smoke check (CI, extending TASK-005): a scripted bring-up follows INSTALL.md against the Compose stack and reaches the health endpoint over HTTPS — verifying the documented procedure actually works (NFR-006 controlled, executable instructions).
- Each test names the SR/process criterion it verifies.

## Acceptance criteria

- [ ] README, INSTALL, and DEPLOY documents exist, are version-controlled, and describe building and running the stack via Docker Compose (dev-plan Coding output, NFR-006).
- [ ] A documented first-sysadmin bootstrap creates the initial sysadmin via the normal account/password mechanisms with a runtime-supplied, policy-compliant credential, audited, and is idempotent (SR-032, SR-025, SR-023).
- [ ] No secret or hard-coded admin password is committed; secrets are env-injected (NFR-007, §8.11).
- [ ] Deploy docs cover TLS/HSTS, at-rest encryption (DB volume + MinIO SSE), migrations, backup/restore, and EU-only data-residency as an operator choice (SR-001, SR-022, ADR-0010).
- [ ] A scripted bring-up following INSTALL.md reaches the health endpoint over HTTPS in CI.

## Definition of Done

- [ ] Lint + type-check pass on the bootstrap script (`ruff`/`mypy`)
- [ ] Bootstrap and docs-smoke tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (N/A)
- [ ] Audit events emitted for the bootstrap account creation (SR-023)
- [ ] Traceability matrix row updated (dev-plan deploy output, SR-032 bootstrap → TASK-115 → tests)
- [ ] Security review N/A here (no new auth/session logic; the seed reuses reviewed `AccountService`/`PasswordService` — auth/session review is TASK-113)
