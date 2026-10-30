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

#### Generate the object-store keys

`OBJECT_STORE_ACCESS_KEY` and `OBJECT_STORE_SECRET_KEY` have no default. Generate both:

```bash
openssl rand -hex 12      # OBJECT_STORE_ACCESS_KEY
openssl rand -base64 32   # OBJECT_STORE_SECRET_KEY
```

The `object-store-preflight` service stops the object store and its bucket initialiser, naming
the setting, when either key is unset or empty, equals a well-known default value
(list in `backend/app/core/object_store_credentials.py`, compared in any case), or when the secret key is shorter than
16 characters.

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

## Migrating from MinIO

For a host that still holds attachments in the old MinIO volume (CR-002 AC-11, TASK-178). A host
with no attachments needs none of this: start the stack, and the new store is empty and ready.

Principles. MinIO writes to any data directory it runs on (starting and stopping it on a restored
copy deleted housekeeping files, no objects), so **the old volume is never given to MinIO**: step 1
backs it up through a read-only mount, step 2 restores the backup into a new volume, and the legacy
MinIO runs only on that copy, which its Compose file also mounts read-only. The old volume, the
backup tars and the dump are never deleted by this procedure. The rehearsal record is in
`docs/design-outputs/tasks/TASK-178-migrate-objects-to-new-store.md`; rehearse on a restored copy
of your own data before the real run.

Output of the migration script names rows by attachment id and orphans by a short hash, never by
storage key (a key holds the patient id and the file name). Still treat the output as operational
data and keep it out of tickets and chats.

Variables used in every command below (one project name throughout):

```bash
P=infra                              # Compose project of the stack (the default is the directory name)
BK=/secure/path/outside/the/repo     # backup directory; must not be inside a Docker volume
HELPER=alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd
# HELPER is any image pinned by digest. This one is the alpine:3.21 digest used in the rehearsal
# (arm64 host). On another host take yours from `docker buildx imagetools inspect alpine:3.21`.
OLD_VOL=${P}_minio_data              # the old MinIO volume: backed up, never run on
PG_VOL=${P}_postgres_data
COPY_VOL=${P}_minio_data_copy        # restored copy: the only volume the legacy MinIO runs on
```

### 1. Stop the stack and back up (read-only)

Stop every container of the old stack so the copies are consistent and no upload happens. Keep the
old `.env` too: rollback needs it.

```bash
docker stop $(docker ps -q --filter "label=com.docker.compose.project=$P")
mkdir -p "$BK" && ( umask 077; cp infra/.env "$BK/env.before" )
docker run --rm --network none -v "$OLD_VOL":/src:ro -v "$BK":/out "$HELPER" \
  tar -C /src -cf /out/minio_data.tar .
docker run --rm --network none -v "$PG_VOL":/src:ro -v "$BK":/out "$HELPER" \
  tar -C /src -cf /out/postgres_data.tar .
( cd "$BK" && shasum -a 256 *.tar > SHA256SUMS && chmod a-w *.tar )
```

Also take a logical dump (`pg_dump -Fc`) from a PostgreSQL container started on a restored scratch
copy of `postgres_data.tar` (never on `$PG_VOL`), and keep it in `$BK`.

### 2. Restore the old volume into a copy

```bash
docker volume create "$COPY_VOL"
docker run --rm --network none -v "$COPY_VOL":/dst -v "$BK":/in:ro "$HELPER" \
  tar -C /dst -xpf /in/minio_data.tar
```

### 3. Configure and start the new store (uploads stay blocked)

In `infra/.env`:

- `OBJECT_STORE_ENDPOINT=http://object-store:8333`. A host that ran MinIO has it pointing at
  `minio`, and the backend, the initialiser and the migration all read it. Remove the line to take
  the default.
