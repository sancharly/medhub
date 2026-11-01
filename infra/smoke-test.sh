#!/usr/bin/env bash
# infra/smoke-test.sh
# Validates Docker Compose configuration and documents runtime security checks.
# Run after `docker compose up -d` to confirm topology is correct.
#
# SR-008: Data in transit must be encrypted (TLS 1.2+, HTTPS redirect, HSTS)
# SR-016: PHI at rest must be encrypted (object-store SSE-S3 AES256)
# SR-040: object store has no console or admin option
# SR-041: every image MedHub builds runs as a non-root user (section 11)
# SR-023 AC 8: the application connects as the runtime role, which cannot alter audit_log (section 12)
# PRB-061: the Celery worker and beat run (sections 11 and 12)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Ensure a .env file exists for docker compose to parse
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "INFO: No infra/.env found — copying .env.example with throwaway secrets for validation only."
    # The template holds no value for a secret and Compose refuses an unset one (SR-041 AC 2), so
    # fill the secret settings with throwaway values: this file only lets `compose config` parse.
    awk -F= '
        $1 == "POSTGRES_PASSWORD" || $1 == "DATABASE_URL" || $1 == "DATABASE_OWNER_URL" \
            || $1 == "AT_REST_ENCRYPTION_KEY" \
            || $1 == "OBJECT_STORE_ACCESS_KEY" || $1 == "OBJECT_STORE_SECRET_KEY" \
            { print $1 "=throwaway-" tolower($1); next }
        { print }' "$SCRIPT_DIR/.env.example" > "$ENV_FILE"
    CLEANUP_ENV=1
else
    CLEANUP_ENV=0
fi
cleanup() { [ "$CLEANUP_ENV" -eq 1 ] && rm -f "$ENV_FILE"; }
trap cleanup EXIT
PASS=0
FAIL=0

check() {
    local name="$1"
    local result="$2"
    if [ "$result" = "ok" ]; then
        echo "  [PASS] $name"
        ((PASS++)) || true
    else
        echo "  [FAIL] $name: $result"
        ((FAIL++)) || true
    fi
}

echo "=== MedHub Smoke Tests ==="
echo ""

# ── 1. Docker Compose config is valid ───────────────────────────────────────
echo "-- Compose config --"
if docker compose -f "$COMPOSE_FILE" config --quiet 2>/dev/null; then
    check "docker-compose.yml is valid" "ok"
else
    check "docker-compose.yml is valid" "docker compose config failed"
fi

# ── 2. All required services are defined ────────────────────────────────────
echo ""
echo "-- Service topology --"
COMPOSE_SERVICES=$(docker compose -f "$COMPOSE_FILE" config 2>/dev/null | grep -E "^  [a-z]" | sed 's/://g' | tr -d ' ' || true)
for svc in reverse-proxy backend frontend postgres redis object-store celery-worker celery-beat db-migrate; do
    if echo "$COMPOSE_SERVICES" | grep -q "^${svc}$"; then
        check "service '${svc}' defined" "ok"
    else
        check "service '${svc}' defined" "missing from docker-compose.yml"
    fi
done

# ── 3. Only reverse-proxy publishes external ports ──────────────────────────
echo ""
echo "-- Port exposure (SR-008) --"
# Check that only reverse-proxy has 'ports:' in the raw compose file (grep-based).
# The backend, frontend, postgres, redis, object-store, celery-worker use 'expose:' (internal only).
UNEXPECTED_PORTS=0
for svc in backend frontend postgres redis object-store celery-worker celery-beat db-migrate; do
    # Look for ports: under each service block in the compose file
    if grep -A5 "^  ${svc}:" "$COMPOSE_FILE" | grep -q "^\s*ports:"; then
        check "service '${svc}' does NOT publish external ports" "FAIL — has ports: entry"
        ((UNEXPECTED_PORTS++)) || true
    fi
done
if [ "$UNEXPECTED_PORTS" -eq 0 ]; then
    check "only reverse-proxy publishes external ports (SR-008)" "ok"
fi

# ── 4. nginx.conf: HTTP→HTTPS redirect present ──────────────────────────────
echo ""
echo "-- TLS / HTTPS redirect (SR-008) --"
NGINX_CONF="$SCRIPT_DIR/reverse-proxy/nginx.conf"
if grep -q "return 301 https" "$NGINX_CONF" 2>/dev/null; then
    check "HTTP→HTTPS redirect configured" "ok"
