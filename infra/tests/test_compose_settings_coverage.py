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

# Setting -> reason it is in no Python service's environment. An entry that is wired after all
# fails the test, so the list cannot go stale.
EXCEPTIONS = {
    "OBJECT_STORE_SSE_KEY": "optional secret the object store will read; TASK-196 wires it to "
    "WEED_S3_SSE_KEY and to the preflight, which is not a service that builds Settings",
}


def settings_fields() -> dict[str, bool]:
    """Field name (as an environment variable) -> whether it has a default, from the class body."""
    text = CONFIG.read_text()
    body = text[text.index("class Settings(") : text.index("@functools.lru_cache")]
    fields = {}
    for m in re.finditer(r"(?m)^    ([a-z][a-z0-9_]*): ([^=\n]+?)(?: = (.+))?$", body):
        name, annotation, default = m.groups()
        if annotation.startswith("ClassVar"):
            continue
        fields[name.upper()] = default is not None
    return fields


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
    def test_the_parsers_find_the_settings(self):
        """Guard against a silent parse failure: known fields must be seen."""
        fields = settings_fields()
        self.assertIs(fields["DATABASE_URL"], False)
        self.assertIs(fields["SMTP_PORT"], True)
        self.assertIn("DATABASE_OWNER_URL", secret_setting_names())
        self.assertGreater(len(environment_names("backend")), 5)

    def test_every_setting_is_in_some_python_service_or_excepted(self):
        wired = set().union(*(environment_names(s) for s in PYTHON_SERVICES))
        wanted = set(settings_fields()) | secret_setting_names()
        missing = wanted - wired - set(EXCEPTIONS)
        self.assertEqual(missing, set(), f"in no Python service's environment: {sorted(missing)}")

    def test_no_exception_is_wired_already(self):
        wired = set().union(*(environment_names(s) for s in PYTHON_SERVICES))
        stale = set(EXCEPTIONS) & wired
        self.assertEqual(stale, set(), f"remove from EXCEPTIONS: {sorted(stale)}")

    def test_every_setting_without_a_default_is_in_every_python_service(self):
        required = {name for name, has_default in settings_fields().items() if not has_default}
        for service in PYTHON_SERVICES:
            missing = required - environment_names(service)
            self.assertEqual(missing, set(), f"{service} lacks required setting(s) {sorted(missing)}")


if __name__ == "__main__":
    unittest.main()
