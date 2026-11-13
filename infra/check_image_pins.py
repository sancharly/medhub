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
Test image rules (SR-028 AC-9 / CR-005 AC-6, ADR-0020), over the repository root:
  - backend/postgres_image.py must hold exactly one ``POSTGRES_IMAGE`` assignment at the start of a
    line, as ``POSTGRES_IMAGE = "<ref>"`` or as ``POSTGRES_IMAGE = (`` / one string literal / ``)``
    (any other form, such as concatenation, an f-string or a name, is a finding); every later
    binding of the name, read from the parsed file (``ast``), is a second assignment: plain,
    annotated, augmented, tuple unpacking, ``:=``, ``for``, ``with ... as``, ``import ... as``,
    ``import POSTGRES_IMAGE`` / ``from x import POSTGRES_IMAGE``, ``global``, ``except ... as``, a
    ``def`` / ``async def`` / ``class`` of that name, a ``match`` capture (``case POSTGRES_IMAGE``,
    ``*POSTGRES_IMAGE``, ``**POSTGRES_IMAGE``), a ``;``-joined statement; so is a call of
    ``globals()``, ``locals()``, ``vars()`` or ``setattr()``;
    ``<ref>`` must carry a digest and equal the ``image:`` of the ``postgres`` service in
    infra/docker-compose.yml; a file of the definition that does not parse is a finding;
  - every workflow ``services.<name>.image`` must equal the Compose ``image:`` of the service with
    the same image repository (``postgres``, ``redis``); a service written as an inline mapping
    (``postgres: {image: ...}``) is a finding, not skipped;
  - no string literal ``"[registry/namespace/]<repo>:<tag>"`` of a Compose image repository may
    appear in backend/**/*.py (``.venv/`` excluded), including in backend/postgres_image.py apart
    from the one recognised ``POSTGRES_IMAGE`` literal. The pattern also matches ``"postgres:5432"``
    or ``"redis:connected"`` (a host:port or a log string): rewrite such a literal, the rule fails
    closed;
  - every ``PostgresContainer(`` call in backend/**/*.py must pass ``POSTGRES_IMAGE`` as its first
    positional argument or as ``image=POSTGRES_IMAGE``; no argument, a literal or another name is
    a finding (a line already reported for an image literal is not reported twice); so is a
    ``PostgresContainer`` imported under an alias (``import ... as``), and so is any binding of
    ``POSTGRES_IMAGE`` (assignment, ``import ... as``, an attribute store such as
    ``postgres_image.POSTGRES_IMAGE = ...``) in a backend/**/*.py file other than the definition.
Standard library only, no YAML parser: line-based matching is enough for the forms used in this
repository. A form of the kinds above that the rules cannot parse is a finding. Matching is
line-based, so these are not seen: an ``npx`` or a ``pip install uv`` reached through a script file,
a ``uses:`` or ``run:`` assembled by a YAML anchor or template expression, and composite actions
under .github/actions/; for the test images, a job ``container:`` or ``uses: docker://`` image
(checked by the image rule only: a digest is present, not equality with Compose), a container class
other than ``PostgresContainer`` (the one that occurs is the ``DockerContainer`` Redis call in
backend/tests/auth/test_session_cap_concurrency.py, which reads the Compose image at run time), a
``PostgresContainer`` reached under another name without ``import ... as``
(``PC = PostgresContainer``, ``getattr``, ``import *``), a ``POSTGRES_IMAGE`` rebound through
``setattr(...)``, ``sys.modules`` or ``vars()`` in a file other than the definition file (inside it,
a ``globals()``, ``locals()``, ``vars()`` or ``setattr()`` call is a finding), and an import of
``POSTGRES_IMAGE`` from a module other than backend/postgres_image.py; none of the others occurs
in the repository.

Usage: check_image_pins.py [PATH ... | --root DIR]
  No arguments: the image rule on every tracked Compose file, Dockerfile and GitHub workflow,
  then the tool and test image rules on the repository (excluding infra/tests/fixtures/).
  PATH ...: the image rule on exactly those files.
  --root DIR: the tool and test image rules only, on the files found under DIR (exit 2 when DIR is
    empty, not a directory, or holds no workflow or Dockerfile).
Output per finding: <path>:<line>: <message>: <reference>
  (image rule message: image reference without @sha256 digest)
Exit: 0 all pinned, 1 at least one finding, 2 usage or read error.
"""

import argparse
import ast
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


YAML_ITEM = re.compile(r"^\s*(?:-(?:\s|$)|[A-Za-z_][\w.-]*:(?:\s|$))")


def logical_lines(lines, yaml=False):
    """Yield (first line number, text) with ``\\``-continued lines joined into one.

    A stray trailing ``\\`` does not join the next line when that line is blank or starts a YAML
    key or list item (``yaml=True``, workflows). In a Dockerfile (``yaml=False``) comment lines
    inside a continuation are dropped, as Docker does.
    """
    start, parts = None, []
    for number, line in enumerate(lines, start=1):
        if parts and yaml and (not line.strip() or YAML_ITEM.match(line)):
            yield start, " ".join(parts)
            start, parts = None, []
        elif parts and not yaml and line.lstrip().startswith("#"):
            continue
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
        for number, line in logical_lines(lines, yaml=is_workflow):
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
    findings += image_findings(root, workflows)
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


# --- Test image rules (SR-028 AC-9) -----------------------------------------------------------

COMPOSE = "infra/docker-compose.yml"
DEFINITION = "backend/postgres_image.py"
DEFINITION_START = re.compile(
    r"^\s*(?:POSTGRES_IMAGE\s*(?::[^=]*)?[-+*|]?=(?!=)|global\s+(?:\w+\s*,\s*)*POSTGRES_IMAGE\b)"
)
ONE_LINE = re.compile(r"""^POSTGRES_IMAGE = (?P<q>["'])(?P<ref>[^"'\\]*)(?P=q)\s*$""")
PAREN_OPEN = re.compile(r"^POSTGRES_IMAGE = \(\s*$")
LITERAL_LINE = re.compile(r"""^\s+(?P<q>["'])(?P<ref>[^"'\\]*)(?P=q)\s*$""")
SERVICES_KEY = re.compile(r"^(?P<indent>\s*)services:\s*$")
INLINE_SERVICE = re.compile(r"^\s*(?P<name>[\w.-]+):\s+(?P<rest>[^#\s].*)$")
INLINE_MESSAGE = "service as an inline mapping, its image is not compared"
CONTAINER_CALL = re.compile(r"(?<!class )\bPostgresContainer\s*\(")
CONTAINER_ARGUMENT = re.compile(r"\s*(?:image\s*=\s*)?POSTGRES_IMAGE\s*[,)]")
SERVICE_KEY = re.compile(r"^(?P<indent>\s*)(?P<name>[\w.-]+):\s*(?:#.*)?$")


def image_repository(reference):
    """The image repository of a reference: everything before the tag or digest."""
    return re.split(r"[:@]", reference, maxsplit=1)[0]


def service_images(lines):
    """Return ([(service name, line number, reference)], [(name, line number, text)]).

    The first list holds the ``image:`` of the block-style services of the ``services:`` block of a
    YAML file; the second the services written as an inline mapping (``name: {image: ...}``),
    whose image is not read.
    """
    result, inline = [], []
    in_services, base, child, service = False, 0, None, None
    for number, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if in_services and indent <= base:
            in_services, service = False, None
        if not in_services:
            match = SERVICES_KEY.match(line)
            if match:
                in_services, base, child = True, indent, None
            continue
        if child is None:
            child = indent
        if indent == child:
            match = SERVICE_KEY.match(line)
            service = match["name"] if match else None
            flow = INLINE_SERVICE.match(line)
            if flow:
                inline.append((flow["name"], number, flow["rest"].strip()))
        elif service is not None:
            for _, reference in image_values([line]):
                result.append((service, number, reference))
    return result, inline


def definition_literal(lines, first):
    """(reference, line number) of the recognised literal of the assignment at ``first``, or (None, first)."""
    one_line = ONE_LINE.match(lines[first - 1])
    if one_line:
        return one_line["ref"], first
    if PAREN_OPEN.match(lines[first - 1]):
        literal = LITERAL_LINE.match(lines[first]) if first < len(lines) else None
        closed = first + 1 < len(lines) and lines[first + 1].rstrip() == ")"
        if literal and closed:
            return literal["ref"], first + 1
    return None, first


def _definition_findings(root, compose):
    """Rule 1: the test image definition, its form and its value."""
    path = root / DEFINITION
    if not path.is_file():
        return [(DEFINITION, 1, "test image definition missing", "<missing>")]
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [n for n, line in enumerate(lines, start=1) if DEFINITION_START.match(line)]
    if not starts:
        return [(DEFINITION, 1, "test image definition missing", "POSTGRES_IMAGE")]
    findings = [
        (DEFINITION, n, "second POSTGRES_IMAGE assignment", lines[n - 1].strip()) for n in starts[1:]
    ]
    first = starts[0]
    unrecognised = "test image definition not in a recognised form"
    reference, literal_line = definition_literal(lines, first)
    if reference is None:
        return findings + [(DEFINITION, first, unrecognised, lines[first - 1].strip())]
    if not PINNED.search(reference):
        return findings + [(DEFINITION, literal_line, "test image without @sha256 digest", reference or "<empty>")]
    if compose is None:  # reported once, by image_findings
        return findings
    postgres = [(n, ref) for name, n, ref in compose if name == "postgres"]
    if not postgres:
        return findings + [(COMPOSE, 1, "no postgres service image to compare the test image with", reference)]
    if reference not in {ref for _, ref in postgres}:
        message = f"test image differs from {COMPOSE}:{postgres[0][0]}"
        findings.append((DEFINITION, literal_line, message, reference))
    return findings


def _rebinding_findings(path, text, known):
    """Rebindings of ``POSTGRES_IMAGE`` and aliased ``PostgresContainer`` imports, read with ``ast``.

    ``known`` holds the lines that are findings or the recognised definition already. Standard
    library only: the file is parsed, never imported.
    """
    is_definition = path == DEFINITION
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        if is_definition:
            return [(path, error.lineno or 1, "test image definition file does not parse", "<syntax error>")]
        return []
    lines = text.splitlines()
    message = "second POSTGRES_IMAGE assignment" if is_definition else f"POSTGRES_IMAGE bound outside {DEFINITION}"
    found = {}

    def add(number, text_message):
        if number not in known and number not in found:
            found[number] = (path, number, text_message, lines[number - 1].strip())

    for node in ast.walk(tree):
        number = getattr(node, "lineno", None)
        if number is None:
            continue
        if isinstance(node, ast.Name) and node.id == "POSTGRES_IMAGE" and not isinstance(node.ctx, ast.Load):
            add(number, message)
        elif isinstance(node, ast.Attribute) and node.attr == "POSTGRES_IMAGE" and not isinstance(node.ctx, ast.Load):
            add(number, message)
        elif isinstance(node, ast.alias):
            if node.asname == "POSTGRES_IMAGE" or (is_definition and node.asname is None and node.name == "POSTGRES_IMAGE"):
                add(number, message)
            elif node.name.split(".")[-1] == "PostgresContainer" and node.asname:
                add(number, "PostgresContainer imported under an alias")
        elif isinstance(node, (ast.Global, ast.Nonlocal)) and "POSTGRES_IMAGE" in node.names:
            add(number, message)
        elif isinstance(node, (ast.ExceptHandler, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.MatchAs, ast.MatchStar)) and node.name == "POSTGRES_IMAGE":
            add(number, message)
        elif isinstance(node, ast.MatchMapping) and node.rest == "POSTGRES_IMAGE":
            add(number, message)
        elif isinstance(node, ast.arg) and not is_definition and node.arg == "POSTGRES_IMAGE":
            add(number, message)
        elif (
            is_definition
            and isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"globals", "locals", "vars", "setattr"}
        ):
            add(number, "namespace access in the test image definition")
    return list(found.values())


def image_findings(root, workflows):
    """Rules 1-4 of the test image rules: definition, CI services, stray image literals, container calls."""
    findings = []
    compose_path = root / COMPOSE
    compose = None
    if compose_path.is_file():
        images, inline = service_images(compose_path.read_text(encoding="utf-8").splitlines())
        compose = [(name, n, ref) for name, n, ref in images if "$" not in ref]
        findings += [(COMPOSE, n, INLINE_MESSAGE, text) for _, n, text in inline]
    else:
        findings.append((COMPOSE, 1, "deployment Compose file missing", "<missing>"))
    findings += _definition_findings(root, compose)
    by_repository = {}
    for _, n, ref in compose or []:
        by_repository.setdefault(image_repository(ref), []).append((n, ref))
    for path in workflows:
        lines = (root / path).read_text(encoding="utf-8").splitlines()
        images, inline = service_images(lines)
        findings += [(path, n, INLINE_MESSAGE, text) for _, n, text in inline]
        for _, number, ref in images:
            deployed = by_repository.get(image_repository(ref))
            if deployed is None:
                findings.append((path, number, f"CI service image has no counterpart in {COMPOSE}", ref))
            elif ref not in {r for _, r in deployed}:
                message = f"CI service image differs from {COMPOSE}:{deployed[0][0]}"
                findings.append((path, number, message, ref))
    literal = None
    if by_repository:
        literal = re.compile(
            r"""(?P<q>["'])(?P<ref>(?:[\w.:-]+/)*(?:%s):[A-Za-z0-9][^"'\s]*)(?P=q)"""
            % "|".join(re.escape(r) for r in by_repository)
        )
    for path in python_sources(root):
        text = (root / path).read_text(encoding="utf-8")
        skip = set()
        if path == DEFINITION:
            lines = text.splitlines()
            starts = [n for n, line in enumerate(lines, start=1) if DEFINITION_START.match(line)]
            reference, literal_line = definition_literal(lines, starts[0]) if starts else (None, 0)
            if reference is None:  # missing or unrecognised: already a finding
                continue
            skip = {literal_line, *starts}  # the later assignment lines are findings already
        reported = set()
        for number, line in enumerate(text.splitlines(), start=1):
            if number in skip or literal is None:
                continue
            for match in literal.finditer(line):
                message = (
                    f"second image literal in {DEFINITION}"
                    if path == DEFINITION
                    else f"image literal outside {DEFINITION}"
                )
                findings.append((path, number, message, match["ref"]))
                reported.add(number)
        if path == DEFINITION:
            known = {*skip, *range(starts[0], literal_line + 1), *reported}
            findings += _rebinding_findings(path, text, known)
        else:
            lines = text.splitlines()
            starts = [n for n, line in enumerate(lines, start=1) if DEFINITION_START.match(line)]
            starts = [n for n in starts if n not in reported]  # a literal line is reported already
            findings += [
                (path, n, f"POSTGRES_IMAGE bound outside {DEFINITION}", lines[n - 1].strip()) for n in starts
            ]
            findings += _rebinding_findings(path, text, {*starts, *reported})
        for call in CONTAINER_CALL.finditer(text):
            number = text.count("\n", 0, call.start()) + 1
            argument = text[call.end():]
            if number in reported or CONTAINER_ARGUMENT.match(argument):
                continue
            first_argument = re.split(r"[,)]", argument, maxsplit=1)[0].strip() or "<none>"
            findings.append((path, number, "PostgresContainer without POSTGRES_IMAGE as its image", first_argument))
    return findings


def python_sources(root):
    """Repository-relative paths of the backend/**/*.py files, ``.venv/`` excluded."""
    if root == REPO_ROOT:
        paths = git_paths()
    else:
        paths = [p.relative_to(root).as_posix() for p in sorted(root.rglob("*.py"))]
    return [
        p
        for p in paths
        if p.startswith("backend/") and p.endswith(".py") and ".venv/" not in p and (root / p).is_file()
    ]


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
    if args.root is not None and args.paths:
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
    if args.root is not None or not args.paths:
        root = Path(args.root).resolve() if args.root else REPO_ROOT
        if args.root is not None:
            if not args.root or not root.is_dir():
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