else
    check "HTTP→HTTPS redirect configured" "missing 'return 301 https' in nginx.conf"
fi

# ── 5. nginx.conf: HSTS header present ──────────────────────────────────────
if grep -q "Strict-Transport-Security" "$NGINX_CONF" 2>/dev/null; then
    check "HSTS header configured (SR-008)" "ok"
else
    check "HSTS header configured (SR-008)" "missing Strict-Transport-Security in nginx.conf"
fi

# ── 6. nginx.conf: TLS 1.2+ only ────────────────────────────────────────────
if grep -q "TLSv1.2" "$NGINX_CONF" 2>/dev/null; then
    check "TLS 1.2+ enforced (SR-008)" "ok"
else
    check "TLS 1.2+ enforced (SR-008)" "missing ssl_protocols TLSv1.2 in nginx.conf"
fi

# ── 7. Object-store SSE and no console ───────────────────────────────────────
echo ""
echo "-- At-rest encryption (SR-016) --"
if docker compose -f "$COMPOSE_FILE" config 2>/dev/null | grep -q "WEED_S3_SSE_KEY"; then
    check "object-store SSE key configured (SR-022)" "ok"
else
    check "object-store SSE key configured (SR-022)" "WEED_S3_SSE_KEY missing from object-store service"
fi
# Static check on the store's command: no console or admin option (SR-040 AC 1).
STORE_CMD=$(docker compose -f "$COMPOSE_FILE" config --format json 2>/dev/null \
    | python3 -c 'import json,sys; print(" ".join(json.load(sys.stdin)["services"]["object-store"]["command"]))' 2>/dev/null || true)
if [ -n "$STORE_CMD" ] && ! echo "$STORE_CMD" | grep -qiE "console|admin|webdav|sftp|9001"; then
    check "object store has no console or admin option (SR-040 AC 1)" "ok"
else
    check "object store has no console or admin option (SR-040 AC 1)" "command missing or names a console/admin option: $STORE_CMD"
fi

# ── 8. Named volumes defined for persistent data ─────────────────────────────
echo ""
echo "-- Data persistence --"
for vol in postgres_data redis_data object_store_data; do
    if grep -q "^  ${vol}:" "$COMPOSE_FILE"; then
        check "named volume '${vol}' defined" "ok"
    else
        check "named volume '${vol}' defined" "missing"
    fi
done

# ── 9. Migrated schema: login endpoint returns 401 not 500 ──────────────────
# A 401 means the schema exists and the auth layer is active.
# A 500 means the DB is empty (no migrations applied).
# Posts through the reverse proxy: the backend port is not published (PRB-037);
# -k because the development certificate is self-signed.
echo ""
echo "-- Schema migration (SR-001.1, SR-003) --"
if command -v curl >/dev/null 2>&1; then
    LOGIN_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" \
        -X POST https://localhost/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"smoke@test.invalid","password":"unused"}' 2>/dev/null || true)
    if [ "$LOGIN_STATUS" = "401" ] || [ "$LOGIN_STATUS" = "422" ]; then
        check "POST /auth/login returns non-500 (schema migrated)" "ok"
    elif [ "$LOGIN_STATUS" = "" ]; then
        check "POST /auth/login reachable" "backend not running — skipping (run after docker compose up)"
    else
        check "POST /auth/login returns non-500 (schema migrated)" "got HTTP $LOGIN_STATUS (expected 401/422; 500 = empty schema)"
    fi
else
    echo "  [SKIP] curl not available — schema migration check skipped"
fi

