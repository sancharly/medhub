"""Runtime database role and its privileges (SR-023 AC 8, ADR-0017, ADD-016 U-PER-Roles).

``apply`` runs as the owner role after the migrations. It creates the unprivileged runtime role
the application connects as, grants it the statements the application needs on every table, and
withholds ``UPDATE``, ``DELETE`` and ``TRUNCATE`` on ``audit_log`` so PostgreSQL refuses them with
a permission error (SQLSTATE 42501). It is idempotent: a table added by a later migration is
granted on the next run. The runtime password is never logged, and PostgreSQL receives a SCRAM
verifier, not the password, so server statement logs never hold it.

``apply`` refuses a runtime role that already exists with more than it should have: a superuser,
a member of any role, or an owner of any object. ``NOINHERIT`` alone does not undo an existing
membership, so the refusal is the control (TASK-191, from the TASK-190 QA review).
"""

from __future__ import annotations

import os
import sys
from contextlib import closing
from typing import Any

from psycopg2 import sql
from psycopg2.extensions import encrypt_password
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url

_SCHEMA = sql.Identifier("public")
_AUDIT_TABLE = sql.Identifier("public", "audit_log")


def _refuse_privileged_role(cur: Any, runtime_user: str) -> None:
    """Raise when the existing role is a superuser, has memberships or owns objects."""
    cur.execute("SELECT oid, rolsuper FROM pg_roles WHERE rolname = %s", (runtime_user,))
    found = cur.fetchone()
    if found is None:
        return
    oid, is_super = found
    if is_super:
        raise ValueError(f"role {runtime_user} exists and is a superuser; refusing to reuse it")
    cur.execute("SELECT count(*) FROM pg_auth_members WHERE member = %s", (oid,))
    if cur.fetchone()[0]:
        raise ValueError(f"role {runtime_user} exists and is a member of another role")
    cur.execute(
        "SELECT count(*) FROM pg_shdepend WHERE refclassid = 'pg_authid'::regclass "
        "AND refobjid = %s AND deptype = 'o'",
        (oid,),
    )
    if cur.fetchone()[0]:
        raise ValueError(f"role {runtime_user} exists and owns objects")


def apply(owner_engine: Engine, runtime_user: str, runtime_password: str) -> None:
    """Create or update ``runtime_user`` and grant it the application's privileges."""
    if not runtime_user or not runtime_password:
        raise ValueError("the runtime role needs a user name and a password")
    if runtime_user == owner_engine.url.username:
        raise ValueError("the runtime role must differ from the owner role")

    role = sql.Identifier(runtime_user)
    conn = owner_engine.raw_connection()
    try:
        with closing(conn.cursor()) as cur:
            _refuse_privileged_role(cur, runtime_user)
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (runtime_user,))
            verb = "ALTER" if cur.fetchone() else "CREATE"
            verifier = encrypt_password(
                runtime_password, runtime_user, scope=cur, algorithm="scram-sha-256"
            )
            attributes = sql.SQL(
                "LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT "
                "NOREPLICATION NOBYPASSRLS PASSWORD {}"
            ).format(sql.Literal(verifier))
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
                "REVOKE ALL ON {audit} FROM {role}",
                "GRANT SELECT, INSERT ON {audit} TO {role}",
            ):
                cur.execute(
                    sql.SQL(statement).format(
                        database=database, schema=_SCHEMA, role=role, audit=_AUDIT_TABLE
                    )
                )
            # The migration history is the owner's: the application cannot rewrite it. The table
            # is absent in databases built by create_all (tests).
            cur.execute("SELECT to_regclass('public.alembic_version') IS NOT NULL")
            version_row = cur.fetchone()
            if version_row is not None and version_row[0]:
                cur.execute(
                    sql.SQL("REVOKE INSERT, UPDATE, DELETE ON {} FROM {}").format(
                        sql.Identifier("public", "alembic_version"), role
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
    engine = create_engine(owner_url, hide_parameters=True)
    try:
        apply(engine, runtime.username, runtime.password)
    finally:
        engine.dispose()
    print(f"database roles applied for runtime role {runtime.username}")


if __name__ == "__main__":
    main()
