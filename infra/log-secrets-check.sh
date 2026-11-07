#!/usr/bin/env bash
# infra/log-secrets-check.sh
# SR-043 AC 4 pass criterion, end to end on a started stack (TASK-206, PRB-068).
#
# DESTRUCTIVE: it stops and restarts `postgres` and `backend`, and it creates two accounts in the
# stack's database. Run it by hand against a scratch stack (never a deployment holding real data);
# it is not run in CI. The stack is the Compose project of the shell (COMPOSE_PROJECT_NAME) and
# infra/.env.
#
# It generates known values, uses each of them against the stack, then fails when any of them is
# found in `docker compose logs` of any service. The report holds counts only, never a value.
#   1. an activation token on the API path, the page path and the e-mail query form;
#   2. one unhandled exception (postgres stopped);
#   3. one reverse-proxy upstream error (backend stopped), with an activation page Referer;
#   4. a sign-in as a seeded test user, then authenticated requests, one of them state-changing and
#      sent with X-CSRF-Token;
#   5. a search of the logs of backend, celery-worker, celery-beat, reverse-proxy, frontend and
#      db-migrate for the activation token, the session token, the CSRF token and the password.
#
# The activation token is issued with the application's own issue_activation_token(): the API never
# returns it (it goes only into the e-mail), so the account is seeded from inside the backend
# container. The test user is created with backend/scripts/setup_test_data.py's create_doctor, with
# a generated password. The e-mailed link itself is the started-stack step 3 of TASK-206.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
BASE_URL="${BASE_URL:-https://localhost}"
SERVICES="backend celery-worker celery-beat reverse-proxy frontend db-migrate"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAIL=0
check() {
    if [ "$2" = "ok" ]; then
        echo "  [PASS] $1"
        ((PASS++)) || true
    else
        echo "  [FAIL] $1: $2"
        ((FAIL++)) || true
    fi
}
compose() { docker compose -f "$COMPOSE_FILE" "$@"; }
status() { curl -sk -o /dev/null -w "%{http_code}" "$@" 2>/dev/null; }
wait_for_backend() {
    for _ in $(seq 1 60); do
        [ "$(status "$BASE_URL/healthz")" = "200" ] && return 0
        sleep 2
    done
    return 1
}

echo "=== MedHub log secrets check (SR-043 AC 4) ==="
if [ -z "$(compose ps -q backend 2>/dev/null)" ] || ! command -v curl >/dev/null 2>&1; then
    echo "The stack is not running (or curl is missing): start it with 'docker compose up -d --build'."
    exit 2
fi
wait_for_backend || { echo "The backend does not answer on $BASE_URL/healthz."; exit 2; }

# ── Known values ─────────────────────────────────────────────────────────────
SUFFIX="$(python3 -c 'import secrets; print(secrets.token_hex(6))')"
PASSWORD="Lc-$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"
EMAIL="logcheck-$SUFFIX@medhub.local"
PENDING_EMAIL="logcheck-pending-$SUFFIX@medhub.local"

SEED=$(compose exec -T -e LC_EMAIL="$EMAIL" -e LC_PENDING="$PENDING_EMAIL" -e LC_PASSWORD="$PASSWORD" \
    backend python - <<'PY' 2>&1 | tr -d '\r'
import contextlib
import io
import os
import sys
import uuid

sys.path.insert(0, "/app")
from sqlalchemy.orm import Session

from app.db.models.account import Account, AccountStatus, UserType
from app.identity.activation import issue_activation_token
from scripts.setup_test_data import create_doctor, get_engine

with Session(get_engine()) as session:
    with contextlib.redirect_stdout(io.StringIO()):  # the script prints a banner
        create_doctor(session, os.environ["LC_EMAIL"], "Log", "Check", os.environ["LC_PASSWORD"])
    pending = Account(
        id=uuid.uuid4(),
        email=os.environ["LC_PENDING"],
        user_type=UserType.PATIENT,
        status=AccountStatus.INACTIVE,
        first_name="Log",
        surname="Pending",
    )
    token = issue_activation_token(pending)
    session.add(pending)
    session.commit()
    print("ACTIVATION_TOKEN=" + token)
PY
)
TOKEN=$(printf '%s\n' "$SEED" | sed -n 's/^ACTIVATION_TOKEN=//p' | head -n 1)
if [ -z "$TOKEN" ]; then
    echo "Could not seed the test accounts (no token). Last lines of the seed output:"
    printf '%s\n' "$SEED" | tail -n 5 | sed -e 's/[A-Za-z0-9_-]\{30,\}/[value]/g'
    exit 2
