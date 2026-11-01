"""No default for any secret setting in the Compose file (SR-041 AC 2, TS-015 TC-015.2, TASK-203).

Standard library only. The static checks read the raw Compose text (`docker compose config`
resolves the expressions, so it cannot show a `:-` default). The bring-up checks run
`docker compose config` with a throwaway env file and are skipped when `docker` is absent.
"""

import importlib.util
import re
import shutil
import unittest

from test_compose_object_store import COMPOSE, GOOD, ROOT, compose_config

_spec = importlib.util.spec_from_file_location(
    "secret_settings", ROOT / "backend" / "app" / "core" / "secret_settings.py"
)
secret_settings = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(secret_settings)

# The secret settings of backend/app/core/secret_settings.py plus the database image's password,
# which SR-041 names too. Compose passes some under other names to the object store.
SECRETS = set(secret_settings.SECRET_SETTINGS) | {"POSTGRES_PASSWORD"}
TARGETS = {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "WEED_S3_SSE_KEY"}
# Required wherever the application reads them from `environment:` (the rest of the list is
# optional or conditional and reaches the containers through env_file).
GUARDED = {
    "backend": set(secret_settings._REQUIRED),
    "celery-worker": set(secret_settings._REQUIRED),
    "postgres": {"POSTGRES_PASSWORD"},
}


# Optional secrets: passed through bare (`${NAME}`), no default and no guard; the application
# checks them only when set. SMTP_PASSWORD is required only with SMTP_USER, the retired keys only
# during a key rotation.
OPTIONAL_PASSTHROUGH = {"SMTP_PASSWORD", "AT_REST_ENCRYPTION_RETIRED_KEYS"}
# Required settings that are not secrets: guarded like one so Compose names the missing setting.
GUARDED_NOT_SECRET = {"AT_REST_ENCRYPTION_KEY_ID"}
PYTHON_SERVICES = ("backend", "celery-worker", "celery-beat", "db-migrate")


def service_blocks() -> dict[str, str]:
    text = COMPOSE.read_text()
    body = text[text.index("\nservices:\n") :]
    parts = re.split(r"(?m)^  ([a-z][a-z-]*):\n", body)
    return dict(zip(parts[1::2], parts[2::2]))


class StaticGuards(unittest.TestCase):
    def test_every_secret_expression_is_required_and_names_its_setting(self):
        """AC 2: `${NAME:?NAME must be set}` and never `${NAME:-x}` or `${NAME-x}`."""
        text = COMPOSE.read_text()
        for name in SECRETS | TARGETS:
            self.assertNotRegex(text, r"\$\{" + name + r":?-", f"{name} has a default")
        found = 0
        for m in re.finditer(r"\$\{([A-Z_]+)([^}]*)\}", text):
            if m.group(1) in SECRETS:
                if m.group(0) == "${" + m.group(1) + "}" and m.group(1) in OPTIONAL_PASSTHROUGH:
                    continue  # optional secret, see test_no_secret_is_set_to_a_literal
                found += 1
                self.assertRegex(
                    m.group(0), r"^\$\{(\w+):\?\1 must be set\}$", f"{m.group(1)} is not guarded"
                )
        self.assertGreater(found, 0)

    def test_no_secret_is_set_to_a_literal(self):
        """Every environment entry that carries a secret is an interpolation, not a value."""
        for service, block in service_blocks().items():
            for m in re.finditer(r"(?m)^\s+([A-Z_]+):[ \t]*(.*)$", block):
                if m.group(1) in SECRETS | TARGETS:
                    if m.group(1) in OPTIONAL_PASSTHROUGH:
                        # Optional or conditional secret: no default, no guard; the application
                        # refuses an empty SMTP_PASSWORD when a user is set.
                        self.assertEqual(m.group(2), "${" + m.group(1) + "}", service)
                        continue
                    self.assertRegex(m.group(2), r"^\$\{\w+:\?", f"{service} {m.group(1)}")

    def test_services_that_use_a_secret_guard_it_in_environment(self):
        """The application services guard each required secret, not only env_file."""
        blocks = service_blocks()
        for service, names in GUARDED.items():
            for name in names:
                self.assertRegex(
                    blocks[service],
                    rf"(?m)^      {name}: \$\{{{name}:\?{name} must be set\}}$",
                    f"{service} does not guard {name}",
                )

    def test_the_key_id_is_guarded_in_every_python_service(self):
        """SR-022 AC 6: the key id has no default; Compose stops, naming it (TASK-193)."""
        blocks = service_blocks()
        for name in GUARDED_NOT_SECRET:
            for service in PYTHON_SERVICES:
                self.assertRegex(
                    blocks[service],
                    rf"(?m)^      {name}: \$\{{{name}:\?{name} must be set\}}$",
                    f"{service} does not guard {name}",
                )
        self.assertNotRegex(COMPOSE.read_text(), r"\$\{AT_REST_ENCRYPTION_KEY_ID:?-")

    def test_the_secret_list_is_the_application_rule_list(self):
        """The test reads the list the application refuses at start-up, not a copy of it."""
        self.assertTrue(set(secret_settings._REQUIRED) <= set(secret_settings.SECRET_SETTINGS))
        self.assertTrue({"DATABASE_URL", "AT_REST_ENCRYPTION_KEY"} <= SECRETS)


