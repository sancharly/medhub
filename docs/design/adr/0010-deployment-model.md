# ADR-0010: Containerized single-tenant deployment via Docker Compose (MVP)

## Status

Accepted

## Context

MedHub must be served over HTTPS as a reachable web app (SR-001), enforce TLS everywhere (SR-022), and meet performance budgets under "normal load" (SR-026) — there is no stated requirement for large-scale multi-region elasticity at the MVP. The development plan follows IEC 62304 with version-controlled build/deploy instructions (NFR-006; dev-plan "Coding activities" outputs include DEPLOY/INSTALL). The team is small and the regulated surface should stay small (ADR-0001). Components to run: SPA static assets, FastAPI backend, PostgreSQL, Redis, Celery worker, MinIO, and a reverse proxy terminating TLS.

## Decision

Package every component as a **Docker container** and orchestrate the MVP with **Docker Compose** as a **single-tenant** deployment (one organization per deployment), behind a **reverse proxy (Traefik or nginx)** that terminates TLS, enforces HTTPS redirect + HSTS (SR-001 AC-2), and applies security headers (SR-031 AC-4).

- Images are built in CI; deployment is reproducible from version-controlled `docker-compose.yml` + env/secret files (NFR-006).
- Secrets (DB credentials, object-store keys, session signing key, SMTP creds) are injected via environment/secret files, never committed.
- The same images target a single VM/host for the MVP; the container boundary keeps a future move to Kubernetes or a managed cloud additive, not a rewrite.

**Data residency is a deployment-time configuration choice made by the operator.** MedHub does not pin a hosting region or depend on any non-EU-only managed service: every backing store (PostgreSQL, Redis, MinIO, SMTP) is a self-hosted container or an externally-configured endpoint, and the deployment region is selected by the operator at deploy time via externalized config (env/secret files, twelve-factor; section 8.11). The architecture therefore imposes **no obstacle to EU-only hosting / EU data residency**; whether a given deployment is hosted in the EU is the client/operator's decision per their GDPR obligations (NFR-004), not a property baked into the architecture. The system only needs to be *technically prepared* for EU residency, which this externalized, self-hostable design guarantees.

## Consequences

### Positive

- Simple, reproducible, version-controlled deployment matching the dev plan's DEPLOY/INSTALL outputs (NFR-006) and a small team's capacity.
- Single reverse proxy gives one place to enforce TLS, HSTS, and security headers (SR-001, SR-022, SR-031).
- Single-tenant isolation simplifies the GDPR/data-residency story (NFR-004) — one organization's PHI per deployment, hostable in any operator-chosen region including EU-only.
- Container images are portable; scaling later (replicas behind the proxy, managed Postgres, managed object store) is incremental.

### Negative

- Docker Compose is not a high-availability orchestrator; a single host is a single point of failure (acceptable at MVP; HA via Kubernetes/managed services is a documented future step).
- Single-tenant means per-organization operational overhead if many organizations are onboarded (revisit multi-tenancy post-MVP).

### Neutral

- Backups (Postgres PITR, object-store replication) are an operational procedure documented alongside deployment, not an application feature.

## Alternatives Considered

**Kubernetes from day one.** Rejected for the MVP: operational complexity and cost not justified by current load (SR-026 "normal load"); contrary to small-team, small-surface philosophy. Containerization keeps it as a clean future option.

**Serverless / PaaS (e.g., functions).** Rejected: cold starts threaten the DICOM-open budget (SR-026), the stateful Postgres/MinIO/Redis components fit poorly, and ADR-0001 already rejected serverless.

**Multi-tenant single deployment.** Rejected for the MVP: multi-tenant PHI isolation raises the GDPR/security bar substantially (NFR-004/NFR-007) with no MVP requirement; single-tenant is the safer, simpler default.

## References

- Requirements: SR-001, SR-022, SR-026, SR-031; NFR-004, NFR-006, NFR-007, NFR-008
- Related: ADR-0001, ADR-0002, ADR-0009, ADR-0011
