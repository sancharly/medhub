"""infra/alembic-head.sh reads the head revision the smoke test compares with (PRB-062, TASK-194 QA).

Synthetic migration directories cover a typed revision, single quotes, a merge, two heads and a
file the parser cannot read (fewer revisions found than files). Standard library only; needs bash
and awk.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

from test_compose_object_store import ROOT

SCRIPT = ROOT / "infra" / "alembic-head.sh"


def head(files: dict[str, str]) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        for name, text in files.items():
            (Path(tmp) / name).write_text(text)
        return subprocess.run(["bash", str(SCRIPT), tmp], capture_output=True, text=True)


class AlembicHead(unittest.TestCase):
    def test_the_real_directory_has_one_head(self):
        out = subprocess.run(
            ["bash", str(SCRIPT), str(ROOT / "backend/app/db/alembic/versions")],
            capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertRegex(out.stdout.strip(), r"^\d{4}$")

    def test_plain_typed_and_single_quoted_forms(self):
        out = head({
            "0001_a.py": 'revision = "0001"\ndown_revision = None\n',
            "0002_b.py": 'revision: str = "0002"\ndown_revision: str | None = "0001"\n',
            "0003_c.py": "revision: str = '0003'\ndown_revision: Union[str, None] = '0002'\n",
        })
        self.assertEqual((out.returncode, out.stdout.strip()), (0, "0003"), out.stderr)

    def test_a_merge_has_one_head(self):
        out = head({
            "0001_a.py": 'revision = "0001"\ndown_revision = None\n',
            "0002_b.py": 'revision = "0002"\ndown_revision = "0001"\n',
            "0003_c.py": 'revision = "0003"\ndown_revision = "0001"\n',
            "0004_m.py": 'revision = "0004"\ndown_revision = ("0002", "0003")\n',
        })
        self.assertEqual((out.returncode, out.stdout.strip()), (0, "0004"), out.stderr)

    def test_two_heads_fail(self):
        out = head({
            "0001_a.py": 'revision = "0001"\ndown_revision = None\n',
            "0002_b.py": 'revision = "0002"\ndown_revision = "0001"\n',
            "0003_c.py": 'revision = "0003"\ndown_revision = "0001"\n',
        })
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("found 2", out.stderr)

    def test_a_revision_the_parser_cannot_read_fails(self):
        out = head({
            "0001_a.py": 'revision = "0001"\ndown_revision = None\n',
            "0002_b.py": 'REV = "0002"\nrevision = REV\ndown_revision = "0001"\n',
        })
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("revisions", out.stderr)


if __name__ == "__main__":
    unittest.main()
