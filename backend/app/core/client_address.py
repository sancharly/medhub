"""Originating client address (SR-042 AC 1 to AC 3, ADR-0019, TASK-185).

One rule, applied once per request: the address is the TCP peer, unless the peer is a trusted
proxy; then it is the right-most ``X-Forwarded-For`` entry that is not itself a trusted proxy.
An empty ``TRUSTED_PROXIES`` setting trusts nothing. The server's own forwarded-header handling
is off (``--forwarded-allow-ips=`` in ``entrypoint.sh``), so the peer in the scope is always the
TCP peer.
"""

from __future__ import annotations

import functools
import ipaddress
from contextvars import ContextVar
from ipaddress import IPv4Network, IPv6Network

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

TrustedProxies = tuple[IPv4Network | IPv6Network, ...]

_current: ContextVar[str | None] = ContextVar("client_address", default=None)


def parse_trusted_proxies(value: str) -> TrustedProxies:
    """Parse a comma-separated list of IP addresses or CIDR blocks; empty means none."""
    networks: list[IPv4Network | IPv6Network] = []
    for raw in value.split(","):
        entry = raw.strip()
        if not entry:
            continue
        try:
            networks.append(ipaddress.ip_network(entry))
        except ValueError as exc:
            raise ValueError("invalid TRUSTED_PROXIES entry " + repr(entry)) from exc
    return tuple(networks)


def _parse_ip(text: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(text.strip())
    except ValueError:
        return None


def _is_trusted(ip: ipaddress.IPv4Address | ipaddress.IPv6Address, trusted: TrustedProxies) -> bool:
    return any(ip in network for network in trusted if ip.version == network.version)


def originating_address(peer: str | None, xff: str | None, trusted: TrustedProxies) -> str | None:
    """Apply the trusted-proxy rule; malformed ``X-Forwarded-For`` entries are skipped."""
    if peer is None:
        return None
    peer_ip = _parse_ip(peer)
    if peer_ip is None or not xff or not _is_trusted(peer_ip, trusted):
        return peer
    entries = [ip for ip in (_parse_ip(part) for part in xff.split(",")) if ip is not None]
    if not entries:
        return peer
    for ip in reversed(entries):
        if not _is_trusted(ip, trusted):
            return str(ip)
    return str(entries[0])


@functools.lru_cache
def _trusted_from_setting(value: str) -> TrustedProxies:
    return parse_trusted_proxies(value)


class ClientAddressMiddleware:
    """Pure ASGI middleware: publish the originating client address for the request."""

    def __init__(self, app: ASGIApp, trusted: TrustedProxies | None = None) -> None:
        self.app = app
        self._trusted = trusted

    def _trusted_proxies(self) -> TrustedProxies:
        if self._trusted is not None:
            return self._trusted
        from app.core.config import get_settings  # noqa: PLC0415

        return _trusted_from_setting(get_settings().trusted_proxies)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        peer = client[0] if client else None
        xff = ", ".join(
            value.decode("latin-1")
            for name, value in scope.get("headers", [])
            if name == b"x-forwarded-for"
        )
        address = originating_address(peer, xff or None, self._trusted_proxies())
        scope.setdefault("state", {})["client_address"] = address
        token = _current.set(address)
        try:
            await self.app(scope, receive, send)
        finally:
            _current.reset(token)


def current_client_address() -> str | None:
    """The address of the request being handled; ``None`` outside a request."""
    return _current.get()


def client_address(request: Request) -> str | None:
    """The originating client address of ``request`` (set by ``ClientAddressMiddleware``)."""
    return getattr(request.state, "client_address", None)
