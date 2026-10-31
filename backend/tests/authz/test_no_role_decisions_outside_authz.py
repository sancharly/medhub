"""TC-002.8: no role use decides access outside ``app/authz/`` (SR-005 AC 1, AC 3).

An AST scan of ``app/`` and ``modules/``. A *role use* is, outside ``app/authz/``:

- a comparison (``==``, ``!=``, ``in``, ``not in``, ``is``) or ``match`` value with a role operand;
- a subscript keyed on a role, ``.get(role)``, or a method call on a role.

A *role operand* is ``.user_type`` or ``.role``, ``UserType.<member>``, a role-name string
(``"SYSADMIN"``), ``getattr(x, "user_type")``, a parameter annotated ``UserType`` or named
``role``/``actor_role``/``user_type``, and any name assigned (in the function, or at module level)
from such an expression, including ``.value``/``.name`` of one, so an alias cannot hide it.

Such a use is an access decision in disguise (ADR-0006, PRB-027), so it lives in ``app/authz/``.
The exceptions are not a file allow-list: each is one exact expression in one function, with its
reason. The test fails on a role use not listed (a new comparison inside an excepted function is a
different expression, so it fails too) and fails on a listed exception that no longer matches.
Reading ``.user_type`` to build a descriptor, a payload or a response is not a use and needs no
entry. Names are tracked within one function; a role passed through another function's return
value is not followed.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
SCAN_ROOTS = ("app", "modules")
AUTHZ_PREFIX = "app/authz/"

# (path relative to backend/, enclosing scope, expression) -> why it is not an access decision
ALLOWED: dict[tuple[str, str, str], str] = {
    (
        "app/appointments/service.py",
        "AppointmentService.create",
        "doctor.user_type != UserType.DOCTOR",
    ): "SR-010 data rule: the referenced doctor account must be a doctor",
    (
        "app/appointments/service.py",
        "AppointmentService.create",
        "patient.user_type != UserType.PATIENT",
    ): "SR-010 data rule: the referenced patient account must be a patient",
    (
        "app/auth/session.py",
        "SessionService._inactivity_ttl",
        "role in _CLINICAL_ROLES",
    ): "SR-030 inactivity timeout, not an access decision",
    (
        "app/api/routers/lifecycle.py",
        "delete_account",
        "target.user_type != body.confirm_account_type",
    ): "SR-034: the typed account type must match the target (confirmation input check)",
    (
        "app/identity/account_service.py",
        "AccountService.get_profile",
        "account.user_type == UserType.PATIENT",
    ): "builds the resource descriptor (patient_id) for account:read; authz decides",
    (
        "app/db/repositories/group_repo.py",
        "GroupRepository.list_auto_groups_for_type",
        "Group.auto_user_type == user_type",
    ): "query filter selecting the automatic groups of a type (membership data, SR-013)",
}


ROLE_NAMES = frozenset({"PATIENT", "DOCTOR", "ADMIN", "SYSADMIN"})
ROLE_ATTRS = frozenset({"user_type", "role"})
ROLE_PARAMS = frozenset({"role", "actor_role", "user_type"})


def _is_atom(node: ast.AST) -> bool:
    """A direct mention of a role: ``.user_type``, ``.role``, ``UserType.<x>``, a role name,
    ``getattr(x, "user_type")``."""
    if isinstance(node, ast.Attribute):
        if node.attr in ROLE_ATTRS:
            return True
        return isinstance(node.value, ast.Name) and node.value.id == "UserType"
    if isinstance(node, ast.Constant):
        return node.value in ROLE_NAMES
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr":
        return any(isinstance(a, ast.Constant) and a.value in ROLE_ATTRS for a in node.args[1:2])
    return False


def _has_role(node: ast.AST, tainted: set[str]) -> bool:
    """Use site: the expression mentions a role atom or a name derived from one anywhere."""
    return any(
        _is_atom(sub) or (isinstance(sub, ast.Name) and sub.id in tainted) for sub in ast.walk(node)
    )


def _is_role_expr(node: ast.AST, tainted: set[str]) -> bool:
    """Taint source: the expression *is* a role (or a collection of roles), not merely mentions
    one (``Account(user_type=...)`` and ``a.user_type == b`` are not roles)."""
    if _is_atom(node) and not isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Name):
        return node.id in tainted
    if isinstance(node, ast.Attribute):  # .value / .name of a role
        return _is_role_expr(node.value, tainted)
    if isinstance(node, ast.Subscript):
        return _is_role_expr(node.value, tainted) or _is_role_expr(node.slice, tainted)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return _is_role_expr(node.func.value, tainted)
    if isinstance(node, ast.IfExp):
        return _is_role_expr(node.body, tainted) or _is_role_expr(node.orelse, tainted)
    if isinstance(node, ast.BoolOp):
        return any(_is_role_expr(v, tainted) for v in node.values)
    if isinstance(node, (ast.Tuple, ast.Set, ast.List)):
        return any(_is_role_expr(e, tainted) for e in node.elts)
    return False


def _assigned_names(target: ast.AST) -> list[str]:
    """Plain names bound by a target; ``obj.attr = ...`` and ``obj[k] = ...`` bind none."""
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        return [n for e in target.elts for n in _assigned_names(e)]
    return []


def _tainted_names(body: ast.AST, tainted: set[str]) -> set[str]:
    """Names assigned from a role expression, to a fixed point (order-insensitive)."""
    tainted = set(tainted)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(body):
            pairs: list[tuple[ast.AST, ast.AST | None]] = []
            if isinstance(node, ast.Assign):
                pairs = [(t, node.value) for t in node.targets]
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
                pairs = [(node.target, node.value)]
            elif isinstance(node, (ast.For, ast.comprehension)):
                pairs = [(node.target, node.iter)]
            for target, value in pairs:
                if value is not None and _is_role_expr(value, tainted):
                    new = set(_assigned_names(target)) - tainted
                    if new:
                        tainted |= new
                        changed = True
    return tainted


def _role_params(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = fn.args
    every = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    for extra in (args.vararg, args.kwarg):
        if extra is not None:
            every.append(extra)
    return {
        a.arg
        for a in every
        if a.arg in ROLE_PARAMS
        or (a.annotation is not None and "UserType" in ast.unparse(a.annotation))
    }


class _Finder(ast.NodeVisitor):
    """Collect (scope, source) of every use of a role that can decide something.

    A use is: a comparison or ``match`` value with a role operand; a subscript keyed on a role
    or on a role-derived value; a ``.get(...)`` keyed on a role; a method call on a role.
    """

    def __init__(self, module_tainted: set[str]) -> None:
        self.scope: list[str] = []
        self.tainted: list[set[str]] = [module_tainted]
        self.found: list[tuple[str, str]] = []

    def _hit(self, node: ast.AST) -> None:
        self.found.append((".".join(self.scope), ast.unparse(node)))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        seed = self.tainted[-1] | _role_params(node)
        self.tainted.append(_tainted_names(node, seed))
        self.generic_visit(node)
        self.tainted.pop()
        self.scope.pop()

    visit_FunctionDef = _function
    visit_AsyncFunctionDef = _function

    def visit_Compare(self, node: ast.Compare) -> None:
        if _has_role(node, self.tainted[-1]):
            self._hit(node)
        self.generic_visit(node)

    def visit_MatchValue(self, node: ast.MatchValue) -> None:
        if _has_role(node.value, self.tainted[-1]):
            self._hit(node.value)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if _has_role(node.slice, self.tainted[-1]):
            self._hit(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute):
            if _is_role_expr(func.value, self.tainted[-1]):  # method call on a role
                self._hit(node)
            elif func.attr == "get" and any(_has_role(a, self.tainted[-1]) for a in node.args):
                self._hit(node)
        self.generic_visit(node)


def role_uses(root: Path, scan_roots: tuple[str, ...] = SCAN_ROOTS) -> set[tuple[str, str, str]]:
    """(relative path, enclosing scope, source) of every role use outside ``app/authz/``."""
    result: set[tuple[str, str, str]] = set()
    for scan in scan_roots:
        for path in sorted((root / scan).rglob("*.py")):
            rel = path.relative_to(root).as_posix()
            if rel.startswith(AUTHZ_PREFIX):
                continue
            tree = ast.parse(path.read_text(), filename=rel)
            module_tainted = _tainted_names(
                ast.Module(
                    body=[
                        n for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.ClassDef))
                    ],
                    type_ignores=[],
                ),
                set(),
            )
            finder = _Finder(module_tainted)
            finder.visit(tree)
            result.update((rel, scope, src) for scope, src in finder.found)
    return result


def test_no_role_use_decides_access_outside_authz() -> None:
    """SR-005 AC 1/AC 3: every role use outside app/authz/ is a listed non-decision."""
    offenders = role_uses(BACKEND) - set(ALLOWED)
    assert not offenders, (
        "role use outside app/authz/ (decide it in AuthorizationService, ADR-0006): "
        f"{sorted(offenders)}"
    )


def test_every_exception_still_matches_a_role_use() -> None:
    """An exception whose expression is gone must be removed, not left to excuse a new one."""
    stale = set(ALLOWED) - role_uses(BACKEND)
    assert not stale, f"stale exceptions: {sorted(stale)}"


# --- the rule itself (negative controls on synthetic files) ----------------------------------

OFFENDING = [
    "def f(actor):\n    if actor.user_type == UserType.ADMIN:\n        pass\n",
    "def f(actor):\n    if actor.user_type != UserType.SYSADMIN:\n        raise X\n",
    "def f(actor):\n    return actor.user_type in (UserType.ADMIN, UserType.SYSADMIN)\n",
    "def f(actor):\n    return actor.user_type not in {UserType.PATIENT}\n",
    "def f(role):\n    return role == UserType.DOCTOR\n",
    "def f(a):\n    return UserType.DOCTOR is a.role\n",
    "def f(a):\n    return a.user_type.value == 'ADMIN'\n",
    "def f(a):\n    return getattr(a, 'user_type') == other\n",
    "def f(a):\n    match a.x:\n        case UserType.ADMIN:\n            pass\n",
    "class C:\n    async def f(self, a):\n        return a.user_type == b\n",
    # the eight forms QA's probe found missed (TASK-189 round 1)
    "def f(actor):\n    t = actor.user_type\n    if t == 'ADMIN':\n        raise X\n",
    "def f(actor_role):\n    if actor_role != 'SYSADMIN':\n        raise X\n",
    "PERMS = {}\ndef f(actor):\n    if not PERMS[actor.user_type]:\n        raise X\n",
    "PERMS = {}\ndef f(actor):\n    if not PERMS.get(actor.user_type):\n        raise X\n",
    "S = {1}\ndef f(actor):\n    r = actor.user_type\n    return r in S\n",
    "def f(actor):\n    v = actor.user_type.value\n    return v == 'DOCTOR'\n",
    "def f(session):\n    return session.role == 'SYSADMIN'\n",
    "def f(actor):\n    return actor.user_type.name.startswith('SYS')\n",
    # further aliases
    "def f(a):\n    t = a.user_type\n    u = t\n    return u == 1\n",
    "def f(a):\n    (x, y) = (a.user_type, 1)\n    return x == 2\n",
    "def f(role: UserType):\n    return role in OTHER\n",
    "def f(who: UserType):\n    return who == 1\n",
    "ROLES = {UserType.DOCTOR}\ndef f(x):\n    return x in ROLES\n",
    "def f(a):\n    return (a.user_type if a else None) == 1\n",
]


def _scan(tmp_path: Path, source: str, name: str = "bad.py") -> set[tuple[str, str, str]]:
    (tmp_path / "app").mkdir(exist_ok=True)
    (tmp_path / "app" / name).write_text(source)
    return role_uses(tmp_path)


@pytest.mark.parametrize("source", OFFENDING)
def test_rule_catches_role_uses(tmp_path: Path, source: str) -> None:
    assert {rel for rel, _, _ in _scan(tmp_path, source)} == {"app/bad.py"}


PERMITTED = [
    "def f(a):\n    return {'type': a.user_type.value}\n",  # data, no comparison
    "def f(a):\n    return Resource(target_user_type=a.user_type)\n",  # descriptor
    "def f(a):\n    return a.status == 'ACTIVE'\n",  # not a role
    "def f(a):\n    x = UserType.ADMIN\n    return x\n",  # a member alone is not a comparison
    "def f(a):\n    acct = Account(user_type=UserType.DOCTOR)\n    return acct.id == a.id\n",
    "def f(a):\n    a.user_type = UserType.DOCTOR\n    return a.id == 1\n",
    "def f(a):\n    p = a.id if a.user_type else None\n    return p == 1\n",
]


@pytest.mark.parametrize("source", PERMITTED)
def test_rule_permits_descriptors_and_data(tmp_path: Path, source: str) -> None:
    assert _scan(tmp_path, source, "ok.py") == set()


def test_rule_ignores_the_authz_package_only(tmp_path: Path) -> None:
    (tmp_path / "app" / "authz").mkdir(parents=True)
    (tmp_path / "app" / "authz" / "x.py").write_text("a.user_type == UserType.ADMIN\n")
    (tmp_path / "app" / "authzx").mkdir()
    (tmp_path / "app" / "authzx" / "y.py").write_text("a.user_type == UserType.ADMIN\n")
    assert {rel for rel, _, _ in role_uses(tmp_path)} == {"app/authzx/y.py"}


def test_a_new_comparison_inside_an_excepted_function_is_not_excused(tmp_path: Path) -> None:
    """An exception covers one exact expression: adding another use beside it still fails."""
    (tmp_path / "app").mkdir()
    source = (
        "class SessionService:\n"
        "    def _inactivity_ttl(self, role):\n"
        "        if role in _CLINICAL_ROLES:\n"
        "            return 1\n"
        "        if role == UserType.ADMIN:\n"
        "            return 2\n"
    )
    (tmp_path / "app" / "session.py").write_text(source)
    excused = {("app/session.py", "SessionService._inactivity_ttl", "role in _CLINICAL_ROLES")}
    unexcused = role_uses(tmp_path) - excused
    assert unexcused == {
        ("app/session.py", "SessionService._inactivity_ttl", "role == UserType.ADMIN")
    }
