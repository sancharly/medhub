"""Tests for anonymized data retrieval endpoint (TASK-062)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.errors import UnauthenticatedError
from app.db.models.anonymized_dataset import AnonymizedDataset
from app.main import create_app


@pytest.fixture()
def client():
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def _make_dataset() -> AnonymizedDataset:
    ds = MagicMock(spec=AnonymizedDataset)
    ds.id = uuid.uuid4()
    ds.payload = {"original_user_type": "PATIENT"}
    return ds


def _mock_redis() -> MagicMock:
    r = MagicMock()
    r.get.return_value = None  # no prior attempts
    r.pipeline.return_value.__enter__ = MagicMock(return_value=MagicMock())
    r.pipeline.return_value.__exit__ = MagicMock(return_value=False)
    r.pipeline.return_value.execute = MagicMock(return_value=[1, True])
    return r


class TestAnonymizedRetrieve:
    def test_valid_code_returns_200(self, client):
        dataset = _make_dataset()
        mock_redis = _mock_redis()

        with patch("app.identity.erasure.ErasureService.retrieve_anonymized", return_value=dataset), \
             patch("app.api.routers.anonymized_data._check_rate_limit"):
            resp = client.post(
                "/api/v1/anonymized-data/retrieve",
                json={"retrievalCode": "valid-code"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["datasetId"] == str(dataset.id)
        assert "payload" in data

    def test_invalid_code_returns_401(self, client):
        with patch(
            "app.identity.erasure.ErasureService.retrieve_anonymized",
            side_effect=UnauthenticatedError("Invalid retrieval code."),
        ), patch("app.api.routers.anonymized_data._check_rate_limit"):
            resp = client.post(
                "/api/v1/anonymized-data/retrieve",
                json={"retrievalCode": "bad-code"},
            )

        assert resp.status_code == 401

    def test_no_auth_required(self, client):
        """Endpoint must be accessible without a session cookie."""
        dataset = _make_dataset()

        with patch("app.identity.erasure.ErasureService.retrieve_anonymized", return_value=dataset), \
             patch("app.api.routers.anonymized_data._check_rate_limit"):
            resp = client.post(
                "/api/v1/anonymized-data/retrieve",
                json={"retrievalCode": "valid-code"},
                # No cookies set
            )

        assert resp.status_code == 200

    def test_rate_limit_rejects_after_threshold(self):
        """Repeated attempts from same IP trigger 429 rate limiting (ADR-0013)."""
        from app.api.deps import get_redis
        from app.api.routers.anonymized_data import _RATE_LIMIT_MAX_ATTEMPTS

        mock_redis = MagicMock()
        # Simulate count already at the limit
        mock_redis.get.return_value = str(_RATE_LIMIT_MAX_ATTEMPTS).encode()

        app = create_app()
        app.dependency_overrides[get_redis] = lambda: mock_redis
        test_client = TestClient(app, raise_server_exceptions=False)

        with patch("app.identity.erasure.ErasureService.retrieve_anonymized"):
            resp = test_client.post(
                "/api/v1/anonymized-data/retrieve",
                json={"retrievalCode": "any-code"},
            )

        assert resp.status_code == 429
