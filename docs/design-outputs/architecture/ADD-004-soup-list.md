---
id: "ADD-004"
type: architecture-doc
title: "SOUP list (software of unknown provenance)"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "SR-001"
    relation: implements
  - target: "SR-012"
    relation: implements
  - target: "SR-017"
    relation: implements
  - target: "SR-021"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "SR-030"
    relation: implements
  - target: "ADD-002"
    relation: relates_to
tags: ["soup", "regulatory", "class:B"]
---

# SOUP list

Every third-party component not developed under this project's process, per IEC 62304 §8.1.2 with
the class B additions of §5.3.3–5.3.4 and the anomaly review of §7.1.2–7.1.3. Versions are the
**locked** ones (`backend/uv.lock`, `frontend/package-lock.json`, image tags in
`infra/docker-compose.yml` and the Dockerfiles) as of 2026-09-17 on branch
`doc/agentic-os-migration`.

Software items (`SI-*`) and units are defined in
[05-building-blocks.md](../../design/05-building-blocks.md).

## Anomaly review status

**Not yet performed.** No published anomaly list, release notes or advisory database has been
reviewed for the versions below, so no row claims one. The review is the first task of the SOUP
monitoring cycle ([TASK-154](../tasks/TASK-154-soup-anomaly-list-review.md)) and is a prerequisite
for a release under §7.1.2. The "Anomaly source" column names where each review must look.

## SOUP items — backend runtime

| Title | Manufacturer | Version | Used by (items) | Required functions / performance | Required HW/SW | Anomaly source |
|---|---|---|---|---|---|---|
| Python | Python Software Foundation | 3.12 (`python:3.12-slim`) | all backend items | Language runtime, stdlib, `hashlib`/`secrets` for tokens | Linux x86-64 container | python.org security advisories, CVE |
| FastAPI | Sebastián Ramírez / Tiangolo | 0.138.0 | SI-API, SI-MODHOST | HTTP routing, dependency injection (authz enforcement point), OpenAPI 3.1 generation | Python 3.12, Starlette | GitHub releases + security advisories |
| Starlette | Encode | 1.3.1 | SI-API | ASGI app, middleware chain (security headers, CSRF) | Python 3.12 | GitHub advisories |
| Uvicorn | Encode | 0.49.0 | SI-API | ASGI server (dev + container entrypoint) | Python 3.12 | GitHub advisories |
| Gunicorn | Benoit Chesneau | 26.0.0 | SI-API | Production process manager for Uvicorn workers | Linux | GitHub advisories, CVE |
| Pydantic | Pydantic Services | 2.13.4 | SI-API, SI-PERSIST, all services | Request/response validation — the authoritative server-side validation for SR-031.5 | Python 3.12 | GitHub releases/advisories |
| pydantic-settings | Pydantic Services | 2.14.2 | SI-API (config) | Typed 12-factor settings, secret handling (NFR-007) | Python 3.12 | GitHub releases |
| SQLAlchemy | SQLAlchemy authors | 2.0.51 | SI-PERSIST | ORM, parameterized queries (SQL-injection mitigation, SR-031), transactions | PostgreSQL 16 | GitHub releases/advisories, CVE |
| Alembic | SQLAlchemy authors | 1.18.4 | SI-PERSIST | Schema migrations, reproducible database state | SQLAlchemy 2.x | GitHub releases |
| psycopg2-binary | Daniele Varrazzo | 2.9.12 | SI-PERSIST | PostgreSQL driver (sync) | PostgreSQL 16, libpq | GitHub releases, CVE |
| greenlet | greenlet authors | 3.5.2 | SI-PERSIST | SQLAlchemy sync/async bridge | Python 3.12 | GitHub releases |
| cryptography | PyCA | 49.0.0 | SI-PERSIST (crypto), SI-AUTH | AES-256-GCM field encryption at rest (SR-022), key handling | OpenSSL (bundled) | PyCA advisories, CVE — **high priority** |
| argon2-cffi | Hynek Schlawack | 25.1.0 | SI-AUTH | Argon2id password hashing (SR-025, SR-029) | libargon2 (bundled) | GitHub advisories |
| Redis (server) | Redis Ltd. | 7 (`redis:7-alpine`) | SI-AUTH (sessions), SI-WORKER (broker) | Opaque session store with TTL (SR-030), Celery broker/result backend | Linux container | Redis release notes, CVE |
| redis-py | Redis Ltd. | 8.0.0 | SI-AUTH, SI-WORKER | Redis client (sync) | Redis 7 | GitHub advisories |
| Celery | Celery authors | 5.6.3 (kombu 5.6.2, billiard 4.2.4, amqp 5.3.1) | SI-WORKER | Asynchronous tasks: notifications, retention, erasure (SR-024, SR-035), retry/backoff | Redis 7 | GitHub advisories, CVE |
| PostgreSQL | PostgreSQL Global Development Group | 16 (`postgres:16`) | SI-PERSIST | Relational storage of PHI, constraints, transactional integrity | Linux container, persistent volume | postgresql.org security page, CVE |
| pydicom | pydicom contributors | 3.0.2 | SI-MOD-DICOM-BE | DICOM parsing, metadata extraction, pixel access for rendering (SR-017) | Python 3.12 | GitHub advisories — **safety-relevant, see RISK records** |
| fhir.resources (fhir-core) | Nazrul Kabir | 1.1.8 | SI-CLINICAL | FHIR R4 resource models for the clinical data model (SR-021) | Python 3.12 | GitHub releases |
| python-multipart | Andrew Dunham | 0.0.32 | SI-API, SI-ATTACH | Multipart upload parsing for attachments (SR-013) | Python 3.12 | GitHub advisories, CVE |
| boto3 | Amazon Web Services | **not declared** (imported optionally in `app/core/object_storage.py`) | SI-ATTACH | S3/MinIO object operations with SSE-AES256 | MinIO or S3 endpoint | AWS SDK advisories |
| MinIO | MinIO, Inc. | `minio/minio:latest` (**floating**) | SI-ATTACH | S3-compatible object storage for attachments, server-side encryption | Linux container, persistent volume | MinIO release notes, CVE |
| MinIO client (mc) | MinIO, Inc. | `minio/mc:latest` (**floating**) | infra bootstrap | Bucket creation and policy at bring-up | Linux container | MinIO release notes |
| nginx | F5 / nginx authors | `nginx:alpine` (**floating**) | reverse proxy, frontend image | TLS termination, HSTS and security headers (SR-001, SR-031) | Linux container, certificates | nginx security advisories, CVE |

