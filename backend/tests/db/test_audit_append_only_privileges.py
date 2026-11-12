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
from postgres_image import POSTGRES_IMAGE

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
    with PostgresContainer(POSTGRES_IMAGE) as container:
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


# --- TASK-191 (carried from the TASK-190 QA review) -------------------------------------------


def test_runtime_role_cannot_become_the_owner_and_has_no_memberships(
    runtime_engine: Engine, owner_engine: Engine
) -> None:
    """SET ROLE <owner> is refused (42501) and pg_auth_members holds no row for the role."""
    owner = owner_engine.url.username
    with pytest.raises(ProgrammingError) as caught:
        with runtime_engine.begin() as conn:
            conn.execute(text(f'SET ROLE "{owner}"'))
    assert caught.value.orig.pgcode == "42501"
    with owner_engine.connect() as conn:
        members = conn.execute(
            text(
                "SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.member "
                "WHERE r.rolname = :n"
            ),
            {"n": _RUNTIME_USER},
        ).scalar_one()
    assert members == 0


def test_truncate_cascade_from_a_referenced_table_is_refused(runtime_engine: Engine) -> None:
    """TRUNCATE ... CASCADE cannot reach audit_log through a table the role may write to."""
    _refused(runtime_engine, 'TRUNCATE "group" CASCADE')


def test_runtime_role_cannot_rewrite_the_migration_history(
    runtime_engine: Engine, owner_engine: Engine
) -> None:
    """alembic_version is readable but not writable by the runtime role."""
    with runtime_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM alembic_version")).scalar_one() == 1
    for statement in (
        "UPDATE alembic_version SET version_num = '0001'",
        "DELETE FROM alembic_version",
        "INSERT INTO alembic_version (version_num) VALUES ('x')",
    ):
        _refused(runtime_engine, statement)


def test_role_password_is_stored_and_sent_as_a_scram_verifier(owner_engine: Engine) -> None:
    with owner_engine.connect() as conn:
        stored = conn.execute(
            text("SELECT rolpassword FROM pg_authid WHERE rolname = :n"), {"n": _RUNTIME_USER}
        ).scalar_one()
    assert stored.startswith("SCRAM-SHA-256$")
    assert _RUNTIME_PASSWORD not in stored


def test_apply_without_alembic_version_table_still_grants(owner_engine: Engine) -> None:
    """A create_all database has no alembic_version: the revoke is skipped (to_regclass)."""
    with owner_engine.begin() as conn:
        conn.execute(text("ALTER TABLE alembic_version RENAME TO alembic_version_moved"))
    try:
        roles.apply(owner_engine, _RUNTIME_USER, _RUNTIME_PASSWORD)
    finally:
        with owner_engine.begin() as conn:
            conn.execute(text("ALTER TABLE alembic_version_moved RENAME TO alembic_version"))
        roles.apply(owner_engine, _RUNTIME_USER, _RUNTIME_PASSWORD)


# apply() on a pre-existing role that has more than the runtime role should (NOINHERIT does not
# remove an existing membership's INHERIT option in PostgreSQL 16).
@pytest.mark.parametrize(
    ("setup", "message"),
    [
        ("ALTER ROLE {r} SUPERUSER", "superuser"),
        ("GRANT pg_read_all_data TO {r}", "member of another role"),
        ("ALTER TABLE later_owned OWNER TO {r}", "owns objects"),
    ],
)
def test_apply_refuses_a_pre_existing_role_with_extra_privileges(
    owner_engine: Engine, setup: str, message: str
) -> None:
    name = "preexisting_role"
    with owner_engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS later_owned"))
        conn.execute(text(f"DROP ROLE IF EXISTS {name}"))
        conn.execute(text(f"CREATE ROLE {name} LOGIN"))
        conn.execute(text("CREATE TABLE later_owned (id int)"))
        conn.execute(text(setup.format(r=name)))
    try:
        with pytest.raises(ValueError, match=message):
            roles.apply(owner_engine, name, "pw-1")
    finally:
        with owner_engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS later_owned"))
            conn.execute(text(f"DROP ROLE {name}"))


# --- SR-041 AC 2 / PRB-061: the migration environment uses the owner URL ---------------------


def _upgrade_cfg() -> Config:
    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "app" / "db" / "alembic"))
    return cfg  # no sqlalchemy.url: env.py must take DATABASE_OWNER_URL


def test_migrations_use_the_owner_url_from_the_environment(
    owner_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_OWNER_URL", owner_engine.url.render_as_string(hide_password=False))
    command.upgrade(_upgrade_cfg(), "head")  # already at head: connects as the owner, no change


def test_migrations_refuse_to_run_without_the_owner_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_OWNER_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_OWNER_URL must be set"):
        command.upgrade(_upgrade_cfg(), "head")


def test_migrations_refuse_a_placeholder_secret_before_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_OWNER_URL", "postgresql://medhub:change-me@localhost:1/medhub")
    with pytest.raises(SystemExit) as caught:
        command.upgrade(_upgrade_cfg(), "head")
    assert "DATABASE_OWNER_URL" in str(caught.value)
    assert "change-me" not in str(caught.value)


# --- TASK-191 round 2: leftover attributes and grants of a pre-existing role -------------------


def test_apply_resets_replication_and_bypassrls_on_a_pre_existing_role(
    owner_engine: Engine,
) -> None:
    name = "preexisting_attrs"
    with owner_engine.begin() as conn:
        conn.execute(text(f"DROP ROLE IF EXISTS {name}"))
        conn.execute(text(f"CREATE ROLE {name} LOGIN REPLICATION BYPASSRLS"))
    try:
        roles.apply(owner_engine, name, "pw-attrs-1")
        with owner_engine.connect() as conn:
            row = conn.execute(
                text("SELECT rolreplication, rolbypassrls FROM pg_roles WHERE rolname = :n"),
                {"n": name},
            ).one()
        assert tuple(row) == (False, False)
    finally:
        with owner_engine.begin() as conn:
            conn.execute(text(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {name}"))
            conn.execute(text(f"REVOKE ALL ON SCHEMA public FROM {name}"))
            conn.execute(text(f"REVOKE ALL ON DATABASE {conn.engine.url.database} FROM {name}"))
            conn.execute(text(f"DROP ROLE {name}"))


def test_apply_removes_extra_direct_grants_on_the_audit_table(
    owner_engine: Engine, runtime_engine: Engine
) -> None:
    with owner_engine.begin() as conn:
        conn.execute(text(f"GRANT TRIGGER, REFERENCES ON audit_log TO {_RUNTIME_USER}"))
    roles.apply(owner_engine, _RUNTIME_USER, _RUNTIME_PASSWORD)
    with owner_engine.connect() as conn:
        privileges = sorted(
            conn.execute(
                text(
                    "SELECT privilege_type FROM information_schema.role_table_grants "
                    "WHERE table_name = 'audit_log' AND grantee = :n"
                ),
                {"n": _RUNTIME_USER},
            ).scalars()
        )
    assert privileges == ["INSERT", "SELECT"]
    _refused(
        runtime_engine, "CREATE TRIGGER t2 BEFORE INSERT ON audit_log EXECUTE FUNCTION no_such_fn()"
    )
