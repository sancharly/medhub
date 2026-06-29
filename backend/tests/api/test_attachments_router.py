"""Tests for attachment endpoints (TASK-066)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routers.attachments import _get_attachment_service
from app.attachments.service import AttachmentService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.db.repositories.session import get_db
from app.main import create_app


def _make_account(user_type: UserType = UserType.DOCTOR) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "doctor@example.com"
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    return acct


def _make_attachment() -> Attachment:
    att = MagicMock(spec=Attachment)
    att.id = uuid.uuid4()
    att.clinical_entry_id = uuid.uuid4()
    att.patient_id = uuid.uuid4()
    att.filename = "test.pdf"
    att.content_type = "application/pdf"
    att.size = 1024
    att.checksum = "abc123"
    att.created_at = datetime.now(UTC)
    return att


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


class TestUploadAttachment:
    def test_upload_attachment_returns_201(self, client):
        actor = _make_account(UserType.DOCTOR)
        entry_id = uuid.uuid4()
        att = _make_attachment()
        _auth_as(client, actor)

        mock_att_svc = MagicMock(spec=AttachmentService)
        mock_att_svc.store.return_value = att
        client.app.dependency_overrides[_get_attachment_service] = lambda: mock_att_svc

        resp = client.post(
            f"/api/v1/clinical-entries/{entry_id}/attachments",
            content=b"PDF content",
            headers={
                "Content-Type": "application/pdf",
                "X-Filename": "test.pdf",
                "X-CSRF-Token": "tok",
            },
            cookies={"medhub_csrf": "tok"},
        )

        client.app.dependency_overrides = {}
        assert resp.status_code == 201

    def test_upload_requires_auth(self, client):
        resp = client.post(
            f"/api/v1/clinical-entries/{uuid.uuid4()}/attachments",
            content=b"data",
        )
        assert resp.status_code == 403


class TestFetchAttachment:
    def test_fetch_attachment_returns_file(self, client):
        actor = _make_account(UserType.DOCTOR)
        att_id = uuid.uuid4()
        _auth_as(client, actor)

        mock_att_svc = MagicMock(spec=AttachmentService)
        mock_att_svc.open.return_value = (b"PDF content", "application/pdf", "test.pdf")
        client.app.dependency_overrides[_get_attachment_service] = lambda: mock_att_svc

        resp = client.get(f"/api/v1/attachments/{att_id}")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        assert resp.content == b"PDF content"

    def test_fetch_requires_auth(self, client):
        resp = client.get(f"/api/v1/attachments/{uuid.uuid4()}")
        assert resp.status_code == 401
