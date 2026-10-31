"""ClientAddressMiddleware and the single-read rule (SR-042 AC 1 to AC 3, TS-016 TC-016.2)."""

import re
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request
from pydantic import ValidationError

from app.core.client_address import (
    ClientAddressMiddleware,
    client_address,
    current_client_address,
    parse_trusted_proxies,
)
from app.core.config import Settings

PROXY = parse_trusted_proxies("10.0.0.2")


def _app(trusted) -> FastAPI:
    app = FastAPI()
    app.add_middleware(ClientAddressMiddleware, trusted=trusted)

    @app.get("/who")
    async def who(request: Request) -> dict[str, str | None]:
        return {"state": client_address(request), "var": current_client_address()}

    return app


async def _get(app: FastAPI, peer: str, headers: dict[str, str] | None = None) -> dict:
    transport = httpx.ASGITransport(app=app, client=(peer, 5000))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        return (await c.get("/who", headers=headers)).json()


async def test_value_reaches_request_state_and_context_var() -> None:
    body = await _get(_app(PROXY), "10.0.0.2", {"X-Forwarded-For": "203.0.113.7"})
    assert body == {"state": "203.0.113.7", "var": "203.0.113.7"}


async def test_forged_header_from_untrusted_peer_is_ignored() -> None:  # SR-042 AC 2
    body = await _get(_app(PROXY), "198.51.100.9", {"X-Forwarded-For": "1.2.3.4"})
    assert body == {"state": "198.51.100.9", "var": "198.51.100.9"}


async def test_empty_setting_ignores_the_header_from_every_peer() -> None:  # SR-042 AC 3
    body = await _get(_app(()), "10.0.0.2", {"X-Forwarded-For": "203.0.113.7"})
    assert body["state"] == "10.0.0.2"


async def test_repeated_headers_are_combined_right_most_wins() -> None:
    app = _app(PROXY)
    transport = httpx.ASGITransport(app=app, client=("10.0.0.2", 5000))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get(
            "/who", headers=[("X-Forwarded-For", "1.2.3.4"), ("X-Forwarded-For", "203.0.113.7")]
        )
    assert r.json()["state"] == "203.0.113.7"


async def test_context_var_is_reset_after_the_request() -> None:
    await _get(_app(PROXY), "10.0.0.2", {"X-Forwarded-For": "203.0.113.7"})
    assert current_client_address() is None


async def test_context_var_is_reset_when_the_application_raises() -> None:
    app = FastAPI()
    app.add_middleware(ClientAddressMiddleware, trusted=PROXY)

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("boom")

    transport = httpx.ASGITransport(app=app, client=("10.0.0.2", 5000), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        assert (await c.get("/boom")).status_code == 500
    assert current_client_address() is None


async def test_setting_is_read_when_no_explicit_value_is_given(monkeypatch) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.2")
    get_settings.cache_clear()
    body = await _get(_app(None), "10.0.0.2", {"X-Forwarded-For": "203.0.113.7"})
    assert body["state"] == "203.0.113.7"
    get_settings.cache_clear()


def test_invalid_setting_refuses_start_up(monkeypatch) -> None:
    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.2, nope")
    with pytest.raises(ValidationError, match="nope"):
        Settings()


# --- static check: nothing reads the raw TCP peer outside client_address.py ---------------------

# Every form of reading the peer: request.client.host, scope["client"], request.client[0],
# scope.get("client"), and any ``.client`` attribute chain ending in ``.host``.
_PEER_READS = re.compile(
    r"""\.client\b(?!\s*\()      # request.client / self.client (not boto3.client(...))
      | \[\s*['"]client['"]\s*\]  # scope["client"]
      | \.get\(\s*['"]client['"]   # scope.get("client")
    """,
    re.VERBOSE,
)
KNOWN_READS: set[str] = set()


def _peer_read_offenders(app_dir: Path) -> set[str]:
    return {
        str(path.relative_to(app_dir))
        for path in app_dir.rglob("*.py")
        if path.name != "client_address.py" and _PEER_READS.search(path.read_text())
    }


def test_no_code_reads_the_tcp_peer_outside_client_address() -> None:
    app_dir = Path(__file__).resolve().parents[2] / "app"
    offenders = _peer_read_offenders(app_dir)
    assert offenders <= KNOWN_READS, f"new read of the TCP peer: {offenders - KNOWN_READS}"


@pytest.mark.parametrize(
    "line",
    [
        "ip = request.client.host",
        "ip = self.request.client.host",
        'peer = scope["client"]',
        "peer = scope['client'][0]",
        "peer = request.client[0]",
        'peer = scope.get("client")',
        "addr, _ = request.client",
    ],
)
def test_static_check_catches_every_form_of_peer_read(tmp_path: Path, line: str) -> None:
    (tmp_path / "bad.py").write_text(line + "\n")
    assert _peer_read_offenders(tmp_path) == {"bad.py"}


def test_static_check_ignores_client_factories(tmp_path: Path) -> None:
    (tmp_path / "ok.py").write_text('c = boto3.client("s3")\nself._client = other\n')
    assert _peer_read_offenders(tmp_path) == set()
