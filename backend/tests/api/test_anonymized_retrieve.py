"""Tests for anonymized data retrieval endpoint (TASK-062)."""

from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.api.errors import RateLimitedError, UnauthenticatedError
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

        with (
            patch(
                "app.identity.erasure.ErasureService.retrieve_anonymized",
                return_value=dataset,
            ),
            patch("app.api.routers.anonymized_data._check_rate_limit"),
        ):
            resp = client.post(
                "/api/v1/anonymized-data/retrieve",
                json={"retrievalCode": "valid-code"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["datasetId"] == str(dataset.id)
        assert "payload" in data

    def test_invalid_code_returns_401(self, client):
        with (
            patch(
                "app.identity.erasure.ErasureService.retrieve_anonymized",
                side_effect=UnauthenticatedError("Invalid retrieval code."),
            ),
            patch("app.api.routers.anonymized_data._check_rate_limit"),
        ):
            resp = client.post(
                "/api/v1/anonymized-data/retrieve",
                json={"retrievalCode": "bad-code"},
            )

        assert resp.status_code == 401

    def test_no_auth_required(self, client):
        """Endpoint must be accessible without a session cookie."""
        dataset = _make_dataset()

        with (
            patch(
                "app.identity.erasure.ErasureService.retrieve_anonymized",
                return_value=dataset,
            ),
            patch("app.api.routers.anonymized_data._check_rate_limit"),
        ):
            resp = client.post(
                "/api/v1/anonymized-data/retrieve",
                json={"retrievalCode": "valid-code"},
                # No cookies set
            )

        assert resp.status_code == 200


PROXY_ADDRESS = "10.0.0.2"


@pytest.fixture()
def rate_env(monkeypatch):
    """Application behind a trusted proxy at PROXY_ADDRESS, a fakeredis, a counting service."""
    from app.api.deps import get_redis
    from app.core.config import get_settings

    monkeypatch.setenv("TRUSTED_PROXIES", PROXY_ADDRESS)
    get_settings.cache_clear()
    server = fakeredis.FakeServer()
    app = create_app()
    app.dependency_overrides[get_redis] = lambda: fakeredis.FakeRedis(server=server)
    retrieve = MagicMock(return_value=_make_dataset())
    with patch("app.identity.erasure.ErasureService.retrieve_anonymized", retrieve):
        yield app, retrieve
    get_settings.cache_clear()


def _post(app, peer: str, forwarded: str | None = None) -> int:
    headers = {"X-Forwarded-For": forwarded} if forwarded else {}
    with TestClient(app, client=(peer, 5000), raise_server_exceptions=False) as c:
        return c.post(
            "/api/v1/anonymized-data/retrieve", json={"retrievalCode": "x"}, headers=headers
        ).status_code


class TestRetrievalRateLimitPerAddress:
    """SR-042 AC 4 and AC 5 (TS-016 TC-016.4, TC-016.5)."""

    def test_sixth_attempt_is_refused_and_not_evaluated(self, rate_env):  # SR-042 AC 4
        app, retrieve = rate_env
        codes = [_post(app, PROXY_ADDRESS, "203.0.113.7") for _ in range(6)]
        assert codes == [200] * 5 + [429]
        assert retrieve.call_count == 5

    def test_client_b_is_evaluated_after_client_a_is_limited(self, rate_env):  # SR-042 AC 5
        app, retrieve = rate_env
        for _ in range(6):
            _post(app, PROXY_ADDRESS, "203.0.113.7")
        assert _post(app, PROXY_ADDRESS, "203.0.113.7") == 429
        before = retrieve.call_count
        assert _post(app, PROXY_ADDRESS, "198.51.100.20") == 200
        assert retrieve.call_count == before + 1

    def test_window_is_fixed_from_the_first_attempt(self, rate_env, monkeypatch):  # SR-042 AC 4
        app, retrieve = rate_env
        start = time.time()
        now = [start]
        monkeypatch.setattr(time, "time", lambda: now[0])
        assert _post(app, PROXY_ADDRESS, "203.0.113.7") == 200
        now[0] = start + 1800
        for _ in range(4):  # attempts 2..5 later in the window must not extend it
            assert _post(app, PROXY_ADDRESS, "203.0.113.7") == 200
        now[0] = start + 3599
        assert _post(app, PROXY_ADDRESS, "203.0.113.7") == 429
        assert retrieve.call_count == 5
        now[0] = start + 3601
        assert _post(app, PROXY_ADDRESS, "203.0.113.7") == 200
        assert retrieve.call_count == 6

    def test_forged_header_from_untrusted_peer_counts_against_the_peer(self, rate_env):
        # SR-042 AC 2 and AC 4: a forged address does not buy a fresh bucket
        app, retrieve = rate_env
        codes = [_post(app, "198.51.100.9", f"1.2.3.{i}") for i in range(6)]
        assert codes == [200] * 5 + [429]
        assert retrieve.call_count == 5

    def test_missing_peer_is_refused_without_a_shared_bucket(self, rate_env):  # SR-042 AC 4
        from app.api.routers.anonymized_data import _check_rate_limit

        _, retrieve = rate_env
        with pytest.raises(RateLimitedError):
            _check_rate_limit(None, fakeredis.FakeRedis())
        assert retrieve.call_count == 0

    def test_concurrent_attempts_from_one_address_evaluate_exactly_five(self, rate_env):
        # SR-042 AC 4: the count is atomic, so 10 simultaneous attempts evaluate exactly 5
        app, retrieve = rate_env
        barrier = threading.Barrier(10)

        def attempt(_: int) -> int:
            barrier.wait()
            return _post(app, PROXY_ADDRESS, "203.0.113.7")

        with ThreadPoolExecutor(max_workers=10) as pool:
            codes = list(pool.map(attempt, range(10)))
        assert codes.count(200) == 5 and codes.count(429) == 5
        assert retrieve.call_count == 5
