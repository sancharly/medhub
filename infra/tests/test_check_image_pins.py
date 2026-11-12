"""Tests for infra/check_image_pins.py (SR-028 AC-5 and AC-8, TS-013 TC-013.6 and TC-013.11).

Each test runs the script as a subprocess on fixture files, so the exit code and the
"<path>:<line>: ..." output are verified exactly as CI sees them.
"""

import re
import shutil
import subprocess
import sys
import tempfile
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


TOOL_FIXTURES = FIXTURES / "tools"
TOOL_FINDING = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+): (?P<message>.+): (?P<ref>[^:]*)$")


def run_tools(workflow, **dockerfiles):
    """Run the tool rules (--root) on a tree built from tools/ fixtures.

    The tree holds the base backend/ and frontend/ Dockerfiles, the workflow fixture as
    .github/workflows/<name>.yml and, for ``backend=`` / ``frontend=``, a Dockerfile fixture
    replacing the base one. Returns (exit code, [(path, line, message, ref)], stderr).
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shutil.copytree(TOOL_FIXTURES / "base", root, dirs_exist_ok=True)
        (root / ".github" / "workflows").mkdir(parents=True)
        shutil.copy(TOOL_FIXTURES / f"{workflow}.yml", root / ".github" / "workflows")
        for part, fixture in dockerfiles.items():
            shutil.copy(TOOL_FIXTURES / fixture, root / part / "Dockerfile")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True
        )
    findings = []
    for out_line in result.stdout.splitlines():
        match = TOOL_FINDING.match(out_line)
        if match is None:
            raise AssertionError(f"unexpected output line: {out_line!r}")
        findings.append((match["path"], int(match["line"]), match["message"], match["ref"]))
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

    def test_docker_uses_without_digest_fails(self):
        code, findings, _ = run_check("workflow_docker_uses_unpinned.yml")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                ("workflow_docker_uses_unpinned.yml", 4, "docker://alpine:3.20"),
                ("workflow_docker_uses_unpinned.yml", 5, "docker://alpine:3.20"),
                ("workflow_docker_uses_unpinned.yml", 6, "docker://alpine:${{ env.ALPINE }}@sha256:" + "a" * 64),
            ],
        )

    def test_docker_uses_with_digest_and_local_action_pass(self):
        self.assertEqual(run_check("workflow_docker_uses_pinned.yml"), (0, [], ""))


def wf(name):
    return f".github/workflows/{name}.yml"


class ToolReferences(unittest.TestCase):
    """SR-028 AC-8: one failing and one passing fixture per form (TC-013.11)."""

    def test_action_without_full_sha_or_tag_comment_fails(self):
        code, findings, _ = run_tools("uses_fail")
        sha = "action not pinned to a commit SHA"
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                (wf("uses_fail"), 4, sha, "actions/checkout@v4"),  # tag
                (wf("uses_fail"), 6, sha, "actions/setup-python@a26af69"),  # short SHA
                (
                    wf("uses_fail"),
                    7,
                    "action pinned without a release tag comment (# vX.Y.Z)",
                    "actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020",
                ),
                (wf("uses_fail"), 8, sha, "actions/cache"),  # no ref at all
            ],  # line 9, ``uses: ./local-action``, is exempt
        )

    def test_action_by_sha_with_tag_comment_and_local_pass(self):
        self.assertEqual(run_tools("uses_pass"), (0, [], ""))

    def test_runtime_version_without_patch_or_off_the_base_image_fails(self):
        code, findings, _ = run_tools("runtime_fail")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                (wf("runtime_fail"), 5, "python-version without a full patch version", "3.12"),
                (
                    wf("runtime_fail"),
                    7,
                    "python-version differs from backend/Dockerfile (3.12.15)",
                    "3.12.16",
                ),
                (
                    wf("runtime_fail"),
                    9,
                    "python-version without a full patch version",
                    "${{ matrix.python }}",
                ),
                (wf("runtime_fail"), 11, "python-version without a full patch version", '["3.12.15"]'),
                (wf("runtime_fail"), 13, "node-version without a full patch version", "24"),
                (
                    wf("runtime_fail"),
                    15,
                    "node-version differs from frontend/Dockerfile (24.22.2)",
                    "24.22.1",
                ),
            ],
        )

    def test_runtime_version_equal_to_the_base_image_passes(self):
        self.assertEqual(run_tools("runtime_pass"), (0, [], ""))

    def test_uv_install_without_exact_version_fails(self):
        code, findings, _ = run_tools("uv_fail")
        message = "uv install without an exact version"
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                (wf("uv_fail"), 4, message, "uv"),
                (wf("uv_fail"), 5, message, "uv>=0.13"),
                (wf("uv_fail"), 6, message, "uv"),  # pipx
                (wf("uv_fail"), 7, message, "uv==0.13"),  # not X.Y.Z
            ],  # line 8, ``uvicorn``, is another package
        )

    def test_uv_install_without_exact_version_in_a_dockerfile_fails(self):
        code, findings, _ = run_tools("uv_pass", backend="Dockerfile.uv_unpinned")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings, [("backend/Dockerfile", 2, "uv install without an exact version", "uv")]
        )

    def test_exact_uv_versions_pass_in_workflow_and_dockerfile(self):
        self.assertEqual(run_tools("uv_pass"), (0, [], ""))

    def test_two_uv_versions_in_one_repository_fail(self):
        message = "uv version differs from the others (0.13.7)"
        code, findings, _ = run_tools("uv_mismatch")
        self.assertEqual((code, findings), (1, [(wf("uv_mismatch"), 7, message, "uv==0.13.6")]))

    def test_backend_dockerfile_is_the_uv_reference(self):
        message = "uv version differs from the others (0.13.6)"
        code, findings, _ = run_tools("uv_pass", backend="Dockerfile.uv_other_version")
        # Three workflow installs of 0.13.7 against one 0.13.6 in the shipped image: the image wins.
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                (wf("uv_pass"), 5, message, "uv==0.13.7"),
                (wf("uv_pass"), 7, message, "uv==0.13.7"),
                (wf("uv_pass"), 9, message, "uv==0.13.7"),
            ],
        )

    def test_uv_install_continued_or_in_exec_form_fails(self):
        code, findings, _ = run_tools("uv_pass", backend="Dockerfile.uv_forms_fail")
        message = "uv install without an exact version"
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [("backend/Dockerfile", 2, message, "uv"), ("backend/Dockerfile", 4, message, "uv")],
        )

    def test_exact_uv_continued_or_in_exec_form_passes(self):
        self.assertEqual(run_tools("uv_pass", backend="Dockerfile.uv_forms_pass"), (0, [], ""))

    def test_version_file_keys_fail(self):
        code, findings, _ = run_tools("versionfile_fail")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                (wf("versionfile_fail"), 6, "python-version-file cannot be compared with the base image", ".python-version"),
                (wf("versionfile_fail"), 9, "node-version-file cannot be compared with the base image", ".nvmrc"),
            ],
        )

    def test_setup_uv_action_fails_even_when_pinned(self):
        code, findings, _ = run_tools("setup_uv_fail")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                (
                    wf("setup_uv_fail"),
                    4,
                    "uv installed by an action, outside the uv==X.Y.Z rule",
                    "astral-sh/setup-uv@e92bafb6253dcd438e0484186d7669ea7a8ca1cc",
                )
            ],
        )

    def test_npx_package_without_exact_version_fails(self):
        code, findings, _ = run_tools("npx_fail")
        message = "npx package without an exact version"
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                (wf("npx_fail"), 4, message, "@redocly/cli"),
                (wf("npx_fail"), 5, message, "redoc-cli@latest"),
                (wf("npx_fail"), 7, message, "prettier@3"),  # inside a run block
            ],
        )

    def test_npx_after_a_quote_or_an_env_prefix_fails(self):
        code, findings, _ = run_tools("npx_forms_fail")
        message = "npx package without an exact version"
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                (wf("npx_forms_fail"), 4, message, "@redocly/cli"),  # quoted scalar
                (wf("npx_forms_fail"), 5, message, "eslint"),  # VAR=value prefix
                (wf("npx_forms_fail"), 7, message, "prettier"),  # prefix after &&
            ],
        )

    def test_npx_package_with_exact_version_passes(self):
        self.assertEqual(run_tools("npx_pass"), (0, [], ""))

    def test_the_repository_passes(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_paths_and_root_together_exit_2(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(FIXTURES), "x.yml"], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("PATH and --root cannot be combined", result.stderr)

    def test_root_missing_or_without_workflows_or_dockerfiles_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            for root, text in ((Path(tmp) / "absent", "is not a directory"), (Path(tmp), "no workflows or Dockerfiles")):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True
                )
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertIn(text, result.stderr)


class UsageErrors(unittest.TestCase):
    def test_missing_file_exits_2(self):
        code, _, stderr = run_check("does_not_exist.yml")
        self.assertEqual(code, 2)
        self.assertIn("does_not_exist.yml", stderr)


if __name__ == "__main__":
    unittest.main()
