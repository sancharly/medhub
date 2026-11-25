"""Module boundary: a module imports only the platform's published interfaces (SR-016 AC 3).

The source of every module is checked against an allow-list of *names* per platform module
(PRB-030, TASK-223); anything else fails with the file and line. Rules:

* ``from <module> import <name>`` is allowed only for a listed module and a listed name. A module
  that re-exports internals (``app.api.deps`` re-exports the database session and repositories) is
  therefore safe: only the listed names pass. ``from app import x`` and ``from app.api import deps``
  are not allowed; import the names from the module that defines them.
* Plain ``import app...`` is not allowed (it binds the root ``app``), nor is any ``app.<x>``
  attribute chain.
* Any string constant, or leading literal of an f-string, equal to ``app`` or starting with
  ``app.`` is not allowed, whatever call it feeds (``import_module``, ``__import__``, keyword
  arguments, conditional expressions).
* ``<module>/tests`` is not module source; a ``tests`` directory inside the shipped package is.

Limits: the check is static. It does not see a non-literal dynamic import
(``import_module(name)``), an aliased or indirect importer (``from importlib import import_module
as im`` is seen only through its string literal), ``sys.modules[...]``, or a string built at run
time. ``app.core.config`` is not on the list: a module reads settings through
``app.modules.module_settings`` (one accessor per setting; human decision of 2026-11-14).
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

MODULES_DIR = Path(__file__).parent.parent.parent / "modules"

# The platform interfaces a module may import (ADD-014), as names per defining module. Add to this
# list only with a design decision; a module that needs anything else gets it through
# ``PlatformServices``.
ALLOWED_PLATFORM_NAMES: dict[str, frozenset[str]] = {
    "app.modules.contract": frozenset({"AuditOutcome", "PlatformServices", "RouterRegistry"}),
    "app.api.deps": frozenset({"get_current_user", "get_platform_services"}),
    "app.api.errors": frozenset({"AuthorizationError", "ProblemDetail", "ValidationProblem"}),
    "app.audit.actions": frozenset({"AuditAction"}),
    "app.modules.module_settings": frozenset({"dicom_max_decoded_bytes", "dicom_max_stored_bytes"}),
    "app.modules.dicom_support": frozenset(
        {
            "read_transfer_syntax",
            "check_inflated_size",
            "InflatedSizeExceeded",
            "DeflateStreamError",
        }
    ),
}

# Names the contract re-exports on purpose; every other allowed name is defined in its module.
INTENDED_REEXPORTS = {("app.modules.contract", "AuditOutcome")}


def _module_sources(modules_dir: Path) -> list[Path]:
    """Module source files: ``<modules_dir>/<module>/**/*.py`` outside ``<module>/tests``."""
    return sorted(
        py_file
        for py_file in modules_dir.glob("*/**/*.py")
        if py_file.relative_to(modules_dir).parts[1] != "tests"
    )


def _attribute_root(node: ast.Attribute) -> ast.expr:
    value = node.value
    while isinstance(value, ast.Attribute):
        value = value.value
    return value


def _app_references(py_file: Path) -> list[tuple[int, str]]:
    """Return (line, text) of each reference to ``app`` that the allow-list does not permit."""
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(py_file.read_text(), filename=str(py_file))):
        if isinstance(node, ast.Import):
            found += [
                (node.lineno, alias.name)
                for alias in node.names
                if alias.name == "app" or alias.name.startswith("app.")
            ]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module == "app" or node.module.startswith("app."):
                allowed = ALLOWED_PLATFORM_NAMES.get(node.module, frozenset())
                found += [
                    (node.lineno, f"{node.module}.{alias.name}")
                    for alias in node.names
                    if alias.name not in allowed
                ]
        elif isinstance(node, ast.Attribute):
            root = _attribute_root(node)
            if isinstance(root, ast.Name) and root.id == "app":
                found.append((node.lineno, f"app.{node.attr}"))
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and (node.value == "app" or node.value.startswith("app."))
        ):
            found.append((node.lineno, node.value))
    return found


def _boundary_violations(modules_dir: Path) -> list[str]:
    return [
        f"{py_file.relative_to(modules_dir)}:{line}: {text}"
        for py_file in _module_sources(modules_dir)
        for line, text in sorted(set(_app_references(py_file)))
    ]


def test_modules_import_only_allowed_platform_interfaces() -> None:
    """SR-016 AC 3: nothing outside the allow-list is imported by module source."""
    assert _module_sources(MODULES_DIR), "no module source found: the check would pass vacuously"
    violations = _boundary_violations(MODULES_DIR)
    assert violations == [], "Modules import outside the platform allow-list:\n" + "\n".join(
        violations
    )


@pytest.mark.parametrize(
    ("module", "name"),
    [(module, name) for module, names in ALLOWED_PLATFORM_NAMES.items() for name in sorted(names)],
)
def test_allowed_name_is_defined_in_its_module(module: str, name: str) -> None:
    """An allowed name is defined where the list says, not re-exported from an internal."""
    obj = getattr(importlib.import_module(module), name)
    if (module, name) not in INTENDED_REEXPORTS:
        assert obj.__module__ == module


PLANTED_FORBIDDEN = {
    "from_module": ("from app.identity.service import IdentityService\n", "app.identity.service"),
    "from_object_storage": (
        "from app.core.object_storage import ObjectStorage\n",
        "app.core.object_storage.ObjectStorage",
    ),
    "from_root": ("from app import db\n", "app.db"),
    "from_package_submodule": ("from app.api import deps\n", "app.api.deps"),
    "from_package_contract": ("from app.modules import contract\n", "app.modules.contract"),
    "name_reexported_session": (
        "from app.api.deps import DbSession\n",
        "app.api.deps.DbSession",
    ),
    "name_reexported_model": ("from app.api.deps import Account\n", "app.api.deps.Account"),
    "name_reexported_repo": (
        "from app.api.deps import AccountRepository\n",
        "app.api.deps.AccountRepository",
    ),
    "name_reexported_redis": ("from app.api.deps import get_redis\n", "app.api.deps.get_redis"),
    "name_unlisted_in_config": (
        "from app.core.config import Settings\n",
        "app.core.config.Settings",
    ),
    "star_import": ("from app.api.deps import *\n", "app.api.deps.*"),
    "module_prefix_lookalike": (
        "from app.core.config_extra import x\n",
        "app.core.config_extra.x",
    ),
    "plain_import": ("import app.core.object_storage\n", "app.core.object_storage"),
    "plain_import_allowed_module": ("import app.api.errors\n", "app.api.errors"),
    "attribute_chain": (
        "import app\n\nx = app.db.models.account.Account\n",
        "app.db",
    ),
    "dynamic_positional": (
        "import importlib\n\nimportlib.import_module('app.identity.service')\n",
        "app.identity.service",
    ),
    "dynamic_keyword": (
        "import importlib\n\nimportlib.import_module(name='app.db')\n",
        "app.db",
    ),
    "dynamic_fstring": (
        "import importlib\n\nm = 'x'\nimportlib.import_module(f'app.db.{m}')\n",
        "app.db.",
    ),
    "dynamic_conditional": (
        "import importlib\n\nimportlib.import_module('app.db' if True else 'y')\n",
        "app.db",
    ),
    "dynamic_dunder_keyword": ("__import__(name='app.db')\n", "app.db"),
    "dynamic_allowed_module": (
        "import importlib\n\nimportlib.import_module('app.api.deps')\n",
        "app.api.deps",
    ),
}


@pytest.mark.parametrize(
    ("source", "expected"), list(PLANTED_FORBIDDEN.values()), ids=list(PLANTED_FORBIDDEN)
)
def test_boundary_check_catches_planted_import(source: str, expected: str, tmp_path: Path) -> None:
    """SR-016 AC 3: each forbidden form, planted in a module source file, fails the check."""
    package = tmp_path / "demo" / "demo"
    package.mkdir(parents=True)
    (package / "planted.py").write_text(source)
    violations = _boundary_violations(tmp_path)
    assert any(v.split(": ", 1)[1].startswith(expected) for v in violations), violations


def test_boundary_check_accepts_allowed_names_and_scopes_the_tests_exclusion(
    tmp_path: Path,
) -> None:
    """Allowed names pass; ``<module>/tests`` is skipped but a nested ``tests`` package is not."""
    package = tmp_path / "demo" / "demo"
    package.mkdir(parents=True)
    (package / "ok.py").write_text(
        "from app.api.deps import get_current_user, get_platform_services\n"
        "from app.api.errors import AuthorizationError, ProblemDetail, ValidationProblem\n"
        "from app.audit.actions import AuditAction\n"
        "from app.modules.module_settings import dicom_max_stored_bytes\n"
        "from app.modules.contract import AuditOutcome, PlatformServices\n"
        "from demo.other import thing\n"
    )
    assert _boundary_violations(tmp_path) == []

    top_tests = tmp_path / "demo" / "tests"
    top_tests.mkdir()
    (top_tests / "test_x.py").write_text("from app.db.models.account import Account\n")
    assert _boundary_violations(tmp_path) == []

    nested = package / "tests"
    nested.mkdir()
    (nested / "helper.py").write_text("from app.db.models.account import Account\n")
    assert _boundary_violations(tmp_path) == [
        "demo/demo/tests/helper.py:1: app.db.models.account.Account"
    ]
