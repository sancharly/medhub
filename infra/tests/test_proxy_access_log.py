"""SR-043 AC 4 / TASK-206 (PRB-068): no credential reaches a proxy or container log.

Text-only checks of the two nginx files, the backend Dockerfile and the Compose files. The started
stack is exercised by infra/log-secrets-check.sh. Standard library only.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROXY = (ROOT / "infra" / "reverse-proxy" / "nginx.conf").read_text()
FRONTEND = (ROOT / "frontend" / "nginx.conf").read_text()
DOCKERFILE = (ROOT / "backend" / "Dockerfile").read_text()
COMPOSE_FILES = sorted((ROOT / "infra").glob("*compose*.yml")) + sorted((ROOT / "infra").glob("docker-compose*.yml"))

FORBIDDEN_IN_FORMAT = (
    "$request ", "$request\"", "$request'", "$request_uri", "$args", "$query_string", "$arg_",
    "$http_", "$cookie_", "$sent_http_", "$upstream_http_", "$upstream_cookie_",
)


def blocks(text, header_pattern):
    """Bodies of the brace blocks whose header matches ``header_pattern``."""
    found = []
    for m in re.finditer(header_pattern + r"\s*\{", text):
        depth, i = 1, m.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        found.append(text[m.end():i - 1])
    return found


def log_format_body():
    m = re.search(r"log_format\s+medhub_redacted\s+(.*?);", PROXY, re.S)
    assert m, "log_format medhub_redacted is missing"
    return m.group(1)


class ProxyAccessLog(unittest.TestCase):
    def test_every_access_log_names_the_redacted_format_and_both_servers_have_one(self):
        servers = blocks(PROXY, r"(?m)^server")
        self.assertEqual(len(servers), 2)
        for server in servers:
            self.assertRegex(server, r"access_log\s+\S+\s+medhub_redacted;")
        for line in re.findall(r"access_log[^;]*;", PROXY):
            self.assertIn("medhub_redacted", line)

    def test_the_format_logs_no_request_line_query_or_header_variable(self):
        body = log_format_body()
        for forbidden in FORBIDDEN_IN_FORMAT:
            self.assertNotIn(forbidden, body + " ", forbidden)
        self.assertIsNone(re.search(r"\$request\b(?!_(method|time))", body))
        self.assertIn("escape=json", PROXY)

    def test_the_format_is_an_allow_list(self):
        variables = set(re.findall(r"\$\w+", log_format_body()))
        self.assertEqual(variables, {
            "$time_iso8601", "$remote_addr", "$request_method", "$medhub_log_path",
            "$server_protocol", "$status", "$body_bytes_sent", "$request_time", "$upstream_status",
        })

    def test_the_map_redacts_the_activation_paths(self):
        m = re.search(r"map\s+\$uri\s+\$medhub_log_path\s*\{(.*?)\}", PROXY, re.S)
        self.assertIsNotNone(m)
        self.assertRegex(m.group(1), r"~\*\^/api/v1/activation/\s+/api/v1/activation/\[redacted\]")
        self.assertRegex(m.group(1), r"~\*\^/activation/\s+/activation/\[redacted\]")
        self.assertRegex(m.group(1), r"default\s+\$uri")

    def test_activation_matching_ignores_case(self):
        """TASK-207: React Router matches without case, so /Activation/<token> is a working URL.
        No activation pattern, in the map or a location, may be case-sensitive."""
        patterns = re.findall(r"^\s*(~\*?)\s*\^/(?:api/v1/)?activat\S*", PROXY, re.M)
        patterns += re.findall(r"location\s+(~\*?)\s+\^/(?:api/v1/)?activat", PROXY)
        self.assertEqual(len(patterns), 4)
        self.assertEqual(set(patterns), {"~*"})

    def test_both_activation_locations_set_the_error_log_to_crit(self):
        for pattern in (r"location\s+~\*\s+\^/api/v1/activation/", r"location\s+~\*\s+\^/activat"):
            found = blocks(PROXY, pattern)
            self.assertEqual(len(found), 1, pattern)
            self.assertRegex(found[0], r"error_log\s+/var/log/nginx/error\.log\s+crit;")

    def test_the_activation_page_sends_no_referer_and_keeps_the_security_headers(self):
        (page,) = blocks(PROXY, r"location\s+~\*\s+\^/activat")
        self.assertIn('add_header Referrer-Policy "no-referrer" always;', page)
        for header in ("Strict-Transport-Security", "X-Content-Type-Options", "X-Frame-Options"):
            self.assertRegex(page, rf"add_header\s+{header}\s.*always;")

    def test_the_frontend_container_logs_no_access(self):
        (server,) = blocks(FRONTEND, r"(?m)^server")
        self.assertRegex(server, r"access_log\s+off;")
        self.assertRegex(server, r"error_log\s+/var/log/nginx/error\.log\s+crit;")

    def test_no_backend_access_log_can_be_enabled(self):
        texts = [DOCKERFILE] + [f.read_text() for f in COMPOSE_FILES]
        for text in texts:
            for option in ("--access-logfile", "--access-log", "--log-config"):
                self.assertNotIn(option, text)


if __name__ == "__main__":
    unittest.main()
