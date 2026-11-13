"""TC-018.5 (real DB): migration 0011 adds the four authorization-lookup indexes.

SR-026 AC 6 (PRB-021, TASK-219): the lookups by appointment time, by consent appointment, and by
patient for clinical entries and for attachments are served by an index. The query-plan check runs
on a database seeded with 10 000 rows per table, ``ANALYZE`` run, ``enable_seqscan`` left on.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Select, create_engine, inspect, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection, Engine
from testcontainers.postgres import PostgresContainer

from app.db.models.appointment import Appointment
from app.db.models.attachment import Attachment
from app.db.models.clinical import ClinicalEntry
from app.db.models.consent import ConsentGrant
from postgres_image import POSTGRES_IMAGE

_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"

_BACKEND_DIR = Path(__file__).parent.parent.parent
_ROWS = 10_000
_PATIENTS = 500  # 20 rows per patient
_TABLES = ("appointment", "consent_grant", "clinical_entry", "attachment")
_INDEXES = {
    "appointment": "ix_appointment_scheduled_at",
    "consent_grant": "ix_consent_grant_appointment_id",
    "clinical_entry": "ix_clinical_entry_patient_id",
    "attachment": "ix_attachment_patient_id",
}


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
    """A database at revision 0010 with the four tables empty."""
    eng = create_engine(pg_url)
    command.upgrade(cfg, "0010")  # no-op when already there
    with eng.begin() as conn:
        conn.execute(
            text("TRUNCATE appointment, consent_grant, clinical_entry, attachment CASCADE")
        )
    command.stamp(cfg, "0010")
    with eng.begin() as conn:
        for name in _INDEXES.values():
            conn.execute(text(f"DROP INDEX IF EXISTS {name}"))
    yield eng
    eng.dispose()


def _seed(engine: Engine) -> None:
    """10 000 rows per table; FK targets are not created (replication role skips the checks)."""
    n, p = _ROWS, _PATIENTS
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        conn.execute(
            text(
                "INSERT INTO appointment (id, doctor_id, patient_id, scheduled_at, state) "
                "SELECT ('00000000-0000-4000-8000-' || lpad(i::text, 12, '0'))::uuid, "
                "gen_random_uuid(), ('00000000-0000-4000-9000-' || lpad((i % :p)::text, 12, '0'))"
                "::uuid, now() + (i || ' minutes')::interval, 'PENDING' "
                "FROM generate_series(1, :n) AS i"
            ),
            {"n": n, "p": p},
        )
        conn.execute(
            text(
                "INSERT INTO consent_grant (id, patient_id, doctor_id, source_type, "
                "appointment_id, active) "
                "SELECT gen_random_uuid(), gen_random_uuid(), gen_random_uuid(), 'APPOINTMENT', "
                "('00000000-0000-4000-8000-' || lpad(i::text, 12, '0'))::uuid, true "
                "FROM generate_series(1, :n) AS i"
            ),
            {"n": n},
        )
        conn.execute(
            text(
                "INSERT INTO clinical_entry (id, patient_id, author_doctor_id, occurred_at, "
                "description) "
                "SELECT ('00000000-0000-4000-a000-' || lpad(i::text, 12, '0'))::uuid, "
                "('00000000-0000-4000-9000-' || lpad((i % :p)::text, 12, '0'))::uuid, "
                "gen_random_uuid(), now(), 'mh1:k:x' FROM generate_series(1, :n) AS i"
            ),
            {"n": n, "p": p},
        )
        conn.execute(
            text(
                "INSERT INTO attachment (id, clinical_entry_id, patient_id, filename, "
                "content_type, size, storage_key, checksum) "
                "SELECT gen_random_uuid(), "
                "('00000000-0000-4000-a000-' || lpad(i::text, 12, '0'))::uuid, "
                "('00000000-0000-4000-9000-' || lpad((i % :p)::text, 12, '0'))::uuid, "
                "'f.bin', 'application/octet-stream', 1, 'k' || i, 'c' "
                "FROM generate_series(1, :n) AS i"
            ),
            {"n": n, "p": p},
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


def test_upgrade_downgrade_0011_empty_and_populated(engine, cfg):
    # empty database
    assert _present(engine) == set()
    command.upgrade(cfg, "0011")
    assert _present(engine) == set(_INDEXES.values())
    command.downgrade(cfg, "0010")
    assert _present(engine) == set()
    assert _counts(engine) == dict.fromkeys(_TABLES, 0)

    # database with 10 000 rows in each table
    _seed(engine)
    before = _counts(engine)
    assert before == dict.fromkeys(_TABLES, _ROWS)
    command.upgrade(cfg, "0011")
    assert _present(engine) == set(_INDEXES.values())
    assert _counts(engine) == before
    command.downgrade(cfg, "0010")
    assert _present(engine) == set()
    assert _counts(engine) == before


def _explain(conn: Connection, stmt: Select) -> str:
    sql = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    return "\n".join(r[0] for r in conn.execute(text("EXPLAIN " + sql)))


def test_authorization_lookups_use_index(engine, cfg):
    _seed(engine)
    command.upgrade(cfg, "0011")
    with engine.begin() as conn:
        conn.execute(text("ANALYZE"))
    patient = "00000000-0000-4000-9000-000000000007"
    appointment = "00000000-0000-4000-8000-000000000042"
    queries: dict[str, Select] = {
        # as ClinicalRepository.list_for_patient and the attachment lookup by patient issue them
        "clinical_entry": select(ClinicalEntry).where(ClinicalEntry.patient_id == patient),
        "attachment": select(Attachment).where(Attachment.patient_id == patient),
        # a one-hour window of appointment times, and the consents of one appointment
        "appointment": select(Appointment).where(
            Appointment.scheduled_at >= text("now() + interval '1 day'"),
            Appointment.scheduled_at < text("now() + interval '1 day 1 hour'"),
        ),
        "consent_grant": select(ConsentGrant).where(ConsentGrant.appointment_id == appointment),
    }
    with engine.connect() as conn:
        assert conn.execute(text("SHOW enable_seqscan")).scalar_one() == "on"
        for table, stmt in queries.items():
            plan = _explain(conn, stmt)
            assert _INDEXES[table] in plan, f"{table}: {plan}"
            assert "Seq Scan" not in plan, f"{table}: {plan}"


def test_without_the_indexes_the_same_lookups_scan(engine, cfg):
    """Negative control: at 0010 the plan check fails, so the test above can fail."""
    _seed(engine)
    with engine.begin() as conn:
        conn.execute(text("ANALYZE"))
    stmt = select(ClinicalEntry).where(
        ClinicalEntry.patient_id == "00000000-0000-4000-9000-000000000007"
    )
    with engine.connect() as conn:
        assert "Seq Scan on clinical_entry" in _explain(conn, stmt)
