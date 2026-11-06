"""Tests for attachment endpoints (TASK-066, TASK-066a)."""

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
            files={"file": ("test.pdf", b"PDF content", "application/pdf")},
            headers={"X-CSRF-Token": "tok"},
            cookies={"medhub_csrf": "tok"},
        )

        client.app.dependency_overrides = {}
        assert resp.status_code == 201

    def test_upload_passes_filename_and_content_type(self, client):
        """Router reads filename and content_type from the UploadFile."""
        actor = _make_account(UserType.DOCTOR)
        entry_id = uuid.uuid4()
        att = _make_attachment()
        _auth_as(client, actor)

        mock_att_svc = MagicMock(spec=AttachmentService)
        mock_att_svc.store.return_value = att
        client.app.dependency_overrides[_get_attachment_service] = lambda: mock_att_svc

        resp = client.post(
            f"/api/v1/clinical-entries/{entry_id}/attachments",
            files={"file": ("report.pdf", b"PDF content", "application/pdf")},
            headers={"X-CSRF-Token": "tok"},
            cookies={"medhub_csrf": "tok"},
        )

        client.app.dependency_overrides = {}
        assert resp.status_code == 201
        call_args = mock_att_svc.store.call_args
        assert call_args[0][2] == "report.pdf"  # filename
        assert call_args[0][3] == "application/pdf"  # content_type

    def test_upload_requires_auth(self, client):
        resp = client.post(
            f"/api/v1/clinical-entries/{uuid.uuid4()}/attachments",
            files={"file": ("test.pdf", b"data", "application/pdf")},
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


class TestFetchSubstitutedAttachment:
    def test_substituted_object_returns_502_problem_without_content(self, client):
        """TC-007.6: through the real service, a substituted object yields a 502 problem."""
        import hashlib  # noqa: PLC0415

        from app.audit.service import AuditService  # noqa: PLC0415
        from app.authz.service import AuthorizationService  # noqa: PLC0415

        actor = _make_account(UserType.DOCTOR)
        _auth_as(client, actor)
        att = _make_attachment()
        att.checksum = hashlib.sha256(b"original bytes").hexdigest()
        att.storage_key = "attachments/x"

        repo = MagicMock()
        repo.get.return_value = att
        storage = MagicMock()
        storage.get_object.return_value = b"planted bytes"
        audit_repo = MagicMock()
        svc = AttachmentService(
            repo,
            MagicMock(),
            AuditService(audit_repo),
            MagicMock(spec=AuthorizationService),
            storage,
        )
        client.app.dependency_overrides[_get_attachment_service] = lambda: svc

        resp = client.get(f"/api/v1/attachments/{att.id}")

        client.app.dependency_overrides = {}
        assert resp.status_code == 502
        assert resp.headers["content-type"].startswith("application/problem+json")
        body = resp.json()
        assert body["type"].endswith("/attachment-integrity-failure")
        assert body["status"] == 502
        assert str(att.id) in body["detail"]
        assert b"planted bytes" not in resp.content
        assert b"original bytes" not in resp.content
        assert att.checksum not in resp.text
        logged = audit_repo.add_independent.call_args.args[0]
        assert logged.outcome.value == "FAILURE"
        assert logged.target_id == str(att.id)


class TestListAttachments:
    def test_list_attachments_returns_200(self, client):
        actor = _make_account(UserType.DOCTOR)
        entry_id = uuid.uuid4()
        att = _make_attachment()
        _auth_as(client, actor)

        mock_att_svc = MagicMock(spec=AttachmentService)
        mock_att_svc.list_attachments.return_value = [att]
        client.app.dependency_overrides[_get_attachment_service] = lambda: mock_att_svc

        resp = client.get(f"/api/v1/clinical-entries/{entry_id}/attachments")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(att.id)

    def test_list_attachments_empty(self, client):
        actor = _make_account(UserType.DOCTOR)
        entry_id = uuid.uuid4()
        _auth_as(client, actor)

        mock_att_svc = MagicMock(spec=AttachmentService)
        mock_att_svc.list_attachments.return_value = []
        client.app.dependency_overrides[_get_attachment_service] = lambda: mock_att_svc

        resp = client.get(f"/api/v1/clinical-entries/{entry_id}/attachments")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_attachments_requires_auth(self, client):
        resp = client.get(f"/api/v1/clinical-entries/{uuid.uuid4()}/attachments")
        assert resp.status_code == 401


_NON_LATIN1_CASES = [
    (
        "résumé 患者 #1.txt",
        'attachment; filename="resume __ #1.txt"; '
        "filename*=UTF-8''r%C3%A9sum%C3%A9%20%E6%82%A3%E8%80%85%20%231.txt",
    ),
    (
        "report’s summary.pdf",
        'attachment; filename="report_s summary.pdf"; '
        "filename*=UTF-8''report%E2%80%99s%20summary.pdf",
    ),
]


class TestFetchAttachmentFileNames:
    """PRB-063 / TASK-204: any file name downloads (AC-1, AC-2); a failure is audited (AC-3)."""

    @staticmethod
    def _fetch(client, filename: str, body: bytes = b"PAYLOAD"):
        actor = _make_account(UserType.DOCTOR)
        _auth_as(client, actor)
        svc = MagicMock(spec=AttachmentService)
        svc.open.return_value = (body, "text/plain", filename)
        client.app.dependency_overrides[_get_attachment_service] = lambda: svc
        att_id = uuid.uuid4()
        try:
            return client.get(f"/api/v1/attachments/{att_id}"), svc, actor, att_id
        finally:
            client.app.dependency_overrides = {}

    @pytest.mark.parametrize(("filename", "header"), _NON_LATIN1_CASES)
    def test_non_latin1_name_downloads_with_encoded_header(self, client, filename, header):
        """AC-1: 200, identical bytes, RFC 6266/5987 header."""
        resp, *_ = self._fetch(client, filename)
        assert resp.status_code == 200
        assert resp.content == b"PAYLOAD"
        assert resp.headers["content-disposition"] == header

    @pytest.mark.parametrize("filename", ['a"b\\c.pdf', "x\r\nX-Injected: 1.txt", "t\tab\x7f.txt"])
    def test_quote_backslash_and_controls_keep_one_well_formed_header(self, client, filename):
        """AC-2: exactly one Content-Disposition, no injected header."""
        resp, *_ = self._fetch(client, filename)
        assert resp.status_code == 200
        raw = [v for k, v in resp.headers.raw if k.lower() == b"content-disposition"]
        assert len(raw) == 1
        raw[0].decode("ascii")
        assert "x-injected" not in resp.headers
        assert b"\r" not in raw[0] and b"\n" not in raw[0]

    def test_response_build_failure_records_access_failure(self, client, monkeypatch):
        """AC-3: a failure while building the response is audited, then the 500 is returned."""

        def _boom(*_a, **_k):
            raise RuntimeError("cannot build header")

        monkeypatch.setattr("app.api.routers.attachments.content_disposition", _boom)
        resp, svc, actor, att_id = self._fetch(client, "test.pdf")
        assert resp.status_code == 500
        svc.record_access_failure.assert_called_once_with(actor, att_id)
