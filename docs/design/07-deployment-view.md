# 07 - Deployment View

Decisions: [ADR-0010](adr/0010-deployment-model.md); object store: [ADR-0015](adr/0015-object-store-component-after-minio.md); database roles: [ADR-0017](adr/0017-database-roles-and-append-only-audit-log.md); keys: [ADR-0018](adr/0018-field-encryption-key-identifier-and-key-separation.md); client address: [ADR-0019](adr/0019-originating-client-address-trusted-proxy-rule.md). Software item: SI-DEPLOY ([05 building blocks](05-building-blocks.md), ADD-026). Diagram: [`../specifications/diagram-deployment.puml`](../specifications/diagram-deployment.puml)

## MVP topology

A single-tenant deployment (one organization per instance) orchestrated with **Docker Compose** on one host, behind a **reverse proxy** that terminates TLS.

| Node / Container                 | Contents                                              | Notes                                 |
|----------------------------------|-------------------------------------------------------|---------------------------------------|
| Client device                    | Browser running the SPA + Cornerstone3D (WebGL)       | desktop / tablet / phone (SR-020)     |
| Reverse proxy (nginx 1.31)       | TLS 1.2+, HTTP→HTTPS redirect, HSTS, security headers; only service that publishes ports (80, 443); fixed address `172.28.77.2` on the `medhub` network; allow-list JSON access log | SR-001, SR-022, SR-031.4, SR-042, SR-043 |
| SPA static server (nginx)        | Built SPA assets; runs as the unprivileged `nginx` user on port 8080; logs no access | served via proxy; SR-041 AC 1, SR-043 |
| Backend API (gunicorn + uvicorn) | FastAPI app, all backend items + mounted modules; user `medhub`, port 8000, connects as the runtime database role | scale by adding replicas behind proxy; SR-041 AC 1 |
| Database migration (one-shot)    | `db-migrate`: secret check, Alembic, runtime role and grants, key-id guard; the only holder of `DATABASE_OWNER_URL` | ADR-0017; SR-023 AC 8, SR-022 AC 7 |
| Celery worker                    | Async email + session-revocation tasks; runs `celery worker` (PRB-061); the only service with SMTP credentials | SR-033, SR-035, SR-034 |
| Celery beat                      | Scheduler for the retention sweep; exactly one instance; schedule file under `/tmp` | SR-024 AC 4; PRB-061 |
| PostgreSQL 16                    | Domain + audit data, encrypted volume; two roles: the owner `medhub` (migrations only) and the runtime role `medhub_app` (no `UPDATE`, `DELETE` or `TRUNCATE` on `audit_log`) | ADR-0004, ADR-0017; PITR backups |
| Redis                            | Server-side sessions + Celery broker                  | SR-030; ADR-0012                      |
| Object store (SeaweedFS 4.51)    | Encrypted attachment objects (SSE-S3 AES-256 under its own `OBJECT_STORE_SSE_KEY`); no console or admin UI, no host port | ADR-0009, ADR-0015, ADR-0018; SR-022, SR-040, SR-041 AC 5 |
| Credential preflight (one-shot)  | Refuses weak or default object-store keys before the store starts; no network | ADR-0015 D3; SR-040 AC 2 |
| Bucket initialiser (one-shot)    | Creates the bucket, sets AES-256 default encryption, checks it has no policy; backend image, boto3 | ADR-0015 D2; SR-040 AC 4, SR-022 AC 4 |
| External SMTP                    | Email delivery                                        | SR-033, SR-035                        |

## Network, start-up order and runtime users

- The `medhub` network has a fixed subnet (`172.28.77.0/24`); containers without a fixed address get one from `ip_range` (`172.28.77.128/25`), so none can take the reverse proxy's address (`172.28.77.2`) first. The backend's `TRUSTED_PROXIES` is set to that one address in the Compose file; a value in `infra/.env` does not override it. Changing the network means changing three lines together: the subnet with its `ip_range`, the proxy's `ipv4_address`, and `TRUSTED_PROXIES` (`infra/tests/test_compose_trusted_proxy.py` checks that they agree). A wrong value does not stop the start: every request then appears to come from the proxy (ADR-0019).
- Start order: PostgreSQL healthy, then `db-migrate` completes, then `backend`, `celery-worker` and `celery-beat` start (the backend also waits for `object-store-init`; runtime view in [06](06-runtime-views.md), 6.8). `db-migrate` is the only migrating process; a refusal of any of its four steps keeps the application services down.
- Ports: only the reverse proxy publishes ports (80, 443). Containers listen on 8000 (backend), 8080 (frontend), 5432, 6379 and 8333, none published.
- Users: the backend image runs as `medhub`; the frontend image runs nginx as its unprivileged `nginx` user on 8080 (SR-041 AC 1). The reverse proxy is the pulled official nginx image, not built by MedHub; its master process runs as UID 0 (a residual for the release evaluation, PRB-007).
- No service reads `infra/.env` as a whole. Each service lists the settings it reads, so the owner password reaches `postgres` and `db-migrate` only, and the API gets no SMTP credential. `celery-beat` holds object-store and field-key settings it does not use, and `db-migrate` holds object-store settings it does not use (it does use the field keyring), because the shared start-up rule checks them; narrowing this is an open decision (section 11).
- Proxy logging: the access log is an allow-list JSON format with no request line, query string or header, and the two activation paths replaced by `[redacted]`; the activation locations log errors at `crit` only and the activation page sends `Referrer-Policy: no-referrer` (SR-043 AC 4).

