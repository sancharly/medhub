"""The CI job that starts the object store writes every variable Compose guards (TASK-203 round 2).

Compose interpolates the whole file, so a `:?` guard on a service the job does not start still
stops it. This reads the `NAME=` lines the "Generate throwaway credentials" step writes to
`infra/.env` and renders the Compose file with exactly those names and throwaway values, using
the same file arguments as the job. Skipped when `docker` is absent.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_compose_object_store import COMPOSE, GOOD, ROOT

WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
OVERRIDE = ROOT / "infra" / "compose.ci-object-store.yml"
STORE_SERVICES = {"object-store-preflight", "object-store", "object-store-init"}


def ci_env_names() -> list[str]:
    text = WORKFLOW.read_text()
    start = text.index("- name: Generate throwaway credentials")
    step = text[start : text.index("\n      - name:", start + 1)]
    return re.findall(r'echo "([A-Z][A-Z0-9_]*)=', step)


def render(names: list[str]):
    with tempfile.TemporaryDirectory() as tmp:
        env_file = Path(tmp) / ".env"
        env_file.write_text("".join(f"{n}={GOOD.get(n, 'throwaway-value')}\n" for n in names))
        env = {k: v for k, v in os.environ.items() if k not in GOOD}
        return subprocess.run(
            ["docker", "compose", "-p", "ci-env-check", "-f", str(COMPOSE), "-f", str(OVERRIDE),
             "--env-file", str(env_file), "config", "--format", "json"],
            capture_output=True, text=True, cwd=tmp, env=env,
        )


@unittest.skipUnless(shutil.which("docker"), "docker is not installed")
class CiObjectStoreJobEnvironment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env_existed = (ROOT / "infra" / ".env").exists()
        if not cls.env_existed:
            (ROOT / "infra" / ".env").write_text("")

    @classmethod
    def tearDownClass(cls):
        if not cls.env_existed:
            (ROOT / "infra" / ".env").unlink()

    def test_the_step_writes_the_secret_variables(self):
        names = ci_env_names()
        for required in ("POSTGRES_PASSWORD", "DATABASE_URL", "AT_REST_ENCRYPTION_KEY",
                         "OBJECT_STORE_ACCESS_KEY", "OBJECT_STORE_SECRET_KEY"):
            self.assertIn(required, names)

    def test_compose_renders_the_object_store_services_with_exactly_those_names(self):
        result = render(ci_env_names())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(STORE_SERVICES <= set(json.loads(result.stdout)["services"]))

    def test_a_missing_guarded_name_would_stop_the_job(self):
        """The check has teeth: without POSTGRES_PASSWORD the render fails naming it."""
        result = render([n for n in ci_env_names() if n != "POSTGRES_PASSWORD"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("POSTGRES_PASSWORD must be set", result.stderr)


if __name__ == "__main__":
    unittest.main()
