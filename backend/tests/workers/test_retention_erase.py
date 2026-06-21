"""TASK-036: Retention sweep task tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch


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
    mock_db.execute.return_value = mock_result
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
        patch.object(db_sess, "get_db", return_value=iter([mock_db])),
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
    """A failure erasing one dataset must not block others."""
    from app.db.models.anonymized_dataset import AnonymizedDataset

    now = datetime.now(UTC)
    ds1 = AnonymizedDataset(
        id=uuid.uuid4(), code_hash="h1", payload={}, retention_deadline=now - timedelta(days=1)
    )
    ds2 = AnonymizedDataset(
        id=uuid.uuid4(), code_hash="h2", payload={}, retention_deadline=now - timedelta(days=1)
    )

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [ds1, ds2]
    mock_db.execute.return_value = mock_result
    mock_db.flush = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.rollback = MagicMock()
    mock_db.close = MagicMock()

    call_count = 0

    def fail_on_first_delete(dataset: object) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Simulated failure")

    mock_db.delete.side_effect = fail_on_first_delete

    import app.audit.service as audit_mod
    import app.db.repositories.audit_repo as audr
    import app.db.repositories.session as db_sess
    import app.workers.retention_tasks as rt

    # Return fresh mock_db on each get_db() call (for isolation recovery)
    fresh_db = MagicMock()
    fresh_result = MagicMock()
    fresh_result.scalars.return_value.all.return_value = []
    fresh_db.execute.return_value = fresh_result
    fresh_db.delete = MagicMock()
    fresh_db.flush = MagicMock()
    fresh_db.commit = MagicMock()
    fresh_db.rollback = MagicMock()
    fresh_db.close = MagicMock()

    with (
        patch.object(db_sess, "get_db", side_effect=[iter([mock_db]), iter([fresh_db])]),
        patch.object(audr.AuditRepository, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "record"),
    ):
        result = rt.erase_expired_anonymized_datasets.run()

    # ds1 failed, ds2 succeeded (isolated recovery)
    assert result["failed"] == 1
    assert result["erased"] == 1
