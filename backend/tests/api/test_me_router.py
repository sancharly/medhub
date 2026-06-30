"""Tests for /me endpoints (TASK-067)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models.account import Account, AccountStatus, UserType
from app.db.repositories.session import get_db
from app.main import create_app


def _make_account(user_type: UserType = UserType.DOCTOR) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "doctor@example.com"
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    acct.first_name = "Jane"
    acct.surname = "Doe"
    acct.date_of_birth = None
    acct.created_at = datetime.now(UTC)
    acct.password_changed_at = None  # not expired; needed by PasswordService.is_expired
    return acct


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _auth_as(client, actor: Account) -> None:
    client.app.dependency_overrides[get_current_user] = lambda: actor

    def override_db():
        yield MagicMock()

    client.app.dependency_overrides[get_db] = override_db


class TestGetMe:
    def test_get_me_returns_200(self, client):
        actor = _make_account(UserType.DOCTOR)
        _auth_as(client, actor)

        resp = client.get("/api/v1/me")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == actor.email
        assert data["userType"] == actor.user_type.value

    def test_get_me_requires_auth(self, client):
        resp = client.get("/api/v1/me")
        assert resp.status_code == 401


class TestGetMyModules:
    def test_get_modules_returns_200(self, client):
        actor = _make_account(UserType.DOCTOR)
        _auth_as(client, actor)

        mock_membership = MagicMock()
        mock_membership.group_id = uuid.uuid4()

        with (
            patch(
                "app.db.repositories.group_repo.GroupRepository.memberships_for_account",
                return_value=[mock_membership],
            ),
            patch(
                "app.db.repositories.module_repo.ModuleRepository.enabled_module_keys_for_groups",
                return_value=["clinical", "appointments"],
            ),
        ):
            resp = client.get("/api/v1/me/modules")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert "modules" in data
        assert isinstance(data["modules"], list)

    def test_get_modules_requires_auth(self, client):
        resp = client.get("/api/v1/me/modules")
        assert resp.status_code == 401
