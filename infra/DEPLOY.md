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
| `OBJECT_STORE_ACCESS_KEY` | `object-store`, `object-store-preflight`, `object-store-init`, `backend`, `celery-worker`, `celery-beat`, `db-migrate` (the last two do not use it; the start-up rule requires it) | `openssl rand -hex 12` | Change the value and recreate the stack (rules in "Generate the object-store keys") |
| `OBJECT_STORE_SECRET_KEY` | same as the access key | `openssl rand -base64 32` | As the access key |
| `AT_REST_ENCRYPTION_KEY` | `backend`, `celery-worker`, `celery-beat`, `db-migrate` (field encryption); `object-store-preflight` (compared with the SSE key, nothing else) | `openssl rand -base64 32` (base64 of exactly 32 bytes) | Not by editing the value (pair it with `AT_REST_ENCRYPTION_KEY_ID`): follow "Field-encryption key rotation" ([ADR-0018](../docs/design/adr/0018-field-encryption-key-identifier-and-key-separation.md)) |
| `OBJECT_STORE_SSE_KEY` | `object-store` (as `WEED_S3_SSE_KEY`) and `object-store-preflight`; no other service | `openssl rand -base64 32` (base64 of exactly 32 bytes), a command of its own: never `AT_REST_ENCRYPTION_KEY` or a retired field key | Not by editing the value: the key belongs to the volume that holds the attachments. Follow "Separating the object-store SSE key" (a copy to a new volume under the new key) |
| `AT_REST_ENCRYPTION_RETIRED_KEYS` | `backend`, `celery-worker`, `celery-beat`, `db-migrate` (optional; decryption only) | Earlier keys as comma-separated `id:key` entries, each key `openssl rand -base64 32` output; empty unless a rotation is under way. Ids differ from `AT_REST_ENCRYPTION_KEY_ID` and from each other; a key must not equal the current key | Remove an entry only as the last step of "Field-encryption key rotation", once `--check` shows no value under its id |
| `SMTP_PASSWORD` | `celery-worker` only | Issued by your mail relay. Required only when `SMTP_USER` is set; leave `SMTP_USER` and `SMTP_PASSWORD` empty for a relay without authentication | Issue a new one at the relay, change the value, recreate `celery-worker` |

`AT_REST_ENCRYPTION_KEY_ID` is **not a secret** but is required, with no default: the identifier of
the current field-encryption key (1 to 32 characters of `a-z`, `0-9`, `-`; for example `k1`). Every
field value written from now on starts with `mh1:<id>:`, and the backend decrypts a value with the
key named in that prefix only. Existing installations must add it to `infra/.env` before upgrading;
pick an identifier for the key already in `AT_REST_ENCRYPTION_KEY` and keep it. Values written by
earlier versions have no prefix and are refused by the application; migration 0010, which
`db-migrate` runs before the backend starts, converts them (see "Converting existing field values"). The identifier and each retired id must have no spaces or
line breaks around them; the application refuses them at start-up.

`OBJECT_STORE_SSE_KEY` is the object store's server-side-encryption key (SR-041 AC 5, ADR-0018). It is
a key of its own: the field key and the SSE key are separate settings and the stack refuses to start
when they are equal, so replacing the field key (rotation) cannot make an attachment unreadable. The
object store and the preflight are the only services that receive it; the backend, the Celery
services and `db-migrate` do not (the object store encrypts, the backend only talks S3). The store
cannot tell which key an object was written under: **the key belongs to the volume**. Changing the
value on a volume that holds attachments makes them unreadable, so the stack checks it (below) and
the only way to move to another key is the copy in "Separating the object-store SSE key".

`OBJECT_STORE_VOLUME` is optional and empty by default (the volume is then `<project>_object_store_data`).
Only "Separating the object-store SSE key" sets it, to switch the store to the volume that holds the
attachments under the new key.

What refuses an unsafe value, and where:

- **Compose**: `POSTGRES_PASSWORD`, `DATABASE_OWNER_URL`, `DATABASE_URL`, `AT_REST_ENCRYPTION_KEY`, `AT_REST_ENCRYPTION_KEY_ID`,
  `OBJECT_STORE_SSE_KEY` and the two object-store keys use `${NAME:?…}`. `docker compose` stops before creating anything and the
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
- **`object-store-preflight`** (before the object store starts): refuses an `OBJECT_STORE_SSE_KEY` that
  is unset, empty, a placeholder, not base64 of exactly 32 bytes, or **the same key as
  `AT_REST_ENCRYPTION_KEY` or as an entry of `AT_REST_ENCRYPTION_RETIRED_KEYS`** (compared as decoded
  bytes, so another spelling of the same key does not pass). The message names the settings
  (`OBJECT_STORE_SSE_KEY is the same key as AT_REST_ENCRYPTION_KEY`), never a value.
- **`object-store-init`** (after the store is healthy, before the backend starts): reads the first byte
  of the first object in the bucket. A store started with a key other than the one its volume was
  written with cannot decrypt it; the initialiser exits 1 with `an object in the bucket cannot be read
  ... OBJECT_STORE_SSE_KEY is not the key this volume was written with`, so the backend stays down and
  nothing is written under the wrong key.

`SESSION_SIGNING_KEY` is no longer a setting (sessions are opaque random tokens held in Redis,
not signed). Remove it from an existing `infra/.env`; a leftover value is ignored.

#### Generate the object-store keys

`OBJECT_STORE_ACCESS_KEY` and `OBJECT_STORE_SECRET_KEY` have no default. Generate both, and
generate `AT_REST_ENCRYPTION_KEY` and `OBJECT_STORE_SSE_KEY` the same way (the other secrets are in
the "Secret settings" table above):

```bash
openssl rand -hex 12      # OBJECT_STORE_ACCESS_KEY
openssl rand -base64 32   # OBJECT_STORE_SECRET_KEY
openssl rand -base64 32   # AT_REST_ENCRYPTION_KEY (base64 of 32 random bytes)
openssl rand -base64 32   # OBJECT_STORE_SSE_KEY (base64 of 32 random bytes)
```

Run each command separately: the four values must all be different.

The `object-store-preflight` service stops the object store and its bucket initialiser, naming
the setting, when either key is unset or empty, equals a well-known default value
(list in `backend/app/core/object_store_credentials.py`, compared in any case), or when the secret key is shorter than
16 characters, and when `OBJECT_STORE_SSE_KEY` is rejected (rules in "Secret settings").

`AT_REST_ENCRYPTION_KEY` and `OBJECT_STORE_SSE_KEY` must be base64 that decodes to exactly 32 bytes.
Thirty-two ASCII characters decode to 24 bytes and `openssl rand -hex 32` to 48 bytes, so neither
works; the application and the preflight refuse them at start-up.

Set `OBJECT_STORE_SSE_KEY` **before the first start** and never change it on a store that holds data
(`WEED_S3_SSE_KEY` is taken from it): with a different value on the same volume the stored
attachments can no longer be read. Back both keys up with the volumes they protect.

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

