"""ADR-0023 / SR-012 AC 5: every use of ``get_db`` has scope ``"function"``.

A dependency with scope ``"function"`` is torn down (commit or rollback) when the endpoint has
returned, before the response is sent. The dependency cache key includes the scope, so one route
that mixes ``Depends(get_db)`` and ``Depends(get_db, scope="function")`` gets two sessions and
two transactions, one of which still commits after the response (PRB-080). The check walks the
dependants of every route of the assembled application (core and, when importable, the installed
modules) and fails on any ``get_db`` dependant that has another scope, or on a route that resolves
more than one ``get_db`` cache key.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Depends, FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute, iter_route_contexts
from sqlalchemy.orm import Session

from app.db.repositories.session import DbSession, get_db
from app.main import create_app


def _walk(dependant: Dependant) -> Iterator[Dependant]:
    yield dependant
    for sub in dependant.dependencies:
        yield from _walk(sub)


def _api_routes(app: FastAPI) -> Iterator[Any]:
    """Every API route with its effective context (FastAPI 0.138 keeps included routers lazy)."""
    for context in iter_route_contexts(app.routes):
        if isinstance(context.original_route, APIRoute):
            yield context


def _violations(app: FastAPI) -> list[str]:
    found: list[str] = []
    for route in _api_routes(app):
        where = f"{sorted(route.methods)} {route.path}"
        keys = set()
        for dep in _walk(route.dependant):
            if dep.call is not get_db:
                continue
            keys.add(dep.cache_key)
            if dep.computed_scope != "function":
                found.append(f"{where}: get_db has scope {dep.computed_scope!r}")
        if len(keys) > 1:
            found.append(f"{where}: {len(keys)} get_db cache keys (two sessions)")
    return found


def _apps() -> list[FastAPI]:
    apps = [create_app()]
    try:
        from dicom_viewer.router import build_router  # noqa: PLC0415
    except ImportError:
        return apps
    module_app = FastAPI()
    module_app.include_router(build_router(), prefix="/studies-test")
    apps.append(module_app)
    return apps


def test_every_route_resolves_get_db_with_function_scope() -> None:
    inspected = 0
    for app in _apps():
        inspected += sum(
            1 for route in _api_routes(app) for d in _walk(route.dependant) if d.call is get_db
        )
        assert _violations(app) == []
    assert inspected > 20  # the walk really reached the routers' dependencies


def test_planted_route_with_default_scope_is_reported() -> None:
    """Negative control: the check fails on a route using plain ``Depends(get_db)``."""
    app = FastAPI()
    router = APIRouter()

    @router.get("/planted")
    def planted(db: Session = Depends(get_db)) -> dict[str, str]:
        return {}

    app.include_router(router)
    assert any("/planted" in v and "'request'" in v for v in _violations(app))


def test_planted_route_mixing_scopes_is_reported() -> None:
    """Negative control: two scopes in one route are two sessions."""
    app = FastAPI()

    def _svc(db: Session = Depends(get_db)) -> int:
        return 1

    @app.get("/mixed")
    def mixed(db: DbSession, other: int = Depends(_svc)) -> dict[str, str]:
        return {}

    assert any("/mixed" in v and "cache keys" in v for v in _violations(app))
