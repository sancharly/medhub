"""TASK-174: object-store credential rule (SR-040 AC 2, TS-014 TC-014.2)."""

import os
import subprocess
import sys

import pytest

from app.core.object_store_credentials import check

GOOD_ACCESS = "a1b2c3d4e5f6a1b2c3d4e5f6"
GOOD_SECRET = "Zx9Qw3Lm7Rt2Vb5Nk8Hy4Jd6Fg1Sa0Pc"
DEFAULTS = ["minioadmin", "changeme", "admin", "password", "secret"]


def test_good_keys_pass() -> None:
    assert check(GOOD_ACCESS, GOOD_SECRET) == []


def test_short_access_key_is_allowed_if_not_default() -> None:
    assert check("ab", GOOD_SECRET) == []


@pytest.mark.parametrize("value, reason", [(None, "not set"), ("", "empty"), ("   ", "empty")])
def test_unset_or_empty_access_key(value: str | None, reason: str) -> None:
    out = check(value, GOOD_SECRET)
    assert len(out) == 1 and "OBJECT_STORE_ACCESS_KEY" in out[0] and reason in out[0]


@pytest.mark.parametrize("value, reason", [(None, "not set"), ("", "empty"), ("\t" * 16, "empty")])
def test_unset_or_empty_secret_key(value: str | None, reason: str) -> None:
    out = check(GOOD_ACCESS, value)
    assert len(out) == 1 and "OBJECT_STORE_SECRET_KEY" in out[0] and reason in out[0]


@pytest.mark.parametrize("value", DEFAULTS + ["MinioAdmin", "ADMIN"])
def test_default_access_key_rejected_whatever_its_length(value: str) -> None:
    out = check(value, GOOD_SECRET)
    assert len(out) == 1 and "OBJECT_STORE_ACCESS_KEY" in out[0] and "default" in out[0]


@pytest.mark.parametrize("value", DEFAULTS + ["ChangeMe", "PASSWORD"])
def test_default_secret_key_rejected(value: str) -> None:
    out = check(GOOD_ACCESS, value)
    assert any("OBJECT_STORE_SECRET_KEY" in m and "default" in m for m in out)


def test_padded_default_is_still_a_default() -> None:
    assert check(" minioadmin ", GOOD_SECRET)
    assert check(GOOD_ACCESS, " changeme" + " " * 10)


def test_secret_shorter_than_16_rejected_and_16_accepted() -> None:
    short = check(GOOD_ACCESS, "x" * 15)
    assert len(short) == 1 and "OBJECT_STORE_SECRET_KEY" in short[0] and "16" in short[0]
    assert check(GOOD_ACCESS, "x" * 16) == []


def test_both_keys_bad_report_both_settings() -> None:
    out = " ".join(check("", None))
    assert "OBJECT_STORE_ACCESS_KEY" in out and "OBJECT_STORE_SECRET_KEY" in out


def _run(
    env_extra: dict[str, str], unset: tuple[str, ...] = ()
) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in unset}
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "app.core.object_store_credentials"],
        capture_output=True,
        text=True,
        env=env,
    )


def test_main_exits_0_silently_for_good_keys() -> None:
    r = _run({"OBJECT_STORE_ACCESS_KEY": GOOD_ACCESS, "OBJECT_STORE_SECRET_KEY": GOOD_SECRET})
    assert r.returncode == 0 and r.stdout == "" and r.stderr == ""


@pytest.mark.parametrize(
    "access, secret, setting",
    [
        (None, GOOD_SECRET, "OBJECT_STORE_ACCESS_KEY"),
        ("", GOOD_SECRET, "OBJECT_STORE_ACCESS_KEY"),
        ("minioadmin", GOOD_SECRET, "OBJECT_STORE_ACCESS_KEY"),
        (GOOD_ACCESS, None, "OBJECT_STORE_SECRET_KEY"),
        (GOOD_ACCESS, "", "OBJECT_STORE_SECRET_KEY"),
        (GOOD_ACCESS, "changeme", "OBJECT_STORE_SECRET_KEY"),
        (GOOD_ACCESS, "short-secret-1", "OBJECT_STORE_SECRET_KEY"),
    ],
)
def test_main_exits_1_naming_the_setting_and_never_the_value(
    access: str | None, secret: str | None, setting: str
) -> None:
    extra, unset = {}, []
    for name, value in (("OBJECT_STORE_ACCESS_KEY", access), ("OBJECT_STORE_SECRET_KEY", secret)):
        if value is None:
            unset.append(name)
        else:
            extra[name] = value
    r = _run(extra, tuple(unset))
    assert r.returncode == 1
    assert setting in r.stderr and r.stdout == ""
    for value in (access, secret):
        if value and value not in (GOOD_ACCESS, GOOD_SECRET):
            assert value not in r.stderr
