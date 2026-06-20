# MedHub Deployment Guide

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- A TLS certificate and key for your domain (see "Cert Provisioning" below)
- A completed `infra/.env` file (copy from `.env.example`)

## Bring-Up Instructions

### 1. Configure the environment

```bash
cp infra/.env.example infra/.env
# Edit infra/.env — fill in every value, especially:
#   DATABASE_URL, POSTGRES_PASSWORD
#   OBJECT_STORE_ACCESS_KEY, OBJECT_STORE_SECRET_KEY
#   SESSION_SIGNING_KEY  (≥32 random bytes)
#   AT_REST_ENCRYPTION_KEY  (exactly 32 bytes)
#   SMTP_HOST, SMTP_USER, SMTP_PASSWORD
```

Never commit `infra/.env` to version control.

### 2. Provision TLS certificates

Place your certificate and key in `infra/certs/`:

```
infra/certs/server.crt   # Full-chain PEM certificate
infra/certs/server.key   # Private key (chmod 600)
```

**Let's Encrypt (recommended for internet-facing deployments):**

```bash
certbot certonly --standalone -d yourdomain.example.com
cp /etc/letsencrypt/live/yourdomain.example.com/fullchain.pem infra/certs/server.crt
cp /etc/letsencrypt/live/yourdomain.example.com/privkey.pem   infra/certs/server.key
```

**Self-signed (local/staging only):**

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout infra/certs/server.key \
  -out infra/certs/server.crt \
  -subj "/CN=localhost"
```

### 3. Start all services

```bash
docker compose -f infra/docker-compose.yml up -d
```

### 4. Verify the stack

```bash
bash infra/smoke-test.sh
```

Expected output: all checks PASS.

### 5. Create the MinIO bucket

On first launch, create the default bucket via the MinIO CLI or console
(`http://localhost:9001` — internal only, not exposed externally):

```bash
docker compose -f infra/docker-compose.yml exec minio \
  mc alias set local http://localhost:9000 $OBJECT_STORE_ACCESS_KEY $OBJECT_STORE_SECRET_KEY
docker compose -f infra/docker-compose.yml exec minio \
  mc mb local/$OBJECT_STORE_BUCKET
```

### 6. Run database migrations

```bash
docker compose -f infra/docker-compose.yml exec backend \
  uv run alembic upgrade head
```

## Data Residency Note

All PHI (Protected Health Information) is stored exclusively in:

- **PostgreSQL** — `postgres_data` named volume on the host running Docker
- **MinIO** — `minio_data` named volume with SSE-AES256 at rest (SR-016)

No PHI is transmitted outside the `medhub` internal Docker network except
through the reverse proxy over TLS 1.2+ (SR-008). Verify your host's data
residency requirements before deploying to a cloud region.

## Stopping Services

```bash
docker compose -f infra/docker-compose.yml down
# To also remove volumes (DESTROYS all data):
docker compose -f infra/docker-compose.yml down -v
```
