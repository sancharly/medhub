"""Tests for RouterRegistry.mount (TASK-072)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.errors import register_error_handlers
from app.authz.module_guard import ModuleAccessGuard
from app.db.models.account import Account, AccountStatus, UserType
from app.modules.router_registry import RouterRegistry


def _make_account(user_type: UserType = UserType.DOCTOR) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    return acct


def _make_sub_router() -> APIRouter:
    sub = APIRouter()

    @sub.get("/ping")
    def ping() -> dict:
        return {"pong": True}

    return sub


class TestRouterMount:
    def test_mount_exposes_routes_under_correct_prefix(self) -> None:
        app = FastAPI()
        register_error_handlers(app)
        registry = RouterRegistry(app)
        sub = _make_sub_router()
        registry.mount("dicom-viewer", sub)

        actor = _make_account()
        app.dependency_overrides[get_current_user] = lambda: actor

        # Module enabled so we get through the gate
        with patch.object(ModuleAccessGuard, "is_module_enabled", return_value=True):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/v1/modules/dicom-viewer/ping")
        assert resp.status_code == 200
        app.dependency_overrides.clear()

    def test_duplicate_module_key_is_skipped(self) -> None:
        app = FastAPI()
        registry = RouterRegistry(app)
        sub = _make_sub_router()

        registry.mount("dicom-viewer", sub)
        # Second call with same key must not crash
        registry.mount("dicom-viewer", sub)

        assert len(registry._mounted) == 1

    def test_mounted_routes_carry_module_enabled_dependency(self) -> None:
        """Routes mounted via RouterRegistry are denied when module not enabled."""
        app = FastAPI()
        register_error_handlers(app)

        registry = RouterRegistry(app)
        sub = _make_sub_router()
        registry.mount("dicom-viewer", sub)

        actor = _make_account()
        app.dependency_overrides[get_current_user] = lambda: actor

        # Guard returns False — module not enabled for this actor
        with patch.object(ModuleAccessGuard, "is_module_enabled", return_value=False):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/v1/modules/dicom-viewer/ping")
        assert resp.status_code == 403
        app.dependency_overrides.clear()
