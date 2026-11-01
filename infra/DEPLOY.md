# MedHub Deployment Guide

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- A TLS certificate and key for your domain (see "Cert Provisioning" below)
- A completed `infra/.env` file (copy from `.env.example`)

## Bring-Up Instructions

### 1. Configure the environment

```bash
cp infra/.env.example infra/.env
# Edit infra/.env — the template holds no value for any secret. Fill in every secret in the
# "Secret settings" table below, plus the non-secret settings for your site:
#   SMTP_HOST (and SMTP_USER, SMTP_PASSWORD if your mail relay needs authentication)
```

Never commit `infra/.env` to version control.

#### Secret settings

This table is the definition of a *secret setting* (SR-041). `infra/.env.example` holds no value
for any of them and `infra/docker-compose.yml` has no default for any of them. Generate each one
with its own command: never reuse a value for two settings (the one exception is the password
inside `DATABASE_OWNER_URL`, which is `POSTGRES_PASSWORD`; the password inside `DATABASE_URL` must
be a different value), and never copy a value from this document or from a ticket.

| Setting | Used by | How to generate | Rotation |
|---|---|---|---|
| `POSTGRES_PASSWORD` | `postgres` (initialises the database owner user `medhub`) | `openssl rand -hex 24` | The image applies it only when the data volume is first created. To change it later run `ALTER USER medhub PASSWORD '…'` in the running database, then change this value and the password in `DATABASE_OWNER_URL` together |
| `DATABASE_OWNER_URL` | `db-migrate` only; no other service receives it | `postgresql://medhub:<POSTGRES_PASSWORD>@postgres:5432/medhub`; the password is `POSTGRES_PASSWORD` (percent-encode it if it is not hex) | With `POSTGRES_PASSWORD`; run `db-migrate` again |
| `DATABASE_URL` | `backend`, `celery-worker`, `celery-beat`, and `db-migrate` (which creates the role from it) | `postgresql://medhub_app:<password>@postgres:5432/medhub`; generate the password with a command of its own (`openssl rand -hex 24`): it must differ from `POSTGRES_PASSWORD`, and the user must be a different one from the owner's | Change the password here and run `db-migrate` (it applies the new password to the role), then recreate `backend`, `celery-worker` and `celery-beat` |
| `OBJECT_STORE_ACCESS_KEY` | `object-store`, `object-store-preflight`, `object-store-init`, `backend`, `celery-worker` | `openssl rand -hex 12` | Change the value and recreate the stack (rules in "Generate the object-store keys") |
| `OBJECT_STORE_SECRET_KEY` | same as the access key | `openssl rand -base64 32` | As the access key |
| `AT_REST_ENCRYPTION_KEY` | `backend`, `celery-worker` (field encryption); `object-store` (SSE key) | `openssl rand -base64 32` (base64 of exactly 32 bytes) | Not by editing the value (pair it with `AT_REST_ENCRYPTION_KEY_ID`): see [ADR-0018](../docs/design/adr/0018-field-encryption-key-identifier-and-key-separation.md) and "Generate the object-store keys" below |
| `AT_REST_ENCRYPTION_RETIRED_KEYS` | `backend`, `celery-worker`, `celery-beat`, `db-migrate` (optional; decryption only) | Earlier keys as comma-separated `id:key` entries, each key `openssl rand -base64 32` output; empty unless a rotation is under way. Ids differ from `AT_REST_ENCRYPTION_KEY_ID` and from each other; a key must not equal the current key | Remove an entry once no stored value names its id (rotation procedure follows with TASK-195) |
| `SMTP_PASSWORD` | `backend`, `celery-worker` | Issued by your mail relay. Required only when `SMTP_USER` is set; leave `SMTP_USER` and `SMTP_PASSWORD` empty for a relay without authentication | Issue a new one at the relay, change the value, recreate `backend` and `celery-worker` |