# ── 10. Object-store network isolation (SR-040 AC 3, AC 5) ──────────────────
# Started-stack checks: skipped, with a message, only when no container of the project is running.
# When the stack is up, a missing object-store or backend is a FAIL, not a skip. The stack is the
# Compose project of the shell (COMPOSE_PROJECT_NAME, default `infra`).
# Probe tool per image: reverse-proxy and frontend (nginx:alpine) have no bash, so busybox
# `nc -z`; postgres and redis (Debian), backend and celery-worker (python:slim, Debian) have bash,
# so a /dev/tcp connect. Each probe has a positive control (same tool, a port that must answer)
# so a missing tool cannot pass as "refused".
echo ""
echo "-- Object-store network isolation (SR-040 AC 3, AC 5) --"
compose() { docker compose -f "$COMPOSE_FILE" "$@"; }
# connects SVC TOOL HOST PORT -> exit 0 when the TCP connection opens
connects() {
    local svc="$1" tool="$2" host="$3" port="$4"
    if [ "$tool" = "nc" ]; then
        compose exec -T "$svc" nc -z -w 3 "$host" "$port" >/dev/null 2>&1
    else
        compose exec -T "$svc" timeout 3 bash -c "exec 3<>/dev/tcp/$host/$port" >/dev/null 2>&1
    fi
}
if [ -z "$(compose ps -q 2>/dev/null)" ]; then
    echo "  [SKIP] stack not running — object-store isolation checks skipped (run after docker compose up)"
elif [ -z "$(compose ps -q object-store 2>/dev/null)" ] || [ -z "$(compose ps -q backend 2>/dev/null)" ]; then
    check "object-store and backend are running (needed for the isolation checks)" \
        "stack is up but object-store or backend is not running"
