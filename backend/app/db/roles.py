"""Runtime database role and its privileges (SR-023 AC 8, ADR-0017, ADD-016 U-PER-Roles).

``apply`` runs as the owner role after the migrations. It creates the unprivileged runtime role
the application connects as, grants it the statements the application needs on every table, and
withholds ``UPDATE``, ``DELETE`` and ``TRUNCATE`` on ``audit_log`` so PostgreSQL refuses them with
a permission error (SQLSTATE 42501). It is idempotent: a table added by a later migration is
granted on the next run. The runtime password is never logged.
"""

from __future__ import annotations

import os
import sys
from contextlib import closing

from psycopg2 import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url

_SCHEMA = sql.Identifier("public")
_AUDIT_TABLE = sql.Identifier("public", "audit_log")


def apply(owner_engine: Engine, runtime_user: str, runtime_password: str) -> None:
    """Create or update ``runtime_user`` and grant it the application's privileges."""
    if not runtime_user or not runtime_password:
        raise ValueError("the runtime role needs a user name and a password")
    if runtime_user == owner_engine.url.username:
        raise ValueError("the runtime role must differ from the owner role")

    role = sql.Identifier(runtime_user)
    attributes = sql.SQL("LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD {}").format(
        sql.Literal(runtime_password)
    )
    conn = owner_engine.raw_connection()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (runtime_user,))
            verb = "ALTER" if cur.fetchone() else "CREATE"
            cur.execute(sql.SQL("{} ROLE {} {}").format(sql.SQL(verb), role, attributes))
            cur.execute("SELECT current_database()")
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("the database name could not be read")
            database = sql.Identifier(row[0])
            for statement in (
                "GRANT CONNECT ON DATABASE {database} TO {role}",
                "GRANT USAGE ON SCHEMA {schema} TO {role}",
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} TO {role}",
                "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO {role}",
                "REVOKE UPDATE, DELETE, TRUNCATE ON {audit} FROM {role}",
            ):
                cur.execute(
                    sql.SQL(statement).format(
                        database=database, schema=_SCHEMA, role=role, audit=_AUDIT_TABLE
                    )
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    """Apply the roles with ``DATABASE_OWNER_URL``; the runtime role comes from ``DATABASE_URL``."""
    owner_url = os.environ.get("DATABASE_OWNER_URL")
    runtime_url = os.environ.get("DATABASE_URL")
    if not owner_url or not runtime_url:
        sys.exit("DATABASE_OWNER_URL and DATABASE_URL must both be set")
    runtime = make_url(runtime_url)
    if not runtime.username or not runtime.password:
        sys.exit("DATABASE_URL must carry the runtime user and password")
    engine = create_engine(owner_url)
    try:
        apply(engine, runtime.username, runtime.password)
    finally:
        engine.dispose()
    print(f"database roles applied for runtime role {runtime.username}")


if __name__ == "__main__":
    main()
