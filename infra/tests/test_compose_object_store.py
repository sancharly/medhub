"""Compose wiring of the object-store credential preflight (SR-040 AC 2, TS-014 TC-014.1, TC-014.3).

Standard library only. Parses `docker compose config --format json` with a throwaway env file
and checks the static files for default credential strings. Skipped when `docker` is absent.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "infra" / "docker-compose.yml"
GOOD = {
    "OBJECT_STORE_ACCESS_KEY": "a1b2c3d4e5f6a1b2c3d4e5f6",
    "OBJECT_STORE_SECRET_KEY": "Zx9Qw3Lm7Rt2Vb5Nk8Hy4Jd6Fg1Sa0Pc",
    "POSTGRES_PASSWORD": "throwaway-postgres-password",
    "AT_REST_ENCRYPTION_KEY": "throwaway-at-rest-key-for-config-only",
}
DEFAULT_STRINGS = ("minioadmin", "changeme")


def compose_config(env: dict, shell: dict | None = None):
    """Run `docker compose config`; return (CompletedProcess, parsed JSON or None)."""
    with tempfile.TemporaryDirectory() as tmp:
        env_file = Path(tmp) / ".env"
        env_file.write_text("".join(f"{k}={v}\n" for k, v in env.items()))
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE), "--env-file", str(env_file),
             "config", "--format", "json"],
            capture_output=True, text=True, cwd=tmp,
            env={**os.environ, **(shell or {})},
        )
    return result, (json.loads(result.stdout) if result.returncode == 0 else None)


@unittest.skipUnless(shutil.which("docker"), "docker is not installed")
class ComposeWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # env_file: .env is resolved relative to infra/; config only needs it to exist.
        cls.env_existed = (ROOT / "infra" / ".env").exists()
        if not cls.env_existed:
            (ROOT / "infra" / ".env").write_text("")
        result, cls.config = compose_config(GOOD)
        if cls.config is None:
            raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        if not cls.env_existed:
            (ROOT / "infra" / ".env").unlink()

    def test_preflight_service_has_no_network_and_runs_once(self):
        svc = self.config["services"]["object-store-preflight"]
        self.assertEqual(svc["network_mode"], "none")
        self.assertEqual(svc["restart"], "no")
        self.assertEqual(svc["entrypoint"], ["python", "-m", "app.core.object_store_credentials"])

    def test_store_and_initialiser_wait_for_preflight(self):
        for name in ("minio", "createbuckets"):
            dep = self.config["services"][name]["depends_on"]["object-store-preflight"]
            self.assertEqual(dep["condition"], "service_completed_successfully", name)

    def test_preflight_checks_the_values_the_store_receives(self):
        """A shell override must reach the preflight and minio identically (QA round 1)."""
        shell = {
            "OBJECT_STORE_ACCESS_KEY": "shell-override-access",
            "OBJECT_STORE_SECRET_KEY": "shell-override-secret-key-1",
        }
        result, config = compose_config(GOOD, shell)
        self.assertEqual(result.returncode, 0, result.stderr)
        pre = config["services"]["object-store-preflight"]
        self.assertNotIn("env_file", pre)
        minio_env = config["services"]["minio"]["environment"]
        self.assertEqual(pre["environment"]["OBJECT_STORE_ACCESS_KEY"], minio_env["MINIO_ROOT_USER"])
        self.assertEqual(pre["environment"]["OBJECT_STORE_SECRET_KEY"], minio_env["MINIO_ROOT_PASSWORD"])
        self.assertEqual(minio_env["MINIO_ROOT_USER"], shell["OBJECT_STORE_ACCESS_KEY"])

    def test_unset_keys_are_refused_by_compose_itself(self):
        for var in ("OBJECT_STORE_ACCESS_KEY", "OBJECT_STORE_SECRET_KEY"):
            env = {k: v for k, v in GOOD.items() if k != var}
            result, _ = compose_config(env)
            self.assertNotEqual(result.returncode, 0, var)
            self.assertIn(f"{var} must be set", result.stderr)

    def test_empty_keys_are_refused_by_compose_itself(self):
        for var in ("OBJECT_STORE_ACCESS_KEY", "OBJECT_STORE_SECRET_KEY"):
            result, _ = compose_config({**GOOD, var: ""})
            self.assertNotEqual(result.returncode, 0, var)
            self.assertIn(f"{var} must be set", result.stderr)


class NoDefaultStrings(unittest.TestCase):
    def test_static_files_hold_no_default_object_store_credential(self):
        for rel in ("infra/docker-compose.yml", "infra/DEPLOY.md", ".github/workflows/ci.yml"):
            text = (ROOT / rel).read_text().lower()
            for s in DEFAULT_STRINGS:
                self.assertNotIn(s, text, f"{rel} contains {s}")

    def test_env_template_has_empty_object_store_keys(self):
        lines = (ROOT / "infra" / ".env.example").read_text().splitlines()
        self.assertIn("OBJECT_STORE_ACCESS_KEY=", lines)
        self.assertIn("OBJECT_STORE_SECRET_KEY=", lines)
        for line in lines:
            if line.startswith("OBJECT_STORE_") or line.startswith("#"):
                for s in DEFAULT_STRINGS:
                    self.assertNotIn(s, line.lower())


if __name__ == "__main__":
    unittest.main()
