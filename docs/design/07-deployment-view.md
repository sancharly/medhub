# 07 - Deployment View

Decision: [ADR-0010](adr/0010-deployment-model.md). Diagram: [`../specifications/diagram-deployment.puml`](../specifications/diagram-deployment.puml)

## MVP topology

A single-tenant deployment (one organization per instance) orchestrated with **Docker Compose** on one host, behind a **reverse proxy** that terminates TLS.

| Node / Container                 | Contents                                              | Notes                                 |
|----------------------------------|-------------------------------------------------------|---------------------------------------|
| Client device                    | Browser running the SPA + Cornerstone3D (WebGL)       | desktop / tablet / phone (SR-020)     |
| Reverse proxy (Traefik/nginx)    | TLS 1.2+, HTTP→HTTPS redirect, HSTS, security headers | SR-001, SR-022, SR-031.4              |
| SPA static server (nginx)        | Built SPA assets                                      | served via proxy                      |
| Backend API (gunicorn + uvicorn) | FastAPI app, all backend items + mounted modules      | scale by adding replicas behind proxy |
| Celery worker                    | Async email + session-revocation tasks                | SR-033, SR-035, SR-034                |
| PostgreSQL 16                    | Domain + audit data, encrypted volume                 | ADR-0004; PITR backups                |
| Redis                            | Server-side sessions + Celery broker                  | SR-030; ADR-0012                      |
| MinIO (S3)                       | Encrypted attachment objects (SSE AES-256)            | ADR-0009; SR-022                      |
| External SMTP                    | Email delivery                                        | SR-033, SR-035                        |

## Operational notes

- **Secrets** (DB creds, object-store keys, session signing key, SMTP creds) injected via environment/secret files; never committed (NFR-007).
- **TLS** terminates at the proxy; internal traffic on the Docker network; PHI never served over plain HTTP (SR-001.2).
- **Backups:** PostgreSQL point-in-time recovery; object-store replication — documented operational procedures (clinical-record durability, UN-008).
- **Build/deploy instructions** (`README`/`DEPLOY`/`INSTALL`) are version-controlled per the development plan (NFR-006).
- **Data residency** is a deployment-time choice of the operator: no hosting region is pinned and no non-EU-only managed service is required, so EU-only hosting/residency is fully supported when the operator selects an EU region (NFR-004, ADR-0010).
- **Future scaling (out of MVP scope):** managed Postgres/object store, multiple API replicas, Kubernetes, and HA are additive because everything is containerized (ADR-0010). Multi-tenancy is deliberately deferred.
