"""Source-store Compose file for the SSE-key separation (TASK-196, SR-041 AC 5, ADR-0018).

Standard library only. Static checks plus `docker compose config` with throwaway values; the
config checks are skipped when `docker` is absent.
"""

import json
import os
import re
import shutil
import subprocess
import unittest

from test_compose_object_store import COMPOSE, ROOT

SOURCE = ROOT / "infra" / "migration" / "compose.sse-source.yml"
ENV = {
    "OBJECT_STORE_ACCESS_KEY": "a1b2c3d4e5f6a1b2c3d4e5f6",
    "OBJECT_STORE_SECRET_KEY": "Zx9Qw3Lm7Rt2Vb5Nk8Hy4Jd6Fg1Sa0Pc",
    "DATABASE_URL": "postgresql://medhub_app:throwaway@postgres:5432/medhub",
    "SOURCE_SSE_KEY": "throwaway-old-sse-key-for-config-only",
    "SOURCE_STORE_VOLUME": "scratch_object_store_data_src",
    "OBJECT_STORE_NETWORK": "scratch_object-store",
    "DATABASE_NETWORK": "scratch_medhub",
}


def image_of(path, service):
    text = path.read_text()
    text = text[text.index("\nservices:\n") :]
    block = re.split(rf"(?m)^  {service}:\n", text)[1]
    return re.search(r"(?m)^    image: (\S+)$", block).group(1)


class SourceComposeStatic(unittest.TestCase):
    def test_source_store_is_the_stacks_pinned_image(self):
        """The same SeaweedFS release as the target, or the copy would cross versions."""
        self.assertEqual(image_of(SOURCE, "object-store-source"), image_of(COMPOSE, "object-store"))

    def test_the_pin_check_covers_the_file(self):
        result = subprocess.run(
            ["python3", str(ROOT / "infra" / "check_image_pins.py"), str(SOURCE)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_old_key_is_required_and_never_defaulted_or_taken_from_the_stack_keys(self):
        text = SOURCE.read_text()
        self.assertIn("${SOURCE_SSE_KEY:?SOURCE_SSE_KEY must be", text)
        self.assertNotRegex(text, r"\$\{SOURCE_SSE_KEY:?-")
        self.assertNotIn("AT_REST", re.sub(r"(?m)^\s*#.*$", "", text))


@unittest.skipUnless(shutil.which("docker"), "docker is not installed")
class SourceComposeConfig(unittest.TestCase):
    def config(self, env=None, profile=True):
        cmd = ["docker", "compose", "-f", str(SOURCE)] + (["--profile", "migrate"] if profile else [])
        result = subprocess.run(
            cmd + ["config", "--format", "json"], capture_output=True, text=True,
            env={**{k: v for k, v in os.environ.items() if k not in ENV}, **(ENV if env is None else env)},
        )
        return result

    def test_source_is_isolated_and_its_volume_is_external(self):
        result = self.config()
        self.assertEqual(result.returncode, 0, result.stderr)
        cfg = json.loads(result.stdout)
        source = cfg["services"]["object-store-source"]
        self.assertNotIn("ports", source)
        self.assertEqual(set(source["networks"]), {"rekey"})
        self.assertIs(cfg["networks"]["rekey"]["internal"], True)
        self.assertIs(cfg["volumes"]["source_data"]["external"], True)
        self.assertEqual(cfg["volumes"]["source_data"]["name"], ENV["SOURCE_STORE_VOLUME"])
        self.assertEqual(source["environment"]["WEED_S3_SSE_KEY"], ENV["SOURCE_SSE_KEY"])
        members = {n for n, s in cfg["services"].items() if "rekey" in s.get("networks", {})}
        self.assertEqual(members, {"object-store-source", "migrate"})

    def test_the_migration_reads_the_source_and_writes_the_stacks_store(self):
        cfg = json.loads(self.config().stdout)
        env = cfg["services"]["migrate"]["environment"]
        self.assertEqual(env["SOURCE_ENDPOINT"], "http://object-store-source:8333")
        self.assertEqual(env["OBJECT_STORE_ENDPOINT"], "http://object-store:8333")
        self.assertEqual(cfg["services"]["migrate"]["entrypoint"],
                         ["python", "scripts/migrate_object_store.py"])
        # Neither key of the stack is handed to the migration container.
        self.assertFalse({"OBJECT_STORE_SSE_KEY", "AT_REST_ENCRYPTION_KEY", "SOURCE_SSE_KEY"} & set(env))

    def test_each_required_variable_is_refused_naming_it(self):
        for name in ("SOURCE_SSE_KEY", "SOURCE_STORE_VOLUME", "OBJECT_STORE_NETWORK",
                     "DATABASE_NETWORK", "DATABASE_URL", "OBJECT_STORE_ACCESS_KEY"):
            result = self.config({k: v for k, v in ENV.items() if k != name})
            self.assertNotEqual(result.returncode, 0, name)
            self.assertIn(name, result.stderr)


if __name__ == "__main__":
    unittest.main()
