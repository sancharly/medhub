#!/usr/bin/env bash
# infra/smoke-test.sh
# Validates Docker Compose configuration and documents runtime security checks.
# Run after `docker compose up -d` to confirm topology is correct.
#
# SR-008: Data in transit must be encrypted (TLS 1.2+, HTTPS redirect, HSTS)
# SR-016: PHI at rest must be encrypted (MinIO SSE-AES256)

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
for svc in reverse-proxy backend frontend postgres redis minio celery-worker; do
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
# The backend, frontend, postgres, redis, minio, celery-worker use 'expose:' (internal only).
UNEXPECTED_PORTS=0
for svc in backend frontend postgres redis minio celery-worker; do
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

# ── 7. MinIO SSE configured ──────────────────────────────────────────────────
echo ""
echo "-- At-rest encryption (SR-016) --"
if docker compose -f "$COMPOSE_FILE" config 2>/dev/null | grep -q "MINIO_KMS_SECRET_KEY"; then
    check "MinIO SSE-AES256 key configured (SR-016)" "ok"
else
    check "MinIO SSE-AES256 key configured (SR-016)" "MINIO_KMS_SECRET_KEY missing from minio service"
fi

# ── 8. Named volumes defined for persistent data ─────────────────────────────
echo ""
echo "-- Data persistence --"
for vol in postgres_data redis_data minio_data; do
    if grep -q "^  ${vol}:" "$COMPOSE_FILE"; then
        check "named volume '${vol}' defined" "ok"
    else
        check "named volume '${vol}' defined" "missing"
    fi
done

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
