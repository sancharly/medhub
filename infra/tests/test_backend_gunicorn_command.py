"""The backend Gunicorn command disables the unused control socket (CR-005 AC-8, PRB-041, TASK-214).

Standard library only. Reads the raw files: the final `CMD` of `backend/Dockerfile` and the Compose
`backend` service. The start-up log of a started stack is checked in TASK-214's record.
"""

import json
import re
import unittest

from test_compose_secrets import service_blocks
from test_images_non_root import BACKEND_DOCKERFILE, last_stage


def final_cmd() -> list:
    """The exec-form `CMD` of the backend image's last stage, as a list of arguments."""
    found = re.findall(r"(?m)^CMD\s+(\[.*\])\s*$", last_stage(BACKEND_DOCKERFILE))
    assert found, "the final stage has no exec-form CMD"
    return json.loads(found[-1])


FORWARDED = "--forwarded-allow-ips"


def forwarded_flags(cmd: list) -> list:
    """The arguments that set Gunicorn's forwarded-allow-ips, also under an abbreviated name.

    Gunicorn's parser accepts any unambiguous prefix of an option (`--forwarded-allow=*`); no other
    option starts with `--forwarded`, so a prefix of at least that length is this option.
    """
    return [
        a for a in cmd if a.startswith("--forwarded") and FORWARDED.startswith(a.split("=", 1)[0])
    ]


class BackendGunicornCommand(unittest.TestCase):
    def test_cmd_starts_gunicorn_without_the_control_socket(self):
        """AC-8: the image CMD runs gunicorn with --no-control-socket (nothing uses gunicornc)."""
        cmd = final_cmd()
        self.assertEqual(cmd[0], "gunicorn")
        self.assertIn("--no-control-socket", cmd)

    def test_compose_does_not_replace_the_backend_cmd(self):
        """AC-8: a Compose `command:` would replace the CMD and drop the flag."""
        self.assertNotRegex(service_blocks()["backend"], r"(?m)^    command:")

    def test_cmd_keeps_the_empty_forwarded_allow_ips(self):
        """ADR-0019: the server never rewrites the TCP peer (SR-042).

        Gunicorn keeps the last value of a repeated option, so the flag must appear once, empty.
        """
        self.assertEqual(forwarded_flags(final_cmd()), ["--forwarded-allow-ips="])

    def test_the_flag_check_sees_an_abbreviated_option_name(self):
        """QA LOW 1: Gunicorn accepts `--forwarded-allow=*`; the check must count it."""
        cmd = ["gunicorn", "--forwarded-allow-ips=", "--forwarded-allow=*", "--workers=2"]
        self.assertEqual(forwarded_flags(cmd), ["--forwarded-allow-ips=", "--forwarded-allow=*"])
        self.assertEqual(forwarded_flags(["gunicorn", "--forwarded-allow-ips", "*"]), ["--forwarded-allow-ips"])
        self.assertEqual(forwarded_flags(["gunicorn", "--forwarder-headers=X", "--workers=2"]), [])


if __name__ == "__main__":
    unittest.main()
