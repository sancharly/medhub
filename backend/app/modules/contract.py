"""Module host contracts — Protocols for ModuleManifest, RouterRegistry, PlatformServices."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    pass


class RouterRegistry(Protocol):
    def mount(self, module_key: str, router: Any) -> None: ...


class PlatformServices(Protocol):
    authorization: Any
    clinical: Any
    attachments: Any
    audit: Any


class ModuleManifest(Protocol):
    module_key: str
    name: str
    version: str
    required_permissions: list[str]

    def register(self, registry: RouterRegistry, services: PlatformServices) -> None: ...
