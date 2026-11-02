"""Every application setting reaches the Python services that read it (TASK-191 round 2, R2-3).

TASK-191 replaced `env_file` with an explicit `environment:` list per service, so a setting added
to `Settings` but not to that list is silently missing in the container. Standard library only:
it reads `backend/app/core/config.py` and `secret_settings.py` as text and the Compose file as
text, so it needs neither the application's dependencies nor Docker.

- Every `Settings` field and every `SECRET_SETTINGS` name appears in the `environment:` of at
  least one Python service, or in EXCEPTIONS below with a reason.
- Every `Settings` field without a default appears in every Python service (each one builds
  `Settings` at start-up, so a missing required field stops it).
"""

import re
import unittest

from test_compose_object_store import ROOT
from test_compose_secrets import service_blocks

CONFIG = ROOT / "backend" / "app" / "core" / "config.py"
SECRET_SETTINGS_PY = ROOT / "backend" / "app" / "core" / "secret_settings.py"

# Services that run the backend image's Python code and so build `Settings`.
PYTHON_SERVICES = ("backend", "celery-worker", "celery-beat", "db-migrate")

# Services that read secrets without building `Settings` (they run the shared secret rule only).
SECRET_RULE_SERVICES = ("object-store-preflight",)

# Setting -> reason it is in no Python service's environment. An entry that is wired after all
# fails the test, so the list cannot go stale. Empty since TASK-196 wired OBJECT_STORE_SSE_KEY.
EXCEPTIONS: dict[str, str] = {}

_FIELD_LINE = re.compile(r"(?m)^    ([a-z_][a-z0-9_]*):[ \t]*(.*)$")


def settings_body() -> str:
    text = CONFIG.read_text()
    return text[text.index("class Settings(") : text.index("@functools.lru_cache")]


def split_default(rest: str) -> tuple[str, str | None]:
    """Split `annotation = default` at the first ` = ` outside brackets (`Field(alias=...)` is inside)."""
    depth = 0
    for i, ch in enumerate(rest):
        depth += ch in "[("
        depth -= ch in "])"
        if depth == 0 and rest[i : i + 3] == " = ":
            return rest[:i], rest[i + 3 :]
    return rest, None


def parse_settings_fields(body: str) -> dict[str, bool]:
    """Field name (as an environment variable) -> whether it has a default, from a class body.

    Every `    name:` line is accounted for. A field written with `alias`, `validation_alias` or
    `Field(...)` is refused, because this parser reads none of them (TASK-193 QA carry-over, R2-3):
    teach it before using the form.
    """
    fields = {}
    for name, rest in _FIELD_LINE.findall(body):
        annotation, default = split_default(rest)
        if annotation.startswith("ClassVar"):
            continue
        for form in ("alias", "Field("):
            if form in rest:
                raise AssertionError(
                    f"Settings.{name} uses {form!r}, which settings_fields() does not read"
                )
        fields[name.upper()] = default is not None
    return fields


def settings_fields() -> dict[str, bool]:
    return parse_settings_fields(settings_body())


def secret_setting_names() -> set[str]:
    text = SECRET_SETTINGS_PY.read_text()
    constants = dict(re.findall(r'(?m)^([A-Z_]+) = "([A-Z_]+)"', text))
    tuple_body = re.search(r"SECRET_SETTINGS = \(([^)]*)\)", text).group(1)
    return {constants[n] for n in re.findall(r"[A-Z_]+", tuple_body)}


def environment_names(service: str) -> set[str]:
    block = service_blocks()[service]
    env = re.search(r"(?m)^    environment:\n((?:      .*\n|\s*#.*\n|\n)+)", block)
    if not env:
        return set()
    return set(re.findall(r"(?m)^      ([A-Z][A-Z0-9_]*):", env.group(1)))


class SettingsReachTheServices(unittest.TestCase):
    def test_the_parser_accounts_for_every_field_line(self):
        """No `    name:` line of the class body is skipped silently (TASK-193 QA carry-over)."""
        body = settings_body()
        declared = {n.upper() for n, _ in _FIELD_LINE.findall(body)}
        class_vars = {n.upper() for n, r in _FIELD_LINE.findall(body) if r.startswith("ClassVar")}
        self.assertEqual(set(settings_fields()), declared - class_vars)

    def test_the_parser_reads_annotations_with_equals_and_refuses_forms_it_cannot_read(self):
        """Probe on synthetic class bodies (the gaps found in the TASK-193 review)."""
        body = "    a: int\n    b: int = 1\n    c: Annotated[list[str], NoDecode] = []\n"
        self.assertEqual(parse_settings_fields(body), {"A": False, "B": True, "C": True})
        for line in (
            "    a: Annotated[str, Field(alias='X')]",
            "    a: Annotated[str, Field(alias='X')] = 'y'",
            "    a: str = Field(...)",
            "    a: str = Field(default='x', validation_alias='Y')",
        ):
            with self.assertRaises(AssertionError, msg=line):
                parse_settings_fields(line + "\n")
        self.assertEqual(parse_settings_fields("    v: ClassVar[int] = 3\n"), {})

    def test_the_parsers_find_the_settings(self):
        """Guard against a silent parse failure: known fields must be seen."""
        fields = settings_fields()
        self.assertIs(fields["DATABASE_URL"], False)
        self.assertIs(fields["SMTP_PORT"], True)
        self.assertIn("DATABASE_OWNER_URL", secret_setting_names())
        self.assertGreater(len(environment_names("backend")), 5)

    def test_every_setting_is_in_some_python_service_or_excepted(self):
        wired = set().union(*(environment_names(s) for s in PYTHON_SERVICES + SECRET_RULE_SERVICES))
        wanted = set(settings_fields()) | secret_setting_names()
        missing = wanted - wired - set(EXCEPTIONS)
        self.assertEqual(missing, set(), f"in no Python service's environment: {sorted(missing)}")

    def test_no_exception_is_wired_already(self):
        wired = set().union(*(environment_names(s) for s in PYTHON_SERVICES + SECRET_RULE_SERVICES))
        stale = set(EXCEPTIONS) & wired
        self.assertEqual(stale, set(), f"remove from EXCEPTIONS: {sorted(stale)}")

    def test_every_setting_without_a_default_is_in_every_python_service(self):
        required = {name for name, has_default in settings_fields().items() if not has_default}
        for service in PYTHON_SERVICES:
            missing = required - environment_names(service)
            self.assertEqual(missing, set(), f"{service} lacks required setting(s) {sorted(missing)}")


if __name__ == "__main__":
    unittest.main()