else
    # service:tool:control host:control port. Each control is a connection to another container,
    # so it also proves the probe tool and the service-name resolution work from that container.
    for entry in reverse-proxy:nc:backend:8000 frontend:nc:backend:8000 postgres:bash:redis:6379 \
                 redis:bash:postgres:5432 celery-worker:bash:redis:6379; do
        IFS=: read -r svc tool chost cport <<<"$entry"
        if ! connects "$svc" "$tool" "$chost" "$cport"; then
            check "probe tool works in '${svc}' (control $chost:$cport)" "control connection failed"
        elif connects "$svc" "$tool" object-store 8333; then
            check "'${svc}' cannot reach object-store:8333" "connection succeeded"
        else
            check "'${svc}' cannot reach object-store:8333" "ok"
        fi
    done
    if connects backend bash object-store 8333; then
        check "'backend' reaches object-store:8333" "ok"
    else
        check "'backend' reaches object-store:8333" "connection failed"
    fi
    ROUND_TRIP=$(compose exec -T backend python -c '
from app.core.object_storage import ObjectStorageClient
c = ObjectStorageClient()
k = "smoke/network-isolation.txt"
c.put_object(k, b"smoke", "text/plain")
try:
    assert c.get_object(k) == b"smoke"
finally:
    c.delete_object(k)
print("ok")' 2>&1 | tail -1)
    check "'backend' stores and reads back an object" "$([ "$ROUND_TRIP" = ok ] && echo ok || echo "$ROUND_TRIP")"
    STORE_ID=$(compose ps -q object-store)
    if [ -z "$STORE_ID" ] || ! STORE_BINDINGS=$(docker inspect "$STORE_ID" --format '{{json .NetworkSettings.Ports}} {{json .HostConfig.PortBindings}}' 2>&1); then
        check "object-store publishes no host port" "docker inspect failed"
    elif printf '%s' "$STORE_BINDINGS" | grep -q HostPort; then
        check "object-store publishes no host port" "published: $STORE_BINDINGS"
    else
        check "object-store publishes no host port" "ok"
    fi
fi

# ── 11. Non-root containers (SR-041 AC 1, AC 6) ─────────────────────────────
# Every image MedHub builds (each Compose service with a `build:` section, so a new one is
# covered by itself): the image configuration `Config.User` is set and is not root or 0, and the
# main process (PID 1) of each running one has a UID other than 0. Skipped, with a message, only
# when no container of the project exists; a missing container of a built service is a FAIL.
# A built service that is not running and whose restart policy is not "no" is a FAIL (a crash loop
# must not pass as "nothing to check"); one-shot services (restart "no") are skipped when stopped.
# PID 1 is the real process: the entrypoint ends with `exec "$@"`, so for `celery-worker` and
# `celery-beat` it is Celery itself (PRB-061), and its command line is checked in section 12.
echo ""
echo "-- Non-root containers (SR-041 AC 1, AC 6) --"
non_root_user() {  # USER[:GROUP] -> exit 0 when it names a user other than root / UID 0
    local u="${1%%:*}"
    [ -n "$u" ] && [ "$u" != "root" ] && [ "$u" != "0" ]
}
if [ -z "$(compose ps -aq 2>/dev/null)" ]; then
    echo "  [SKIP] stack not running — non-root checks skipped (run after docker compose up)"
else
    BUILT=$(compose config --format json 2>/dev/null | python3 -c '
import json, sys
services = json.load(sys.stdin)["services"]
print(" ".join(sorted(n for n, s in services.items() if "build" in s)))' 2>/dev/null || true)
    if [ -z "$BUILT" ]; then
        check "built services found in the Compose file" "none listed"
    fi
    for svc in $BUILT; do
        CID=$(compose ps -aq "$svc" 2>/dev/null | head -n 1)
        if [ -z "$CID" ]; then
            check "'${svc}' (built image) has a container" "no container; run docker compose up first"
            continue
        fi
        IMAGE_USER=$(docker inspect "$(docker inspect --format '{{.Image}}' "$CID")" --format '{{.Config.User}}' 2>/dev/null || true)
        if non_root_user "$IMAGE_USER"; then
            check "'${svc}' image Config.User is non-root (SR-041 AC 1)" "ok"
        else
            check "'${svc}' image Config.User is non-root (SR-041 AC 1)" "Config.User is '${IMAGE_USER}'"
        fi
        if [ "$(docker inspect --format '{{.State.Status}}' "$CID" 2>/dev/null)" = "running" ]; then
            PID1_UID=$(compose exec -T "$svc" sed -n 's/^Uid:[[:space:]]*\([0-9]*\).*/\1/p' /proc/1/status 2>/dev/null | tr -d '\r')
            EXEC_UID=$(compose exec -T "$svc" id -u 2>/dev/null | tr -d '\r')
            for pair in "PID 1:$PID1_UID" "id -u:$EXEC_UID"; do
                what="${pair%%:*}"; uid="${pair#*:}"
                case "$uid" in
                    ''|*[!0-9]*) check "'${svc}' ${what} UID is non-root (SR-041 AC 6)" "could not read a UID (got '${uid}')" ;;
                    0)           check "'${svc}' ${what} UID is non-root (SR-041 AC 6)" "UID is 0" ;;
                    *)           check "'${svc}' ${what} UID is non-root (SR-041 AC 6)" "ok" ;;
                esac
            done
        else
            POLICY=$(docker inspect --format '{{.HostConfig.RestartPolicy.Name}}' "$CID" 2>/dev/null || true)
            if [ -n "$POLICY" ] && [ "$POLICY" != "no" ]; then
                check "'${svc}' is running (restart: ${POLICY})" "not running (state: $(docker inspect --format '{{.State.Status}}' "$CID" 2>/dev/null))"
            fi
        fi
    done
    # The single-page app is served through the proxy from the frontend on 8080.
    if command -v curl >/dev/null 2>&1; then
        SPA_BODY=$(mktemp)
        SPA_STATUS=$(curl -sk -o "$SPA_BODY" -w "%{http_code}" https://localhost/ 2>/dev/null || true)
        if [ "$SPA_STATUS" = "200" ] && grep -q 'id="root"' "$SPA_BODY"; then
            check "the SPA index is served through the reverse proxy (200)" "ok"
        else
            check "the SPA index is served through the reverse proxy (200)" "got HTTP '${SPA_STATUS}' or no app root in the body"
        fi
        rm -f "$SPA_BODY"
    else
        echo "  [SKIP] curl not available — SPA check skipped"
    fi
fi

# ── 12. Database roles and background processes (SR-023 AC 8, SR-041 AC 2, PRB-061) ──────────
# Started-stack checks, run from inside the containers with the credentials they hold. The
# backend must be connected as the runtime role (not the owner, not a superuser), the role must be
# refused UPDATE/DELETE/TRUNCATE on audit_log with SQLSTATE 42501 and refused SET ROLE to any other
# role, no container but db-migrate may hold the owner URL, and db-migrate must have exited 0.
# The worker must answer a Celery ping, and beat must run with the retention task scheduled.
echo ""
echo "-- Database roles and background processes (SR-023 AC 8, PRB-061) --"
if [ -z "$(compose ps -q backend 2>/dev/null)" ]; then
    echo "  [SKIP] stack not running — database role checks skipped (run after docker compose up)"
else
    MIGRATE_CID=$(compose ps -aq db-migrate 2>/dev/null | head -n 1)
    if [ -n "$MIGRATE_CID" ] && [ "$(docker inspect --format '{{.State.Status}} {{.State.ExitCode}}' "$MIGRATE_CID" 2>/dev/null)" = "exited 0" ]; then
        check "db-migrate ran once and exited 0" "ok"
    else
        check "db-migrate ran once and exited 0" "state: $(docker inspect --format '{{.State.Status}} {{.State.ExitCode}}' "$MIGRATE_CID" 2>&1)"
    fi
    # The owner (superuser) password must reach no container but postgres (SR-041 AC 2, PRB-007).
    # Value-based: read it from the postgres container and look for it, without printing it, in
    # the environment of every other running container (/proc/1/environ and the image/Compose
    # Config.Env). A name-only check missed env_file passing POSTGRES_PASSWORD (TASK-191 round 2).
    OWNER_PW_FILE=$(mktemp)
    chmod 600 "$OWNER_PW_FILE"
    compose exec -T postgres printenv POSTGRES_PASSWORD 2>/dev/null | tr -d '\r\n' > "$OWNER_PW_FILE"
    POSTGRES_CID=$(compose ps -q postgres 2>/dev/null | head -n 1)
    if [ ! -s "$OWNER_PW_FILE" ]; then
        check "the owner password can be read from the postgres container" "empty or unreadable"
    else
        for CID in $(compose ps -q 2>/dev/null); do
            [ "$CID" = "$POSTGRES_CID" ] && continue
            [ "$(docker inspect --format '{{.State.Status}}' "$CID" 2>/dev/null)" = "running" ] || continue
            NAME=$(docker inspect --format '{{index .Config.Labels "com.docker.compose.service"}}' "$CID" 2>/dev/null)
            ENV_DUMP=$(mktemp)
            chmod 600 "$ENV_DUMP"
            # /proc/1/environ is readable only by PID 1's own user (root lacks CAP_SYS_PTRACE).
            PID1_USER=$(docker exec "$CID" sed -n 's/^Uid:[[:space:]]*\([0-9]*\).*/\1/p' /proc/1/status 2>/dev/null | tr -d '\r')
            if [ -z "$PID1_USER" ] || ! docker exec -u "$PID1_USER" "$CID" cat /proc/1/environ > "$ENV_DUMP" 2>/dev/null; then
                check "'${NAME}' holds no owner credential (SR-041 AC 2)" "could not read /proc/1/environ"
            else
                docker inspect --format '{{json .Config.Env}}' "$CID" >> "$ENV_DUMP" 2>/dev/null
                if grep -qaF -f "$OWNER_PW_FILE" "$ENV_DUMP"; then
                    check "'${NAME}' holds no owner credential (SR-041 AC 2)" "the owner password is in its environment"
                else
                    check "'${NAME}' holds no owner credential (SR-041 AC 2)" "ok"
                fi
            fi
            rm -f "$ENV_DUMP"
        done
    fi
    rm -f "$OWNER_PW_FILE"
    # Exactly one beat: a second one would send every scheduled task twice (round 2).
    BEATS=0
    for CID in $(compose ps -q celery-beat 2>/dev/null); do
        [ "$(docker inspect --format '{{.State.Status}}' "$CID" 2>/dev/null)" = "running" ] && BEATS=$((BEATS + 1))
    done
    if [ "$BEATS" -eq 1 ]; then
        check "exactly one celery-beat container is running" "ok"
    else
        check "exactly one celery-beat container is running" "$BEATS running"
    fi
    # Prints one `name=value` line per fact; the URL is read from the container, never printed.
    ROLE_FACTS=$(compose exec -T backend python -c '
import os
import psycopg2
from psycopg2 import errors

url = os.environ["DATABASE_URL"]


def refused(statement):
    conn = psycopg2.connect(url)
    try:
        with conn.cursor() as cur:
            cur.execute(statement)
        return "executed"
    except errors.InsufficientPrivilege as exc:
        return exc.pgcode
    finally:
        conn.rollback()
        conn.close()


conn = psycopg2.connect(url)
with conn.cursor() as cur:
    cur.execute("SELECT current_user, rolsuper FROM pg_roles WHERE rolname = current_user")
    user, is_super = cur.fetchone()
    cur.execute("SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.member WHERE r.rolname = current_user")
    members = cur.fetchone()[0]
    cur.execute("SELECT rolname FROM pg_roles WHERE rolname <> current_user AND rolname !~ %s", ("^pg_",))
    others = [r[0] for r in cur.fetchall()]
conn.close()
print("user=" + user)
print("super=" + str(is_super))
print("members=" + str(members))
print("update=" + refused("UPDATE audit_log SET action = action WHERE false"))
print("delete=" + refused("DELETE FROM audit_log WHERE false"))
print("truncate=" + refused("TRUNCATE audit_log"))
print("setrole=" + ",".join(sorted({refused("SET ROLE \"" + r + "\"") for r in others}) or ["none"]))
' 2>&1 | tr -d '\r')
    fact() { printf '%s\n' "$ROLE_FACTS" | sed -n "s/^$1=//p" | head -n 1; }
    EXPECTED_USER=$(compose exec -T backend python -c 'import os; from urllib.parse import urlsplit; print(urlsplit(os.environ["DATABASE_URL"]).username)' 2>/dev/null | tr -d '\r')
    if [ -n "$(fact user)" ] && [ "$(fact user)" = "$EXPECTED_USER" ] && [ "$(fact super)" = "False" ] \
        && [ "$(fact user)" != "$(compose exec -T postgres printenv POSTGRES_USER 2>/dev/null | tr -d '\r')" ]; then
        check "'backend' is connected as the runtime role, not the owner or a superuser" "ok"
    else
        check "'backend' is connected as the runtime role, not the owner or a superuser" "user='$(fact user)' superuser='$(fact super)'"
    fi
    for stmt in update delete truncate; do
        if [ "$(fact $stmt)" = "42501" ]; then
            check "runtime role: ${stmt} on audit_log fails with 42501 (SR-023 AC 8)" "ok"
        else
            check "runtime role: ${stmt} on audit_log fails with 42501 (SR-023 AC 8)" "got '$(fact $stmt)'"
        fi
    done
    if [ "$(fact setrole)" = "42501" ]; then
        check "runtime role: SET ROLE to any other role fails with 42501" "ok"
    else
        check "runtime role: SET ROLE to any other role fails with 42501" "got '$(fact setrole)'"
    fi
    if [ "$(fact members)" = "0" ]; then
        check "runtime role has no row in pg_auth_members" "ok"
    else
        check "runtime role has no row in pg_auth_members" "members='$(fact members)'"
    fi
    # Worker and beat: the container's main process is Celery (PRB-061).
    for entry in celery-worker:worker celery-beat:beat; do
        svc="${entry%%:*}"; sub="${entry#*:}"
        CMDLINE=$(compose exec -T "$svc" sh -c 'tr "\0" " " < /proc/1/cmdline' 2>/dev/null | tr -d '\r')
        case "$CMDLINE" in
            *celery*" $sub "*|*celery*" $sub") check "'${svc}' runs Celery ${sub} as its main process" "ok" ;;
            *) check "'${svc}' runs Celery ${sub} as its main process" "main process is '${CMDLINE}'" ;;
        esac
    done
    PING=$(compose exec -T celery-worker celery -A app.workers.celery_app inspect ping 2>&1 | tr -d '\r')
    if printf '%s' "$PING" | grep -q "pong"; then
        check "the Celery worker answers 'inspect ping'" "ok"
    else
        check "the Celery worker answers 'inspect ping'" "$(printf '%s' "$PING" | tail -n 1)"
    fi
    SCHEDULE=$(compose exec -T celery-beat python -c 'from app.workers.celery_app import celery_app; print(sorted(celery_app.conf.beat_schedule))' 2>&1 | tail -n 1 | tr -d '\r')
    if printf '%s' "$SCHEDULE" | grep -q "erase-expired-anonymized-datasets"; then
        check "the retention sweep is in the beat schedule" "ok"
    else
        check "the retention sweep is in the beat schedule" "schedule: $SCHEDULE"
    fi
    if compose logs celery-beat 2>/dev/null | grep -q "beat: Starting"; then
        check "celery-beat logged 'beat: Starting'" "ok"
    else
        check "celery-beat logged 'beat: Starting'" "no start line in the log"
    fi
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