## SOUP items — frontend runtime

| Title | Manufacturer | Version | Used by (items) | Required functions / performance | Required HW/SW | Anomaly source |
|---|---|---|---|---|---|---|
| Node.js | OpenJS Foundation | 20 (`node:20-slim`, build only) | build toolchain | Build and bundle the SPA | Linux container | nodejs.org security releases, CVE |
| React | Meta | 18.3.1 | SI-FE-SHELL, SI-FE-CORE, SI-FE-AUTH, SI-FE-MODREG | Component rendering, concurrent features | Modern browsers (SR-019) | GitHub advisories |
| React DOM | Meta | 18.3.1 | SI-FE-SHELL | DOM rendering, XSS-safe escaping by default (SR-031) | Modern browsers | GitHub advisories |
| React Router | Remix / Shopify | 7.18.0 | SI-FE-SHELL | Routing and route-level guards | React 18 | GitHub advisories, CVE |
| TanStack Query | Tanner Linsley | 5.101.0 | SI-FE-APICLIENT, SI-FE-CORE | Server-state caching and invalidation (consent immediacy, SR-008) | React 18 | GitHub releases |
| MUI Material + Icons | MUI | 9.1.1 | SI-FE-CORE, SI-FE-SHELL | Accessible, responsive components and theming (SR-020, SR-027, ADD-001) | React 18, Emotion | GitHub advisories |
| Emotion (react, styled) | Emotion authors | 11.14.0 / 11.14.1 | SI-FE-SHELL | CSS-in-JS engine behind MUI theming | React 18 | GitHub releases |
| openapi-fetch | Drew Powers | 0.17.0 | SI-FE-APICLIENT | Typed HTTP client generated from the OpenAPI contract, RFC 7807 handling | Browser `fetch` | GitHub releases |
| Fontsource Inter / Manrope | Fontsource | 5.2.8 | SI-FE-SHELL | Self-hosted variable fonts (no third-party font CDN, privacy) | — | GitHub releases |

## Development and verification tools (not shipped)

Not SOUP in the delivered product, but recorded because verification evidence depends on them:
ruff 0.15.18, black 26.5.1, mypy 2.1.0, pytest 9.1.1 (+ pytest-cov 7.1.0, pytest-asyncio 1.4.0),
httpx 0.28.1, fakeredis 2.36.2, testcontainers 4.14.2, TypeScript 5.9.3, Vite 5.4.21, Vitest 1.6.1
(+ @vitest/coverage-v8 1.6.1), Testing Library (react 16.3.2, jest-dom 6.9.1, user-event 14.6.1),
jsdom 24.1.3, msw 2.3.0, openapi-typescript 7.13.0, ESLint 8.57.1 with
@typescript-eslint 7.18.0, Prettier 3.8.4. Their exact versions are recorded in each test report.

## Pinning findings (§8.1.2)

| Finding | Where | Problem report |
|---|---|---|
| `minio/minio:latest`, `minio/mc:latest`, `nginx:alpine`, `redis:7-alpine`, `postgres:16`, `python:3.12-slim`, `node:20-slim` are floating tags, so the built image is not reproducible and the SOUP version is not uniquely designated | `infra/docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` | [PRB-001](../../problem-reports/PRB-001-floating-container-image-tags.md) |
| `boto3` is imported at runtime by `ObjectStorageClient` but is not declared in `backend/pyproject.toml`, so no version is pinned or identified | `backend/app/core/object_storage.py` | [PRB-002](../../problem-reports/PRB-002-undeclared-boto3-dependency.md) |
| Python and npm manifests use ranges (`>=`, `^`); the lock files pin exact versions, which is what this list records. Container images have no lock file, hence the finding above | `backend/pyproject.toml`, `frontend/package.json` | covered by PRB-001 |

## Monitoring

- **Who:** the Software Architect role, with the human accountable.
- **When:** at every dependency change (add, upgrade, remove), before every release, and at least
  every 365 days per `soup_anomaly_max_age_days` in `docs/medtrace.yml`.
- **How:** for each item, read the manufacturer's release notes, issue tracker and security
  advisories for the exact locked version, plus the CVE database; record the source and the review
  date in the item's row. An anomaly that could contribute to a hazardous situation goes to
  `risk-management` as a RISK record (§7.1.2), and a defect that affects MedHub becomes a PRB.
- **Automation:** CI dependency audit (`uv pip audit` / `npm audit`) is a signal, not a substitute
  for the documented review.

## Change log

- 2026-09-17 — Initial list created from `backend/uv.lock`, `frontend/package-lock.json`,
  `infra/docker-compose.yml` and the Dockerfiles. Two pinning findings raised as PRB-001 and
  PRB-002. Anomaly review pending (TASK-154).
