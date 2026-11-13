"""SR-026 AC 5, NFR-008 / ADR-0022: no blocking client is called on the event loop.

A FastAPI ``async def`` dependency or handler runs on the event loop; a plain ``def`` runs in a
worker thread. Redis (redis-py), the database (SQLAlchemy / psycopg2) and the object store (boto3)
are blocking, so any ``async def`` under ``app/api`` that calls one stalls every concurrent request
(PRB-009). The fix is a plain ``def``, or ``run_in_threadpool`` for a handler that must stay
``async`` (the upload awaits ``UploadFile``).

This is a static check: it walks ``app/api`` with ``ast`` and fails on any call of a name from the
deny list made directly inside an ``async def``. ``run_in_threadpool(svc.store, ...)`` passes the
method without calling it, so it is not a call here; an awaited call is an async API and is not
flagged either. The deny list is closed on purpose: a new blocking call that is not on it needs
the name added, which is the review point.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[2] / "app" / "api"

# Methods of the SQLAlchemy session, the object-store client and boto3.
BLOCKING_ATTRIBUTES = frozenset(
    {
        "query",
        "execute",
        "scalar",
        "scalars",
        "commit",
        "rollback",
        "flush",
        "refresh",
        "put_object",
        "get_object",
        "upload_fileobj",
        "download_fileobj",
        "delete_object",
        "head_object",
    }
)
# Methods of the services and repositories that block (session store, database, object store).
BLOCKING_SERVICE_METHODS = frozenset(
    {
        "resolve",
        "invalidate",
        "get_inactivity_expiry",
        "list_account_session_ids",
        "store",
        "open_stream",
        "get_by_id",
        "authorize",
        "decide",
        "record",
    }
)
# Redis commands; only on a receiver that is named like a Redis client, because `.get` and `.set`
# are also harmless methods of dicts, cookies and headers.
REDIS_COMMANDS = frozenset(
    {"get", "set", "setex", "delete", "incr", "expire", "ttl", "eval", "evalsha", "pipeline"}
)
REDIS_RECEIVERS = frozenset({"r", "redis", "redis_client", "redis_lib"})


def _receiver_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return func.value.id
    return None


def _blocking_name(call: ast.Call) -> str | None:
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr in BLOCKING_ATTRIBUTES | BLOCKING_SERVICE_METHODS:
        return func.attr
    if func.attr in REDIS_COMMANDS and _receiver_name(call) in REDIS_RECEIVERS:
        return f"{_receiver_name(call)}.{func.attr}"
    return None


class _AsyncScan(ast.NodeVisitor):
    """Collect blocking calls made directly in an `async def` body (not in nested sync defs)."""

    def __init__(self) -> None:
        self.found: list[tuple[str, int, str]] = []
        self._async: list[str] = []
        self._awaited: set[int] = set()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._async.append(node.name)
        self.generic_visit(node)
        self._async.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        saved, self._async = self._async, []  # a nested plain def runs in a thread when used so
        self.generic_visit(node)
        self._async = saved

    def visit_Lambda(self, node: ast.Lambda) -> None:
        saved, self._async = self._async, []
        self.generic_visit(node)
        self._async = saved

    def visit_Await(self, node: ast.Await) -> None:
        if isinstance(node.value, ast.Call):
            self._awaited.add(id(node.value))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self._async and id(node) not in self._awaited:
            name = _blocking_name(node)
            if name:
                self.found.append((self._async[-1], node.lineno, name))
        self.generic_visit(node)


def blocking_calls_in_async(source: str) -> list[tuple[str, int, str]]:
    """(async function, line, called name) for each blocking call made on the event loop."""
    scan = _AsyncScan()
    scan.visit(ast.parse(source))
    return scan.found


def test_no_async_def_calls_blocking_client() -> None:
    """SR-026 AC 5: every `async def` under app/api is free of blocking calls."""
    offenders = []
    for path in sorted(API_DIR.rglob("*.py")):
        for function, line, name in blocking_calls_in_async(path.read_text()):
            offenders.append(
                f"{path.relative_to(API_DIR.parent.parent)}:{line} {function} -> {name}"
            )
    assert offenders == [], "blocking call on the event loop:\n" + "\n".join(offenders)


def test_the_scan_covers_the_async_handlers_it_is_meant_to_guard() -> None:
    """The guard is not vacuous: it sees the async functions that exist under app/api."""
    names = set()
    for path in API_DIR.rglob("*.py"):
        names |= {
            n.name
            for n in ast.walk(ast.parse(path.read_text()))
            if isinstance(n, ast.AsyncFunctionDef)
        }
    assert {"upload_attachment", "healthz"} <= names


# ---------------------------------------------------------------------------
# Planted negative cases: the guard must fail on the PRB-009 shapes
# ---------------------------------------------------------------------------

PLANTED_REDIS = """
async def get_session(request, svc):
    return svc.resolve(request.cookies.get("c"))
