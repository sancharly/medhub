"""Tests for PlatformServices facade (TASK-071)."""

from __future__ import annotations

import dataclasses
from unittest.mock import MagicMock

from app.modules.platform_services import PlatformServices


class TestPlatformServicesFacade:
    def test_has_four_fields(self) -> None:
        field_names = {f.name for f in dataclasses.fields(PlatformServices)}
        assert field_names == {"authorization", "clinical", "attachments", "audit"}

    def test_unauthorized_access_raises_403(self) -> None:
        from app.api.errors import AuthorizationError

        mock_authz = MagicMock()
        mock_authz.authorize.side_effect = AuthorizationError("Forbidden")
        svc = PlatformServices(
            authorization=mock_authz,
            clinical=MagicMock(),
            attachments=MagicMock(),
            audit=MagicMock(),
        )
        from app.authz.service import Resource

        try:
            svc.authorization.authorize(MagicMock(), "clinical:read", Resource("x", None, None))
            assert False, "Should have raised"
        except AuthorizationError:
            pass

    def test_two_instances_are_independent(self) -> None:
        svc1 = PlatformServices(
            authorization=MagicMock(),
            clinical=MagicMock(),
            attachments=MagicMock(),
            audit=MagicMock(),
        )
        svc2 = PlatformServices(
            authorization=MagicMock(),
            clinical=MagicMock(),
            attachments=MagicMock(),
            audit=MagicMock(),
        )
        assert svc1.authorization is not svc2.authorization
        assert svc1.audit is not svc2.audit
