"""Tests for groups endpoints (TASK-063)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.group import Group
from app.db.repositories.session import get_db
from app.main import create_app


def _make_account(user_type: UserType = UserType.SYSADMIN) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "sysadmin@example.com"
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    return acct


def _make_group(name: str = "Test Group") -> Group:
    grp = MagicMock(spec=Group)
    grp.id = uuid.uuid4()
    grp.name = name
    grp.created_at = datetime.now(UTC)
    return grp


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


class TestCreateGroup:
    def test_create_group_returns_201(self, client):
        actor = _make_account(UserType.SYSADMIN)
        group = _make_group("Cardiology")
        _auth_as(client, actor)

        with patch("app.groups.service.GroupService.create_group", return_value=group):
            resp = client.post(
                "/api/v1/groups",
                json={"name": "Cardiology"},
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 201
        assert resp.json()["name"] == "Cardiology"

    def test_create_group_requires_auth(self, client):
        resp = client.post("/api/v1/groups", json={"name": "Test"})
        assert resp.status_code == 403


class TestListGroups:
    def test_list_groups_returns_200(self, client):
        actor = _make_account(UserType.SYSADMIN)
        group = _make_group()
        _auth_as(client, actor)

        with patch("app.groups.service.GroupService.list_groups", return_value=[group]):
            resp = client.get("/api/v1/groups")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_groups_requires_auth(self, client):
        resp = client.get("/api/v1/groups")
        assert resp.status_code == 401


class TestAddMember:
    def test_add_member_returns_204(self, client):
        actor = _make_account(UserType.SYSADMIN)
        group_id = uuid.uuid4()
        member_id = uuid.uuid4()
        _auth_as(client, actor)

        with patch("app.groups.service.GroupService.add_member"):
            resp = client.post(
                f"/api/v1/groups/{group_id}/members",
                json={"accountId": str(member_id)},
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 204


class TestRemoveMember:
    def test_remove_member_returns_204(self, client):
        actor = _make_account(UserType.SYSADMIN)
        group_id = uuid.uuid4()
        member_id = uuid.uuid4()
        _auth_as(client, actor)

        with patch("app.groups.service.GroupService.remove_member"):
            resp = client.delete(
                f"/api/v1/groups/{group_id}/members/{member_id}",
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 204


class TestSetModuleEnabled:
    def test_set_module_enabled_returns_204(self, client):
        actor = _make_account(UserType.SYSADMIN)
        group_id = uuid.uuid4()
        _auth_as(client, actor)

        with patch("app.groups.service.GroupService.set_module_enabled"):
            resp = client.put(
                f"/api/v1/groups/{group_id}/modules/clinical",
                json={"enabled": True},
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 204
