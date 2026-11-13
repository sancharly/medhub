"""SR-013 AC 1 / AC 6, PRB-078, TASK-135: the reverse proxy lets a maximum-size attachment through.

nginx's default `client_max_body_size` is 1 MiB, which refuses every larger upload before it reaches
the application. Text-only checks (standard library only); a started proxy is exercised by hand,
see TASK-135.
"""

import json
import re
import unittest

from test_compose_object_store import ROOT
from test_compose_secrets import service_blocks
from test_proxy_access_log import PROXY, blocks

CONFIG = (ROOT / "backend" / "app" / "core" / "config.py").read_text()
UNITS = {"k": 1024, "m": 1024**2, "g": 1024**3, "": 1}


def attachment_max_bytes() -> int:
    m = re.search(r"(?m)^    attachment_max_bytes: int = (\d+)\s*$", CONFIG)
    assert m, "Settings.attachment_max_bytes has no integer default"
    return int(m.group(1))


def api_location() -> str:
    found = blocks(PROXY, r"location\s+/api/")
    assert len(found) == 1, "expected exactly one `location /api/` block"
    return found[0]


class ProxyBodyLimit(unittest.TestCase):
    def test_the_api_location_sets_a_body_limit_not_smaller_than_the_attachment_maximum(self):
        m = re.search(r"client_max_body_size\s+(\d+)([kKmMgG]?);", api_location())
        self.assertIsNotNone(m, "location /api/ has no client_max_body_size")
        limit = int(m.group(1)) * UNITS[m.group(2).lower()]
        self.assertGreaterEqual(limit, attachment_max_bytes())

    def test_a_413_is_answered_with_the_apis_problem_document(self):
        """SR-013 AC 6: nginx's own refusal has the API's status, type and media type."""
        self.assertRegex(api_location(), r"error_page\s+413\s+=400\s+@upload_too_large;")
        self.assertNotRegex(api_location(), r"proxy_intercept_errors\s+on")
        named = blocks(PROXY, r"location\s+@upload_too_large")
        self.assertEqual(len(named), 1)
        self.assertIn("internal;", named[0])
        self.assertIn("default_type application/problem+json;", named[0])
        m = re.search(r"return\s+400\s+'(\{.*\})';", named[0])
        self.assertIsNotNone(m, "the named location returns no JSON body")
        body = json.loads(m.group(1))
        self.assertEqual(body["status"], 400)
        self.assertEqual(body["type"], "https://medhub.example/errors/validation-error")
        self.assertEqual(body["title"], "Validation Error")
        self.assertNotIn("instance", body)
        self.assertNotRegex(m.group(1), r"\$|nginx|upstream|backend")

    def test_the_limit_is_not_unbounded(self):
        self.assertNotRegex(api_location(), r"client_max_body_size\s+0\s*;")

    def test_the_backend_service_defaults_to_the_maximum_the_proxy_is_sized_from(self):
        env = re.search(
            r"(?m)^      ATTACHMENT_MAX_BYTES: \$\{ATTACHMENT_MAX_BYTES:-(\d+)\}\s*$",
            service_blocks()["backend"],
        )
        self.assertIsNotNone(env, "backend service does not default ATTACHMENT_MAX_BYTES")
        self.assertEqual(int(env.group(1)), attachment_max_bytes())


if __name__ == "__main__":
    unittest.main()
