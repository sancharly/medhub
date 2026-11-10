"""PRB-070 / TASK-206: the e-mailed activation link and the SPA route cannot diverge.

Reads the link template in the Celery task and the route in the app; fails if either side changes
alone. Standard library only, text only.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMAIL_TASKS = ROOT / "backend" / "app" / "workers" / "email_tasks.py"
APP = ROOT / "frontend" / "src" / "app" / "App.tsx"


class ActivationLinkMatchesRoute(unittest.TestCase):
    def test_the_email_link_is_the_activation_path_form(self):
        source = EMAIL_TASKS.read_text()
        match = re.search(r'link = f"\{settings\.public_base_url\}(/[^{"]*)\{activation_token\}"', source)
        self.assertIsNotNone(match, "activation link template not found in email_tasks.py")
        self.assertEqual(match.group(1), "/activation/")
        self.assertNotIn("?token=", match.group(0))

    def test_the_app_serves_that_route(self):
        self.assertIn('<Route path="/activation/:token"', APP.read_text())


if __name__ == "__main__":
    unittest.main()