"""
PLANTED_SQLALCHEMY = """
async def handler(db):
    return db.execute("select 1")
"""
PLANTED_REDIS_CLIENT = """
async def handler(r):
    r.setex("k", 1, "v")
"""
PLANTED_OBJECT_STORE = """
async def handler(storage):
    storage.put_object("k", b"x", 1, "text/plain")
"""


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (PLANTED_REDIS, "resolve"),
        (PLANTED_SQLALCHEMY, "execute"),
        (PLANTED_REDIS_CLIENT, "r.setex"),
        (PLANTED_OBJECT_STORE, "put_object"),
    ],
)
def test_planted_blocking_call_in_async_def_is_found(source: str, expected: str) -> None:
    found = blocking_calls_in_async(source)
    assert [name for _, _, name in found] == [expected]


def test_the_sanctioned_shapes_are_not_flagged() -> None:
    """A plain def, run_in_threadpool and an awaited call are the allowed ways."""
    allowed = """
def get_session(request, svc):
    return svc.resolve(request.cookies.get("c"))

async def upload(svc, actor, file):
    return await run_in_threadpool(svc.store, actor, file)

async def handler(queue):
    await queue.get_object()
    return {}.get("k")
"""
    assert blocking_calls_in_async(allowed) == []


# ---------------------------------------------------------------------------
# Runtime check: a slow call for one request does not delay unrelated ones
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slow_db_call_does_not_block_unrelated_request() -> None:
    """SR-026 AC 5: with the session lookup blocked for 2 s, a concurrent GET /healthz is < 200 ms.

    `get_session` calls `SessionService.resolve` (a Redis round trip). Patched to sleep, it stands
    for any slow dependency call. While `get_session` was `async def` the sleep ran on the event
    loop and `/healthz` waited the full 2 s (PRB-009); as a plain `def` it sleeps in a thread.
    """
    import asyncio  # noqa: PLC0415
    import time  # noqa: PLC0415
    from unittest.mock import MagicMock, patch  # noqa: PLC0415

    from httpx import ASGITransport, AsyncClient  # noqa: PLC0415

    from app.api.deps import get_redis  # noqa: PLC0415
    from app.db.repositories.session import get_db  # noqa: PLC0415
    from app.main import create_app  # noqa: PLC0415

    app = create_app()
    app.dependency_overrides[get_redis] = lambda: MagicMock()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    def slow_resolve(self: object, session_id: str) -> None:
        time.sleep(2)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", cookies={"medhub_session": "x"}
    ) as client:
        with patch("app.auth.session.SessionService.resolve", slow_resolve):
            begun = time.perf_counter()
            slow = asyncio.create_task(client.get("/api/v1/me"))
            await asyncio.sleep(0.3)  # the slow request is inside its blocking call
            # Latency is taken from the moment the request was due, not from when a blocked loop
            # got round to sending it: a loop stalled for 2 s still shows the full wait.
            due = begun + 0.3
            health = await client.get("/healthz")
            health_seconds = time.perf_counter() - due
            slow_response = await slow
    assert health.status_code == 200
    assert health_seconds < 0.2, f"/healthz waited {health_seconds:.2f} s behind a slow call"
    assert slow_response.status_code == 401  # the stub resolved no session