**Module manifests.** At start-up the backend discovers installed modules (entry-point group
`medhub.modules`). A module whose manifest is invalid (a `module_key` not matching
`^[a-z][a-z0-9_-]{0,63}$`, an empty name, a version that is not a complete semantic version, or
`required_permissions` that is not a list) is skipped, and the only trace is a WARNING in the
`backend` log (`Manifest rejected: ...`, showing at most 80 characters of the offending value). Read
the log after installing or upgrading a module:
`docker compose -f infra/docker-compose.yml logs backend | grep "Manifest rejected"`.

**The backend can then fail to start.** When at least one module is valid, the registry sync deletes
the registry row of every module that is no longer discovered: one whose manifest is now rejected, and
one that was uninstalled. That delete fails with a foreign-key error
(`fk_group_module_enablement_module_id`, no `ON DELETE`) whenever any group has an enablement row for
the module, enabled or not. Disabling the module for the groups does not help: it only sets
`enabled=false` and keeps the row. The lifespan then logs `Module registry sync failed at startup` and
re-raises, so the backend does not start. Remedy: fix the manifest, or reinstall the previous version
of the module, then restart the backend. This is a known defect (PRB-075).

### 5. Check the object store

There is nothing to create by hand: the bucket is created by the stack. The object store is
SeaweedFS 4.51, pinned by tag and digest in `infra/docker-compose.yml` (ADR-0015, SOUP-036). It
has no console or admin UI, no host port, and sits on its own `object-store` network (below).

| Service (one-shot unless noted) | What it does |
|---|---|
| `object-store-preflight` | Checks the two credentials and the SSE key (rules in "Generate the object-store keys" and "Secret settings") with no network; exits non-zero, naming the setting, when one is rejected |
| `object-store` (long-running) | The S3 server. Healthy only when its S3 endpoint answers |
| `object-store-init` | Waits for a healthy store; creates the bucket `OBJECT_STORE_BUCKET` (default `medhub`) if missing, sets AES256 default encryption, reads it back, checks the bucket has no policy, and reads the first byte of the first stored object (a wrong SSE key for the volume fails here). Exits non-zero on any failure |

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
docker compose -f infra/docker-compose.yml up --build --exit-code-from db-migrate db-migrate   # re-run at any time; it is idempotent
```

Always run it with both flags. `--build` rebuilds the image from the current source: without it
Compose reuses the image of the previous release, which has none of the new migrations, and the run
ends with exit code 0 and `database roles applied` while the database stays where it was (PRB-062).
`--exit-code-from db-migrate` makes the command return the container's exit code: a plain `up` returns 0
even when `db-migrate` refused and exited 1. The smoke test also fails when `alembic_version` is not
the head revision of the tree.

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
   `openssl rand -hex 24`. Remove no other setting. **If the object store holds attachments written
   under `AT_REST_ENCRYPTION_KEY` (every release before this one), also make the `infra/.env` edits of
   "Separating the object-store SSE key" now (step 3 there): this release's Compose file needs
   `OBJECT_STORE_SSE_KEY` for every command, including the next one. Then run steps 1 to 3 here,
   skip step 4, and continue with that section** (its step 7 starts the stack).
3. `docker compose -f infra/docker-compose.yml up --build --exit-code-from db-migrate db-migrate`. Expect the migrations since your
   version (0009 drops the `audit_log` rules that turned `UPDATE` and `DELETE` into silent no-ops)
   and the line `database roles applied for runtime role medhub_app`; exit code 0. Until this
   step has run, an owner connection can still alter `audit_log` after 0009 (the window accepted
   in CR-004 D-4); the stack is never started on the old settings in between.
4. `docker compose -f infra/docker-compose.yml up -d --build`, then `bash infra/smoke-test.sh`
   (not while attachments are still under the old key: see step 2 and "Separating the object-store SSE key").
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

### Converting existing field values (migration 0010)

Applies to a database that holds `clinical_entry.description` values written before the key
identifier existed (the only field-encrypted column). Migration 0010 re-encrypts each of them
under the key in `AT_REST_ENCRYPTION_KEY`, as `mh1:<AT_REST_ENCRYPTION_KEY_ID>:...`. Run it
as part of the upgrade, and rehearse it first on a restored copy of your data.

1. Back up as in step 1 above (volume copy and `pg_dump -Fc`). Migration 0010 changes every
   description, so the backup is the only way back from a mistake you find later.
2. In `infra/.env` add `AT_REST_ENCRYPTION_KEY_ID` (for example `k1`; the id you pick for the key
   already in `AT_REST_ENCRYPTION_KEY`, which stays unchanged) and, if you have none,
   `AT_REST_ENCRYPTION_RETIRED_KEYS=` empty. The key must be the one that wrote the existing values.
3. `docker compose -f infra/docker-compose.yml up --build --exit-code-from db-migrate db-migrate`.
   **Use both flags** (section 6): without `--build` Compose runs the previous `db-migrate` image, which
   does not contain 0010 and exits 0 without converting anything; without `--exit-code-from` a refusal
   (exit 1) is reported as exit code 0. Expect the line `migration 0010 upgrade: N clinical_entry.description
   value(s) converted` and exit code 0 (check `echo $?` right after the command).
4. `docker compose -f infra/docker-compose.yml up -d --build`, then `bash infra/smoke-test.sh`.
   If the object store still holds attachments under the old key, skip this step and continue with
   "Separating the object-store SSE key" (step 4 there).

Behaviour: the table is locked against writes while the migration runs (readers continue); all
values are checked first and nothing is written if one fails; then they are converted in batches of
500 in one transaction. If any value does not decrypt with the current key (a wrong
`AT_REST_ENCRYPTION_KEY`, or a damaged value) the migration stops with exit code 1 (with `--exit-code-from`), the message
`migration 0010 upgrade refused: N clinical_entry.description value(s) do not decrypt with the
current key` and the row ids (first 100), and the database is unchanged. Values and ciphertext are
never printed. Fix the key (or the rows, see "A row that does not decrypt") and run it again; a second run converts nothing that is
already converted and changes no `mh1:` value. A value that already starts with `mh1:` is never
touched, whichever key it names (rotation is a separate procedure: "Field-encryption key rotation").

Roll back: restore the step-1 backup. The migration also has a `downgrade` (it writes the unprefixed
format back under the current key and stops, changing nothing, if any value names another key), which
is tested but not part of this procedure and was not rehearsed on a stack.

### A row that does not decrypt (migration 0010 refused)

The same procedure applies when the rotation command (`python -m app.db.reencrypt`, see "Field-encryption
key rotation") refuses with `value(s) do not decrypt`: it names the same row ids and changes nothing.
Where this section says "run the `db-migrate` command again", run the command that refused again
(`--check` or `--apply`). A value under a retired key that the command reports as `do not decrypt`
while the retired key is configured is damaged in the same sense; one that reports `name key id
'<id>', which is not configured` is not damaged, its key is missing: put the key back first.

`db-migrate` printed `migration 0010 upgrade refused: N clinical_entry.description value(s) do not
decrypt with the current key` and row ids, and exited 1. Nothing was changed. While it refuses, `backend`,
`celery-worker` and `celery-beat` do not start (they wait for `db-migrate` to complete), so the
application cannot be used to repair or annotate anything. This is a manual procedure: the repository
has no tool for it, and the SQL below is run with `psql` as the owner. **Direct SQL is not written to
`audit_log`**, which only the application writes.

**Never `DELETE` a `clinical_entry`.** The application has no path that deletes one (SR-012 AC 4,
SR-024 AC 4), a delete is not audited, and it fails for an entry that has attachments.

1. Back up first (volume copy and `pg_dump -Fc`) and keep the `db-migrate` output. It lists the first
   100 ids; if N is larger, fix those and run again to get the next ones.
2. **Check the key settings before suspecting the rows.** A wrong or swapped `AT_REST_ENCRYPTION_KEY`
   makes every unconverted row fail, so N equal to the number of unconverted rows points at the key.
   Compare with the key that was in `infra/.env` when the rows were written (an old copy of `.env`, a
   secret store). With the right key, run the `db-migrate` command again.
3. If only some rows are named, the stored value was damaged after it was written (a partial restore, a
   manual edit, a disk fault). **Open a problem report (PRB, IEC 62304 §9) for every damaged row.** Record
   in it the row id, the `db-migrate` output, the cause if known, the decision taken, and **every manual
   change** you make (each `UPDATE`, with the date, who ran it and the old and new value's SHA-256),
   because `audit_log` does not see them.
4. Then, in this order:
   - **(a) Restore the value from a backup taken before the damage.** Restore that backup to a scratch
     database, copy that one value into the live row (`UPDATE clinical_entry SET description = '<value>'
     WHERE id = '<id>'`), note it in the PRB, and run `db-migrate` again. The value may be in either
     format (the migration converts the earlier one; a value in `mh1:` form must name a configured key),
     and it must decrypt with the key of step 2. **A value in `mh1:` form is skipped by migration 0010,
     so `db-migrate` exiting 0 does not prove that it decrypts.** Once the stack is up, open that
     clinical entry through the API (as a doctor with consent for the patient) and confirm the text is
     readable; if it is not, the value is still damaged, or names a key that is not configured (the
     key-id check of `db-migrate` catches the second case, not the first). Note the result in the PRB.
   - **(b) No good copy exists: stay on, or roll back to, the previous release** (restore the step-1
     volume copy if the new release has already changed data) until the responsible person decides what
     to do. Do not continue the upgrade meanwhile.
   - **(c) Only if the responsible person decides in writing to go on without the text** (record the
     decision in the PRB):
     1. Keep the damaged stored value outside the application schema. For example, write it to a file in
        the backup set: `docker compose -f infra/docker-compose.yml exec -T postgres sh -c 'psql -U
        "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT id, description FROM clinical_entry"' | grep
        '^<id>|' > damaged-<id>.txt`. **Treat that file as PHI**: it is ciphertext, but it can be read if
        the right key is found, and it is the only copy of the original value. Create it with `umask 077`
        in force (`(umask 077; docker compose ... > damaged-<id>.txt)`), write it into the backup location
        (the same access control as the backup set), never into the repository or a ticket, and record its
        SHA-256 (`shasum -a 256 damaged-<id>.txt`) in the PRB, not its content. Do **not** create a table for it in `public`: the next
        `db-migrate` grants the runtime role access to every table there, and erasure (SR-024) does not
        know the table.
     2. Produce a placeholder encrypted under the current key (it prints one `mh1:<id>:...` line):
        `docker compose -f infra/docker-compose.yml run --rm --no-deps -T --entrypoint python db-migrate
        -c "from app.db.crypto import encrypt; print(encrypt('[Original text unreadable since <date>;
        see <PRB id>]'))"`.
     3. `UPDATE clinical_entry SET description = '<that line>' WHERE id = '<id>'`, and note it in the PRB.
     4. Run the `db-migrate` command again. It skips values that start with `mh1:`, so the row, its
        attachments and its place in the patient's history are kept, and the application shows the
        placeholder text.
