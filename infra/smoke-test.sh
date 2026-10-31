#!/usr/bin/env bash
# infra/smoke-test.sh
# Validates Docker Compose configuration and documents runtime security checks.
# Run after `docker compose up -d` to confirm topology is correct.
#
# SR-008: Data in transit must be encrypted (TLS 1.2+, HTTPS redirect, HSTS)
# SR-016: PHI at rest must be encrypted (object-store SSE-S3 AES256)
# SR-040: object store has no console or admin option

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Ensure a .env file exists for docker compose to parse
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "INFO: No infra/.env found — copying .env.example for validation only."
    cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
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
for svc in reverse-proxy backend frontend postgres redis object-store celery-worker; do
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
for svc in backend frontend postgres redis object-store celery-worker; do
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

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