fi

# ── 1. Activation token on the three forms ───────────────────────────────────
echo ""
echo "-- 1. Activation token: API path, page path, e-mail query form --"
API_STATUS=$(status "$BASE_URL/api/v1/activation/$TOKEN")
PAGE_STATUS=$(status "$BASE_URL/activation/$TOKEN")
QUERY_STATUS=$(status "$BASE_URL/activate?token=$TOKEN")
[ "$API_STATUS" = "200" ] && check "GET /api/v1/activation/<token> answers 200" "ok" \
    || check "GET /api/v1/activation/<token> answers 200" "got $API_STATUS"
[ "$PAGE_STATUS" = "200" ] && check "GET /activation/<token> answers the page (200)" "ok" \
    || check "GET /activation/<token> answers the page (200)" "got $PAGE_STATUS"
[ "$QUERY_STATUS" = "200" ] && check "GET /activate?token=<token> answers (200)" "ok" \
    || check "GET /activate?token=<token> answers (200)" "got $QUERY_STATUS"

# ── 2. One unhandled exception ───────────────────────────────────────────────
echo ""
echo "-- 2. Unhandled exception (postgres stopped) --"
compose stop postgres >/dev/null 2>&1
EXC_STATUS=$(status --max-time 60 "$BASE_URL/api/v1/activation/$TOKEN")
compose start postgres >/dev/null 2>&1
[ "$EXC_STATUS" = "500" ] && check "the activation API answers 500 while the database is down" "ok" \
    || check "the activation API answers 500 while the database is down" "got $EXC_STATUS"
for _ in $(seq 1 60); do
    [ "$(status "$BASE_URL/api/v1/activation/$TOKEN")" = "200" ] && break
    sleep 2
done

# ── 3. One reverse-proxy upstream error ──────────────────────────────────────
echo ""
echo "-- 3. Upstream error (backend stopped), activation page Referer --"
compose stop backend >/dev/null 2>&1
REFERER="$BASE_URL/activation/$TOKEN"
# An unreachable upstream ends in 502 (refused) or 504 (timed out, nginx's default 60 s): both are
# per-request upstream errors. The control request has no token: its error IS written to the error
# log, so a missing line for the activation request is by design and not a broken log.
status --max-time 120 -H "Referer: $REFERER" "$BASE_URL/api/v1/activation/$TOKEN" > "$WORK/up_api" &
status --max-time 120 "$BASE_URL/api/v1/me" > "$WORK/up_ctl" &
UP_PAGE=$(status -H "Referer: $REFERER" "$BASE_URL/activation/$TOKEN")
wait
UP_API=$(cat "$WORK/up_api")
UP_CTL=$(cat "$WORK/up_ctl")
compose logs --no-color reverse-proxy > "$WORK/proxy_during.log" 2>&1
compose start backend >/dev/null 2>&1
compose restart reverse-proxy >/dev/null 2>&1  # the backend may come back on another address
case "$UP_API" in
    502|504) check "the activation API answers $UP_API while the backend is down" "ok" ;;
    *) check "the activation API answers 502 or 504 while the backend is down" "got $UP_API" ;;
esac
case "$UP_CTL" in
    502|504) check "a request without a token answers $UP_CTL too (control)" "ok" ;;
    *) check "a request without a token answers 502 or 504 (control)" "got $UP_CTL" ;;
esac
CTL_ERRORS=$(grep -cE '\[error\].*(upstream|connect\(\))' "$WORK/proxy_during.log" || true)
[ "$CTL_ERRORS" -ge 1 ] && check "the control upstream error is in the proxy error log ($CTL_ERRORS lines)" "ok" \
    || check "the control upstream error is in the proxy error log" "no [error] upstream line: the control proves nothing"
