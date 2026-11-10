"""Every DEPLOY.md command that runs db-migrate alone rebuilds it and returns its exit code (PRB-062).

`docker compose up db-migrate` reuses the image of the previous release, which has none of the new
migrations (exit 0, nothing migrated), and returns 0 even when the container exits 1. Both flags are
required on every such line. Standard library only.
"""

import re
import unittest

from test_compose_object_store import ROOT

DEPLOY = ROOT / "infra" / "DEPLOY.md"
COMMAND = re.compile(r"docker compose\b[^\n`]*\bup\b[^\n`]*\bdb-migrate\b[^\n`]*")


class DeployDbMigrateCommands(unittest.TestCase):
    def test_every_db_migrate_up_command_has_both_flags(self):
        commands = COMMAND.findall(DEPLOY.read_text())
        self.assertGreaterEqual(len(commands), 3, "the DEPLOY.md db-migrate commands were not found")
        for command in commands:
            with self.subTest(command=command.strip()):
                self.assertIn("--build", command)
                self.assertIn("--exit-code-from db-migrate", command)

    def test_the_stack_start_commands_are_not_matched_by_mistake(self):
        self.assertIsNone(COMMAND.search("docker compose -f infra/docker-compose.yml up -d --build"))


if __name__ == "__main__":
    unittest.main()