`AT_REST_ENCRYPTION_KEY_ID` is **not a secret** but is required, with no default: the identifier of
the current field-encryption key (1 to 32 characters of `a-z`, `0-9`, `-`; for example `k1`). Every
field value written from now on starts with `mh1:<id>:`, and the backend decrypts a value with the
key named in that prefix only. Existing installations must add it to `infra/.env` before upgrading;
pick an identifier for the key already in `AT_REST_ENCRYPTION_KEY` and keep it. Values written by
earlier versions have no prefix and are refused by this version until the migration of TASK-194
converts them, so do not deploy this version to a database that holds field-encrypted values
without that migration (CR-004 D-5). The identifier and each retired id must have no spaces or
line breaks around them; the application refuses them at start-up.

One optional secret setting is not read by the Compose stack yet: `OBJECT_STORE_SSE_KEY` (a separate
server-side-encryption key, `openssl rand -base64 32`); the application checks it **only when it is
set** and refuses a placeholder. Its task adds it to the template and to this table.

What refuses an unsafe value, and where:

- **Compose**: `POSTGRES_PASSWORD`, `DATABASE_OWNER_URL`, `DATABASE_URL`, `AT_REST_ENCRYPTION_KEY`, `AT_REST_ENCRYPTION_KEY_ID` and the two
  object-store keys use `${NAME:?…}`. `docker compose` stops before creating anything and the
  message names the first setting it finds unset or empty. Check it without starting anything: take
  a filled `.env`, remove one line (for example `POSTGRES_PASSWORD=`) and run
  `docker compose -f infra/docker-compose.yml --env-file <that file> config`; the message is
  `POSTGRES_PASSWORD must be set`.
- **The application** (backend and worker start-up): refuses a secret that is a known placeholder
  (the weak words, any value starting with the `change-me` prefix and any value earlier templates
  shipped; any case; list in `backend/app/core/secret_settings.py`), a database URL
  without a password, an `AT_REST_ENCRYPTION_KEY` that does not decode to 32 bytes, a missing or
  malformed `AT_REST_ENCRYPTION_KEY_ID`, a retired key that is malformed, repeats an id, does not
  decode to 32 bytes or equals the current key, and (in
  `db-migrate`, where both URLs are present) a `DATABASE_URL` that names the same user or has the
  same password as `DATABASE_OWNER_URL`. The message names the setting, never the value. The
  backend, the Celery worker and Celery beat refuse at start-up; `db-migrate` refuses before it
  connects.

`SESSION_SIGNING_KEY` is no longer a setting (sessions are opaque random tokens held in Redis,
not signed). Remove it from an existing `infra/.env`; a leftover value is ignored.

#### Generate the object-store keys

`OBJECT_STORE_ACCESS_KEY` and `OBJECT_STORE_SECRET_KEY` have no default. Generate both, and
generate `AT_REST_ENCRYPTION_KEY` the same way (the other secrets are in the "Secret settings"
table above):

```bash
openssl rand -hex 12      # OBJECT_STORE_ACCESS_KEY
openssl rand -base64 32   # OBJECT_STORE_SECRET_KEY
openssl rand -base64 32   # AT_REST_ENCRYPTION_KEY (base64 of 32 random bytes)
```

Run the last command separately: the secret key and the encryption key must be different values.

The `object-store-preflight` service stops the object store and its bucket initialiser, naming
the setting, when either key is unset or empty, equals a well-known default value
(list in `backend/app/core/object_store_credentials.py`, compared in any case), or when the secret key is shorter than
16 characters.

`AT_REST_ENCRYPTION_KEY` must be base64 that decodes to exactly 32 bytes: the backend
(`backend/app/db/crypto.py`) refuses any other length, but only when it first encrypts a field
(for example the first clinical entry), not at start-up. Thirty-two ASCII characters decode to 24
bytes and `openssl rand -hex 32` to 48 bytes, so neither works. The object store accepts any
string, so a wrong key does not stop the stack from starting.