ACT_ERRORS=$(grep -E '\[error\].*(upstream|connect\(\))' "$WORK/proxy_during.log" | grep -cE 'activation|activat' || true)
[ "$ACT_ERRORS" = "0" ] && check "no upstream error entry names an activation request (0 lines)" "ok" \
    || check "no upstream error entry names an activation request" "$ACT_ERRORS line(s)"
[ "$UP_PAGE" = "200" ] && check "the activation page is served by the frontend (200)" "ok" \
    || check "the activation page is served by the frontend (200)" "got $UP_PAGE"
wait_for_backend || check "the backend is back" "no answer on /healthz"

# ── 4. Sign-in and authenticated requests ────────────────────────────────────
echo ""
echo "-- 4. Sign-in and authenticated requests --"
JAR="$WORK/jar.txt"
LOGIN_STATUS=$(curl -sk -c "$JAR" -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" 2>/dev/null)
cookie() { awk -v name="$1" '$6 == name { print $7 }' "$JAR" | tail -n 1; }
SESSION="$(cookie medhub_session)"
CSRF="$(cookie medhub_csrf)"
[ "$LOGIN_STATUS" = "200" ] && check "sign-in answers 200" "ok" || check "sign-in answers 200" "got $LOGIN_STATUS"
[ -n "$SESSION" ] && [ -n "$CSRF" ] && check "the session and CSRF cookies were issued" "ok" \
    || check "the session and CSRF cookies were issued" "session or CSRF cookie missing"
ME_STATUS=$(status -b "$JAR" "$BASE_URL/api/v1/me")
EXT_STATUS=$(status -b "$JAR" -X POST -H "X-CSRF-Token: $CSRF" "$BASE_URL/api/v1/auth/session/extend")
[ "$ME_STATUS" = "200" ] && check "GET /api/v1/me with the session answers 200" "ok" \
    || check "GET /api/v1/me with the session answers 200" "got $ME_STATUS"
[ "$EXT_STATUS" = "200" ] && check "POST /auth/session/extend with X-CSRF-Token answers 200" "ok" \
    || check "POST /auth/session/extend with X-CSRF-Token answers 200" "got $EXT_STATUS"

# ── 5. Search the logs ───────────────────────────────────────────────────────
echo ""
echo "-- 5. No known value in any service log --"
sleep 2
for svc in $SERVICES; do
    compose logs --no-color "$svc" > "$WORK/$svc.log" 2>&1
    LINES=$(wc -l < "$WORK/$svc.log" | tr -d ' ')
    [ "$LINES" -gt 0 ] && check "log of '$svc' is readable ($LINES lines)" "ok" \
        || check "log of '$svc' is readable" "empty"
done
# Positive control: the proxy logged these requests, with the token path redacted.
REDACTED=$(grep -cF '/api/v1/activation/[redacted]' "$WORK/reverse-proxy.log" || true)
[ "$REDACTED" -ge 1 ] && check "the proxy logged the activation requests, path redacted ($REDACTED lines)" "ok" \
    || check "the proxy logged the activation requests, path redacted" "no redacted path in the proxy log"
for entry in "activation token:$TOKEN" "session token:$SESSION" "CSRF token:$CSRF" "test password:$PASSWORD"; do
    label="${entry%%:*}"
    value="${entry#*:}"
    if [ -z "$value" ]; then
        check "the $label is absent from every log" "value not available"
        continue
    fi
    TOTAL=0
    DETAIL=""
    for svc in $SERVICES; do
        N=$(grep -cF -- "$value" "$WORK/$svc.log" || true)
        TOTAL=$((TOTAL + N))
        [ "$N" -gt 0 ] && DETAIL="$DETAIL $svc=$N"
    done
    if [ "$TOTAL" -eq 0 ]; then
        check "the $label is absent from every log (0 matches in 6 services)" "ok"
    else
        check "the $label is absent from every log" "$TOTAL matching line(s):$DETAIL"
    fi
done

echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
[ "$FAIL" -gt 0 ] && exit 1
exit 0