## Object store network and start-up order

Software item: SI-OBJSTORE ([05 building blocks](05-building-blocks.md)). Compose file: `infra/docker-compose.yml`.

- The `object-store` Docker network is `internal: true` (no egress, no published port). Only `object-store`, `object-store-init` and `backend` join it. The proxy, frontend, PostgreSQL, Redis and the Celery worker cannot reach the store (SR-040 AC 3; checked by `infra/smoke-test.sh`).
- Object-store start order: `object-store-preflight` completes, then `object-store` becomes healthy, then `object-store-init` completes, then `backend` starts. Any failure keeps the backend down.
- The store runs `weed server` with master, volume server and filer bound to loopback; only S3 (8333, plus its gRPC port 18333) listens on the container address. Admin UI, WebDAV, SFTP, Iceberg, Lance and telemetry are off (SOUP-036 lists the listeners).
- `infra/compose.ci-object-store.yml` is a CI-only override (extra non-internal network, S3 port on the runner's loopback). It is never part of a deployment (SI-DEVINFRA, ADD-024).

## Operational notes

- **Keys:** `OBJECT_STORE_ACCESS_KEY` and `OBJECT_STORE_SECRET_KEY` have no default and are generated by the operator; the preflight rejects unset, empty, well-known-default or short values. The store's SSE-S3 key is its own setting, `OBJECT_STORE_SSE_KEY` (base64 of 32 bytes), never `AT_REST_ENCRYPTION_KEY`: the preflight refuses the stack when they are equal, so rotating the field key cannot make an attachment unreadable. The SSE key belongs to the volume that holds the attachments, so it changes only by the copy procedure. The field key `AT_REST_ENCRYPTION_KEY` carries an identifier (`AT_REST_ENCRYPTION_KEY_ID`) and optional retired keys, and rotates by `app.db.reencrypt` (sections 6.10, 6.11, 8.11). Procedures: `infra/DEPLOY.md`.
- **No console:** the store has no admin UI. The bucket is created and configured by `object-store-init` (re-run with `docker compose run --rm object-store-init`); other administration is scripted S3 calls from the backend image (`infra/DEPLOY.md`, "Check the object store").
- **Component currency:** SeaweedFS ships fixes only in its latest release, so its advisories are read monthly (PLAN-002, SOUP-036); see [11 risks](11-risks-and-technical-debt.md).
- **Migration from MinIO:** a host that still holds attachments in the old MinIO volume follows `infra/DEPLOY.md`, "Migrating from MinIO" (`backend/scripts/migrate_object_store.py`, `infra/migration/compose.minio-legacy.yml`): backup through a read-only mount, copy through the S3 API with checksum comparison, rehearsal on a restored copy.

- **Secrets** (owner and runtime database credentials, object-store access, secret and SSE keys, the field-encryption key and its retired keys, SMTP creds) injected via environment; never committed. The template `infra/.env.example` holds no value for any of them and Compose has no default (`${NAME:?…}`); the session signing key no longer exists, because sessions are opaque tokens held in Redis (PRB-018, ADR-0010 note) (NFR-007, SR-041).
- **TLS** terminates at the proxy; internal traffic on the Docker network; PHI never served over plain HTTP (SR-001.2).
- **Backups:** PostgreSQL point-in-time recovery; object-store volume (`object_store_data`) backup, together with `OBJECT_STORE_SSE_KEY`; the field-encryption key and its retired keys are needed to read the database backup too (a lost key makes the encrypted descriptions unrecoverable) — operator procedures. No backup and restore procedure exists yet in `infra/DEPLOY.md` for `postgres_data` or `object_store_data`; it is recorded in [PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md) (clinical-record durability, UN-008).
- **Build/deploy instructions** (`README`/`DEPLOY`/`INSTALL`) are version-controlled per the development plan (NFR-006).
- **Data residency** is a deployment-time choice of the operator: no hosting region is pinned and no non-EU-only managed service is required, so EU-only hosting/residency is fully supported when the operator selects an EU region (NFR-004, ADR-0010).
- **Future scaling (out of MVP scope):** managed Postgres/object store, multiple API replicas, Kubernetes, and HA are additive because everything is containerized (ADR-0010). Multi-tenancy is deliberately deferred.
