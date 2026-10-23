#!/usr/bin/env python3
"""Fail when a container image reference has no @sha256:<64 hex> digest.

SR-028 AC-5 / CR-001 AC-3: scans Compose and workflow ``image:`` values and Dockerfile
``FROM`` instructions. Standard library only, no YAML parser: line-based matching is
enough for the forms used in this repository.

Usage: check_image_pins.py [PATH ...]
  No arguments: every tracked Compose file, Dockerfile and GitHub workflow
  (excluding infra/tests/fixtures/). With arguments: exactly those files.
Output per finding: <path>:<line>: image reference without @sha256 digest: <ref>
Exit: 0 all pinned, 1 at least one finding, 2 usage or read error.
"""

import fnmatch
import re
import subprocess
import sys
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


def image_values(lines):
    """Yield (line number, reference) for every image value in a Compose/workflow file.

    An empty ``image:`` value (value on the next line, or only a comment) is yielded as
    ``<empty>`` so that it is reported, not skipped. ``container:`` with no value is the
    mapping form, whose ``image:`` key is checked on its own line.
    """
    for number, line in enumerate(lines, start=1):
        match = IMAGE_KEY.match(line)
        if match is None:
            continue
        value = re.sub(r"(^|\s)#.*$", "", match["value"]).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value:
            yield number, value
        elif match["key"] == "image":
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


def tracked_files():
    output = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    files = []
    for path in output.splitlines():
        if path.startswith(FIXTURES_DIR):
            continue
        name = Path(path).name
        if any(fnmatch.fnmatchcase(name, p) for p in DEFAULT_PATTERNS) or any(
            fnmatch.fnmatchcase(path, p) for p in WORKFLOW_PATTERNS
        ):
            files.append(str(REPO_ROOT / path))
    return files


def main(argv):
    try:
        paths = argv or tracked_files()
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"error: cannot list tracked files: {error}", file=sys.stderr)
        return 2
    if not paths:
        print("error: no files to scan", file=sys.stderr)
        return 2
    found = False
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
    return 1 if found else 0


def _display(path):
    """Show repository-relative paths for repository files, the path as given otherwise."""
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return path


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