5. Once the stack is up, a doctor with consent for that patient can add a clinical note about the lost
   text if it is needed. An operator cannot do that.

Rehearsed (TASK-194 round 3, scratch project `task194c`, removed afterwards): a stack at 0010 with two
entries, one of them with an attachment; that entry's `description` set to a non-envelope value and
`alembic_version` set to 0009. `db-migrate` exited 1 naming that one row and no value; the damaged
value was written to a file; the placeholder command printed one `mh1:k1:` line; after the `UPDATE`,
`db-migrate` exited 0 and left both rows, the API returned the placeholder text for the entry, the
attachment downloaded byte-identical, the other entry was unchanged, and the smoke test passed (65
checks). The export command of 4(c) step 1 was run in the form shown against a scratch PostgreSQL (the full run used an equivalent `docker exec psql`). Steps 4(a) and 4(b) were not run on a stack.

Rehearsal result (TASK-194, 2026-11-01, scratch Compose projects `task194` and `task194r`, removed
afterwards): the layout of commit `284e7e6` (migrations through 0009) was seeded through the API
with 1100 clinical entries (unicode, 25 to about 500 characters). After the steps above, `db-migrate`
converted all 1100 in about 8 seconds including the image build; a SHA-256 of each row's decrypted
plaintext, computed by a separate script, was identical before and after for all 1100; the API read
the same descriptions; a new entry was stored as `mh1:k1:`; a second `db-migrate` run left the
column byte-identical (same MD5 over id and stored value); the smoke test passed (64 checks). On a
restored `pg_dump` copy, a run with a wrong `AT_REST_ENCRYPTION_KEY` exited 1 naming 1100 rows
and left the column unchanged, and the run with the right key then converted all 1100. The full
record is in TASK-194 and TS-008.

### Separating the object-store SSE key