- New `OBJECT_STORE_ACCESS_KEY` and `OBJECT_STORE_SECRET_KEY` (see "Generate the object-store
  keys"). Keep the old pair as `LEGACY_ACCESS_KEY` and `LEGACY_SECRET_KEY`.
- `AT_REST_ENCRYPTION_KEY` stays: it is now the new store's encryption key. Add `LEGACY_KMS_KEY` only
  if the MinIO volume was written under a different key. `MINIO_KMS_SECRET_KEY` is no longer used
  by the stack.

Start the data services and the backend only. Do not start the reverse proxy yet, so no upload can
reach the new store before verification passes.

```bash
docker compose -p "$P" -f infra/docker-compose.yml up -d --build postgres redis object-store-init backend
```

### 4. Start the legacy store on the copy and migrate

The legacy file lives in `infra/migration/`, so give it the same env file and the names of the
networks and database of the project:

```bash
export OBJECT_STORE_NETWORK=${P}_object-store DATABASE_NETWORK=${P}_medhub
export LEGACY_MINIO_VOLUME="$COPY_VOL"
export MIGRATION_DATABASE_URL='postgresql://<user>:<password>@postgres:5432/medhub'
L="docker compose -p ${P}-legacy -f infra/migration/compose.minio-legacy.yml --env-file infra/.env"
$L up -d minio-legacy
$L run --rm migrate; echo "exit=$?"
```

The pinned MinIO image is arm64 only and cannot be pulled (SOUP-022); the file sets
`pull_policy: never`, so the host needs the cached image. MinIO logs rename errors on the read-only
mount; they concern its housekeeping files.

For each attachment row the script reads the object from MinIO (which decrypts it), compares its
SHA-256 with the recorded checksum, writes it to the new store with `ServerSideEncryption=AES256`,
reads it back and compares again. It prints four counts (copied, already-present-and-matching,
missing-in-source, checksum-mismatch) and lists source objects with no row (orphans, reported only,
never copied). Exit 0: every row is on the new store. Exit 1: an object is missing or mismatched,
or the database has no attachment rows while the source holds objects (usually the wrong
`MIGRATION_DATABASE_URL` or project name). Do not go on after exit 1; fix the cause and run again
(the script can be re-run and copies nothing that is already present and correct).

### 5. Verify

1. Run the `migrate` command again: it must report every row as already present and copy nothing.
2. With the backend running (and still no proxy), log in as the owner of an attachment written
   before the change and download it through `GET /api/v1/attachments/<id>` (for example with
   `docker compose -p "$P" exec backend python` and `urllib`, keeping the session and CSRF cookies).
   The bytes must equal the original and the response must be 200; a stored-checksum mismatch is
   answered with 502 and never served.
3. Search the new store's volume (`${P}_object_store_data`) read-only for a plaintext marker from one
   of the documents. It must find nothing.

### 6. Open the stack and retire the legacy store

```bash
docker compose -p "$P" -f infra/docker-compose.yml up -d
$L --profile migrate down        # no -v: the volumes stay
```

Uploads are accepted from this point and exist only on the new store. Keep `$OLD_VOL`, `$COPY_VOL`,
the tars, the dump and `env.before` until the owner of the data decides to delete them; nothing in
this procedure deletes them.

### Rollback

`infra/migration/compose.minio-legacy.yml` is for migration only. The application cannot use it,
because it sits on an internal network of its own and the current `infra/docker-compose.yml` has no
MinIO service. To go back to MinIO:

1. Stop the new stack: `docker compose -p "$P" -f infra/docker-compose.yml down` (no `-v`).
2. Check out the last release before CR-002 in a second tree
   (`git worktree add ../medhub-pre-cr002 b1d0b78`; this repository's last commit before CR-002).
3. Put the old `.env` back (`$BK/env.before`, mode 600) for that tree.
4. The original volume `$OLD_VOL` was never run on, so it is the one the old Compose file mounts
   (`minio_data` of project `$P`). If it is lost, restore it first from `$BK/minio_data.tar` with the
   restore command of step 2, naming `$OLD_VOL`.
5. Start that release: `docker compose -p "$P" -f ../medhub-pre-cr002/infra/docker-compose.yml up -d --build`.

Uploads made after step 6 exist only on the new store. They would have rows in PostgreSQL and no
object in MinIO, so their downloads fail. The script copies in one direction only, so there is no
reverse copy. Roll back only before step 6, while uploads are blocked; after that, fix forward.
Rolling back after step 6 is not supported and has not been rehearsed.

## Stopping Services

```bash
docker compose -f infra/docker-compose.yml down
# To also remove volumes (DESTROYS all data):
docker compose -f infra/docker-compose.yml down -v
```
