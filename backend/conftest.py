"""Root conftest — set Docker/testcontainers env vars before any test module loads."""

import os

# macOS Docker Desktop: socket lives outside /var/run
_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"

# Disable Ryuk sidecar (causes hangs on macOS Docker Desktop)
os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")
