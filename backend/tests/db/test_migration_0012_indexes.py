"""TC-018.8 (real DB): migration 0012 adds the two remaining lookup indexes.

SR-026 AC 6 (PRB-021, CR-006 D-29, TASK-220): the attachments of a clinical entry and a doctor's
patients by active consent are served by an index. The query-plan check runs on a database seeded
with 10 000 rows, ``ANALYZE`` run, ``enable_seqscan`` left on, with the statements compiled from the
repositories. Runs only on throwaway test databases.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Select, create_engine, inspect, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection, Engine
from testcontainers.postgres import PostgresContainer

from app.db.models.base import Base
from app.db.repositories.attachment_repo import AttachmentRepository
from app.db.repositories.consent_repo import ConsentRepository
from postgres_image import POSTGRES_IMAGE

_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"

_BACKEND_DIR = Path(__file__).parent.parent.parent
_ROWS = 10_000
_ENTRIES = 5_000  # two attachments per clinical entry
_DOCTORS = 50  # 200 consent grants per doctor, a quarter of them revoked
_TABLES = ("consent_grant", "attachment")
_INDEXES = {
    "attachment": "ix_attachment_clinical_entry_id",
    "consent_grant": "ix_consent_grant_doctor_id_active",
}
_ENTRY = "00000000-0000-4000-a000-000000000042"
_DOCTOR = "00000000-0000-4000-b000-000000000007"


@pytest.fixture(scope="module")
def pg_url() -> Iterator[str]:
    with PostgresContainer(POSTGRES_IMAGE) as container:
        yield container.get_connection_url()


@pytest.fixture
def cfg(pg_url: str) -> Config:
    c = Config(str(_BACKEND_DIR / "alembic.ini"))
    c.set_main_option("script_location", str(_BACKEND_DIR / "app" / "db" / "alembic"))
    c.set_main_option("sqlalchemy.url", pg_url)
    return c


@pytest.fixture
def engine(pg_url: str, cfg: Config) -> Iterator[Engine]:
    """A database at revision 0011 with the two tables empty."""
    eng = create_engine(pg_url)
    command.upgrade(cfg, "0011")  # no-op when already there
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE account, consent_grant, attachment CASCADE"))
        for name in _INDEXES.values():
            conn.execute(text(f"DROP INDEX IF EXISTS {name}"))
    command.stamp(cfg, "0011")
    yield eng
    eng.dispose()


def _seed(engine: Engine) -> None:
    """10 000 rows per table and 10 000 patients; the replication role skips FK checks."""
    n = _ROWS
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        # The patients: the doctor lookup joins account, so the planner needs its rows.
        conn.execute(
            text(
                "INSERT INTO account (id, email, user_type, status) "
                "SELECT ('00000000-0000-4000-9000-' || lpad(i::text, 12, '0'))::uuid, "
                "'p' || i || '@example.com', 'PATIENT', 'ACTIVE' FROM generate_series(1, :n) AS i"
            ),
            {"n": n},
        )
        conn.execute(
            text(
                "INSERT INTO consent_grant (id, patient_id, doctor_id, source_type, active) "
                "SELECT gen_random_uuid(), "
                "('00000000-0000-4000-9000-' || lpad(i::text, 12, '0'))::uuid, "
                "('00000000-0000-4000-b000-' || lpad((i % :d)::text, 12, '0'))::uuid, "
                "'MANUAL', (i % 4 <> 0) FROM generate_series(1, :n) AS i"
            ),
            {"n": n, "d": _DOCTORS},
        )
        conn.execute(
            text(
                "INSERT INTO attachment (id, clinical_entry_id, patient_id, filename, "
                "content_type, size, storage_key, checksum) "
                "SELECT gen_random_uuid(), "
                "('00000000-0000-4000-a000-' || lpad((i % :e)::text, 12, '0'))::uuid, "
                "gen_random_uuid(), 'f.bin', 'application/octet-stream', 1, 'k' || i, 'c' "
                "FROM generate_series(1, :n) AS i"
            ),
            {"n": n, "e": _ENTRIES},
        )


def _counts(engine: Engine) -> dict[str, int]:
    with engine.connect() as conn:
        return {t: conn.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in _TABLES}


def _present(engine: Engine) -> set[str]:
    insp = inspect(engine)
    names: set[str] = set()
    for table in _TABLES:
        names |= {i["name"] for i in insp.get_indexes(table) if i["name"]}
    return names & set(_INDEXES.values())


def test_upgrade_downgrade_0012_empty_and_populated(engine, cfg):
    # empty database
    assert _present(engine) == set()
    command.upgrade(cfg, "0012")
    assert _present(engine) == set(_INDEXES.values())
    command.downgrade(cfg, "0011")
    assert _present(engine) == set()
    assert _counts(engine) == dict.fromkeys(_TABLES, 0)

    # database with 10 000 rows in each table
    _seed(engine)
    before = _counts(engine)
    assert before == dict.fromkeys(_TABLES, _ROWS)
    command.upgrade(cfg, "0012")
    assert _present(engine) == set(_INDEXES.values())
    assert _counts(engine) == before
    command.downgrade(cfg, "0011")
    assert _present(engine) == set()
    assert _counts(engine) == before


def _explain(conn: Connection, stmt: Select) -> str:
    sql = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    return "\n".join(r[0] for r in conn.execute(text("EXPLAIN " + sql)))


class _CapturingSession:
    """Stands in for a Session: records the statement a repository method executes."""

    def __init__(self) -> None:
        self.stmt: Select | None = None

    def execute(self, stmt: Select):  # type: ignore[no-untyped-def]
        self.stmt = stmt
        raise _Captured


class _Captured(Exception):
    pass


def _lookups() -> dict[str, Select]:
    """The two statements exactly as the repositories issue them (not hand-written copies)."""
    out: dict[str, Select] = {}
    for table, call in (
        ("attachment", lambda s: AttachmentRepository(s).list_for_clinical_entry(_ENTRY)),
        ("consent_grant", lambda s: ConsentRepository(s).list_patients_for_doctor(_DOCTOR)),
    ):
        session = _CapturingSession()
        with pytest.raises(_Captured):
            call(session)
        assert session.stmt is not None
        out[table] = session.stmt
    return out


def test_remaining_lookups_use_index(engine, cfg):
    _seed(engine)
    command.upgrade(cfg, "0012")
    with engine.begin() as conn:
        conn.execute(text("ANALYZE"))
    with engine.connect() as conn:
        assert conn.execute(text("SHOW enable_seqscan")).scalar_one() == "on"
        for table, stmt in _lookups().items():
            plan = _explain(conn, stmt)
            assert _INDEXES[table] in plan, f"{table}: {plan}"
            # the doctor lookup joins account, which the planner may scan; the table the
            # new index serves must not be scanned
            assert f"Seq Scan on {table}" not in plan, f"{table}: {plan}"


def test_without_the_0012_indexes_the_same_lookups_scan(engine, cfg):
    """Negative control: at 0011 both lookups plan as a sequential scan."""
    _seed(engine)
    with engine.begin() as conn:
        conn.execute(text("ANALYZE"))
    with engine.connect() as conn:
        for table, stmt in _lookups().items():
            assert f"Seq Scan on {table}" in _explain(conn, stmt), table


def test_orm_drift_at_head_and_at_0011(engine, cfg):
    """At head the ORM and the migrations agree; at 0011 exactly the two add_index diffs remain."""

    def _diff() -> list:
        with engine.connect() as conn:
            return compare_metadata(MigrationContext.configure(conn), Base.metadata)

    command.upgrade(cfg, "0012")
    assert _diff() == []
    command.downgrade(cfg, "0011")
    diff = _diff()
    assert sorted((d[0], d[1].name) for d in diff) == [
        ("add_index", "ix_attachment_clinical_entry_id"),
        ("add_index", "ix_consent_grant_doctor_id_active"),
    ], diff
