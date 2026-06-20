"""Static guard: no raw SQL string interpolation anywhere in app/ (TASK-012, SR-031.1)."""

import ast
import re
from pathlib import Path

# Scan the entire app/ package — SR-031.1 forbids string-concatenated SQL everywhere,
# not only in repositories.
APP_DIR = Path(__file__).parent.parent.parent / "app"


def _python_files() -> list[Path]:
    return list(APP_DIR.rglob("*.py"))


def test_no_fstring_sql():
    """No f-strings used in repository files (risk of SQL injection)."""
    for path in _python_files():
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                # f-string found — check if it appears near SQL keywords
                # Extract the surrounding source line for context
                lineno = node.lineno
                lines = source.splitlines()
                line = lines[lineno - 1] if lineno <= len(lines) else ""
                sql_keywords = re.compile(
                    r"\b(SELECT|INSERT|UPDATE|DELETE|WHERE|FROM|JOIN)\b", re.IGNORECASE
                )
                if sql_keywords.search(line):
                    pytest.fail(
                        f"f-string with SQL keyword found in {path}:{lineno}: {line.strip()}"
                    )


def test_no_string_concat_sql():
    """No string concatenation with SQL keywords in repository files."""
    sql_pattern = re.compile(
        r'["\'][^"\']*\b(SELECT|INSERT|UPDATE|DELETE|WHERE|FROM)\b[^"\']*["\']'
        r"\s*\+",
        re.IGNORECASE,
    )
    for path in _python_files():
        source = path.read_text()
        for i, line in enumerate(source.splitlines(), 1):
            if sql_pattern.search(line):
                pytest.fail(f"String-concatenated SQL found in {path}:{i}: {line.strip()}")


def test_no_text_with_variable_interpolation():
    """No sqlalchemy text() with % or .format() interpolation."""
    pattern = re.compile(r"text\([^)]*%[^)]*\)|text\([^)]*\.format\(")
    for path in _python_files():
        source = path.read_text()
        if pattern.search(source):
            pytest.fail(f"text() with variable interpolation found in {path}")


import pytest  # noqa: E402 — imported last to avoid circular in comprehension
