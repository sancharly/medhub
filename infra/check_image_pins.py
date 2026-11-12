#!/usr/bin/env python3
"""Fail when a container image, a build tool or a CI tool reference is not pinned exactly.

Image rule (SR-028 AC-5 / CR-001 AC-3): scans Compose and workflow ``image:`` values, workflow
``uses: docker://<image>`` references and Dockerfile ``FROM`` instructions for a missing
@sha256:<64 hex> digest.

Tool rules (SR-028 AC-8 / CR-005 AC-4, ADR-0020), over the tracked workflows and Dockerfiles:
  - a workflow ``uses:`` of a repository action must be owner/repo[/path]@<40 hex> followed by a
    ``# v<tag>`` comment (``./local`` actions are exempt, ``docker://`` goes to the image rule), and
    ``astral-sh/setup-uv`` is a finding (it installs uv outside the ``uv==X.Y.Z`` rule);
  - a workflow ``python-version`` / ``node-version`` must be X.Y.Z and equal the tag version of
    ``FROM python:X.Y.Z-...`` in backend/Dockerfile / ``FROM node:X.Y.Z-...`` in
    frontend/Dockerfile (an expression or a list is a finding; so is ``python-version-file`` /
    ``node-version-file``);
  - a ``uv`` install (``pip install`` / ``pipx install``) in a workflow or a Dockerfile must be
    ``uv==X.Y.Z`` (``\\``-continued lines are joined, the Dockerfile exec form is read), and every
    such version in the repository must equal the one in backend/Dockerfile (the shipped image;
    the most common version when that Dockerfile installs no uv);
  - a workflow ``npx`` call must name its package with an exact version (``pkg@X.Y.Z``), also after a
    quote or a ``VAR=value`` prefix.
Standard library only, no YAML parser: line-based matching is enough for the forms used in this
repository. A form of the kinds above that the rules cannot parse is a finding; forms outside
them (a multi-line ``run:`` command assembled by a script file, a composite action under
.github/actions/, an ``npx`` run through a script) are not seen.

Usage: check_image_pins.py [PATH ... | --root DIR]
  No arguments: the image rule on every tracked Compose file, Dockerfile and GitHub workflow,
  then the tool rules on the repository (excluding infra/tests/fixtures/).
  PATH ...: the image rule on exactly those files.
  --root DIR: the tool rules only, on the workflows and Dockerfiles found under DIR (exit 2 when
    DIR is not a directory or holds none).
Output per finding: <path>:<line>: <message>: <reference>
  (image rule message: image reference without @sha256 digest)
Exit: 0 all pinned, 1 at least one finding, 2 usage or read error.
"""

import argparse
import fnmatch
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = "infra/tests/fixtures/"
DEFAULT_PATTERNS = (
    "docker-compose*.yml",
    "docker-compose*.yaml",
    "compose*.yml",
    "compose*.yaml",
    "Dockerfile",
    "Dockerfile.*",
)
WORKFLOW_PATTERNS = (".github/workflows/*.yml", ".github/workflows/*.yaml")

PINNED = re.compile(r"@sha256:[0-9a-f]{64}$")
# ``image:`` always names an image; the workflow shorthand ``container: <ref>`` does too.
IMAGE_KEY = re.compile(r"^\s*(?:-\s+)?(?P<key>image|container):\s*(?P<value>.*)$")
FROM = re.compile(r"^\s*FROM\s+(?P<rest>.*)$", re.IGNORECASE)
DOCKER_USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<value>[\"']?docker://.*)$")


def image_values(lines):
    """Yield (line number, reference) for every image value in a Compose/workflow file.

    A workflow ``uses: docker://<image>`` counts as an image value.

    An empty ``image:`` value (value on the next line, or only a comment) is yielded as
    ``<empty>`` so that it is reported, not skipped. ``container:`` with no value is the
    mapping form, whose ``image:`` key is checked on its own line.
    """
    for number, line in enumerate(lines, start=1):
        match = IMAGE_KEY.match(line) or DOCKER_USES.match(line)
        if match is None:
            continue
        value = re.sub(r"(^|\s)#.*$", "", match["value"]).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value:
            yield number, value
        elif match.groupdict().get("key") == "image":
            yield number, "<empty>"


def from_references(lines):
    """Yield (line number, reference) for every Dockerfile FROM that names an external image."""
    stages = set()
    for number, line in enumerate(lines, start=1):
        match = FROM.match(line)
        if match is None:
            continue
        tokens = [t for t in match["rest"].split() if not t.startswith("--")]
        if not tokens:
            continue
        reference = tokens[0]
        if len(tokens) >= 3 and tokens[1].lower() == "as":
            stages.add(tokens[2].lower())
        if reference.lower() == "scratch" or reference.lower() in stages:
            continue
        yield number, reference


def is_dockerfile(path):
    name = Path(path).name
    return name == "Dockerfile" or name.startswith("Dockerfile.")


