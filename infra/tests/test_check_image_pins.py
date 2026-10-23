"""Tests for infra/check_image_pins.py (SR-028 AC-5, TS-013 TC-013.6).

Each test runs the script as a subprocess on fixture files, so the exit code and the
"<path>:<line>: ..." output are verified exactly as CI sees them.
"""

import re
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
SCRIPT = HERE.parent / "check_image_pins.py"
FINDING = re.compile(r"^(?P<path>.+):(?P<line>\d+): image reference without @sha256 digest: (?P<ref>.+)$")


def run_check(*names):
    """Run the check on fixture files; return (exit code, [(fixture name, line, ref)], stderr)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *(str(FIXTURES / n) for n in names)],
        capture_output=True,
        text=True,
    )
    findings = []
    for out_line in result.stdout.splitlines():
        match = FINDING.match(out_line)
        if match is None:
            raise AssertionError(f"unexpected output line: {out_line!r}")
        findings.append((Path(match["path"]).name, int(match["line"]), match["ref"]))
    return result.returncode, findings, result.stderr


class UnpinnedReferences(unittest.TestCase):
    def test_compose_image_without_digest(self):
        code, findings, _ = run_check("compose_unpinned.yml")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                ("compose_unpinned.yml", 5, "redis:7-alpine"),
                ("compose_unpinned.yml", 7, "postgres:16"),
                ("compose_unpinned.yml", 9, "minio/minio:latest"),
                ("compose_unpinned.yml", 11, "${REGISTRY}/app:1.0@sha256:" + "a" * 64),
            ],
        )

    def test_dockerfile_from_without_digest(self):
        code, findings, _ = run_check("Dockerfile.unpinned")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                ("Dockerfile.unpinned", 1, "python:3.12-slim"),
                ("Dockerfile.unpinned", 2, "node:20-slim"),  # --platform parsed
                ("Dockerfile.unpinned", 3, "golang:1.22"),  # AS parsed
                ("Dockerfile.unpinned", 4, "alpine:3.20"),  # lowercase from/as
            ],
        )

    def test_workflow_service_and_container_image_without_digest(self):
        code, findings, _ = run_check("workflow_unpinned.yml")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                ("workflow_unpinned.yml", 7, "postgres:16"),
                ("workflow_unpinned.yml", 13, "python:3.12"),
            ],
        )

    def test_short_uppercase_long_and_wrong_algorithm_digests_are_flagged(self):
        code, findings, _ = run_check("Dockerfile.badpin")
        self.assertEqual(code, 1)
        self.assertEqual([line for _, line, _ in findings], [1, 2, 3, 4])

    def test_variable_reference_is_flagged(self):
        code, findings, _ = run_check("Dockerfile.variable")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [("Dockerfile.variable", 2, "${BASE}"), ("Dockerfile.variable", 3, "$OTHER")],
        )

    def test_empty_image_value_fails_closed(self):
        code, findings, _ = run_check("compose_empty_image.yml")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                ("compose_empty_image.yml", 3, "<empty>"),  # value on the next line
                ("compose_empty_image.yml", 6, "<empty>"),  # only a comment
                ("compose_empty_image.yml", 8, ">-"),  # block scalar
            ],
        )

    def test_workflow_container_shorthand_is_checked(self):
        code, findings, _ = run_check("workflow_container_shorthand.yml")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                ("workflow_container_shorthand.yml", 5, "node:20"),
                ("workflow_container_shorthand.yml", 8, "python:3.12"),
            ],
        )

    def test_all_files_are_scanned_and_each_finding_names_its_file(self):
        code, findings, _ = run_check("compose_pinned.yml", "Dockerfile.unpinned", "workflow_pinned.yml")
        self.assertEqual(code, 1)
        self.assertEqual({name for name, _, _ in findings}, {"Dockerfile.unpinned"})


class AcceptedReferences(unittest.TestCase):
    def test_stage_and_scratch_references_are_not_flagged(self):
        code, findings, _ = run_check("Dockerfile.stages")
        self.assertEqual((code, findings), (0, []))

    def test_fully_pinned_fixtures_pass(self):
        code, findings, stderr = run_check("compose_pinned.yml", "Dockerfile.pinned", "workflow_pinned.yml")
        self.assertEqual((code, findings, stderr), (0, [], ""))


class UsageErrors(unittest.TestCase):
    def test_missing_file_exits_2(self):
        code, _, stderr = run_check("does_not_exist.yml")
        self.assertEqual(code, 2)
        self.assertIn("does_not_exist.yml", stderr)


if __name__ == "__main__":
    unittest.main()
