"""Alembic environment configuration.

Migrations run as the owner role (SR-023 AC 8, ADR-0017): the URL is ``DATABASE_OWNER_URL``, not
the application's ``DATABASE_URL``, and the secret settings are checked first (SR-041 AC 3) so the
owner credential is validated where it is used. Only the ``db-migrate`` Compose service has it.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import all models so metadata is populated
import app.db.models  # noqa: F401
from app.core.secret_settings import DATABASE_OWNER_URL, enforce
from app.db.models.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    url = (os.environ.get(DATABASE_OWNER_URL) or "").strip()
    if not url:
        raise RuntimeError(f"{DATABASE_OWNER_URL} must be set: migrations run as the owner role")
    return url


def check_secrets() -> None:
    """Refuse placeholder secrets before connecting, unless a caller supplied the URL itself.

    A caller that sets ``sqlalchemy.url`` (the test suites) brings its own database; the
    deployment (``db-migrate``) never does, so its owner credential is always checked.
    """
    if not config.get_main_option("sqlalchemy.url"):
        enforce()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    check_secrets()
    url = config.get_main_option("sqlalchemy.url") or get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section, {})
    check_secrets()
    # Prefer URL already set in config (e.g. from test override via set_main_option)
    if not configuration.get("sqlalchemy.url"):
        configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
