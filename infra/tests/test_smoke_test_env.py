"""The throwaway-value fill in infra/smoke-test.sh yields a Compose-valid environment (TASK-193 QA).

When there is no infra/.env, smoke-test.sh copies .env.example through an awk program that fills
the secret settings, then runs `docker compose config`. A required setting that the awk does not
fill stops Compose (exit 15), so a new required setting would break the script unnoticed. This
extracts that awk program from the script itself, runs it over the template, and renders the
Compose file with the result. Standard library only; skipped when `docker` or `awk` is absent.
"""

import re
import shutil
import subprocess
import unittest

from test_compose_object_store import ROOT, compose_config

SMOKE = ROOT / "infra" / "smoke-test.sh"
TEMPLATE = ROOT / "infra" / ".env.example"


def filled_template() -> dict:
    script = SMOKE.read_text()
    program = re.search(r"awk -F= '(.*?)' \"\$SCRIPT_DIR/\.env\.example\"", script, re.S).group(1)
    out = subprocess.run(["awk", "-F=", program, str(TEMPLATE)], capture_output=True, text=True,
                         check=True).stdout
    return {m.group(1): m.group(2) for ln in out.splitlines()
            if (m := re.match(r"^([A-Z_][A-Z0-9_]*)=(.*)$", ln))}


@unittest.skipUnless(shutil.which("docker") and shutil.which("awk"), "docker or awk is missing")
class SmokeTestThrowawayEnvironment(unittest.TestCase):
    def test_the_awk_fills_every_guarded_setting_so_compose_config_succeeds(self):
        env = filled_template()
        self.assertEqual(env["ENVIRONMENT"], "local")  # the rest of the template passes through
        result, config = compose_config(env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("backend", config["services"])

    def test_the_awk_extraction_finds_the_secret_fills(self):
        env = filled_template()
        self.assertTrue(env["AT_REST_ENCRYPTION_KEY_ID"].startswith("throwaway-"))

    def test_the_smoke_test_compares_bucket_objects_with_attachment_rows(self):
        """TASK-196 QA 3: a store on a wrong or empty volume must turn the smoke test red."""
        script = SMOKE.read_text()
        self.assertIn("SELECT count(*) FROM attachment", script)
        self.assertIn("the object store holds every attachment (SR-041 AC 6)", script)
        self.assertIn('[ "$OBJECTS" -ge "$ROWS" ]', script)


if __name__ == "__main__":
    unittest.main()
