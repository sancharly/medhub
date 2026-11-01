"""Every image MedHub builds runs as a non-root user (SR-041 AC 1, TS-015 TC-015.1, TASK-198).

Standard library only. Reads the raw files: the Dockerfiles of every Compose service that has a
`build:` section, the frontend's nginx configuration, the reverse proxy configuration and the
Compose `expose:` list. The image configuration and the running processes of a started stack are
checked by section 11 of `infra/smoke-test.sh`.
"""

import re
import unittest

from test_compose_secrets import service_blocks
from test_compose_object_store import ROOT

BACKEND_DOCKERFILE = ROOT / "backend" / "Dockerfile"
FRONTEND_DOCKERFILE = ROOT / "frontend" / "Dockerfile"
FRONTEND_NGINX = ROOT / "frontend" / "nginx.conf"
PROXY_NGINX = ROOT / "infra" / "reverse-proxy" / "nginx.conf"
ROOT_USERS = {"root", "0"}


def last_stage(dockerfile) -> str:
    """The text of the final build stage: what the built image is made of."""
    parts = re.split(r"(?m)^FROM\s", dockerfile.read_text())
    return parts[-1]


def final_user(dockerfile) -> str | None:
    """The user of the built image: the last `USER` of the last stage, `user:group` cut to user."""
    users = re.findall(r"(?m)^USER\s+(\S+)", last_stage(dockerfile))
    return users[-1].split(":")[0] if users else None


def built_dockerfiles() -> dict:
    """Compose service -> Dockerfile path, for every service MedHub builds."""
    found = {}
    for name, block in service_blocks().items():
        build = re.search(r"(?m)^    build:\n((?:      .*\n)+)", block)
        if build:
            context = re.search(r"context:\s*(\S+)", build.group(1)).group(1)
            dockerfile = re.search(r"dockerfile:\s*(\S+)", build.group(1)).group(1)
            found[name] = (ROOT / "infra" / context / dockerfile).resolve()
    return found


class ImageUsers(unittest.TestCase):
    def test_backend_image_ends_as_an_unprivileged_user(self):
        """AC 1: the backend image's last stage sets a USER that is not root."""
        self.assertNotIn(final_user(BACKEND_DOCKERFILE), ROOT_USERS | {None})

    def test_frontend_image_ends_as_an_unprivileged_user(self):
        """AC 1: the frontend image's last stage sets a USER that is not root."""
        self.assertNotIn(final_user(FRONTEND_DOCKERFILE), ROOT_USERS | {None})

    def test_every_built_compose_image_is_covered_and_non_root(self):
        """AC 1: every service with a `build:` uses a Dockerfile whose final USER is not root,
        so a new built image cannot be added without this check seeing it."""
        built = built_dockerfiles()
        # backend, the worker, the one-shot services (backend image) and the frontend
        self.assertTrue(
            {"backend", "celery-worker", "object-store-preflight", "object-store-init", "frontend"}
            <= set(built)
        )
        for name, path in built.items():
            self.assertTrue(path.exists(), name)
            self.assertNotIn(final_user(path), ROOT_USERS | {None}, f"{name} ({path})")

    def test_compose_does_not_override_a_built_image_to_root(self):
        """AC 1: no built service sets `user:` to root in Compose (it would beat the image)."""
        for name in built_dockerfiles():
            block = service_blocks()[name]
            override = re.search(r"(?m)^    user:\s*['\"]?(\S+?)['\"]?\s*$", block)
            if override:
                self.assertNotIn(override.group(1).split(":")[0], ROOT_USERS, name)


class FrontendPort(unittest.TestCase):
    def test_frontend_listens_on_an_unprivileged_port(self):
        """AC 1: a non-root nginx cannot bind below 1024; it listens on 8080 (CR-004 D-2)."""
        ports = re.findall(r"(?m)^\s*listen\s+(?:[^\s;]*:)?(\d+)\b", FRONTEND_NGINX.read_text())
        self.assertEqual(ports, ["8080"])

    def test_proxy_targets_the_frontend_port(self):
        """The proxy's upstream for `/` is the port the frontend listens on, and Compose exposes it."""
        text = PROXY_NGINX.read_text()
        targets = re.findall(r"proxy_pass\s+http://frontend:(\d+)\s*;", text)
        self.assertEqual(targets, ["8080"])
        block = service_blocks()["frontend"]
        self.assertRegex(block, r'expose:\n\s+- "8080"')
        self.assertNotRegex(block, r'- "80"')

    def test_pid_and_temp_paths_are_writable_by_the_unprivileged_user(self):
        """AC 1: the pid file is not under root-owned /run, and the cache directory is chowned."""
        text = FRONTEND_DOCKERFILE.read_text()
        self.assertRegex(text, r"/tmp/nginx\.pid")
        self.assertRegex(text, r"chown\s+-R\s+nginx:nginx\s+[^\n]*/var/cache/nginx")


if __name__ == "__main__":
    unittest.main()
