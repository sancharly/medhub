"""The test-data script creates and updates accounts (TASK-169, CR-003 AC-20, PRB-049)."""

import importlib.util
from datetime import timedelta
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "setup_test_data.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("setup_test_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_utc(value) -> None:
    assert value is not None
    assert value.utcoffset() == timedelta(0)


def test_create_doctor_and_patient_then_set_password(db_session) -> None:
    script = _load_script()

    doctor = script.create_doctor(db_session, "seed.doctor@test.local", "Seed", "Doctor", "pw-1")
    patient = script.create_patient(
        db_session, "seed.patient@test.local", "Seed", "Patient", "pw-2"
    )
    _assert_utc(doctor.password_changed_at)
    _assert_utc(patient.password_changed_at)

    assert script.set_password(db_session, "seed.patient@test.local", "pw-3") is True
    db_session.refresh(patient)
    _assert_utc(patient.password_changed_at)
