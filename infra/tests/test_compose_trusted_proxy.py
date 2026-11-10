"""Compose wiring of the trusted proxy (SR-042 AC 3, TS-016 TC-016.3).

Standard library only. Parses `docker compose config --format json` with a throwaway env file.
Skipped when `docker` is absent.
"""

import ipaddress
import shutil
import unittest
from pathlib import Path

from test_compose_object_store import GOOD, ROOT, compose_config

DOCKERFILE = ROOT / "backend" / "Dockerfile"  # the gunicorn command is the image CMD (TASK-191)


@unittest.skipUnless(shutil.which("docker"), "docker is not installed")
class TrustedProxyWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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

    def proxy_address(self):
        return self.config["services"]["reverse-proxy"]["networks"]["medhub"]["ipv4_address"]

    def test_medhub_network_has_a_fixed_subnet_holding_the_proxy_address(self):
        configs = self.config["networks"]["medhub"]["ipam"]["config"]
        self.assertEqual(len(configs), 1)
        proxy = ipaddress.ip_address(self.proxy_address())
        self.assertIn(proxy, ipaddress.ip_network(configs[0]["subnet"]))
        # Dynamic addresses come from ip_range only: no other container can take the proxy's
        # address before the proxy starts (found on the started stack, TASK-185).
        ip_range = ipaddress.ip_network(configs[0]["ip_range"])
        self.assertTrue(ip_range.subnet_of(ipaddress.ip_network(configs[0]["subnet"])))
        self.assertNotIn(proxy, ip_range)

    def test_medhub_subnet_is_outside_dockers_default_address_pools(self):
        """PRB-076: Docker gives the other networks (the project's `object-store`, other projects')
        subnets from 172.16.0.0/12 and 192.168.0.0/16, in order. A fixed subnet inside either can
        overlap one and then `up` fails with "networks have overlapping IPv4"."""
        subnet = ipaddress.ip_network(
            self.config["networks"]["medhub"]["ipam"]["config"][0]["subnet"]
        )
        for pool in ("172.16.0.0/12", "192.168.0.0/16"):
            self.assertFalse(subnet.overlaps(ipaddress.ip_network(pool)), pool)

    def test_object_store_network_takes_its_subnet_from_the_default_pool(self):
        """The reverse of the above: nothing pins `object-store`, so it cannot collide with a pinned one."""
        self.assertFalse(self.config["networks"]["object-store"].get("ipam", {}).get("config"))

    def test_backend_trusts_exactly_the_reverse_proxy_address(self):
        env = self.config["services"]["backend"]["environment"]
        self.assertEqual(env["TRUSTED_PROXIES"], self.proxy_address())
        # one address: no CIDR block, no list
        ipaddress.ip_address(env["TRUSTED_PROXIES"])

    def test_no_other_service_holds_the_proxy_address(self):
        for name, svc in self.config["services"].items():
            if name == "reverse-proxy":
                continue
            nets = svc.get("networks") or {}
            if isinstance(nets, dict):
                for net in nets.values():
                    self.assertNotEqual((net or {}).get("ipv4_address"), self.proxy_address(), name)

    def test_env_file_and_shell_cannot_widen_the_setting(self):
        for env, shell in (
            ({**GOOD, "TRUSTED_PROXIES": "0.0.0.0/0"}, None),
            (GOOD, {"TRUSTED_PROXIES": "0.0.0.0/0"}),
        ):
            result, config = compose_config(env, shell)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                config["services"]["backend"]["environment"]["TRUSTED_PROXIES"],
                self.proxy_address(),
            )

    def test_server_forwarded_header_handling_is_off(self):
        """ADR-0019: Gunicorn is started with an empty --forwarded-allow-ips."""
        self.assertRegex(DOCKERFILE.read_text(), r'--forwarded-allow-ips=("|\s|$)')


if __name__ == "__main__":
    unittest.main()
