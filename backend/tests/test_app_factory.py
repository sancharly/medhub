"""TASK-002: App factory and OpenAPI tests."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


def test_create_app_returns_fastapi_instance(app) -> None:
    assert isinstance(app, FastAPI)


def test_app_title(app) -> None:
    assert app.title == "MedHub API"


def test_app_version(app) -> None:
    assert app.version == "0.1.0"


@pytest.mark.asyncio
async def test_openapi_json_returns_3x_doc(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"].startswith("3.")


@pytest.mark.asyncio
async def test_api_v1_prefix_exists(app) -> None:
    """Verify the /api/v1 router is mounted (openapi doc is accessible)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
