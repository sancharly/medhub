# TASK-004 — Docker Compose topology + reverse proxy

- **Phase:** 0 — Foundation & toolchain
- **Software item / unit:** — / — (deployment enabler; realizes 07-deployment-view)
- **Implements:** SR-001, SR-022, §07 (Deployment View)
- **Depends on:** TASK-002 (must be merged first)
- **Branch:** `enabler-story/docker-compose-topology`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Define the MVP single-host deployment topology from [07-deployment-view.md](../../design/07-deployment-view.md) as a Docker Compose stack behind a TLS-terminating reverse proxy. This makes the application reachable only over HTTPS with HTTP→HTTPS redirect and HSTS (SR-001.2, SR-022.1) and stands up the supporting stores (PostgreSQL, Redis, MinIO) and Celery worker that later tasks depend on. Application logic is unchanged; this is infrastructure wiring.

## Interfaces to honor

- Realizes the deployment table in 07-deployment-view: proxy terminates TLS; SPA + API reachable only through it; internal traffic stays on the Docker network; PHI is never served over plain HTTP (SR-001.2). Backend is served by **gunicorn + uvicorn** (the ASGI seam from TASK-002).
- Secrets are injected via env/secret files, never committed — consume the `Settings` contract and `infra/.env.example` keys from TASK-003 (NFR-007, §8.11).
- Must **not** change application code, add endpoints, or weaken any security header. TLS, at-rest encryption (DB volume, MinIO SSE) are configured here at the infrastructure layer; application-layer security headers/CSP set in middleware are a separate later task (SR-031) and must not be duplicated/contradicted here.

## Implementation detail

- Files to create:
  - `backend/Dockerfile` — Python 3.12 slim, `uv sync --frozen`, run `gunicorn -k uvicorn.workers.UvicornWorker app.main:app` (binds internal port; not published to host).
  - `frontend/Dockerfile` — multi-stage: Vite `npm run build`, then static `nginx` serving `dist/` (internal only).
  - `infra/docker-compose.yml` — services:
    - `reverse-proxy` (**Traefik** or nginx) — the only service publishing host ports `80`/`443`; terminates **TLS 1.2+**; **HTTP→HTTPS redirect**; **HSTS**; routes `/` → frontend, `/api`, `/healthz` → backend.
    - `backend` (gunicorn+uvicorn), `frontend` (nginx static) — internal network only.
    - `postgres:16` — named volume on an **encrypted volume** (ADR-0004; SR-022.2 at-rest); creds from env.
    - `redis` — sessions + Celery broker.
    - `minio` — object storage with **server-side encryption (SSE, AES-256)** enabled and a default bucket created (ADR-0009; SR-022.2).
    - `celery-worker` — runs `celery -A app.workers worker` (worker package exists from TASK-001; concrete tasks land in later phases).
  - `infra/reverse-proxy/` — proxy config (Traefik dynamic/static config or `nginx.conf`) encoding: TLS cert paths, redirect, HSTS header (`Strict-Transport-Security: max-age=...; includeSubDomains`), and dev self-signed cert generation notes.
  - Update root `README.md`/add `infra/DEPLOY.md` — bring-up instructions, env-file requirement, cert provisioning (NFR-006 version-controlled build/deploy instructions; 07 operational notes). Document that **data residency is a deploy-time operator choice** ([ADR-0010](../../design/adr/0010-deployment-model.md)): no hosting region is pinned and no non-EU-only managed service is required, so the operator selects the hosting region/host (e.g. an EU region for EU-only residency) — the compose stack does not hard-code one.
- Config keys: all consumed from the env file per TASK-003 (`database_url`, `redis_url`, `object_store_*`, `smtp_*`, signing/crypto keys). No secret values committed.
- Error cases (infra): backend container fails fast if required env missing (TASK-003 behaviour); proxy serves no plain-HTTP content (redirect only).

## Tests (write first — TDD, CLAUDE.md §4)

This is infrastructure; "tests" are scripted, repeatable verifications recorded in `infra/`:
- `compose config` validates the file (`docker compose -f infra/docker-compose.yml config` exits 0).
- Bring-up smoke (documented script): `GET http://<host>/healthz` returns a **redirect to HTTPS** (SR-001.2); `GET https://<host>/healthz` returns 200 (reachable, SR-001.1).
- HTTPS response carries `Strict-Transport-Security` (HSTS); plain-HTTP content is never served (SR-001.2, SR-022.1).
- MinIO bucket exists and SSE is enabled; Postgres volume is the encrypted-volume mount (SR-022.2) — verified via documented commands.
- Each check cites its SR criterion in the verification script comments.

## Acceptance criteria

Distilled from SR-001, SR-022, and 07-deployment-view:

- [ ] The stack starts with `docker compose up` and the app is reachable via the proxy without client installation (SR-001.1).
- [ ] All HTTP traffic is served over HTTPS; plain-HTTP requests are redirected to HTTPS (SR-001.2).
- [ ] HSTS is set on HTTPS responses; TLS is 1.2+ and terminates at the proxy.
- [ ] PHI/services are reachable only through the proxy; backend/stores are not published to the host (SR-001.2 transport isolation).
- [ ] Data at rest is encrypted: Postgres on an encrypted volume and MinIO with SSE (AES-256) (SR-022.2/3).
- [ ] Containers exist for backend (gunicorn+uvicorn), frontend (nginx static), postgres:16, redis, minio, celery worker, and the reverse proxy (matches 07 topology table).
- [ ] Secrets injected via env/secret files; nothing sensitive committed (NFR-007, §8.11).
- [ ] Build/deploy instructions are version-controlled (NFR-006).

## Definition of Done

- [ ] Lint + type-check pass (Dockerfiles/compose validated; no app code changed)
- [ ] Bring-up smoke checks pass (HTTPS reachable, HTTP redirected, HSTS present, SSE/encrypted volume confirmed)
- [ ] OpenAPI regenerated and re-linted (N/A — no contract change)
- [ ] Audit events emitted for security-relevant actions (N/A — infra)
- [ ] Traceability matrix row updated (SR-001, SR-022, §07 → TASK-004 → bring-up smoke checks)
- [ ] Security review completed (N/A — no auth/session code; TLS/at-rest config noted for the system-test security review)

## Audit verdict (2026-06-29)

- **Verdict:** FAIL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-004a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