@unittest.skipUnless(shutil.which("docker"), "docker is not installed")
class BringUpRefusal(unittest.TestCase):
    """Bring-up stops, naming the setting, when a secret is unset or empty (AC 2)."""

    @classmethod
    def setUpClass(cls):
        cls.env_existed = (ROOT / "infra" / ".env").exists()
        if not cls.env_existed:
            (ROOT / "infra" / ".env").write_text("")

    @classmethod
    def tearDownClass(cls):
        if not cls.env_existed:
            (ROOT / "infra" / ".env").unlink()

    def test_complete_environment_renders(self):
        result, config = compose_config(GOOD)
        self.assertEqual(result.returncode, 0, result.stderr)
        for service in PYTHON_SERVICES:
            env = config["services"][service]["environment"]
            self.assertEqual(env["AT_REST_ENCRYPTION_KEY_ID"], GOOD["AT_REST_ENCRYPTION_KEY_ID"], service)
            self.assertEqual(env["AT_REST_ENCRYPTION_RETIRED_KEYS"], "", service)
            self.assertEqual(env["DATABASE_URL"], GOOD["DATABASE_URL"], service)
            self.assertEqual(env["AT_REST_ENCRYPTION_KEY"], GOOD["AT_REST_ENCRYPTION_KEY"], service)
        self.assertEqual(
            config["services"]["postgres"]["environment"]["POSTGRES_PASSWORD"],
            GOOD["POSTGRES_PASSWORD"],
        )

    def test_unset_secret_is_refused_naming_it(self):
        for name in ("POSTGRES_PASSWORD", "DATABASE_URL", "DATABASE_OWNER_URL", "AT_REST_ENCRYPTION_KEY",
                     "AT_REST_ENCRYPTION_KEY_ID"):
            result, _ = compose_config({k: v for k, v in GOOD.items() if k != name})
            self.assertNotEqual(result.returncode, 0, name)
            self.assertIn(f"{name} must be set", result.stderr)

    def test_empty_secret_is_refused_naming_it(self):
        for name in ("POSTGRES_PASSWORD", "DATABASE_URL", "DATABASE_OWNER_URL", "AT_REST_ENCRYPTION_KEY",
                     "AT_REST_ENCRYPTION_KEY_ID"):
            result, _ = compose_config({**GOOD, name: ""})
            self.assertNotEqual(result.returncode, 0, name)
            self.assertIn(f"{name} must be set", result.stderr)

    def test_the_template_alone_is_refused(self):
        """AC 2 and AC 4 together: copying the template without filling it in does not start."""
        template = {
            m.group(1): m.group(2)
            for line in (ROOT / "infra" / ".env.example").read_text().splitlines()
            if (m := re.match(r"^([A-Z_][A-Z0-9_]*)=(.*)$", line))
        }
        result, _ = compose_config(template)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex(result.stderr, r"(POSTGRES_PASSWORD|DATABASE_OWNER_URL|DATABASE_URL|AT_REST_ENCRYPTION_KEY|AT_REST_ENCRYPTION_KEY_ID|OBJECT_STORE_\w+_KEY) must be set")


if __name__ == "__main__":
    unittest.main()
