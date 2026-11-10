"""Compose wiring of the migration service and the runtime role (TASK-191, TS-009 TC-009.11,
TS-015 TC-015.2; SR-023 AC 8, SR-041 AC 2; PRB-061).

Standard library only. Static checks read the Compose file, the Dockerfile and the entrypoint;
the rendered checks run `docker compose config` with a throwaway env file and are skipped when
`docker` is absent.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from test_compose_object_store import COMPOSE, GOOD, ROOT, compose_config
from test_compose_secrets import service_blocks

ENTRYPOINT = ROOT / "backend" / "entrypoint.sh"
DOCKERFILE = ROOT / "backend" / "Dockerfile"
APP_SERVICES = ("backend", "celery-worker", "celery-beat")


def code(block: str) -> str:
    """The block without comment lines."""
    return "\n".join(ln for ln in block.splitlines() if not ln.lstrip().startswith("#"))


def config_with_dotenv(env: dict) -> dict:
    """Render a copy of the Compose file whose project `.env` holds `env`, so that any `env_file`
    or `.env` interpolation would show. Never touches the real infra/.env."""
    with tempfile.TemporaryDirectory() as tmp:
        infra = Path(tmp) / "infra"
        infra.mkdir()
        shutil.copy(COMPOSE, infra / "docker-compose.yml")
        (infra / ".env").write_text("".join(f"{k}={v}\n" for k, v in env.items()))
        result = subprocess.run(
            ["docker", "compose", "-f", str(infra / "docker-compose.yml"), "config", "--format", "json"],
            capture_output=True, text=True, cwd=infra,
            env={k: v for k, v in os.environ.items() if k not in GOOD},
        )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)["services"]


def command_text(service: dict) -> str:
    parts = []
    for key in ("entrypoint", "command"):
        value = service.get(key) or []
        parts += [value] if isinstance(value, str) else value
    return " ".join(parts)


class StaticWiring(unittest.TestCase):
    def test_owner_url_is_guarded_in_db_migrate_only(self):
        blocks = service_blocks()
        guarded = r"DATABASE_OWNER_URL: \$\{DATABASE_OWNER_URL:\?DATABASE_OWNER_URL must be set\}"
        self.assertRegex(blocks["db-migrate"], guarded)
        for name, block in blocks.items():
            if name != "db-migrate":
                self.assertNotIn("DATABASE_OWNER_URL", code(block), f"{name} mentions the owner URL")
        self.assertNotRegex(COMPOSE.read_text(), r"DATABASE_OWNER_URL:?-")

    def test_no_service_reads_env_file(self):
        """env_file would pass every line of infra/.env, owner credentials included (round 2)."""
        text = COMPOSE.read_text()
        self.assertNotRegex(text, r"(?m)^\s+env_file:")
        self.assertNotIn("POSTGRES_PASSWORD", "".join(
            code(block) for name, block in service_blocks().items() if name != "postgres"))

    def test_the_entrypoint_does_not_migrate_and_ends_with_exec(self):
        lines = [ln for ln in ENTRYPOINT.read_text().splitlines() if not ln.lstrip().startswith("#")]
        self.assertNotIn("alembic", "\n".join(lines))
        self.assertEqual(lines[-1], 'exec "$@"')

    def test_gunicorn_is_the_image_default_command(self):
        text = DOCKERFILE.read_text()
        self.assertRegex(text, r'(?m)^CMD \["gunicorn", .*"--forwarded-allow-ips=", "app.main:app"\]$')
        self.assertRegex(text, r'(?m)^ENTRYPOINT \["\./entrypoint\.sh"\]$')

    def test_env_template_holds_both_urls_empty(self):
        template = (ROOT / "infra" / ".env.example").read_text()
        for name in ("DATABASE_OWNER_URL", "DATABASE_URL"):
            self.assertRegex(template, rf"(?m)^{name}=$")
        self.assertIn("medhub_app", template)


@unittest.skipUnless(shutil.which("docker"), "docker is not installed")
class RenderedWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env_existed = (ROOT / "infra" / ".env").exists()
        if not cls.env_existed:
            (ROOT / "infra" / ".env").write_text("")
        result, cls.config = compose_config(GOOD)
        if cls.config is None:
            raise AssertionError(result.stderr)
        cls.services = cls.config["services"]

    @classmethod
    def tearDownClass(cls):
        if not cls.env_existed:
            (ROOT / "infra" / ".env").unlink()

    def test_db_migrate_is_a_one_shot_service_that_checks_then_migrates_then_grants(self):
        svc = self.services["db-migrate"]
        self.assertEqual(svc["restart"], "no")
        self.assertEqual(list(svc["networks"]), ["medhub"])
        text = command_text(svc)
        steps = (
            "enforce()",
            "alembic upgrade head",
            "app.db.roles",
            "app.db.reencrypt --verify-key-ids",
        )
        positions = [text.find(x) for x in steps]
        self.assertTrue(all(p >= 0 for p in positions), text)
        self.assertEqual(positions, sorted(positions), text)
        self.assertEqual(svc["environment"]["DATABASE_OWNER_URL"], GOOD["DATABASE_OWNER_URL"])
        self.assertEqual(svc["depends_on"]["postgres"]["condition"], "service_healthy")
        self.assertIn("healthcheck", self.services["postgres"])

    def test_application_services_wait_for_a_successful_migration(self):
        for name in APP_SERVICES:
            dep = self.services[name]["depends_on"]["db-migrate"]
            self.assertEqual(dep["condition"], "service_completed_successfully", name)

    def test_no_owner_credential_value_reaches_a_service_but_postgres_and_db_migrate(self):
        """Value-based (round 2): the owner password and URL appear in no other service's
        environment, command or entrypoint. `compose config` renders interpolation and env_file."""
        owner_url = GOOD["DATABASE_OWNER_URL"]
        owner_password = urlsplit(owner_url).password
        self.assertNotEqual(owner_password, urlsplit(GOOD["DATABASE_URL"]).password)
        # The same values are in the project .env, which an env_file would pass on whole.
        services = config_with_dotenv({**GOOD, "SMTP_PASSWORD": "throwaway-smtp-password"})
        for name, svc in services.items():
            if name in ("postgres", "db-migrate"):
                continue
            rendered = json.dumps(svc)
            self.assertNotIn(owner_password, rendered, f"{name} holds the owner password")
            self.assertNotIn(owner_url, rendered, f"{name} holds the owner URL")
        self.assertIn(owner_password, json.dumps(services["postgres"]))
        self.assertIn(owner_password, json.dumps(services["db-migrate"]))

    def test_each_application_service_gets_only_the_settings_it_reads(self):
        names = {n: set(self.services[n]["environment"]) for n in APP_SERVICES}
        common = {"DATABASE_URL", "AT_REST_ENCRYPTION_KEY", "ENVIRONMENT", "REDIS_URL", "SMTP_HOST",
                  "OBJECT_STORE_ENDPOINT", "OBJECT_STORE_ACCESS_KEY", "OBJECT_STORE_SECRET_KEY",
                  "OBJECT_STORE_BUCKET"}
        for n in APP_SERVICES:
            self.assertTrue(common <= names[n], n)
            self.assertFalse({"POSTGRES_PASSWORD", "POSTGRES_USER", "DATABASE_OWNER_URL"} & names[n], n)
        self.assertNotIn("SMTP_PASSWORD", names["backend"])  # the API sends no mail
        self.assertNotIn("SMTP_PASSWORD", names["celery-beat"])
        self.assertIn("SMTP_PASSWORD", names["celery-worker"])  # the worker sends it

    def test_application_services_connect_as_the_runtime_role(self):
        for name in APP_SERVICES:
            url = self.services[name]["environment"]["DATABASE_URL"]
            self.assertEqual(url, GOOD["DATABASE_URL"], name)
            self.assertNotEqual(url, GOOD["DATABASE_OWNER_URL"], name)
        self.assertTrue(GOOD["DATABASE_URL"].startswith("postgresql://medhub_app:"))

    def test_no_service_but_db_migrate_runs_alembic(self):
        for name, svc in self.services.items():
            if name != "db-migrate":
                self.assertNotIn("alembic", command_text(svc), name)

    def test_worker_and_beat_run_celery(self):
        worker = command_text(self.services["celery-worker"])
        self.assertRegex(worker, r"celery -A app\.workers\.celery_app worker")
        beat = command_text(self.services["celery-beat"])
        self.assertRegex(beat, r"celery -A app\.workers\.celery_app beat")
        self.assertIn("--schedule=/tmp/", beat)
        self.assertEqual(self.services["celery-beat"]["restart"], "unless-stopped")

    def test_the_backend_has_no_command_so_the_image_cmd_applies(self):
        self.assertFalse(self.services["backend"].get("command"))
        self.assertFalse(self.services["backend"].get("entrypoint"))

    def test_owner_url_unset_or_empty_is_refused_naming_it(self):
        for env in ({k: v for k, v in GOOD.items() if k != "DATABASE_OWNER_URL"},
                    {**GOOD, "DATABASE_OWNER_URL": ""}):
            result, _ = compose_config(env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("DATABASE_OWNER_URL must be set", result.stderr)

    def test_an_owner_url_in_the_shell_does_not_reach_the_backend(self):
        result, config = compose_config(GOOD, shell={"DATABASE_OWNER_URL": "postgresql://x:y@h/d"})
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in APP_SERVICES:
            self.assertNotIn("DATABASE_OWNER_URL", config["services"][name]["environment"])

    def test_postgres_healthcheck_uses_tcp(self):
        """The socket check answers during the image's first-start init server (round 2)."""
        test = " ".join(self.services["postgres"]["healthcheck"]["test"])
        self.assertIn("pg_isready -h 127.0.0.1", test)

if __name__ == "__main__":
    unittest.main()