Set it **before the first start**. It is also the object store's server-side-encryption key
(`WEED_S3_SSE_KEY`): with a different value on the same volume the stored objects can no longer
be read, so it cannot be changed later on a store that holds data. Back it up with the volumes it
protects.

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

Compose runs the database and object-store services in a fixed order (steps 5 and 6). The
`backend` service starts only after `object-store-init` and `db-migrate` have completed
successfully, and `celery-worker` and `celery-beat` only after `db-migrate`. A rejected key or an
unhealthy store keeps the backend and the reverse proxy down (`up` exits non-zero and reports the
failed dependency); PostgreSQL, Redis and the frontend still start. Read the failed service's log
(`docker compose -f infra/docker-compose.yml logs object-store-preflight object-store-init db-migrate`).

### Trusted proxy and the Compose subnet

The backend takes the caller's address from `X-Forwarded-For` only when the request comes from
the reverse proxy (SR-042, ADR-0019). Compose therefore gives the `medhub` network a fixed
subnet (`172.28.77.0/24`, dynamic addresses from `172.28.77.128/25`), the `reverse-proxy` the
fixed address `172.28.77.2`, and sets the backend's `TRUSTED_PROXIES` to that one address in
`environment:` (a value in `infra/.env` does not override it). Gunicorn is started with an empty
`--forwarded-allow-ips=`, so the server never rewrites the peer.

If the subnet collides with a host network, change these lines in `infra/docker-compose.yml`
together, keeping the proxy address inside `subnet` and outside `ip_range`:

1. `networks.medhub.ipam.config`: `subnet` and `ip_range`;
2. `reverse-proxy.networks.medhub.ipv4_address`;
3. `backend.environment.TRUSTED_PROXIES`: the same address as in 2.

`infra/tests/test_compose_trusted_proxy.py` checks that the three agree. A wrong value does not
stop the start: every request then appears to come from the proxy.

### 4. Verify the stack

```bash
bash infra/smoke-test.sh
```

Expected output: all checks PASS.

### 5. Check the object store

There is nothing to create by hand: the bucket is created by the stack. The object store is
SeaweedFS 4.51, pinned by tag and digest in `infra/docker-compose.yml` (ADR-0015, SOUP-036). It
has no console or admin UI, no host port, and sits on its own `object-store` network (below).

| Service (one-shot unless noted) | What it does |
|---|---|
| `object-store-preflight` | Checks the two keys (rules in "Generate the object-store keys") with no network; exits non-zero, naming the setting, when one is rejected |
| `object-store` (long-running) | The S3 server. Healthy only when its S3 endpoint answers |
| `object-store-init` | Waits for a healthy store; creates the bucket `OBJECT_STORE_BUCKET` (default `medhub`) if missing, sets AES256 default encryption, reads it back, and checks the bucket has no policy. Exits non-zero on any failure |

Re-run the initialiser at any time (it is safe to repeat):

```bash
docker compose -f infra/docker-compose.yml run --rm object-store-init
```

It prints `object-store init ok: bucket <name> private, AES256` on success and one line on
stderr naming the failed step otherwise. Do not create buckets or set policies by other means:
a bucket policy makes the initialiser fail.

#### Bucket administration

There is no console and no `mc`. Administer the bucket with scripted S3 calls (boto3) from the
backend image, which already holds the endpoint and keys in its environment. Example, with the
stack running: show the default encryption and how many objects the bucket holds. It prints no
key names, because a key contains the patient id and the file name:

```bash
docker compose -f infra/docker-compose.yml exec -T backend python - <<'PY'
import os, boto3
s3 = boto3.client("s3", endpoint_url=os.environ["OBJECT_STORE_ENDPOINT"],
                  aws_access_key_id=os.environ["OBJECT_STORE_ACCESS_KEY"],
                  aws_secret_access_key=os.environ["OBJECT_STORE_SECRET_KEY"],
                  region_name="us-east-1")
bucket = os.environ["OBJECT_STORE_BUCKET"]
print(s3.get_bucket_encryption(Bucket=bucket)["ServerSideEncryptionConfiguration"]["Rules"])
pages = s3.get_paginator("list_objects_v2").paginate(Bucket=bucket)
print(sum(p.get("KeyCount", 0) for p in pages), "objects")
PY
```

The backend container can reach the store because it is one of three services on the
`object-store` network (below). The store's S3 credentials are the only identity it has.

#### Network and component

- Network `object-store` is `internal: true`: no egress and no published port. Only
  `object-store`, `object-store-init` and `backend` join it. The reverse proxy, frontend,
  PostgreSQL, Redis, `db-migrate`, the Celery worker and `celery-beat` cannot reach the store
  (checked by `infra/smoke-test.sh` for the services it lists).
- Inside the container the master, volume server and filer listen on loopback only; only S3 (8333,
  and its gRPC port 18333) listens on the container address.
- `infra/compose.ci-object-store.yml` is for the CI job `object-store-integration` only. It
  publishes the S3 port on the runner's loopback. Never use it on a deployment.

#### Keeping the component current

SeaweedFS ships fixes only in its latest release and has had critical advisories, so the
maintainer reads its advisories **every month** (PLAN-002, "Items with rolling releases"; the
sources are named in `docs/soup/SOUP-036-seaweedfs.md`). A fix for a hazard-relevant advisory
reaches a deployment as a reviewed change of the pinned image digest in
`infra/docker-compose.yml`, with the SOUP-036 record updated, then a restart of the stack.

### 6. Database migrations and roles

`db-migrate` is a one-shot service and the only process that migrates. In one run, as the owner
user `medhub` (`DATABASE_OWNER_URL`), it (1) checks the secret settings, (2) runs
`alembic upgrade head`, and (3) runs `python -m app.db.roles`, which creates or updates the
runtime role named in `DATABASE_URL` (`medhub_app`: no superuser, no ownership, no membership,
SCRAM password) and grants it the statements the application needs. The role can read and insert
`audit_log` rows but cannot `UPDATE`, `DELETE` or `TRUNCATE` them (SQLSTATE `42501`, SR-023 AC 8),
and cannot write `alembic_version`. A table added by a later migration is granted by the same run
that creates it. `backend`, `celery-worker` and `celery-beat` connect as the runtime role and
start only after `db-migrate` exits 0. Do not run `alembic` in any other container.

```bash
docker compose -f infra/docker-compose.yml up db-migrate   # re-run at any time; it is idempotent
```

`db-migrate` refuses a runtime role that already exists as a superuser, as a member of another
role, or as an owner of objects, and a `DATABASE_URL` that names the owner's user or password.

The Celery worker (`celery-worker`) and the scheduler (`celery-beat`, which runs the retention
sweep on `RETENTION_SWEEP_CRON`) are separate containers started from the same image. Run exactly
one `celery-beat`: a second one sends every scheduled task twice. Compose cannot forbid
`--scale celery-beat=2`, so `bash infra/smoke-test.sh` (section 12) fails unless exactly one
`celery-beat` container is running.

No service reads `infra/.env` as a whole (there is no `env_file`). Compose fills each service's
settings from `infra/.env` or the shell by interpolation, and each service lists only the settings
it reads, so the owner password (`POSTGRES_PASSWORD`, `DATABASE_OWNER_URL`) reaches `postgres` and
`db-migrate` only. The smoke test checks this by value: it reads the owner password from the
`postgres` container and fails when it appears in the environment of any other running container.
A new setting for a service must be added to that service's `environment:` in
`infra/docker-compose.yml`; a line in `infra/.env` alone does not reach it. The API container gets no
SMTP credential (only the worker sends mail), and the beat container gets the secret settings only
because the start-up rule checks them all.

