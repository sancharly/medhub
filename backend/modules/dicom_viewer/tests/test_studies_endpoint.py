"""Tests for DICOM studies endpoint (TASK-073)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from dicom_viewer.manifest import DICOMViewerManifest
from dicom_viewer.router import build_router
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.errors import AuthorizationError, register_error_handlers
from app.audit.actions import AuditAction
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.audit import AuditOutcome
from app.modules.platform_services import PlatformServices


def _make_account(user_type: UserType = UserType.DOCTOR) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    return acct


def _build_app_with_dicom(
    attachment_bytes: bytes = b"DICOM_DATA",
    content_type: str = "application/dicom",
    raise_authz: bool = False,
) -> tuple[FastAPI, MagicMock, Account]:
    app = FastAPI()
    register_error_handlers(app)

    actor = _make_account()

    mock_attachments = MagicMock()
    if raise_authz:
        mock_attachments.open.side_effect = AuthorizationError("Forbidden")
    else:
        mock_attachments.open.return_value = (attachment_bytes, content_type, "test.dcm")

    mock_audit = MagicMock()
    services = PlatformServices(
        authorization=MagicMock(),
        clinical=MagicMock(),
        attachments=mock_attachments,
        audit=mock_audit,
    )

    router = build_router(services)
    app.include_router(router, prefix="/studies-test")

    app.dependency_overrides[get_current_user] = lambda: actor
    return app, mock_audit, actor


class TestDICOMManifest:
    def test_manifest_has_correct_module_key(self) -> None:
        m = DICOMViewerManifest()
        assert m.module_key == "dicom-viewer"

    def test_manifest_name_and_version(self) -> None:
        m = DICOMViewerManifest()
        assert m.name == "DICOM Viewer"
        assert m.version == "0.1.0"

    def test_manifest_required_permissions(self) -> None:
        m = DICOMViewerManifest()
        assert "clinical:read" in m.required_permissions

    def test_manifest_register_mounts_router(self) -> None:
        m = DICOMViewerManifest()
        mock_registry = MagicMock()
        mock_services = MagicMock()
        m.register(mock_registry, mock_services)
        assert mock_registry.mount.called
        assert mock_registry.mount.call_args[0][0] == "dicom-viewer"


class TestDICOMStudiesEndpoint:
    def test_authorized_returns_dicom_bytes(self) -> None:
        dicom_bytes = b"DICOM_BYTES_HERE"
        app, mock_audit, actor = _build_app_with_dicom(attachment_bytes=dicom_bytes)
        client = TestClient(app, raise_server_exceptions=False)
        attachment_id = uuid.uuid4()
        resp = client.get(f"/studies-test/studies/{attachment_id}")
        assert resp.status_code == 200
        assert resp.content == dicom_bytes
        assert resp.headers["content-type"] == "application/dicom"

    def test_authorized_returns_bytes_from_attachments_service(self) -> None:
        expected = b"SPECIFIC_DICOM"
        app, mock_audit, actor = _build_app_with_dicom(attachment_bytes=expected)
        client = TestClient(app, raise_server_exceptions=False)
        attachment_id = uuid.uuid4()
        resp = client.get(f"/studies-test/studies/{attachment_id}")
        assert resp.content == expected

    def test_enabled_but_unauthorized_returns_403(self) -> None:
        app, _, _ = _build_app_with_dicom(raise_authz=True)
        client = TestClient(app, raise_server_exceptions=False)
        attachment_id = uuid.uuid4()
        resp = client.get(f"/studies-test/studies/{attachment_id}")
        assert resp.status_code == 403

    def test_non_dicom_attachment_returns_400(self) -> None:
        app, _, _ = _build_app_with_dicom(
            attachment_bytes=b"PDF_DATA", content_type="application/pdf"
        )
        client = TestClient(app, raise_server_exceptions=False)
        attachment_id = uuid.uuid4()
        resp = client.get(f"/studies-test/studies/{attachment_id}")
        assert resp.status_code == 400

    def test_audit_event_emitted(self) -> None:
        app, mock_audit, actor = _build_app_with_dicom()
        client = TestClient(app, raise_server_exceptions=False)
        attachment_id = uuid.uuid4()
        client.get(f"/studies-test/studies/{attachment_id}")
        mock_audit.record.assert_called_once()
        call_kwargs = mock_audit.record.call_args.kwargs
        assert call_kwargs["action"] == AuditAction.DICOM_STUDY_READ
        assert call_kwargs["outcome"] == AuditOutcome.SUCCESS

    def test_frame_query_param_extracts_frame(self) -> None:
        """Frame extraction is attempted when ?frame=0 is passed."""
        mock_frame_bytes = b"FRAME_BYTES"

        patch_path = "dicom_viewer.router.stream_dicom"
        with patch(patch_path, return_value=mock_frame_bytes) as mock_stream:
            app, mock_audit, actor = _build_app_with_dicom()
            client = TestClient(app, raise_server_exceptions=False)
            attachment_id = uuid.uuid4()
            client.get(f"/studies-test/studies/{attachment_id}?frame=0")
            # stream_dicom called with frame=0
            mock_stream.assert_called_once_with(b"DICOM_DATA", 0)

    def test_ct_modality_streams_successfully(self) -> None:
        """CT DICOM data streams without error when stream_dicom is mocked."""
        with patch("dicom_viewer.router.stream_dicom", return_value=b"CT_DATA"):
            app, _, _ = _build_app_with_dicom(attachment_bytes=b"CT_RAW")
            client = TestClient(app, raise_server_exceptions=False)
            attachment_id = uuid.uuid4()
            resp = client.get(f"/studies-test/studies/{attachment_id}")
        assert resp.status_code == 200

    def test_mri_modality_streams_successfully(self) -> None:
        with patch("dicom_viewer.router.stream_dicom", return_value=b"MRI_DATA"):
            app, _, _ = _build_app_with_dicom(attachment_bytes=b"MRI_RAW")
            client = TestClient(app, raise_server_exceptions=False)
            attachment_id = uuid.uuid4()
            resp = client.get(f"/studies-test/studies/{attachment_id}")
        assert resp.status_code == 200

    def test_xr_modality_streams_successfully(self) -> None:
        with patch("dicom_viewer.router.stream_dicom", return_value=b"XR_DATA"):
            app, _, _ = _build_app_with_dicom(attachment_bytes=b"XR_RAW")
            client = TestClient(app, raise_server_exceptions=False)
            attachment_id = uuid.uuid4()
            resp = client.get(f"/studies-test/studies/{attachment_id}")
        assert resp.status_code == 200
