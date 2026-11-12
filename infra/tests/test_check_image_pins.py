"""Tests for infra/check_image_pins.py (SR-028 AC-5, AC-8 and AC-9, TS-013 TC-013.6, .11 and .13).

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

    def test_stray_backslash_does_not_swallow_the_next_yaml_item(self):
        code, findings, _ = run_tools("backslash_stray")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [
                (wf("backslash_stray"), 7, "action not pinned to a commit SHA", "actions/checkout@v4"),
                (wf("backslash_stray"), 10, "uv install without an exact version", "uv"),
            ],
        )

    def test_comment_line_inside_a_dockerfile_continuation_is_skipped(self):
        code, findings, _ = run_tools("uv_pass", backend="Dockerfile.uv_comment_continuation")
        self.assertEqual(code, 1)
        self.assertEqual(
            findings, [("backend/Dockerfile", 2, "uv install without an exact version", "uv")]
        )

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


    def test_empty_root_exits_2(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", ""], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertIn("is not a directory", result.stderr)


IMAGE_FINDING = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+): (?P<message>.+?): (?P<ref>.+)$")
DIGEST = "a" * 64
PG = f"postgres:16.15@sha256:{DIGEST}"
REDIS = f"redis:7.4.12@sha256:{'b' * 64}"
PAREN = 'POSTGRES_IMAGE = (\n    "{ref}"\n)\n'


def run_images(definition=PAREN.format(ref=PG), workflow=None, files=None, remove=()):
    """Run the test image rules (--root) on the base tree with the given overrides.

    ``definition`` is the text of backend/postgres_image.py, ``workflow`` the text of a workflow
    file, ``files`` extra {relative path: text}; ``remove`` lists base files to delete. Returns
    (exit code, [(path, line, message, ref)], stderr).
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shutil.copytree(TOOL_FIXTURES / "base", root, dirs_exist_ok=True)
        files = dict(files or {})
        files["backend/postgres_image.py"] = definition
        if workflow is not None:
            files[".github/workflows/ci.yml"] = workflow
        for name, text in files.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(text, encoding="utf-8")
        for name in remove:
            (root / name).unlink()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True
        )
    findings = []
    for out_line in result.stdout.splitlines():
        match = IMAGE_FINDING.match(out_line)
        if match is None:
            raise AssertionError(f"unexpected output line: {out_line!r}")
        findings.append((match["path"], int(match["line"]), match["message"], match["ref"]))
    return result.returncode, findings, result.stderr


DEF = "backend/postgres_image.py"
NOT_RECOGNISED = "test image definition not in a recognised form"


def ci_services(postgres, redis=REDIS):
    return (
        "jobs:\n  a:\n    services:\n      postgres:\n"
        f"        image: {postgres}\n      redis:\n        image: {redis}\n"
    )