def scan(path):
    """Return the (line number, reference) findings of one file."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    references = from_references(lines) if is_dockerfile(path) else image_values(lines)
    # A reference with a variable cannot be verified statically, so it is a finding too.
    return [(n, ref) for n, ref in references if "$" in ref or not PINNED.search(ref)]


def git_paths():
    """Return the repository-relative paths of the tracked files, fixtures excluded."""
    output = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    return [path for path in output.splitlines() if not path.startswith(FIXTURES_DIR)]


def tracked_files():
    files = []
    for path in git_paths():
        name = Path(path).name
        if any(fnmatch.fnmatchcase(name, p) for p in DEFAULT_PATTERNS) or any(
            fnmatch.fnmatchcase(path, p) for p in WORKFLOW_PATTERNS
        ):
            files.append(str(REPO_ROOT / path))
    return files


# --- Tool rules (SR-028 AC-8) ---------------------------------------------------------------

USES_KEY = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<value>.*)$")
ACTION_SHA = re.compile(r"^[\w.-]+/[\w.-]+(?:/\S+?)?@[0-9a-f]{40}$")
TAG_COMMENT = re.compile(r"^v\d")
VERSION_KEY = re.compile(r"^\s*(?:-\s+)?(?P<tool>python|node)-version:\s*(?P<value>.*)$")
PATCH_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
BASE_IMAGES = {"python": "backend/Dockerfile", "node": "frontend/Dockerfile"}
PIP_INSTALL = re.compile(r"\b(?:pip[0-9.]*|pipx)\s+install\b(?P<args>[^&|;#]*)")
UV_TOKEN = re.compile(r"^uv(?:[=<>~!@\[].*)?$")
UV_EXACT = re.compile(r"^uv==(?P<version>\d+\.\d+\.\d+)$")
VERSION_FILE_KEY = re.compile(r"^\s*(?:-\s+)?(?P<tool>python|node)-version-file:\s*(?P<value>.*)$")
SETUP_UV = re.compile(r"^astral-sh/setup-uv(?:[/@]|$)", re.IGNORECASE)
EXEC_FORM = re.compile(r"^\s*RUN\s+\[", re.IGNORECASE)
NPX_CALL = re.compile(
    r"(?:^\s*(?:-\s+)?(?:run:\s*)?|&&\s*|;\s*|\|\s*|\(\s*)[\"']?(?:\w+=\S*\s+)*npx\s+(?P<args>.*)$"
)
NPX_PACKAGE = re.compile(r"^(?:@[\w.-]+/)?[\w.-]+@\d+\.\d+\.\d+$")


def _split_comment(value):
    """Return (value, comment) of a YAML scalar line tail; quotes around the value are removed."""
    parts = re.split(r"\s+#", value, maxsplit=1)
    value = parts[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value, (parts[1].strip() if len(parts) > 1 else "")


def logical_lines(lines):
    """Yield (first line number, text) with ``\\``-continued lines joined into one."""
    start, parts = None, []
    for number, line in enumerate(lines, start=1):
        if start is None:
            start = number
        if line.rstrip().endswith("\\") and not line.lstrip().startswith("#"):
            parts.append(line.rstrip()[:-1])
            continue
        parts.append(line)
        yield start, " ".join(parts)
        start, parts = None, []
    if parts:
        yield start, " ".join(parts)


def root_paths(root):
    """Repository-relative paths of the files the tool rules read."""
    if root == REPO_ROOT:
        paths = git_paths()
    else:
        paths = [p.relative_to(root).as_posix() for p in sorted(root.rglob("*")) if p.is_file()]
    workflows = [p for p in paths if any(fnmatch.fnmatchcase(p, pat) for pat in WORKFLOW_PATTERNS)]
    dockerfiles = [p for p in paths if is_dockerfile(p)]
    return workflows, dockerfiles


def base_versions(root):
    """Map ``python`` / ``node`` to (Dockerfile path, tag version) from the shipped FROM lines."""
    versions = {}
    for tool, dockerfile in BASE_IMAGES.items():
        path = root / dockerfile
        version = None
        if path.is_file():
            lines = path.read_text(encoding="utf-8").splitlines()
            for _, reference in from_references(lines):
                match = re.match(rf"^{tool}:(\d+\.\d+\.\d+)(?:-|@|$)", reference)
                if match:
                    version = match[1]
                    break
        versions[tool] = (dockerfile, version)
    return versions


def tool_findings(root):
    """Return sorted (path, line, message, reference) findings of the tool rules under root."""
    workflows, dockerfiles = root_paths(root)
    bases = base_versions(root)
    findings = []
    uv_versions = []  # (path, line, version) of every exact uv install
    for path in workflows + dockerfiles:
        is_workflow = path in workflows
        lines = (root / path).read_text(encoding="utf-8").splitlines()
        for number, line in logical_lines(lines):
            if line.lstrip().startswith("#"):
                continue
            if is_workflow:
                findings += _action_findings(path, number, line)
                findings += _runtime_findings(path, number, line, bases)
                findings += _version_file_findings(path, number, line)
                findings += _npx_findings(path, number, line)
            for token in _uv_tokens(line):
                exact = UV_EXACT.match(token)
                if exact:
                    uv_versions.append((path, number, exact["version"]))
                else:
                    findings.append((path, number, "uv install without an exact version", token))
    counts = Counter(version for _, _, version in uv_versions)
    if len(counts) > 1:
        # The shipped image is the reference; without a uv install there, the most common version.
        shipped = [v for path, _, v in uv_versions if path == "backend/Dockerfile"]
        expected = shipped[0] if shipped else counts.most_common(1)[0][0]
        for path, number, version in uv_versions:
            if version != expected:
                findings.append(
                    (path, number, f"uv version differs from the others ({expected})", f"uv=={version}")
                )
    return sorted(findings, key=lambda f: (f[0], f[1]))


def _action_findings(path, number, line):
    match = USES_KEY.match(line)
    if match is None:
        return []
    value, comment = _split_comment(match["value"])
    if value.startswith(("./", "docker://")):  # docker:// is checked by the image rule
        return []
    findings = []
    if SETUP_UV.match(value):
        findings.append((path, number, "uv installed by an action, outside the uv==X.Y.Z rule", value))
    if not ACTION_SHA.match(value):
        findings.append((path, number, "action not pinned to a commit SHA", value or "<empty>"))
    elif not TAG_COMMENT.match(comment):
        findings.append((path, number, "action pinned without a release tag comment (# vX.Y.Z)", value))
    return findings


def _runtime_findings(path, number, line, bases):
    match = VERSION_KEY.match(line)
    if match is None:
        return []
    key = f"{match['tool']}-version"
    value, _ = _split_comment(match["value"])
    if not PATCH_VERSION.match(value):
        return [(path, number, f"{key} without a full patch version", value or "<empty>")]
    dockerfile, version = bases[match["tool"]]
    if version is None:
        return [(path, number, f"{key} has no FROM {match['tool']}:X.Y.Z in {dockerfile} to match", value)]
    if value != version:
        return [(path, number, f"{key} differs from {dockerfile} ({version})", value)]
    return []


def _version_file_findings(path, number, line):
    match = VERSION_FILE_KEY.match(line)
    if match is None:
        return []
    value, _ = _split_comment(match["value"])
    message = f"{match['tool']}-version-file cannot be compared with the base image"
    return [(path, number, message, value or "<empty>")]


def _uv_tokens(line):
    """Yield the ``uv`` package argument of every pip/pipx install on the line."""
    if EXEC_FORM.match(line):  # RUN ["pip", "install", "uv"]
        line = re.sub(r"[\[\]\",]", " ", line)
    for install in PIP_INSTALL.finditer(line):
        for raw in install["args"].split():
            token = raw.strip("\"'")
            if not token.startswith("-") and UV_TOKEN.match(token):
                yield token


def _npx_findings(path, number, line):
    match = NPX_CALL.search(re.sub(r"\s+#.*$", "", line))
    if match is None:
        return []
    words = re.split(r"&&|;|\|", match["args"])[0].split()
    package = next((w.strip("\"'") for w in words if not w.startswith("-")), "<none>")
    if NPX_PACKAGE.match(package):
        return []
    return [(path, number, "npx package without an exact version", package)]


def main(argv):
    parser = argparse.ArgumentParser(
        prog="check_image_pins.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("paths", nargs="*", metavar="PATH")
    parser.add_argument("--root", metavar="DIR")
    args = parser.parse_args(argv)
    if args.root and args.paths:
        parser.error("PATH and --root cannot be combined")
    found = False
    if args.root is None:
        try:
            paths = args.paths or tracked_files()
        except (OSError, subprocess.CalledProcessError) as error:
            print(f"error: cannot list tracked files: {error}", file=sys.stderr)
            return 2
        if not paths:
            print("error: no files to scan", file=sys.stderr)
            return 2
        for path in paths:
            try:
                findings = scan(path)
            except (OSError, UnicodeDecodeError) as error:
                print(f"error: cannot read {path}: {error}", file=sys.stderr)
                return 2
            display = _display(path)
            for number, reference in findings:
                print(f"{display}:{number}: image reference without @sha256 digest: {reference}")
                found = True
    if args.root or not args.paths:
        root = Path(args.root).resolve() if args.root else REPO_ROOT
        if args.root:
            if not root.is_dir():
                print(f"error: --root {args.root} is not a directory", file=sys.stderr)
                return 2
            if not any(root_paths(root)):
                print(f"error: no workflows or Dockerfiles under {root}", file=sys.stderr)
                return 2
        try:
            tool = tool_findings(root)
        except (OSError, UnicodeDecodeError, subprocess.CalledProcessError) as error:
            print(f"error: cannot read the tool references under {root}: {error}", file=sys.stderr)
            return 2
        for path, number, message, reference in tool:
            print(f"{path}:{number}: {message}: {reference}")
            found = True
    return 1 if found else 0


def _display(path):
    """Show repository-relative paths for repository files, the path as given otherwise."""
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return path


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
