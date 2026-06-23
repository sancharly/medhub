"""Tests for module discovery (TASK-070)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models.account import Account, AccountStatus, UserType
from app.main import create_app
from app.modules.discovery import discover_modules


def _fake_manifest(
    module_key: str = "test-module",
    name: str = "Test Module",
    version: str = "1.0.0",
    required_permissions: object = None,
) -> MagicMock:
    m = MagicMock()
    m.module_key = module_key
    m.name = name
    m.version = version
    m.required_permissions = required_permissions if required_permissions is not None else []
    return m


def _fake_ep(manifest: object) -> MagicMock:
    ep = MagicMock()
    ep.name = getattr(manifest, "module_key", "unknown")
    ep.load.return_value = manifest
    return ep


def _make_account(user_type: UserType = UserType.SYSADMIN) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    acct.email = "sysadmin@example.com"
    return acct


class TestModuleDiscovery:
    def test_valid_entry_point_is_discovered(self) -> None:
        manifest = _fake_manifest()
        eps = [_fake_ep(manifest)]
        with patch("app.modules.discovery.importlib.metadata.entry_points", return_value=eps):
            result = discover_modules()
        assert len(result) == 1
        assert result[0].module_key == "test-module"

    def test_missing_module_key_is_skipped(self) -> None:
        manifest = _fake_manifest(module_key="")
        eps = [_fake_ep(manifest)]
        with patch("app.modules.discovery.importlib.metadata.entry_points", return_value=eps):
            result = discover_modules()
        assert result == []

    def test_bad_version_is_skipped(self) -> None:
        manifest = _fake_manifest(version="not-semver")
        eps = [_fake_ep(manifest)]
        with patch("app.modules.discovery.importlib.metadata.entry_points", return_value=eps):
            result = discover_modules()
        assert result == []

    def test_non_list_permissions_is_skipped(self) -> None:
        manifest = _fake_manifest(required_permissions="clinical:read")
        eps = [_fake_ep(manifest)]
        with patch("app.modules.discovery.importlib.metadata.entry_points", return_value=eps):
            result = discover_modules()
        assert result == []

    def test_entry_point_that_raises_is_isolated(self) -> None:
        bad_ep = MagicMock()
        bad_ep.name = "bad-module"
        bad_ep.load.side_effect = ImportError("boom")

        good_manifest = _fake_manifest(module_key="good-module")
        good_ep = _fake_ep(good_manifest)

        eps = [bad_ep, good_ep]
        with patch("app.modules.discovery.importlib.metadata.entry_points", return_value=eps):
            result = discover_modules()
        assert len(result) == 1
        assert result[0].module_key == "good-module"

    def test_no_entry_points_returns_empty(self) -> None:
        with patch("app.modules.discovery.importlib.metadata.entry_points", return_value=[]):
            result = discover_modules()
        assert result == []


class TestModuleRegistrySync:
    def test_list_installed_returns_upserted_modules(self) -> None:
        from unittest.mock import MagicMock

        from app.modules.registry_service import ModuleRegistryService

        mock_repo = MagicMock()
        mock_repo.list_installed.return_value = []
        mock_audit = MagicMock()
        svc = ModuleRegistryService(mock_repo, mock_audit)
        db = MagicMock()

        manifests = [_fake_manifest("mod-a"), _fake_manifest("mod-b")]
        svc.sync_installed(manifests, db)

        assert mock_repo.upsert.call_count == 2
        mock_repo.remove_absent.assert_called_once()
        present_keys = mock_repo.remove_absent.call_args[0][0]
        assert set(present_keys) == {"mod-a", "mod-b"}

    def test_registry_sync_emits_audit_event(self) -> None:
        from app.modules.registry_service import ModuleRegistryService

        mock_repo = MagicMock()
        mock_audit = MagicMock()
        svc = ModuleRegistryService(mock_repo, mock_audit)
        db = MagicMock()

        svc.sync_installed([_fake_manifest("m1")], db)

        mock_audit.record.assert_called_once()
        call_kwargs = mock_audit.record.call_args.kwargs
        assert "MODULE_REGISTRY_SYNC" in call_kwargs.get("action", "")

    def test_absent_module_is_removed(self) -> None:
        from app.modules.registry_service import ModuleRegistryService

        mock_repo = MagicMock()
        mock_audit = MagicMock()
        svc = ModuleRegistryService(mock_repo, mock_audit)
        db = MagicMock()

        svc.sync_installed([], db)

        mock_repo.remove_absent.assert_called_once_with([])


class TestModulesEndpoint:
    @pytest.fixture()
    def app(self):
        return create_app()

    @pytest.fixture()
    def client(self, app):
        return TestClient(app, raise_server_exceptions=False)

    def test_non_sysadmin_denied(self, client) -> None:
        actor = _make_account(UserType.DOCTOR)
        client.app.dependency_overrides[get_current_user] = lambda: actor
        resp = client.get("/api/v1/modules")
        assert resp.status_code == 403
        client.app.dependency_overrides.clear()

    def test_sysadmin_gets_empty_list(self, client) -> None:
        actor = _make_account(UserType.SYSADMIN)

        from app.db.repositories.module_repo import ModuleRepository

        mock_repo = MagicMock()
        mock_repo.list_installed.return_value = []

        def override_db():
            db = MagicMock()
            return db

        client.app.dependency_overrides[get_current_user] = lambda: actor

        # Patch ModuleRepository.list_installed directly
        with patch.object(ModuleRepository, "list_installed", return_value=[]):
            resp = client.get("/api/v1/modules")

        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        client.app.dependency_overrides.clear()
