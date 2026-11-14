"""TASK-036: Retention sweep task tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


def test_erase_expired_datasets_deletes_expired_rows() -> None:
    """Expired datasets are permanently deleted and audited."""
    from app.db.models.anonymized_dataset import AnonymizedDataset

    now = datetime.now(UTC)
    expired_ds = AnonymizedDataset(
        id=uuid.uuid4(),
        code_hash="$argon2id$fakehash",
        payload={},
        retention_deadline=now - timedelta(days=1),
    )
    # Mock the DB session and scalars
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [expired_ds]  # only expired
    mock_result.scalars.return_value.all.return_value = [expired_ds.id]  # ids only (TASK-141)
    mock_db.execute.return_value = mock_result
    # the second session's locked select (TASK-228) returns the dataset; the listing returns ids
    mock_db.execute.return_value.scalar_one_or_none.return_value = expired_ds
    mock_db.delete = MagicMock()
    mock_db.flush = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.rollback = MagicMock()
    mock_db.close = MagicMock()

    captured_audit: list = []

    import app.audit.service as audit_mod
    import app.db.repositories.audit_repo as audr
    import app.db.repositories.session as db_sess
    import app.workers.retention_tasks as rt

    with (
        # one session lists the ids, one handles the dataset (TASK-141)
        patch.object(db_sess, "get_db", side_effect=[iter([mock_db]), iter([mock_db])]),
        patch.object(audr.AuditRepository, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "__init__", return_value=None),
        patch.object(
            audit_mod.AuditService,
            "record",
            side_effect=lambda *a, **kw: captured_audit.append((a, kw)),
        ),
    ):
        result = rt.erase_expired_anonymized_datasets.run()

    assert result["erased"] == 1
    assert result["failed"] == 0
    mock_db.delete.assert_called_once_with(expired_ds)
    # Audit must have been called for the erased dataset
    assert len(captured_audit) == 1
    call_str = str(captured_audit)
    assert "ANONYMIZED_DATASET_ERASED" in call_str
    assert str(expired_ds.id) in call_str


def test_erase_per_dataset_failure_isolation() -> None:
    """A failure erasing one dataset must not block others (the task then retries, TASK-141)."""
    from celery.exceptions import Retry

    from app.db.models.anonymized_dataset import AnonymizedDataset

    now = datetime.now(UTC)
    ds1 = AnonymizedDataset(
        id=uuid.uuid4(), code_hash="h1", payload={}, retention_deadline=now - timedelta(days=1)
    )
    ds2 = AnonymizedDataset(
        id=uuid.uuid4(), code_hash="h2", payload={}, retention_deadline=now - timedelta(days=1)
    )

    list_db = MagicMock()
    list_db.execute.return_value.scalars.return_value.all.return_value = [ds1.id, ds2.id]
    db1, db2 = MagicMock(), MagicMock()
    db1.execute.return_value.scalar_one_or_none.return_value = ds1
    db1.delete.side_effect = RuntimeError("Simulated failure")
    db2.execute.return_value.scalar_one_or_none.return_value = ds2

    import app.audit.service as audit_mod
    import app.db.repositories.audit_repo as audr
    import app.db.repositories.session as db_sess
    import app.workers.retention_tasks as rt

    with (
        patch.object(db_sess, "get_db", side_effect=[iter([list_db]), iter([db1]), iter([db2])]),
        patch.object(audr.AuditRepository, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "record"),
        pytest.raises(Retry),
    ):
        rt.erase_expired_anonymized_datasets.run()

    # ds1 failed and was rolled back, ds2 was erased and committed in its own session
    db1.rollback.assert_called_once()
    db1.commit.assert_not_called()
    db2.delete.assert_called_once_with(ds2)
    db2.commit.assert_called_once()
    for session in (list_db, db1, db2):
        session.close.assert_called_once()