### Upgrading an installation that connects as the owner

For a host that ran the stack before `db-migrate` existed (`DATABASE_URL` is the owner's
connection). Applies PRB-005, PRB-007 and PRB-061. Do not merge, tag or deploy this change to a
shared database until you have rehearsed these steps on a copy of your data.

1. Back up: stop the stack and keep a copy of the `postgres_data` volume and a `pg_dump -Fc`
   (see "Migrating from MinIO", step 1, for read-only volume copies).
2. In `infra/.env`: move the current `DATABASE_URL` value to the new `DATABASE_OWNER_URL`
   (the owner connection, password `POSTGRES_PASSWORD`), then set `DATABASE_URL` to
   `postgresql://medhub_app:<new password>@postgres:5432/medhub` with a password generated by
   `openssl rand -hex 24`. Remove no other setting.
3. `docker compose -f infra/docker-compose.yml up db-migrate`. Expect the migrations since your
   version (0009 drops the `audit_log` rules that turned `UPDATE` and `DELETE` into silent no-ops)
   and the line `database roles applied for runtime role medhub_app`; exit code 0. Until this
   step has run, an owner connection can still alter `audit_log` after 0009 (the window accepted
   in CR-004 D-4); the stack is never started on the old settings in between.
4. `docker compose -f infra/docker-compose.yml up -d --build`, then `bash infra/smoke-test.sh`.
5. Roll back by restoring the volume copy from step 1 and the previous `infra/.env`; the previous
   release's entrypoint migrates as the owner. **Every row written after the upgrade is lost**
   (the restore returns the database to step 1). Roles are cluster-wide, not part of one database,
   so `medhub_app` is not removed by restoring a `pg_restore` dump into the upgraded server: the
   role survives it. Only restoring the step-1 volume copy (which predates the role) removes it.
   Leaving the role in place is harmless (it can log in only with its own password and no
   application uses it). To remove it, run `DROP OWNED BY medhub_app; DROP ROLE medhub_app;` as the
   owner.

Rehearsal result (TASK-191, 2026-11-01, scratch Compose projects, removed afterwards): the
previous release (migrations through 0008, the `audit_log` rules in place, 5015 `audit_log` rows,
two accounts, one clinical entry with an attachment) was upgraded in this way. `db-migrate` took
about 3 seconds; table row counts and a checksum of the 5015 pre-existing `audit_log` rows were
unchanged; an attachment written before the upgrade downloaded byte-identical through the reverse
proxy; the runtime role was refused `UPDATE`, `DELETE` and `TRUNCATE` on `audit_log` with
`42501`; the smoke test passed (59 checks). The full record is in TS-009 and TASK-191.

## Data Residency Note

All PHI (Protected Health Information) is stored exclusively in:

- **PostgreSQL** — `postgres_data` named volume on the host running Docker
- **Object store (SeaweedFS)** — `object_store_data` named volume with SSE-S3 AES256 at rest
  (SR-016, SR-022)

No PHI is transmitted outside the stack's two Docker networks (`medhub`, and `object-store`,
which is the only one with `internal: true`: no egress) except
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
old `.env` too: rollback needs it. (`xargs -r` means "do nothing when no container runs". It is a
GNU option; the BSD `xargs` of macOS already does nothing on empty input and accepts `-r` as a
no-op, so the line is the same on Linux and macOS.)

```bash
docker ps -q --filter "label=com.docker.compose.project=$P" | xargs -r docker stop
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
legacy() { docker compose -p "${P}-legacy" -f infra/migration/compose.minio-legacy.yml --env-file infra/.env "$@"; }
legacy up -d minio-legacy
legacy run --rm migrate; echo "exit=$?"
```

`legacy` is a shell function, so it works in bash and in zsh (a variable holding the command line
does not split into words in zsh). Define it in the same shell session as the later steps.

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
legacy --profile migrate down   # no -v: the volumes stay
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
