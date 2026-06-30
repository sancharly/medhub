#!/usr/bin/env bash
set -euo pipefail
echo "Running database migrations..."
alembic upgrade head
echo "Starting application..."
exec gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app