class TestImagesMatchDeployment(unittest.TestCase):
    """SR-028 AC-9: the test images equal the deployment's (TC-013.13)."""

    def test_one_line_and_parenthesised_definitions_equal_to_compose_pass(self):
        self.assertEqual(run_images(f'POSTGRES_IMAGE = "{PG}"\n'), (0, [], ""))
        self.assertEqual(run_images(f"POSTGRES_IMAGE = '{PG}'\n"), (0, [], ""))
        self.assertEqual(run_images(PAREN.format(ref=PG)), (0, [], ""))
        self.assertEqual(run_images('"""Doc."""\n\n' + PAREN.format(ref=PG)), (0, [], ""))

    def test_definition_forms_that_are_not_recognised_fail(self):
        cases = {
            "implicit concatenation": ('POSTGRES_IMAGE = (\n    "postgres:16.15"\n    "@sha256:%s"\n)\n' % DIGEST, 1, 'POSTGRES_IMAGE = ('),
            "plus concatenation": ('POSTGRES_IMAGE = "postgres:16.15" + "@sha256:%s"\n' % DIGEST, 1, None),
            "f-string": (f'POSTGRES_IMAGE = f"{PG}"\n', 1, None),
            "name": ("TAG = 'x'\nPOSTGRES_IMAGE = TAG\n", 2, "POSTGRES_IMAGE = TAG"),
            "no closing parenthesis": (f'POSTGRES_IMAGE = (\n    "{PG}"\nX = 1\n', 1, "POSTGRES_IMAGE = ("),
            "annotation": (f'POSTGRES_IMAGE: str = "{PG}"\n', 1, None),
            "trailing comment": (f'POSTGRES_IMAGE = "{PG}"  # noqa\n', 1, None),
        }
        for name, (text, line, ref) in cases.items():
            with self.subTest(name):
                code, findings, _ = run_images(text)
                self.assertEqual(code, 1)
                self.assertEqual([(p, n, m) for p, n, m, _ in findings], [(DEF, line, NOT_RECOGNISED)])
                if ref:
                    self.assertEqual(findings[0][3], ref)

    def test_second_assignment_fails_at_its_line(self):
        code, findings, _ = run_images(f'POSTGRES_IMAGE = "{PG}"\nPOSTGRES_IMAGE = "{PG}"\n')
        self.assertEqual(code, 1)
        self.assertEqual(
            findings, [(DEF, 2, "second POSTGRES_IMAGE assignment", f'POSTGRES_IMAGE = "{PG}"')]
        )

    def test_later_assignments_in_any_form_fail_as_second_assignments(self):
        first = f'POSTGRES_IMAGE = "{PG}"\n'
        cases = {
            "indented under if": (first + 'if os.getenv("X") is None:\n    POSTGRES_IMAGE = "postgres:16"\n', 3, 'POSTGRES_IMAGE = "postgres:16"'),
            "annotated": (first + 'POSTGRES_IMAGE: str = "x"\n', 2, 'POSTGRES_IMAGE: str = "x"'),
            "augmented": (first + 'POSTGRES_IMAGE += "x"\n', 2, 'POSTGRES_IMAGE += "x"'),
            "or-assigned": (first + 'POSTGRES_IMAGE |= x\n', 2, 'POSTGRES_IMAGE |= x'),
            "global": (first + "def f():\n    global POSTGRES_IMAGE\n", 3, "global POSTGRES_IMAGE"),
        }
        for name, (text, line, ref) in cases.items():
            with self.subTest(name):
                code, findings, _ = run_images(text)
                self.assertEqual((code, findings), (1, [(DEF, line, "second POSTGRES_IMAGE assignment", ref)]))

    def test_comparison_is_not_an_assignment(self):
        text = f'POSTGRES_IMAGE = "{PG}"\nOK = POSTGRES_IMAGE == "x"\nif POSTGRES_IMAGE == "y":\n    pass\n'
        self.assertEqual(run_images(text), (0, [], ""))

    def test_other_image_literal_in_the_definition_file_fails(self):
        text = f'POSTGRES_IMAGE = "{PG}"\nOTHER = "postgres:16"\n'
        code, findings, _ = run_images(text)
        self.assertEqual(
            (code, findings), (1, [(DEF, 2, "second image literal in backend/postgres_image.py", "postgres:16")])
        )
        code, findings, _ = run_images(PAREN.format(ref=PG) + 'OTHER = "docker.io/library/postgres:16"\n')
        self.assertEqual(findings[0][1:], (4, "second image literal in backend/postgres_image.py", "docker.io/library/postgres:16"))

    def test_postgres_container_must_take_postgres_image(self):
        message = "PostgresContainer without POSTGRES_IMAGE as its image"
        cases = {
            "no argument": ("PostgresContainer()", "<none>"),
            "bare repository": ('PostgresContainer("postgres")', '"postgres"'),
            "another name": ("PostgresContainer(IMAGE)", "IMAGE"),
            "image keyword with another name": ("PostgresContainer(image=IMAGE)", "image=IMAGE"),
            "extra first argument": ("PostgresContainer(x, image=POSTGRES_IMAGE)", "x"),
            "starred": ("PostgresContainer(*args)", "*args"),
            "prefix of the name": ("PostgresContainer(POSTGRES_IMAGE_OLD)", "POSTGRES_IMAGE_OLD"),
        }
        for name, (call, ref) in cases.items():
            with self.subTest(name):
                code, findings, _ = run_images(files={"backend/tests/x.py": f"x = 1\nwith {call} as c:\n    pass\n"})
                self.assertEqual((code, findings), (1, [("backend/tests/x.py", 2, message, ref)]))

    def test_postgres_container_with_postgres_image_passes(self):
        calls = (
            "PostgresContainer(POSTGRES_IMAGE)",
            "PostgresContainer(image=POSTGRES_IMAGE)",
            "PostgresContainer(\n    POSTGRES_IMAGE,\n    username='u',\n)",
            "PostgresContainer(\n    image=POSTGRES_IMAGE\n)",
            "PostgresContainer( POSTGRES_IMAGE , driver=None)",
        )
        for call in calls:
            with self.subTest(call):
                text = f"with {call} as c:\n    pass\n"
                self.assertEqual(run_images(files={"backend/tests/x.py": text}), (0, [], ""))
        text = "class PostgresContainer(Base):\n    pass\nfrom testcontainers.postgres import PostgresContainer\n"
        self.assertEqual(run_images(files={"backend/tests/x.py": text}), (0, [], ""))

    def test_postgres_container_multi_line_call_is_reported_at_the_call_line(self):
        text = 'x = 1\nwith PostgresContainer(\n    "postgres"\n) as c:\n    pass\n'
        code, findings, _ = run_images(files={"backend/tests/x.py": text})
        self.assertEqual(
            (code, findings),
            (1, [("backend/tests/x.py", 2, "PostgresContainer without POSTGRES_IMAGE as its image", '"postgres"')]),
        )

    def test_registry_prefixed_literals_fail(self):
        message = "image literal outside backend/postgres_image.py"
        for ref in ("docker.io/library/postgres:16", "library/postgres:16", "localhost:5000/lib/postgres:16.15"):
            with self.subTest(ref):
                code, findings, _ = run_images(files={"backend/tests/x.py": f'IMAGE = "{ref}"\n'})
                self.assertEqual((code, findings), (1, [("backend/tests/x.py", 1, message, ref)]))

    def test_host_port_and_log_strings_are_false_positives_that_fail_closed(self):
        message = "image literal outside backend/postgres_image.py"
        for ref in ("postgres:5432", "redis:6379", "redis:connected"):
            with self.subTest(ref):
                code, findings, _ = run_images(files={"backend/tests/x.py": f'HOST = "{ref}"\n'})
                self.assertEqual((code, findings), (1, [("backend/tests/x.py", 1, message, ref)]))

    def test_service_as_an_inline_mapping_fails(self):
        message = "service as an inline mapping, its image is not compared"
        ref = f'{{image: "{PG}"}}'
        workflow = f"jobs:\n  a:\n    services:\n      postgres: {ref}\n"
        code, findings, _ = run_images(workflow=workflow)
        self.assertEqual((code, findings), (1, [(wf("ci"), 4, message, ref)]))
        compose = f"services:\n  postgres: {ref}\n  redis:\n    image: {REDIS}\n"
        code, findings, _ = run_images(files={"infra/docker-compose.yml": compose})
        self.assertIn(("infra/docker-compose.yml", 2, message, ref), findings)
        self.assertEqual(code, 1)

    def test_missing_definition_file_or_assignment_fails(self):
        for text in (None, "X = 1\n"):
            with self.subTest(text):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    shutil.copytree(TOOL_FIXTURES / "base", root, dirs_exist_ok=True)
                    (root / DEF).unlink()
                    if text:
                        (root / DEF).write_text(text)
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True
                    )
                self.assertEqual(result.returncode, 1)
                self.assertTrue(result.stdout.startswith(f"{DEF}:1: test image definition missing: "))

    def test_value_differences_are_reported_at_the_literal_line(self):
        other = "c" * 64
        cases = {
            "tag differs": (f"postgres:16.16@sha256:{DIGEST}", "test image differs from infra/docker-compose.yml:3"),
            "digest missing": ("postgres:16", "test image without @sha256 digest"),
            "digest differs": (f"postgres:16.15@sha256:{other}", "test image differs from infra/docker-compose.yml:3"),
        }
        for name, (ref, message) in cases.items():
            with self.subTest(name):
                code, findings, _ = run_images(PAREN.format(ref=ref))
                self.assertEqual((code, findings), (1, [(DEF, 2, message, ref)]))  # literal on line 2
                code, findings, _ = run_images(f'POSTGRES_IMAGE = "{ref}"\n')
                self.assertEqual((code, findings), (1, [(DEF, 1, message, ref)]))

    def test_missing_compose_file_or_postgres_service_fails(self):
        code, findings, _ = run_images(remove=("infra/docker-compose.yml",))
        self.assertEqual(
            findings, [("infra/docker-compose.yml", 1, "deployment Compose file missing", "<missing>")]
        )
        compose = f"services:\n  redis:\n    image: {REDIS}\n"
        code, findings, _ = run_images(files={"infra/docker-compose.yml": compose})
        self.assertEqual(code, 1)
        self.assertEqual(
            findings,
            [("infra/docker-compose.yml", 1, "no postgres service image to compare the test image with", PG)],
        )

    def test_ci_service_images_equal_to_compose_pass(self):
        self.assertEqual(run_images(workflow=ci_services(PG)), (0, [], ""))

    def test_ci_service_image_differing_from_compose_fails(self):
        message = "CI service image differs from infra/docker-compose.yml:3"
        for ref in ("postgres:16", f"postgres:16.14@sha256:{DIGEST}", f"postgres:16.15@sha256:{'c' * 64}"):
            with self.subTest(ref):
                code, findings, _ = run_images(workflow=ci_services(ref))
                self.assertEqual((code, findings), (1, [(wf("ci"), 5, message, ref)]))

    def test_ci_service_without_a_compose_counterpart_fails(self):
        code, findings, _ = run_images(workflow=ci_services(PG, redis="mailhog/mailhog:v1.0.1"))
        self.assertEqual(
            findings,
            [(wf("ci"), 7, "CI service image has no counterpart in infra/docker-compose.yml", "mailhog/mailhog:v1.0.1")],
        )

    def test_image_literal_in_test_code_fails_at_its_line(self):
        message = "image literal outside backend/postgres_image.py"
        for path in ("backend/tests/db/x.py", "backend/modules/dicom_viewer/tests/x.py"):
            with self.subTest(path):
                text = 'x = 1\nPostgresContainer("postgres:16")\n'
                code, findings, _ = run_images(files={path: text})
                self.assertEqual((code, findings), (1, [(path, 2, message, "postgres:16")]))
        code, findings, _ = run_images(files={"backend/tests/x.py": "r = Redis(image='redis:7')\n"})
        self.assertEqual(findings, [("backend/tests/x.py", 1, message, "redis:7")])

    def test_definition_at_the_old_path_is_not_exempt(self):
        code, findings, _ = run_images(files={"backend/tests/postgres_image.py": f'POSTGRES_IMAGE = "{PG}"\n'})
        self.assertEqual(
            (code, findings),
            [(1, [("backend/tests/postgres_image.py", 1, "image literal outside backend/postgres_image.py", PG)])][0],
        )

    def test_connection_urls_and_other_strings_pass(self):
        text = (
            'a = "redis://localhost:6379/0"\n'
            'b = "postgresql+psycopg://u:p@postgres:5432/db"\n'
            'c = "redis-cli"\n'
            'd = "postgres"\n'
        )
        self.assertEqual(run_images(files={"backend/tests/x.py": text}), (0, [], ""))

    def test_venv_and_non_backend_files_are_not_scanned(self):
        files = {"backend/.venv/lib/x.py": 'a = "postgres:16"\n', "tools/x.py": 'a = "postgres:16"\n'}
        self.assertEqual(run_images(files=files), (0, [], ""))


class UsageErrors(unittest.TestCase):
    def test_missing_file_exits_2(self):
        code, _, stderr = run_check("does_not_exist.yml")
        self.assertEqual(code, 2)
        self.assertIn("does_not_exist.yml", stderr)


if __name__ == "__main__":
    unittest.main()
