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
        for name in ("object-store", "object-store-init"):
            dep = self.config["services"][name]["depends_on"]["object-store-preflight"]
            self.assertEqual(dep["condition"], "service_completed_successfully", name)

    def test_store_has_a_healthcheck_and_initialiser_waits_for_it(self):
        """PRB-039: the initialiser starts only once the store is healthy."""
        self.assertIn("healthcheck", self.config["services"]["object-store"])
        dep = self.config["services"]["object-store-init"]["depends_on"]["object-store"]
        self.assertEqual(dep["condition"], "service_healthy")

    def test_initialiser_runs_once_from_the_backend_image_with_the_store_keys(self):
        """TASK-175: boto3 module, no mc, keys via the same expressions as the store."""
        svc = self.config["services"]["object-store-init"]
        self.assertEqual(svc["entrypoint"], ["python", "-m", "app.core.object_store_init"])
        self.assertEqual(svc["restart"], "no")
        self.assertEqual(svc["build"]["context"], str(ROOT / "backend"))
        self.assertNotIn("env_file", svc)
        shell = {
            "OBJECT_STORE_ACCESS_KEY": "shell-override-access",
            "OBJECT_STORE_SECRET_KEY": "shell-override-secret-key-1",
        }
        result, config = compose_config(GOOD, shell)
        self.assertEqual(result.returncode, 0, result.stderr)
        init_env = config["services"]["object-store-init"]["environment"]
        store_env = config["services"]["object-store"]["environment"]
        self.assertEqual(init_env["OBJECT_STORE_ACCESS_KEY"], store_env["AWS_ACCESS_KEY_ID"])
        self.assertEqual(init_env["OBJECT_STORE_SECRET_KEY"], store_env["AWS_SECRET_ACCESS_KEY"])
        self.assertEqual(init_env["OBJECT_STORE_ACCESS_KEY"], shell["OBJECT_STORE_ACCESS_KEY"])

    def test_backend_and_initialiser_resolve_the_same_store_settings(self):
        """TASK-175 QA carry-over: a shell variable cannot split init and backend.

        `environment:` beats `env_file`, so the backend must take endpoint, bucket and keys from
        the same interpolation as the initialiser. GOOD's .env is not the backend's env_file, so
        a decoy in infra/.env must not win either.
        """
        shell = {
            "OBJECT_STORE_ENDPOINT": "http://decoy-store:1234",
            "OBJECT_STORE_BUCKET": "decoy-bucket",
            "OBJECT_STORE_ACCESS_KEY": "shell-override-access",
            "OBJECT_STORE_SECRET_KEY": "shell-override-secret-key-1",
        }
        result, config = compose_config(GOOD, shell)
        self.assertEqual(result.returncode, 0, result.stderr)
        init_env = config["services"]["object-store-init"]["environment"]
        backend_env = config["services"]["backend"]["environment"]
        for name, value in shell.items():
            self.assertEqual(init_env[name], value, f"init {name}")
            self.assertEqual(backend_env[name], value, f"backend {name}")
        # Without overrides both use the same defaults, pointing at the object-store service.
        _, defaults = compose_config(GOOD)
        for name in ("OBJECT_STORE_ENDPOINT", "OBJECT_STORE_BUCKET"):
            self.assertEqual(
                defaults["services"]["backend"]["environment"][name],
                defaults["services"]["object-store-init"]["environment"][name],
            )
        self.assertEqual(
            defaults["services"]["backend"]["environment"]["OBJECT_STORE_ENDPOINT"],
            "http://object-store:8333",
        )

    def test_object_store_is_pinned_internal_and_has_no_console_or_admin_option(self):
        """TASK-176: SR-040 AC 1, SR-028 AC-5, SR-022 (SSE key), TS-014 TC-014.5."""
        svc = self.config["services"]["object-store"]
        self.assertRegex(svc["image"], r"^chrislusf/seaweedfs:4\.51@sha256:[0-9a-f]{64}$")
        command = " ".join(svc["command"])
        for option in ("console", "admin", "webdav", "sftp", "9001"):
            self.assertNotIn(option, command.lower())
        for option in ("-ip.bind=127.0.0.1", "-s3.ip.bind=0.0.0.0", "-master.telemetry=false",
                       "-s3.port.iceberg=0", "-s3.port.lance=0"):
            self.assertIn(option, command)
        self.assertNotIn("ports", svc)
        self.assertEqual([str(p) for p in svc["expose"]], ["8333"])
        self.assertEqual(svc["environment"]["WEED_S3_SSE_KEY"], GOOD["AT_REST_ENCRYPTION_KEY"])
        self.assertIn("object_store_data", self.config["volumes"])
        # TASK-178: the MinIO volume is no longer declared here; the legacy file names it external.
        self.assertNotRegex(COMPOSE.read_text(), r"(?m)^  minio_data:")
        self.assertNotIn("minio", self.config["services"])
        mounts = [v["source"] for v in svc["volumes"]]
        self.assertEqual(mounts, ["object_store_data"])

    def test_object_store_network_is_internal_and_joined_only_by_backend_and_initialiser(self):
        """TASK-177: SR-040 AC 3, ADR-0015 D4, TS-014 TC-014.6."""
        nets = self.config["networks"]
        self.assertIs(nets["object-store"]["internal"], True)
        self.assertFalse(nets["medhub"].get("internal", False))
        members = {
            name: set(svc.get("networks", {}))
            for name, svc in self.config["services"].items()
            if "object-store" in svc.get("networks", {})
        }
        self.assertEqual(set(members), {"object-store", "object-store-init", "backend"})
        self.assertEqual(members["object-store"], {"object-store"})
        self.assertEqual(members["object-store-init"], {"object-store"})
        self.assertEqual(members["backend"], {"medhub", "object-store"})
        for name in ("reverse-proxy", "frontend", "postgres", "redis", "celery-worker"):
            self.assertEqual(set(self.config["services"][name]["networks"]), {"medhub"}, name)
        self.assertEqual(self.config["services"]["object-store-preflight"]["network_mode"], "none")
        self.assertNotIn("networks", self.config["services"]["object-store-preflight"])
        # No service but the proxy publishes a port.
        published = [n for n, s in self.config["services"].items() if s.get("ports")]
        self.assertEqual(published, ["reverse-proxy"])

    def test_ci_override_publishes_the_store_on_loopback_over_a_separate_network(self):
        """TASK-179: the CI-only file adds no image, one non-internal network and a loopback port."""
        override = ROOT / "infra" / "compose.ci-object-store.yml"
        self.assertNotRegex(override.read_text(), r"(?m)^\s*image:")
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("".join(f"{k}={v}\n" for k, v in GOOD.items()))
            result = subprocess.run(
                ["docker", "compose", "-f", str(COMPOSE), "-f", str(override),
                 "--env-file", str(env_file), "config", "--format", "json"],
                capture_output=True, text=True, cwd=tmp,
                env={k: v for k, v in os.environ.items() if k != "OBJECT_STORE_CI_PORT"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        merged = json.loads(result.stdout)
        store = merged["services"]["object-store"]
        self.assertEqual(set(store["networks"]), {"object-store", "ci-publish"})
        self.assertFalse(merged["networks"]["ci-publish"].get("internal", False))
        self.assertIs(merged["networks"]["object-store"]["internal"], True)
        self.assertEqual(
            [(p["host_ip"], int(p["published"]), int(p["target"])) for p in store["ports"]],
            [("127.0.0.1", 8333, 8333)],
        )
        # Nothing else changes: the other services publish what they did before.
        published = [n for n, s in merged["services"].items() if s.get("ports")]
        self.assertEqual(sorted(published), ["object-store", "reverse-proxy"])

    def test_backend_waits_for_a_successful_initialisation(self):
        """SR-040 AC 4: a failed initialisation keeps the backend down."""
        dep = self.config["services"]["backend"]["depends_on"]["object-store-init"]
        self.assertEqual(dep["condition"], "service_completed_successfully")

    def test_no_mc_image_or_createbuckets_service(self):
        self.assertNotIn("createbuckets", self.config["services"])
        for name, svc in self.config["services"].items():
            self.assertNotIn("minio/mc", svc.get("image", ""), name)

    def test_preflight_checks_the_values_the_store_receives(self):
        """A shell override must reach the preflight and the object store identically (QA round 1)."""
        shell = {
            "OBJECT_STORE_ACCESS_KEY": "shell-override-access",
            "OBJECT_STORE_SECRET_KEY": "shell-override-secret-key-1",
        }
        result, config = compose_config(GOOD, shell)
        self.assertEqual(result.returncode, 0, result.stderr)
        pre = config["services"]["object-store-preflight"]
        self.assertNotIn("env_file", pre)
        store_env = config["services"]["object-store"]["environment"]
        self.assertEqual(pre["environment"]["OBJECT_STORE_ACCESS_KEY"], store_env["AWS_ACCESS_KEY_ID"])
        self.assertEqual(pre["environment"]["OBJECT_STORE_SECRET_KEY"], store_env["AWS_SECRET_ACCESS_KEY"])
        self.assertEqual(store_env["AWS_ACCESS_KEY_ID"], shell["OBJECT_STORE_ACCESS_KEY"])

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
