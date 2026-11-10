"""TC-009.12 (real module key): the audit writer accepts the real ``dicom-viewer`` key.

The key comes from the real manifest, never an invented one (TASK-192 QA round 1): module
discovery, the registry sync, the module gate and module enablement all write it as a
``target_id`` (SR-023 AC 7, AC 9).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from dicom_viewer.manifest import manifest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
from app.api.deps import get_current_user, require_module_enabled
from app.api.errors import register_error_handlers
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.audit import AuditLog, AuditOutcome
from app.db.models.base import Base
from app.db.repositories.audit_repo import AuditRepository
from app.groups.service import GroupService
from app.modules.discovery import _is_valid_manifest
from app.modules.registry_service import ModuleRegistryService

KEY = manifest.module_key


def _capturing_audit() -> tuple[AuditService, list[AuditLog]]:
    repo = MagicMock(spec=AuditRepository)
    added: list[AuditLog] = []
    repo.add.side_effect = lambda log: added.append(log) or log
    repo.add_independent.side_effect = lambda log: added.append(log) or log
    return AuditService(repo), added


def test_real_manifest_passes_discovery() -> None:
    assert KEY == "dicom-viewer"
    assert _is_valid_manifest(manifest)


def test_sync_installed_records_module_discovered_for_the_real_key() -> None:
    audit, added = _capturing_audit()
    ModuleRegistryService(MagicMock(), audit).sync_installed([manifest], MagicMock())
    assert [(r.action, r.target_type, r.target_id) for r in added] == [
        (AuditAction.MODULE_DISCOVERED, "module", KEY),
        (AuditAction.MODULE_REGISTRY_SYNC, "module_registry", None),
    ]


def test_module_enable_records_one_row_for_the_real_key() -> None:
    audit, added = _capturing_audit()
    group_id = uuid.uuid4()
    module_repo = MagicMock()
    group_repo = MagicMock()
    svc = GroupService(group_repo, MagicMock(), module_repo, audit, MagicMock())
    actor = MagicMock(spec=Account)
    actor.id = uuid.uuid4()

    svc.set_module_enabled(actor, group_id, KEY, True)

    assert [(r.action, r.target_type, r.target_id) for r in added] == [
        (AuditAction.MODULE_ENABLE, "group_module", f"{group_id}:{KEY}")
    ]


@pytest.fixture(scope="module")
def pg_engine():
    with PostgresContainer("postgres:16") as container:
        engine = create_engine(container.get_connection_url())
        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def factory(pg_engine, monkeypatch) -> Iterator[sessionmaker[Session]]:
    monkeypatch.setattr("app.db.repositories.session.get_engine", lambda: pg_engine)
    maker = sessionmaker(bind=pg_engine)
    yield maker
    with maker() as s:
        s.execute(delete(AuditLog))
        s.commit()


def test_denied_module_gate_returns_403_with_one_authz_denied_row(factory) -> None:
    # Real get_db, real guard, real AuthorizationService; the actor is in no group.
    actor = MagicMock(spec=Account)
    actor.id = uuid.uuid4()
    actor.user_type = UserType.DOCTOR
    actor.status = AccountStatus.ACTIVE

    app_ = FastAPI()
    register_error_handlers(app_)

    @app_.get("/probe", dependencies=[Depends(require_module_enabled(KEY))])
    def probe() -> dict:
        return {}

    app_.dependency_overrides[get_current_user] = lambda: actor
    resp = TestClient(app_, raise_server_exceptions=False).get("/probe")

    assert resp.status_code == 403
    with factory() as s:
        rows = s.execute(select(AuditLog).where(AuditLog.actor_id == actor.id)).scalars().all()
    assert [(r.action, r.outcome, r.target_type, r.target_id) for r in rows] == [
        (AuditAction.AUTHZ_DENIED, AuditOutcome.FAILURE, "module", KEY)
    ]
