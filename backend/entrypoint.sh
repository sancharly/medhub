#!/usr/bin/env bash
set -euo pipefail
echo "Running database migrations..."
PYTHONPATH=/app alembic upgrade head
echo "Starting application..."
# --forwarded-allow-ips= (empty): the server never rewrites the TCP peer; the application applies
# the trusted-proxy rule once (SR-042, ADR-0019).
exec gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --forwarded-allow-ips= app.main:app
