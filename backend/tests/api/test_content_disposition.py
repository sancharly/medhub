"""TASK-204: ``content_disposition`` helper (SR-013 AC 3; AC-1, AC-2 of TASK-204)."""

from __future__ import annotations

import re
import unicodedata
from email.message import Message
from email.utils import collapse_rfc2231_value
from pathlib import Path
from urllib.parse import unquote

import pytest

from app.api.content_disposition import content_disposition

_BACKEND = Path(__file__).resolve().parents[2]

_TABLE = [
    (
        "résumé 患者 #1.txt",
        "resume __ #1.txt",
        "r%C3%A9sum%C3%A9%20%E6%82%A3%E8%80%85%20%231.txt",
    ),
    ("report’s summary.pdf", "report_s summary.pdf", "report%E2%80%99s%20summary.pdf"),
    ('a"b\\c.pdf', "a_b_c.pdf", "a%22b%5Cc.pdf"),
    ("x\r\nX-Injected: 1.txt", "x__X-Injected: 1.txt", "x__X-Injected%3A%201.txt"),
    ("患者.dcm", "__.dcm", "%E6%82%A3%E8%80%85.dcm"),
    ("scan.dcm", "scan.dcm", "scan.dcm"),
]


@pytest.mark.parametrize(("name", "fallback", "encoded"), _TABLE)
def test_worked_examples(name, fallback, encoded):
    """AC-1: ASCII fallback plus RFC 5987 filename*."""
    assert content_disposition(name) == (
        f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{encoded}"
    )


def _expected_roundtrip(name: str) -> str:
    return "".join("_" if unicodedata.category(c) in ("Cc", "Cs") else c for c in name)


@pytest.mark.parametrize("name", [t[0] for t in _TABLE] + ["tab\there.txt", "€ – “q”.pdf"])
def test_round_trip_returns_original_name(name):
    """AC-1: the stdlib parser recovers the original name (controls become ``_``)."""
    msg = Message()
    msg["Content-Disposition"] = content_disposition(name)
    params = dict(msg.get_params(header="content-disposition"))
    assert collapse_rfc2231_value(params["filename"]) == _expected_roundtrip(name)


_SAMPLE = [
    "\x00\x01\x1f\x7f\x80\x9f",  # Cc
    "a\ud800b\udfffc",  # lone surrogates (Cs)
    "a​b‮c﻿",  # Cf
    "a b c",  # Zl, Zp
    "😀𝔘𠀀.txt",  # astral plane
    "\r\n\r\nSet-Cookie: x=1",
    "ü" * 300,
]


@pytest.mark.parametrize("name", _SAMPLE)
def test_value_is_pure_ascii_without_line_breaks(name):
    """AC-2: latin-1 safe (indeed ASCII), no CR/LF, never raises."""
    value = content_disposition(name)
    value.encode("latin-1")
    value.encode("ascii")
    assert "\r" not in value and "\n" not in value
    assert len(re.findall(r"filename=", value)) == 1
    assert len(re.findall(r"filename\*=", value)) == 1


def test_crlf_replaced_so_no_header_can_be_injected():
    """AC-2: CR and LF become ``_`` in both parameters."""
    value = content_disposition("x\r\nX-Injected: 1.txt")
    assert "x__X-Injected" in value
    assert "%0D" not in value and "%0A" not in value


@pytest.mark.parametrize("name", ["", "...", " . "])
def test_empty_or_dots_use_download(name):
    assert content_disposition(name).startswith('attachment; filename="download";')


def test_disposition_argument():
    assert content_disposition("a.pdf", "inline").startswith("inline; ")


def test_content_disposition_is_built_only_by_the_helper():
    """AC-2: only the helper writes the header; others may only call it."""
    helper = _BACKEND / "app" / "api" / "content_disposition.py"
    offenders = []
    for root in (_BACKEND / "app", _BACKEND / "modules"):
        for path in root.rglob("*.py"):
            if path == helper or ".venv" in path.parts or "tests" in path.parts:
                continue
            for n, line in enumerate(path.read_text().splitlines(), 1):
                if "content-disposition" in line.lower() and not re.search(
                    r"""["']Content-Disposition["']\s*:\s*content_disposition\(""", line
                ):
                    offenders.append(f"{path.relative_to(_BACKEND)}:{n}")
    assert offenders == []


# --- TASK-206 slice B (PRB-069; TASK-204 QA finding 3) ---


def _parts(value: str) -> tuple[str, str]:
    m = re.fullmatch(r"attachment; filename=\"(.*)\"; filename\*=UTF-8''(.*)", value)
    assert m, value
    return m.group(1), unquote(m.group(2))


@pytest.mark.parametrize(
    "name",
    ["\ufdfa" * 255 + ".pdf", "患" * 10000 + ".txt", "😀" * 10000 + ".dcm", "a" * 10000 + ".pdf"],
    ids=["u-fdfa", "cjk", "emoji", "ascii"],
)
def test_value_is_bounded_for_any_name(name):
    value = content_disposition(name)
    assert len(value.encode("ascii")) <= 1024
    fallback, star = _parts(value)
    assert fallback.endswith(name[-4:]) and star.endswith(name[-4:])


def test_fallback_cut_to_150_keeping_extension():
    fallback, _ = _parts(content_disposition("a" * 400 + ".pdf"))
    assert len(fallback) == 150
    assert fallback.endswith(".pdf")


def test_fallback_without_a_short_extension_is_cut_at_150():
    fallback, _ = _parts(content_disposition("a" * 400 + "." + "b" * 30))
    assert len(fallback) == 150


def test_filename_star_cut_at_character_boundary():
    _, star = _parts(content_disposition("患" * 300 + ".txt"))
    encoded = star.encode("utf-8")
    assert len(encoded) <= 255
    encoded.decode("utf-8")  # valid UTF-8, no split character
    assert star.endswith(".txt") and star.startswith("患")


def test_name_within_the_bound_is_not_cut():
    name = "患" * 83 + "ab.txt"  # 255 bytes
    assert _parts(content_disposition(name))[1] == name


def test_bidi_controls_mapped_to_underscore():
    controls = "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
    value = content_disposition(f"a{controls}b.txt")
    _, star = _parts(value)
    assert star == "a" + "_" * len(controls) + "b.txt"
    assert "%E2%80%AE" not in value and "%D8%9C" not in value


def test_zero_width_joiner_kept():
    name = "👨\u200d👩.txt"
    assert _parts(content_disposition(name))[1] == name
