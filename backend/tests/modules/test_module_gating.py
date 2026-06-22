"""Tests for module access gating (TASK-072)."""

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


class TestModuleGating:
    def test_module_enabled_request_reaches_handler(self) -> None:
        app = FastAPI()
        register_error_handlers(app)

        sub = APIRouter()

        @sub.get("/ping")
        def ping() -> dict:
            return {"pong": True}

        registry = RouterRegistry(app)
        registry.mount("test-module", sub)

        actor = _make_account()
        app.dependency_overrides[get_current_user] = lambda: actor

        # Patch is_module_enabled to allow access
        with patch.object(ModuleAccessGuard, "is_module_enabled", return_value=True):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/v1/modules/test-module/ping")
        assert resp.status_code == 200
        app.dependency_overrides.clear()

    def test_module_not_enabled_returns_403(self) -> None:
        app = FastAPI()
        register_error_handlers(app)

        sub = APIRouter()

        @sub.get("/ping")
        def ping() -> dict:
            return {"pong": True}

        registry = RouterRegistry(app)
        registry.mount("test-module", sub)

        actor = _make_account()
        app.dependency_overrides[get_current_user] = lambda: actor
        with patch.object(ModuleAccessGuard, "is_module_enabled", return_value=False):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/v1/modules/test-module/ping")

        assert resp.status_code == 403
        app.dependency_overrides.clear()

    def test_module_disabled_after_enable_returns_403(self) -> None:
        """Live read: enabling then disabling the module produces a 403 on next request."""
        enabled = [True]

        app = FastAPI()
        register_error_handlers(app)

        sub = APIRouter()

        @sub.get("/ping")
        def ping() -> dict:
            return {"pong": True}

        registry = RouterRegistry(app)
        registry.mount("live-module", sub)

        actor = _make_account()
        app.dependency_overrides[get_current_user] = lambda: actor

        client = TestClient(app, raise_server_exceptions=False)

        with patch.object(
            ModuleAccessGuard, "is_module_enabled", side_effect=lambda *a, **k: enabled[0]
        ):
            resp = client.get("/api/v1/modules/live-module/ping")
            assert resp.status_code == 200

            enabled[0] = False
            resp = client.get("/api/v1/modules/live-module/ping")
            assert resp.status_code == 403

        app.dependency_overrides.clear()
