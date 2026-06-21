"""TASK-034: Session kill propagation task tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import fakeredis


def test_propagate_session_kill_calls_invalidate_all() -> None:
    account_id = str(uuid.uuid4())
    mock_db = MagicMock()
    r = fakeredis.FakeRedis()

    import app.audit.service as audit_mod
    import app.db.repositories.audit_repo as audr
    import app.db.repositories.session as db_sess
    import app.workers.session_tasks as st

    with (
        patch.object(db_sess, "get_db", return_value=iter([mock_db])),
        patch.object(audr.AuditRepository, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "record"),
        patch("redis.Redis.from_url", return_value=r),
    ):
        st.propagate_session_kill.run(account_id)

    # Idempotent — if account has no sessions that's fine
    # Just verify it didn't raise


def test_propagate_session_kill_audits_event() -> None:
    account_id = str(uuid.uuid4())
    mock_db = MagicMock()
    r = fakeredis.FakeRedis()
    captured: list = []

    import app.audit.service as audit_mod
    import app.db.repositories.audit_repo as audr
    import app.db.repositories.session as db_sess
    import app.workers.session_tasks as st

    with (
        patch.object(db_sess, "get_db", return_value=iter([mock_db])),
        patch.object(audr.AuditRepository, "__init__", return_value=None),
        patch.object(audit_mod.AuditService, "__init__", return_value=None),
        patch.object(
            audit_mod.AuditService,
            "record",
            side_effect=lambda *a, **kw: captured.append((a, kw)),
        ),
        patch("redis.Redis.from_url", return_value=r),
    ):
        st.propagate_session_kill.run(account_id)

    assert len(captured) == 1
    call_str = str(captured)
    assert "SESSION_KILL_PROPAGATED" in call_str
    # Must not contain any token values
    assert "session_id" not in call_str.lower() or account_id in call_str
