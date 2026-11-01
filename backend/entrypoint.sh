#!/usr/bin/env bash
# Runs the container's command (the image CMD or the Compose `command:`). It does not migrate:
# the db-migrate service is the only process that runs alembic (TASK-191, ADR-0017).
set -euo pipefail
exec "$@"