For a host whose object store was written under `AT_REST_ENCRYPTION_KEY` (every release before
TASK-196 used it as the store's SSE key). SR-041 AC 5, ADR-0018, RISK-011, RISK-007. A host with no
attachments needs none of this: set `OBJECT_STORE_SSE_KEY` (a new value) and start the stack. A new
installation sets it from the start. This procedure changes no database row.

**Order on an installation that comes from a release before this one.** Compose reads the whole
file, so once this release's files are in place every `docker compose` command needs
`OBJECT_STORE_SSE_KEY`, and the stack cannot be started on a store that holds attachments under the
old key until step 7 (the initialiser refuses it, as designed). The copy tool also needs the runtime
database role that `db-migrate` creates. So the sections run in this order, in one maintenance window:

1. Take the `pg_dump` first (it needs a running `postgres`), then stop the stack once, with
   `docker compose down` from the old release's directory and files (step 1; no `-v`), and take the other backups of the other upgrade sections (the `postgres_data` copy and the `pg_dump`)
   together with steps 1 and 2 of this section. `down` is needed, not only `stop`: a release before the
   fixed subnet (`172.28.77.0/24`, see "Trusted proxy and the Compose subnet") leaves a `medhub` network
   that this release cannot attach the reverse proxy's fixed address to, and `up` then fails with `user
   specified IP address is supported only when connecting to networks with user configured subnets`.
2. Edit `infra/.env` as in step 3 of this section **first**: `OBJECT_STORE_SSE_KEY` (new),
   `OBJECT_STORE_VOLUME` (`$NEW_VOL`) and the temporary `SOURCE_SSE_KEY`; then make the edits the
   other sections ask for (owner and runtime connection, `AT_REST_ENCRYPTION_KEY_ID`).
3. Run "Upgrading an installation that connects as the owner" steps 1 to 3 and "Converting existing field
   values" steps 1 to 3, that is, up to and including their `db-migrate` command (one run does both,
   so do them in this order and **stop there**). Skip their `up -d` and smoke-test steps: they fail
   while the attachments are under the old key.
4. Steps 4 to 7 of this section. Step 7 starts the stack; the smoke test runs after it.

An installation that already has the earlier changes (migrated, `AT_REST_ENCRYPTION_KEY_ID` set) starts
at step 1 of this section.

Why a copy. SeaweedFS has one SSE key per volume and cannot re-key an object in place (SOUP-036 F-4),
and it cannot tell which key an object was written under: reading with the wrong key fails with
HTTP 500. So the key of an object is the key of the volume it is on, and the attachments are moved by
**copying** every object from a store running on a copy of the old volume under the old key to the
stack's store running on a new volume under the new key
(`backend/scripts/migrate_object_store.py`, the tool of "Migrating from MinIO"). For each attachment
row the tool reads the object from the source, compares its SHA-256 with `attachment.checksum`,
writes it to the target, reads it back and compares again. The source is only read, nothing is
deleted anywhere, the run can be repeated (an object that is already on the target with the right
checksum is skipped), and any object that is missing, mismatched or cannot be read is listed by
attachment id (never by storage key, which holds the patient id and the file name) with exit code 1.

Variables used in every command below (one project name throughout):

```bash
P=infra                              # Compose project of the stack (the default is the directory name)
BK=/secure/path/outside/the/repo     # holds the tar of the old volume; must not be inside a Docker volume
BKENV=/other/secret/store/path       # holds the copy of the old .env; NOT the same place as $BK
HELPER=alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd   # any image pinned by digest
OLD_VOL=${P}_object_store_data       # the volume of the running stack: backed up, never changed
SRC_VOL=${P}_object_store_data_src   # a copy of it; the store that reads the old key runs on this
NEW_VOL=${P}_object_store_data_sse   # new; Compose creates it empty in step 4; the stack's store runs on it under the new key
```

If you upgrade the code and start the stack before doing this, nothing is lost and nothing is written
under the wrong key: Compose stops naming `OBJECT_STORE_SSE_KEY` while it is unset; the preflight
refuses it while it equals `AT_REST_ENCRYPTION_KEY`; with a new key on the old volume `object-store-init`
exits 1 (`... OBJECT_STORE_SSE_KEY is not the key this volume was written with`) and the backend stays down.

#### 1. Stop the stack and back up (read-only)

```bash
docker compose -p "$P" -f infra/docker-compose.yml down     # run with the files and .env of the release you are leaving; no -v: removes containers and networks, keeps every volume
( umask 077; mkdir -p "$BK" "$BKENV"; cp infra/.env "$BKENV/env.before-sse" )
docker run --rm --network none -v "$OLD_VOL":/src:ro -v "$BK":/out "$HELPER" sh -c \
  'tar -C /src -cf /out/object_store_data.tar . && cd /out && sha256sum object_store_data.tar > SHA256SUMS-sse && chmod 400 object_store_data.tar SHA256SUMS-sse'
```

The tar holds the attachments encrypted under the old key, and `env.before-sse` holds that key (it is
`AT_REST_ENCRYPTION_KEY`): **together they are the attachments in plain text.** Keep them in
different places, both with restricted access (the commands above create them mode 077 / 400), and never
copy `env.before-sse` into `$BK`.

Also take the PostgreSQL backup of the section you used for the upgrade; this procedure reads the
database but does not change it.

#### 2. Restore the backup into the copy

```bash
docker volume create "$SRC_VOL"
docker run --rm --network none -v "$SRC_VOL":/dst -v "$BK":/in:ro "$HELPER" \
  tar -C /dst -xpf /in/object_store_data.tar
```

#### 3. Configure

In `infra/.env` add:

- `OBJECT_STORE_SSE_KEY=` a new value from `openssl rand -base64 32`, a command of its own.
- `OBJECT_STORE_VOLUME=` the value of `$NEW_VOL` (the store now runs on the new volume).
  **Once set, never clear it and never change it.** It is part of the `.env` you back up. An empty value
  falls back to `$OLD_VOL`, and a mistyped one names a volume that does not exist: Compose creates it
  empty, the store starts, the initialiser passes (an empty bucket is valid) and every attachment
  answers 500 while new uploads go to the wrong volume. The smoke test compares the objects in the bucket
  with the attachment rows and fails in that case. A change of this setting alone does not recreate
  `object-store` under Compose 2.20.2, so the mistake would surface at a later restart.
- `SOURCE_SSE_KEY=` the current value of `AT_REST_ENCRYPTION_KEY`: the key the old volume was written
  under. Temporary; step 7 removes it. Only the migration file below reads it.

`AT_REST_ENCRYPTION_KEY` itself stays as it is.

#### 4. Start the new store on the new volume (uploads stay blocked)

```bash
docker compose -p "$P" -f infra/docker-compose.yml up -d postgres
docker compose -p "$P" -f infra/docker-compose.yml up -d --build --force-recreate object-store-init
docker wait "$(docker compose -p "$P" -f infra/docker-compose.yml ps -a -q object-store-init)"   # prints the initialiser's exit code: 0
docker inspect "$(docker compose -p "$P" -f infra/docker-compose.yml ps -a -q object-store)" --format '{{range .Mounts}}{{.Name}}{{end}}'   # prints $NEW_VOL
```

This runs the preflight (it must exit 0: a value equal to the field key is refused here), recreates
`object-store` on `$NEW_VOL` (`--force-recreate`, so the new volume is mounted even if only
`OBJECT_STORE_VOLUME` changed), and creates the empty bucket. `up -d` returns before the one-shot
initialiser has finished, so `docker wait` is how you see its exit code; anything but 0 means stop and
read `docker compose -p "$P" -f infra/docker-compose.yml logs object-store-preflight object-store-init`.
Do not start the reverse proxy or the backend yet, so no upload can reach the new store before
verification passes.

#### 5. Start the source store on the copy and copy

```bash
export OBJECT_STORE_NETWORK=${P}_object-store DATABASE_NETWORK=${P}_medhub SOURCE_STORE_VOLUME="$SRC_VOL"
rekey() { docker compose -p "${P}-rekey" -f infra/migration/compose.sse-source.yml --env-file infra/.env "$@"; }
rekey up -d object-store-source
rekey run --rm --build migrate; echo "exit=$?"
```

`rekey` is a shell function, so it works in bash and in zsh. The file `infra/migration/compose.sse-source.yml`
starts the same pinned SeaweedFS image on `$SRC_VOL` with `SOURCE_SSE_KEY`, on an internal network
that only the migration container joins. The tool prints six counts: `copied`,
`already-present-and-matching`, `missing-in-source`, `checksum-mismatch`, `read-or-write-error`,
`orphans-in-source`, then one `MISSING`, `MISMATCH`, `ERROR` or `ORPHAN` line per exception.

- **Exit 0**: every attachment row is on the new store with the recorded checksum.
- **Exit 1**: do not go on. `ERROR` lines on every row mean the source could not decrypt: check
  that `SOURCE_SSE_KEY` is the key the old volume was written with. `MISSING` or `MISMATCH` name rows
  whose object is absent or damaged in the source: the old volume and the backup are untouched, so
  investigate before any further step. Fix the cause and run the command again; it copies only what is
  not yet on the target. `ORPHAN` lines are objects in the old volume that no row refers to: they are
  reported and never copied.
- The tool needs the runtime database role to read `attachment`; it changes nothing in the database.

#### 6. Verify

1. Run the `rekey run --rm --build migrate` command again: `copied: 0`, every row
   `already-present-and-matching`, exit 0.
2. Start the backend only (still no proxy): `docker compose -p "$P" -f infra/docker-compose.yml up -d --build backend celery-worker celery-beat`.
   `object-store-init` has read an object back by now. Download every attachment through
   `GET /api/v1/attachments/<id>` as its owner (the way the section "Migrating from MinIO", step 5, does
   it) and compare the SHA-256 of each response with `attachment.checksum`; the application also refuses
   a stored-checksum mismatch with 502.
3. Search the new volume read-only for a plaintext marker from one of the documents (a phrase you
   know is inside a stored file). It must find nothing:
   `docker run --rm --network none -v "$NEW_VOL":/src:ro "$HELPER" grep -rlaF 'a phrase from a stored file' /src`.

The smoke test is not part of this step: the reverse proxy and the frontend are not running yet, so
several of its checks (login through the proxy, the probe tools in `reverse-proxy` and `frontend`, the
`frontend` container and image, the single-page app) would fail (five did in the rehearsal). It runs after
step 7.

#### 7. Retire the source store, open the stack and run the smoke test

Step 7 works in a new shell: define the variables at the top of this section again, then

```bash
export OBJECT_STORE_NETWORK=${P}_object-store DATABASE_NETWORK=${P}_medhub SOURCE_STORE_VOLUME="$SRC_VOL"
rekey() { docker compose -p "${P}-rekey" -f infra/migration/compose.sse-source.yml --env-file infra/.env "$@"; }
rekey --profile migrate down        # no -v: the volumes stay; it still needs SOURCE_SSE_KEY in infra/.env
# now remove SOURCE_SSE_KEY from infra/.env
docker compose -p "$P" -f infra/docker-compose.yml up -d --build
COMPOSE_PROJECT_NAME="$P" bash infra/smoke-test.sh
```

Without the shell function the first command is `docker compose -p "${P}-rekey" -f infra/migration/compose.sse-source.yml --env-file infra/.env --profile migrate down`.
The smoke test must report 0 failed. It checks that the store's SSE key differs from the field key and
is in no container but the store, and that **the bucket holds at least as many objects as there are
`attachment` rows** (a store on a wrong or empty volume fails it).

Uploads are accepted from this point and exist only on `$NEW_VOL`. Keep `$OLD_VOL`, `$SRC_VOL`, the
tar and `env.before-sse` until the owner of the data releases them; nothing here deletes them.
**They hold the attachments under the old key, which is also your field key**, and the tar with
`env.before-sse` is those attachments in plain text. Until they are deleted, rotating the field key does
not protect those copies. Delete them (the volumes, the tar, `env.before-sse` and any other copy of the old
`.env`) as soon as the owner agrees. Deleting them also deletes for good any `ORPHAN` object (an object
that no attachment row refers to, normally the remains of a failed upload): the tool reports orphans and
never copies them, so they exist only on `$OLD_VOL`, `$SRC_VOL` and the tar. Decide about them first.

#### Rollback

Only before step 7's `up -d`, while uploads are blocked. The path depends on where the installation came from.
After uploads have been accepted on `$NEW_VOL` they exist nowhere else; **rolling back loses them**. The tool
copies in one direction only (swapping the roles of the two stores is possible but has not been rehearsed), so
after that point fix forward. The current release cannot run on `$OLD_VOL`: a key equal to the field key is refused.

**(a) From `f7d79fc`, an installation that already had the earlier changes** (the owner/runtime roles, the key
identifier). `docker compose -p "$P" -f infra/docker-compose.yml down` (no `-v`), check out the last release before
TASK-196 in a second tree (`git worktree add ../medhub-pre-task196 f7d79fc`), put `$BKENV/env.before-sse` back as its
`infra/.env` and start it; `$OLD_VOL` was never changed, and it is the volume that release mounts.

**(b) From a release before CR-004** (`4d57094`, the owner connection as `DATABASE_URL`, no key identifier).
`env.before-sse` is that release's `.env`, which `f7d79fc` cannot start with, and `db-migrate` has already taken the
database to migration 0010 (descriptions are `mh1:k1:…`), which the old release cannot read. So:
1. `docker compose -p "$P" -f infra/docker-compose.yml down` (no `-v`), with this release's files.
2. Restore the `postgres_data` copy taken in step 1 of "Upgrading an installation that connects as the owner" (or
   the `pg_dump` into an empty volume). Without it the old release meets a database it cannot read.
3. Check out the release you came from in a second tree (`git worktree add ../medhub-pre-cr004 4d57094`) and put
   `$BKENV/env.before-sse` back as its `infra/.env`.
4. Start it (`docker compose -p "$P" -f infra/docker-compose.yml up -d --build` in that tree): it mounts `$OLD_VOL`.
5. Verify: the backend is healthy, every attachment downloads with the status and SHA-256 it had before the upgrade,
   and the clinical descriptions read as before.

QA ran path (b) on 2026-11-02 (scratch project, from `4d57094`): backend healthy, the store on the original volume,
5 of 5 downloads with the status and SHA-256 of before the upgrade, 3 of 3 descriptions identical. The role note of
"Upgrading an installation that connects as the owner", step 5, applies: restoring the volume copy removes
`medhub_app`; a `pg_restore` does not.

A later change of `OBJECT_STORE_SSE_KEY` is the same procedure with this section's roles: the source is
a copy of the volume under the current `OBJECT_STORE_SSE_KEY` (`SOURCE_SSE_KEY` is that value) and the
target a new volume under the new one.

#### Rehearsal result

TASK-196, 2026-11-01 and 2026-11-02, scratch Compose project `task196` (images, volumes and networks created
for it and removed afterwards, `infra/.env` untouched).

**Path from the release before CR-004 (round 2, the reference path).** Commit `4d57094` with its own layout:
the owner as the application's database user (`DATABASE_URL`), `env_file`, no key identifier, the store's SSE key
equal to `AT_REST_ENCRYPTION_KEY`, a leftover `SESSION_SIGNING_KEY`, a fixed-subnet-less `medhub` network.
Seeded through the API with 30 clinical entries and 16 attachments on 12 of them: 0, 1, 17, 300, 1,023, 1,920,
4,096, 5,000, 65,537, 70,000, 999,999, 1,048,576, 3,145,728, 8,388,608, 25,165,824 and 50,331,648 bytes
(89,228,277 bytes in all; one holds a plaintext marker; two have file names outside Latin-1, see PRB-063). The
sections were followed in the order of this section's introduction:
- Order 1: live `pg_dump -Fc` (39,147 bytes), `docker compose down` (no `-v`), tar of the object volume (sha256
  `7b924c81…5ab2`) with mode 400 in `$BK`, `env.before-sse` in `$BKENV` with mode 600; the file-by-file hash of the
  original volume (67 files) equals that of the restored copy `$SRC_VOL`.
- Order 2 and 3: the `infra/.env` edits (SSE key, volume, `SOURCE_SSE_KEY`, owner and runtime URLs,
  `AT_REST_ENCRYPTION_KEY_ID=k1`), then one `up --build --exit-code-from db-migrate db-migrate`: exit 0, 10.7 s,
  `Running upgrade 0008 -> 0009`, `0009 -> 0010`, 30 values converted, `database roles applied for runtime role
  medhub_app`, `key ids verified; ... k1=30`. Nothing else was started.
- Step 4: `object-store-init` exit code 0 (`docker wait`), the store on `$NEW_VOL`.
- Step 5: `copied: 16`, every other count 0, exit 0 (24 s with the image build). Step 6.1: `copied: 0`,
  `already-present-and-matching: 16`.
- Step 6.2 and 6.3: 16 of 16 downloads with the status and SHA-256 they had on the old release (14 with status 200
  and the SHA-256 of the uploaded bytes; the two names outside Latin-1 answer 500 before and after, PRB-063; the
  tool compared their bytes); the marker in 0 files of the new volume and of the copy. The smoke test before step 7:
  64 passed, 5 failed (login through the proxy, the probe tools in `reverse-proxy` and `frontend`, the `frontend`
  container, the SPA through the proxy), as the text says.
- Step 7 in a new shell: `rekey --profile migrate down`, `SOURCE_SSE_KEY` removed, `up -d --build`, then the smoke test:
  **75 passed, 0 failed**, including "the object store holds every attachment" and, for each running container,
  that the SSE key is in the store's environment only. 16 of 16 downloads identical again. The original volume's
  file-by-file hash is unchanged.
- Earlier in the round a first run used `up -d` (without `--build`) and `docker stop` in step 1: the reverse proxy
  could not start (`user specified IP address is supported only when connecting to networks with user configured
  subnets`, the old `medhub` network has no fixed subnet) and the frontend image was the old one. That is why step 1
  uses `docker compose down` and step 7 uses `up -d --build`.
- A mistyped `OBJECT_STORE_VOLUME` (one character added) with the store force-recreated: the store started on an
  empty new volume, 0 of 16 attachments downloaded, and the smoke test reported **74 passed, 1 failed** (`the
  database has 16 attachment rows, the bucket 0 objects`); with the setting restored: 75 passed, 0 failed, 16 of 16
  identical.

**Path from the last commit before TASK-196 (round 1).** The old layout was the tree of commit `f7d79fc`, seeded
with 30 clinical entries and 15 attachments (0 B to 50,331,648 B). Steps 1 to 7 were run as written then:

- Refusals, each before the store started (`docker compose up` of the preflight only): `OBJECT_STORE_SSE_KEY`
  empty (Compose: `OBJECT_STORE_SSE_KEY must be set`), equal to `AT_REST_ENCRYPTION_KEY`, equal to a
  retired field key, `change-me-to-a-random-32-byte-key!`, 31 bytes and 48 bytes: exit 1 with the messages
  above and no value. A new key on a copy of the old volume (the upgrade without this procedure): the store
  started, `object-store-init` exited 1 with `an object in the bucket cannot be read (InternalError):
  OBJECT_STORE_SSE_KEY is not the key this volume was written with`, and the backend was not started. (The
  first version of that check read the first listed object; that object had size 0 and a range read on it
  answers `InvalidRange` before any decryption, so the check passed. An empty object is now read whole,
  and the smallest object of the first page is the one read.)
- Step 5: `copied: 15`, others 0, exit 0. With the source store started under a wrong key the tool listed all 15
  attachment ids as `ERROR`, copied nothing and exited 1; with the right key again it exited 0.
- Step 6: 15 of 15 downloads identical to the old ones; the marker in 0 files of the new volume and of the copy (and in
  1 file of a control volume holding it in plain text). The smoke test passed (74) after the stack was open.
- Rollback: the stack was taken down, the `f7d79fc` tree was started with `env.before-sse`, the
  PostgreSQL dump and the original volume: 15 of 15 downloads equal to the first ones.
- The field-key rotation after the separation is rehearsed at the end of "Field-encryption key rotation".

### Field-encryption key rotation

Replaces the key that encrypts `clinical_entry.description` (and any later `EncryptedString`
column) without making a stored value unreadable (SR-022 AC 8, ADR-0018, RISK-011). The tool is
`python -m app.db.reencrypt`, run from the `db-migrate` image as the database owner. Rotate when a
key may have been exposed, when someone who held it leaves, or on the schedule your site sets.
Rehearse it first on a restored copy of your data; the rehearsal result is at the end of this section.

**Precondition (met by the shipped Compose file).** The object store's SSE key is its own setting,
`OBJECT_STORE_SSE_KEY`, and the stack refuses to start when it equals `AT_REST_ENCRYPTION_KEY` or a
retired field key (`object-store-preflight`, rendered Compose test `infra/tests/test_compose_object_store.py`).
Replacing the field key therefore does not touch the key that encrypts the attachments: step 4 may
restart `object-store` (Compose restarts it with the preflight it depends on), and it comes back with
the same `WEED_S3_SSE_KEY` on the same volume. An installation that still has attachments under the old shared key first
completes "Separating the object-store SSE key": the shipped stack cannot be started on such a volume
(the initialiser refuses), so this rotation cannot be reached by mistake.

How the keys work: every stored value starts with `mh1:<key id>:` and is decrypted with the key of
that id. `AT_REST_ENCRYPTION_KEY` (id `AT_REST_ENCRYPTION_KEY_ID`) is the current key and encrypts
every new value. Keys in `AT_REST_ENCRYPTION_RETIRED_KEYS` (`id:key,id:key`) only decrypt. A rotation
makes the new key current, keeps the old one retired, re-encrypts every stored value under the new
key, and only then drops the old one. An id names one key for ever: never give a used id to a different
key, and never put two keys under one id. (Rotating back to an earlier key, as in "Rolling back",
uses its own id again; that is the same key.)

The command (all of them print counts, key ids, table and column names and row ids; never a value,
a ciphertext or a key):

| Option | What it does | Exit code |
|---|---|---|
| `--check` | Read only. Decrypts every value and counts them per key id | 0 every value is readable and under the current key; 3 readable, but some are under a retired key (rotation pending); 1 some value names a key id that is not configured, or does not decrypt: the row ids are listed |
| `--apply [--batch-size N]` | Re-encrypts every value not under the current key. First checks everything as `--check` does and, if anything is unreadable, stops with the counts and row ids before writing a single row. Then converts in batches of 500 (or N). Each batch is one transaction: lock the table against writers (the lock migration 0010 uses; readers continue), decrypt, encrypt under the current key, decrypt the new value and compare it with the plaintext, update, read the rows back from the database and compare again, commit. Any difference or error rolls that batch back and stops | 0 done (or nothing to do); 1 refused or failed, the failing batch was rolled back |
| `--verify-key-ids` | Read only, does not decrypt. Refuses if a stored value names a key id that is not configured. `db-migrate` runs it as its last step | 0 / 1 |

Run it as `docker compose -f infra/docker-compose.yml run --rm --no-deps --build -T --entrypoint python db-migrate -m app.db.reencrypt --check`
(`--apply`, `--verify-key-ids` likewise). `--build` makes Compose use the current source, not the
image of the previous release (PRB-062); `run` returns the command's exit code, so check `echo $?`
right after it. Each batch commits on its own: if the command is interrupted (a crash, a lost
connection, `Ctrl-C`) every row is readable under the current or a retired key; run it again and
it continues, and a run with nothing left to convert writes nothing. If it cannot get the table lock
within 10 seconds (a long write transaction) it stops. For the first batch that leaves the database
unchanged; after it, the batches already done stay committed and every row is readable under the
current or a retired key. The instruction is the same either way: run it again (see "If `--check` or
`--apply` exits 1").

**The application does not need to be stopped.** The lock is held for one batch at a time and a
write that arrives meanwhile waits for it. After step 4 the backend and worker write under the new
key, so a running application never creates work for the command. It must be restarted first
(step 4), because a process still running with the old key would keep writing values under the old
id; if one did, `--check` shows it (exit 3) and `--apply` converts it.

1. **Back up.** The values under the old key exist only in the database, and a restored backup is
   readable only with the key it was written with.
   - **Mandatory:** a live `pg_dump -Fc` (the stack stays up):
     `docker compose -f infra/docker-compose.yml exec -T postgres sh -c 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup-before-rotation.dump`.
     Check that the file is not empty.
   - Optional, and only with the stack stopped: a copy of the `postgres_data` volume, as in
     "Upgrading an installation that connects as the owner", step 1. Skip it to rotate with the
     application up.
   - There is no automated backup (PRB-057): the dump is the minimum.
   - Copy the current `infra/.env` to your secret store. It holds the old key and its id.
   - Run `--check` and keep the output (the count per key id before you start). Expect exit 0.
2. **Generate the new key and a new id.**
   `openssl rand -base64 32` (run on its own, never reuse a value). The id is new: `[a-z0-9-]`, 1 to
   32 characters, different from every id this installation has used (for example `k2` after `k1`).
3. **Edit `infra/.env`.** Move the old key to the retired list and set the new key and id:
   ```
   AT_REST_ENCRYPTION_RETIRED_KEYS=<old id>:<old AT_REST_ENCRYPTION_KEY value>   # append with a comma to an existing list
   AT_REST_ENCRYPTION_KEY=<the new key>
   AT_REST_ENCRYPTION_KEY_ID=<the new id>
   ```
   No spaces or line breaks around the id, and the new key must differ from every retired key; the
   settings are checked when each service starts and on every `db-migrate` run.
4. **Restart.** `docker compose -f infra/docker-compose.yml up -d --build`. `db-migrate` runs
   first (its key-id check passes because the old id is retired), then `backend`, `celery-worker`
   and `celery-beat` are recreated with the new settings. Confirm the services use the new id:
   `docker compose -f infra/docker-compose.yml exec -T backend printenv AT_REST_ENCRYPTION_KEY_ID`.
   Reading an entry still works: old values are decrypted with the retired key.
5. **Re-encrypt.** `… run --rm --no-deps --build -T --entrypoint python db-migrate -m app.db.reencrypt --apply`.
   Expect `clinical_entry.description before: <old id>=N`, `converted: N value(s) in B batch(es)`,
   `after: <new id>=N (current)` and exit 0. Then run `--check`: **it must exit 0 and list only the
   new id. A count under the old id means the old key is still needed.** If it exits 3, run `--apply` again.
6. **Only then remove the retired key.** Delete the `<old id>:<old key>` entry from
   `AT_REST_ENCRYPTION_RETIRED_KEYS` in `infra/.env` (leave the variable empty if that was the only
   entry) and run `docker compose -f infra/docker-compose.yml up -d --build` again. If a stored value
   still names the removed id, `db-migrate` prints `stored values need a key that is not
   configured` with the count and the row ids, exits 1, and `up` ends with `service "db-migrate"
   didn't complete successfully: exit 1`. Nothing in the database was changed. **The application is
   down while that is so**: Compose stops `backend`, `celery-worker`, `celery-beat` and
   `reverse-proxy` before it recreates `db-migrate` and does not start them again. Put the entry
   back in `infra/.env`, run `up -d --build` again (about 40 seconds with `--wait`; the
   application returns with its data intact), and go back to step 5. Keep the old key in your secret store for as long as you
   keep any backup made before step 3: restoring such a backup needs it (set it in
   `AT_REST_ENCRYPTION_RETIRED_KEYS` for the restore, then run step 5 again).
7. **Verify.** `bash infra/smoke-test.sh`, then open a clinical entry in the application (a doctor
   account) and read one that existed before the rotation.

**If `--check` or `--apply` exits 1.** Read the first line it printed.
- A *refusal* (`refused, nothing was changed`, or `--check` listing problems) changes nothing:
  - `value(s) name key id '<id>', which is not configured`: the key of that id is missing from the
    settings. Put it back in `AT_REST_ENCRYPTION_RETIRED_KEYS` (from your secret store or the backup
    of the old `.env`), restart, run the command again. Nothing is lost; the data was never touched.
  - `value(s) do not decrypt`: the stored value is damaged or the key under that id is not the one
    that wrote it. Check the key first; then follow "A row that does not decrypt".
- A *failure after `--apply` started* (`reencrypt failed: <Class>`, or a batch message ending
  `batch rolled back`) leaves the batches that were already committed in place and rolls back only
  the failing one. The table then holds a mix of old and new keys, all readable, and nothing is
  lost. Find the cause (`<Class>` is the database or Python error class; the database log has the
  rest: a lost connection, a lock that could not be had within 10 seconds, a full disk), fix it,
  and run `--apply` again; it continues where it stopped. Then `--check`.
- `values remain under another key after apply` means the run finished its batches but `--check`'s
  scan still finds values not under the current key (an old process wrote one meanwhile, or a
  value was damaged). Nothing was lost. Run `--check`: exit 3 means run `--apply` again, exit 1
  names the rows (see the two cases above). Do not remove the retired key until `--check` exits 0.

**Rolling back.**
- *Before step 5, or if step 5 converted nothing:* restore the `.env` copy from step 1 and run
  `up -d --build`. The database was not changed.
- *During or after step 5, without losing anything written since:* rotate back. Make the old key
  current again with its original id and retire the new one (`AT_REST_ENCRYPTION_KEY=<old key>`,
  `AT_REST_ENCRYPTION_KEY_ID=<old id>`, `AT_REST_ENCRYPTION_RETIRED_KEYS=<new id>:<new key>`),
  restart as in step 4 and run `--apply`: every value moves back under the old key. Then run
  `--check` (it must exit 0 and list only the old id) and finish with step 6, removing the
  now-retired new key, and step 7.
- *Last resort:* restore the step-1 backup and the `.env` copy. Every row written after the backup is lost.

Rehearsal result (TASK-195, 2026-11-01, scratch Compose projects `task195` and `task195r`, removed
afterwards, `infra/.env` untouched): a stack at the layout of this tree was seeded through the API
with 1100 clinical entries under key `k1` (unicode, 25 to about 500 characters) and six attachments.
That rehearsal used a scratch copy of `docker-compose.yml` whose object store had a separate SSE key,
because the shipped file shared the field key; the rehearsal on the shipped file (TASK-196) follows the
steps below. Steps 1 to 7 were run
as written, with the application up the whole time:
- Step 1: `pg_dump -Fc` (493 KB) and the `.env` copy; `--check` exit 0, `k1=1100`.
- Step 4: all three Python services reported `k2`; `--check` exit 3, `k1=1100`; the API returned
  all 1100 descriptions with the same SHA-256 as before (old values read through the retired key).
- **Step 6 run too early** (before step 5): `db-migrate` exit 1, `1100 value(s) name key id 'k1',
  which is not configured` with the first 100 row ids, `up` ended with `service "db-migrate" didn't
  complete successfully: exit 1`, the application was down (as warned), the database unchanged; with the entry put
  back, `up -d --build` took 19 seconds (40 with `--wait`) and the API again returned the same 1100 hashes.
- Step 5: 8 API writes (a background writer started with the command; they were committed before its first scan, so they
  were already under `k2`), then `--apply --batch-size 200`: `k1=1100, k2=8` before,
  `converted: 1100 value(s) in 6 batch(es)`, `k2=1108` after, exit 0; `--check` exit 0 listing only `k2`.
- Step 6 (in order): `db-migrate` exit 0 (`key ids verified; ... k2=1108`), services without any retired key.
  A SHA-256 of every row's plaintext, computed in a backend container with `AESGCM` and the keys
  from the environment (so with `k2` only), was identical to the one taken before the rotation for
  all 1100 pre-existing rows; the API list was identical for the same 1100; all six attachments
  downloaded with their original SHA-256.
- Step 7: `bash infra/smoke-test.sh` from a copy of the tree, 65 passed, 0 failed.
- Not rehearsed on a stack: the volume copy of step 1, rollback by rotating back, a power loss during `--apply`
  (tested with injected faults in `backend/tests/db/test_reencrypt.py`).
- On a **restored backup copy** (`task195r`: the step-1 dump restored into a new project, new key
  only): `db-migrate` exit 1 naming the 1100 values under `k1` (a backup taken before a rotation
  needs the old key); with `k1:<key>` retired, exit 0 and `--check` exit 3; `--apply` converted 1100
  in 3 batches, a second `--apply` converted 0 (exit 0); `--check` exit 0; with the retired key
  removed again `db-migrate` exit 0; all 1100 plaintext hashes equal to the ones taken on the first stack before the rotation.
- Why the shared key had to go (before TASK-196): on the first stack the object store's SSE key was
  changed to another value and the store restarted; all six attachment downloads then returned HTTP 500.
  Putting the key back restored them.

Rehearsal result on the shipped Compose file (TASK-196, 2026-11-01, project `task196`, removed
afterwards): after "Separating the object-store SSE key", with 30 clinical entries and 15 attachments (the
set described there), k1 was rotated to k2 as written, steps 1 to 7, with the application up:
- Step 1: `pg_dump -Fc` (42,743 bytes) and the `.env` copy; `--check` exit 0, `k1=30`.
- Step 4: `up -d --build` took 20 seconds; `backend`, `celery-worker` and `celery-beat` reported `k2`;
  `object-store` was recreated by Compose (it depends on the preflight, whose settings changed) and came
  back with the same `WEED_S3_SSE_KEY`; **all 15 attachments downloaded with the same status and SHA-256
  as before the rotation**.
- Step 5: a new 2.5 MB attachment was uploaded under `k2` first; `--apply`: `k1=30` before, `converted: 30
  value(s) in 1 batch(es)`, `k2=30 (current)` after, exit 0; `--check` exit 0. All 15 old attachments
  and the new one downloaded identically.
- Step 6: `db-migrate` alone exit 0 (`key ids verified; ... k2=30`), `up -d --build` 20 seconds; all 16
  attachments identical again; the SHA-256 of every clinical description returned by the API equal to
  the one taken before the rotation (30 of 30).
- Step 7: `bash infra/smoke-test.sh` 74 passed, 0 failed.
- With the shipped file, rotation of the field key therefore leaves the attachments readable at every
  step (TASK-195, on the earlier file, ended with six HTTP 500).

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
- `AT_REST_ENCRYPTION_KEY` stays: it encrypts field values and is what the old MinIO volume was
  written under. The new store has a key of its own: add `OBJECT_STORE_SSE_KEY` (a new value, see
  "Generate the object-store keys"). Add `LEGACY_KMS_KEY` only if the MinIO volume was written under a
  different key. `MINIO_KMS_SECRET_KEY` is no longer used by the stack.

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
