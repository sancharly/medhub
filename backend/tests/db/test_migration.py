"""Migration tests: upgrade head / downgrade base cycle (TASK-011)."""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer

from app.db.models.base import Base

# Ensure Docker socket is found on macOS
_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"

_BACKEND_DIR = Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def migration_container():
    with PostgresContainer("postgres:16") as container:
        yield container


@pytest.fixture(scope="module")
def alembic_cfg(migration_container):
    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "app" / "db" / "alembic"))
    cfg.set_main_option("sqlalchemy.url", migration_container.get_connection_url())
    return cfg


def test_upgrade_and_downgrade(alembic_cfg):
    """upgrade head then downgrade base must run without error."""
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")


def test_no_pending_diff_after_upgrade(alembic_cfg, migration_container):
    """After upgrade head, ORM metadata and migration schema must match (no drift)."""
    command.upgrade(alembic_cfg, "head")
    engine = create_engine(migration_container.get_connection_url())
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        diff = compare_metadata(ctx, Base.metadata)
    engine.dispose()
    assert diff == [], f"ORM/migration drift detected: {diff}"
