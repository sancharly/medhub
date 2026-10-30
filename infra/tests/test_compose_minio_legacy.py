"""Legacy MinIO Compose file for the migration (TASK-178, CR-002 AC-11, SR-022).

Standard library only. Static checks plus `docker compose config` with throwaway values; the
config checks are skipped when `docker` is absent.
"""

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "infra" / "migration" / "compose.minio-legacy.yml"
MAIN = ROOT / "infra" / "docker-compose.yml"
PINNED = (
    "minio/minio:RELEASE.2025-09-07T16-13-09Z@sha256:"
    "14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e"
)
ENV = {
    "OBJECT_STORE_ACCESS_KEY": "a1b2c3d4e5f6a1b2c3d4e5f6",
    "OBJECT_STORE_SECRET_KEY": "Zx9Qw3Lm7Rt2Vb5Nk8Hy4Jd6Fg1Sa0Pc",
    "AT_REST_ENCRYPTION_KEY": "throwaway-at-rest-key-for-config-only",
    "OBJECT_STORE_NETWORK": "scratch_object-store",
    "DATABASE_NETWORK": "scratch_default",
    "LEGACY_MINIO_VOLUME": "scratch_minio_data",
    "MIGRATION_DATABASE_URL": "postgresql://u:p@postgres:5432/medhub",
}


class LegacyComposeStatic(unittest.TestCase):
    def test_image_is_the_soup_022_reference_and_the_pin_check_covers_the_file(self):
        self.assertIn(f"image: {PINNED}", LEGACY.read_text())
        result = subprocess.run(
            ["python3", str(ROOT / "infra" / "check_image_pins.py"), str(LEGACY)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pin_check_default_patterns_include_the_file_name(self):
        import fnmatch
        import importlib.util

        spec = importlib.util.spec_from_file_location("pins", ROOT / "infra" / "check_image_pins.py")
        pins = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pins)
        self.assertTrue(any(fnmatch.fnmatchcase(LEGACY.name, p) for p in pins.DEFAULT_PATTERNS))

    def test_main_compose_no_longer_declares_the_minio_volume(self):
        self.assertNotIn("minio_data", MAIN.read_text())


@unittest.skipUnless(shutil.which("docker"), "docker is not installed")
class LegacyComposeConfig(unittest.TestCase):
    def config(self):
        result = subprocess.run(
            ["docker", "compose", "-f", str(LEGACY), "--profile", "migrate", "config",
             "--format", "json"],
            capture_output=True, text=True, env={**os.environ, **ENV},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_store_is_isolated_and_volume_is_external(self):
        cfg = self.config()
        legacy = cfg["services"]["minio-legacy"]
        self.assertNotIn("ports", legacy)
        self.assertEqual(set(legacy["networks"]), {"legacy"})
        self.assertIs(cfg["networks"]["legacy"]["internal"], True)
        self.assertIs(cfg["volumes"]["minio_data"]["external"], True)
        self.assertEqual(cfg["volumes"]["minio_data"]["name"], ENV["LEGACY_MINIO_VOLUME"])
        self.assertEqual(legacy["pull_policy"], "never")
        self.assertEqual([v["source"] for v in legacy["volumes"]], ["minio_data"])
        self.assertIs(legacy["volumes"][0]["read_only"], True)

    def test_only_the_migration_container_shares_the_legacy_network(self):
        cfg = self.config()
        members = {n for n, s in cfg["services"].items() if "legacy" in s.get("networks", {})}
        self.assertEqual(members, {"minio-legacy", "migrate"})

    def test_volume_and_networks_are_required(self):
        for var in ("LEGACY_MINIO_VOLUME", "OBJECT_STORE_NETWORK", "DATABASE_NETWORK"):
            env = {k: v for k, v in ENV.items() if k != var}
            result = subprocess.run(
                ["docker", "compose", "-f", str(LEGACY), "config", "--format", "json"],
                capture_output=True, text=True,
                env={**{k: v for k, v in os.environ.items() if k != var}, **env},
            )
            self.assertNotEqual(result.returncode, 0, var)
            self.assertIn(f"{var} must", result.stderr)


if __name__ == "__main__":
    unittest.main()
