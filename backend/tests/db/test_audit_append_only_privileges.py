"""TC-009.11 (real DB): the runtime role cannot alter the audit log (SR-023 AC 8, ADR-0017).

The schema is built by the migrations to head as the owner role (the container superuser), then
``app.db.roles.apply`` creates the runtime role. Each privilege case connects as that role.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import psycopg2.errors
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError
from testcontainers.postgres import PostgresContainer

from app.db import roles

_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"

_BACKEND_DIR = Path(__file__).parent.parent.parent
_RUNTIME_USER = "medhub_app"
_RUNTIME_PASSWORD = "runtime-pw-4k9x2m7q"

_INSERT_AUDIT = (
    "INSERT INTO audit_log (id, action, outcome) "
    "VALUES (gen_random_uuid(), 'TEST_EVENT', 'SUCCESS')"
)


@pytest.fixture(scope="module")
def owner_engine() -> Iterator[Engine]:
    with PostgresContainer("postgres:16") as container:
        url = container.get_connection_url()
        cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(_BACKEND_DIR / "app" / "db" / "alembic"))
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "head")
        engine = create_engine(url)
        roles.apply(engine, _RUNTIME_USER, _RUNTIME_PASSWORD)
        yield engine
        engine.dispose()


@pytest.fixture(scope="module")
def runtime_engine(owner_engine: Engine) -> Iterator[Engine]:
    url = owner_engine.url.set(username=_RUNTIME_USER, password=_RUNTIME_PASSWORD)
    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def _one_audit_row(owner_engine: Engine) -> Iterator[None]:
    with owner_engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_log"))
        conn.execute(text(_INSERT_AUDIT))
    yield


def _refused(engine: Engine, statement: str) -> ProgrammingError:
    with pytest.raises(ProgrammingError) as caught:
        with engine.begin() as conn:
            conn.execute(text(statement))
    assert isinstance(caught.value.orig, psycopg2.errors.InsufficientPrivilege)
    assert caught.value.orig.pgcode == "42501"
    return caught.value


# --- AC 1 (SR-023 AC 8): UPDATE, DELETE and TRUNCATE are refused, not silently ignored ---------


def test_runtime_role_can_insert_and_select_audit_rows(runtime_engine: Engine) -> None:
    """AC 2 (statements the application needs): INSERT and SELECT on audit_log."""
    with runtime_engine.begin() as conn:
        conn.execute(text(_INSERT_AUDIT))
        count = conn.execute(text("SELECT count(*) FROM audit_log")).scalar_one()
    assert count == 2


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE audit_log SET action = 'TAMPERED'",
        "UPDATE audit_log SET action = 'TAMPERED' WHERE false",
        "DELETE FROM audit_log",
        "DELETE FROM audit_log WHERE false",
        "TRUNCATE audit_log",
    ],
)
def test_runtime_role_cannot_update_delete_or_truncate_audit_rows(
    runtime_engine: Engine, owner_engine: Engine, statement: str
) -> None:
    """AC 1: a permission error (42501) rather than a silent no-op; the row is untouched."""
    _refused(runtime_engine, statement)
    with owner_engine.connect() as conn:
        actions = conn.execute(text("SELECT action FROM audit_log")).scalars().all()
    assert actions == ["TEST_EVENT"]


@pytest.mark.parametrize(
    "statement",
    [
        "ALTER TABLE audit_log ADD COLUMN extra text",
        "ALTER TABLE audit_log DISABLE TRIGGER ALL",
        "DROP TABLE audit_log",
        "CREATE RULE no_op AS ON UPDATE TO audit_log DO INSTEAD NOTHING",
        "CREATE TRIGGER t BEFORE INSERT ON audit_log EXECUTE FUNCTION no_such_fn()",
    ],
)
def test_runtime_role_cannot_alter_or_drop_the_audit_table(
    runtime_engine: Engine, statement: str
) -> None:
    """AC 1: the runtime role does not own the table, so DDL on it is refused."""
    _refused(runtime_engine, statement)


def test_runtime_role_cannot_run_migrations(runtime_engine: Engine) -> None:
    """The runtime role cannot create tables, so it cannot migrate."""
    _refused(runtime_engine, "CREATE TABLE should_not_exist (id int)")


def test_audit_log_rules_of_0006_are_gone_after_upgrade(owner_engine: Engine) -> None:
    """AC 3: migration 0009 dropped no_update_audit_log and no_delete_audit_log."""
    with owner_engine.connect() as conn:
        found = conn.execute(
            text("SELECT rulename FROM pg_rules WHERE tablename = 'audit_log'")
        ).all()
    assert found == []


# --- AC 2: the application's normal statements work as the runtime role --------------------


def test_runtime_role_can_insert_update_and_delete_on_a_business_table(
    runtime_engine: Engine,
) -> None:
    with runtime_engine.begin() as conn:
        conn.execute(
            text("INSERT INTO \"group\" (id, name) VALUES (gen_random_uuid(), 'g-privilege-test')")
        )
        conn.execute(
            text("UPDATE \"group\" SET name = 'g-renamed' WHERE name = 'g-privilege-test'")
        )
        deleted = conn.execute(text("DELETE FROM \"group\" WHERE name = 'g-renamed'")).rowcount
    assert deleted == 1


def test_runtime_role_is_unprivileged_and_owns_nothing(owner_engine: Engine) -> None:
    with owner_engine.connect() as conn:
        role = conn.execute(
            text(
                "SELECT rolsuper, rolcreatedb, rolcreaterole, rolinherit, rolcanlogin "
                "FROM pg_roles WHERE rolname = :n"
            ),
            {"n": _RUNTIME_USER},
        ).one()
        owned = conn.execute(
            text("SELECT tablename FROM pg_tables WHERE tableowner = :n"), {"n": _RUNTIME_USER}
        ).all()
    assert tuple(role) == (False, False, False, False, True)
    assert owned == []


def test_apply_twice_is_a_noop_and_grants_new_tables(
    owner_engine: Engine, runtime_engine: Engine
) -> None:
    roles.apply(owner_engine, _RUNTIME_USER, _RUNTIME_PASSWORD)
    roles.apply(owner_engine, _RUNTIME_USER, _RUNTIME_PASSWORD)
    with owner_engine.begin() as conn:
        conn.execute(text("CREATE TABLE later_table (id int PRIMARY KEY)"))
    try:
        _refused(runtime_engine, "SELECT * FROM later_table")
        roles.apply(owner_engine, _RUNTIME_USER, _RUNTIME_PASSWORD)
        with runtime_engine.begin() as conn:
            conn.execute(text("INSERT INTO later_table (id) VALUES (1)"))
        _refused(runtime_engine, "TRUNCATE audit_log")
    finally:
        with owner_engine.begin() as conn:
            conn.execute(text("DROP TABLE later_table"))


def test_apply_refuses_the_owner_as_runtime_user(owner_engine: Engine) -> None:
    with pytest.raises(ValueError, match="differ from the owner"):
        roles.apply(owner_engine, owner_engine.url.username, "x")


# --- AC 3: the owner role runs the migrations -----------------------------------------------


def test_owner_role_runs_migrations_up_and_down(owner_engine: Engine) -> None:
    """AC 3: 0009 down recreates the 0006 rules, up drops them again, as the owner."""
    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "app" / "db" / "alembic"))
    cfg.set_main_option("sqlalchemy.url", owner_engine.url.render_as_string(hide_password=False))
    query = text("SELECT rulename FROM pg_rules WHERE tablename = 'audit_log' ORDER BY 1")
    command.downgrade(cfg, "0008")
    with owner_engine.connect() as conn:
        assert conn.execute(query).scalars().all() == [
            "no_delete_audit_log",
            "no_update_audit_log",
        ]
    command.upgrade(cfg, "head")
    with owner_engine.connect() as conn:
        assert conn.execute(query).scalars().all() == []
