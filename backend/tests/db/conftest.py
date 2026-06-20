"""Shared fixtures for database tests using testcontainers."""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.db.models.base import Base

# macOS Docker Desktop: socket lives outside /var/run
_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"

# Disable Ryuk sidecar (causes hangs on macOS Docker Desktop)
os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")


@pytest.fixture(scope="module")
def pg_container():
    with PostgresContainer("postgres:16") as container:
        yield container


@pytest.fixture(scope="module")
def pg_engine(pg_container):
    engine = create_engine(pg_container.get_connection_url())
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(pg_engine):
    SessionLocal = sessionmaker(bind=pg_engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()
