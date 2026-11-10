"""TASK-174: object-store credential rule (SR-040 AC 2, TS-014 TC-014.2)."""

import base64
import os
import subprocess
import sys

import pytest

from app.core.object_store_credentials import check, check_sse_key

GOOD_ACCESS = "a1b2c3d4e5f6a1b2c3d4e5f6"
GOOD_SECRET = "Zx9Qw3Lm7Rt2Vb5Nk8Hy4Jd6Fg1Sa0Pc"
FIELD_KEY = base64.urlsafe_b64encode(bytes(range(32))).decode()
SSE_KEY = base64.urlsafe_b64encode(bytes(range(1, 33))).decode()
RETIRED_KEY = base64.urlsafe_b64encode(bytes(range(2, 34))).decode()
GOOD_ENV = {
    "OBJECT_STORE_ACCESS_KEY": GOOD_ACCESS,
    "OBJECT_STORE_SECRET_KEY": GOOD_SECRET,
    "OBJECT_STORE_SSE_KEY": SSE_KEY,
    "AT_REST_ENCRYPTION_KEY": FIELD_KEY,
}
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
    env = {k: v for k, v in os.environ.items() if k not in GOOD_ENV}
    env.update({k: v for k, v in env_extra.items() if k not in unset})
    return subprocess.run(
        [sys.executable, "-m", "app.core.object_store_credentials"],
        capture_output=True,
        text=True,
        env=env,
    )


def test_main_exits_0_silently_for_good_keys() -> None:
    r = _run(GOOD_ENV)
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
    r = _run({**GOOD_ENV, **extra}, tuple(unset))
    assert r.returncode == 1
    assert setting in r.stderr and r.stdout == ""
    for value in (access, secret):
        if value and value not in (GOOD_ACCESS, GOOD_SECRET):
            assert value not in r.stderr


# TASK-196, SR-041 AC 5: the store's SSE key is its own setting, distinct from the field keys
def test_distinct_sse_key_passes() -> None:
    assert check_sse_key(SSE_KEY, FIELD_KEY, None) == []
    assert check_sse_key(SSE_KEY, FIELD_KEY, f"old:{RETIRED_KEY}") == []


@pytest.mark.parametrize("value, reason", [(None, "not set"), ("", "empty"), ("  ", "empty")])
def test_unset_or_empty_sse_key_is_refused(value: str | None, reason: str) -> None:
    out = check_sse_key(value, FIELD_KEY, None)
    assert out and all("OBJECT_STORE_SSE_KEY" in m for m in out) and reason in out[0]


@pytest.mark.parametrize("value", ["changeme", "change-me", "CHANGE-ME-TO-ANYTHING", "minioadmin"])
def test_placeholder_sse_key_is_refused_without_the_value(value: str) -> None:
    out = check_sse_key(value, FIELD_KEY, None)
    assert out and all("OBJECT_STORE_SSE_KEY" in m and value not in m for m in out)


@pytest.mark.parametrize("size", [1, 31, 33, 48])
def test_sse_key_of_the_wrong_length_is_refused(size: int) -> None:
    key = base64.urlsafe_b64encode(bytes(range(size))).decode()
    out = check_sse_key(key, FIELD_KEY, None)
    assert len(out) == 1 and "OBJECT_STORE_SSE_KEY" in out[0] and key not in out[0]


def test_sse_key_that_is_not_base64_is_refused() -> None:
    out = check_sse_key("not base64 !!!", FIELD_KEY, None)
    assert out and all("OBJECT_STORE_SSE_KEY" in m for m in out)


def test_sse_key_equal_to_the_field_key_is_refused_naming_both_settings() -> None:
    out = check_sse_key(FIELD_KEY, FIELD_KEY, None)
    assert len(out) == 1
    assert "OBJECT_STORE_SSE_KEY" in out[0] and "AT_REST_ENCRYPTION_KEY" in out[0]
    assert FIELD_KEY not in out[0]


def test_equality_is_compared_as_decoded_bytes_not_text() -> None:
    raw = bytes([0xFB, 0xEF, 0xBE] * 10 + [1, 2])  # encodes with "-"/"_" or "+"/"/"
    url_safe, standard = base64.urlsafe_b64encode(raw).decode(), base64.b64encode(raw).decode()
    assert url_safe != standard
    assert check_sse_key(standard, url_safe, None)  # same bytes, other alphabet
    assert check_sse_key(f" {url_safe} ", url_safe, None)  # surrounding whitespace


def test_sse_key_equal_to_a_retired_field_key_is_refused() -> None:
    out = check_sse_key(RETIRED_KEY, FIELD_KEY, f"older:{SSE_KEY},k0:{RETIRED_KEY}")
    assert len(out) == 1 and "AT_REST_ENCRYPTION_RETIRED_KEYS entry 2" in out[0]
    assert RETIRED_KEY not in out[0]


def test_the_field_key_must_be_given_to_the_preflight() -> None:
    out = check_sse_key(SSE_KEY, None, None)
    assert out == ["AT_REST_ENCRYPTION_KEY is not set, so the two keys cannot be compared"]


@pytest.mark.parametrize(
    "changes, setting",
    [
        ({"OBJECT_STORE_SSE_KEY": None}, "OBJECT_STORE_SSE_KEY"),
        ({"OBJECT_STORE_SSE_KEY": ""}, "OBJECT_STORE_SSE_KEY"),
        ({"OBJECT_STORE_SSE_KEY": "changeme"}, "OBJECT_STORE_SSE_KEY"),
        ({"OBJECT_STORE_SSE_KEY": base64.b64encode(bytes(31)).decode()}, "OBJECT_STORE_SSE_KEY"),
        ({"OBJECT_STORE_SSE_KEY": FIELD_KEY}, "same key as AT_REST_ENCRYPTION_KEY"),
        (
            {"AT_REST_ENCRYPTION_RETIRED_KEYS": f"k0:{SSE_KEY}"},
            "same key as AT_REST_ENCRYPTION_RETIRED_KEYS",
        ),
    ],
)
def test_main_refuses_a_bad_sse_key_naming_the_setting_and_never_the_value(
    changes: dict[str, str | None], setting: str
) -> None:
    env = {**GOOD_ENV, **{k: v for k, v in changes.items() if v is not None}}
    unset = tuple(k for k, v in changes.items() if v is None)
    r = _run(env, unset)
    assert r.returncode == 1 and r.stdout == ""
    assert setting in r.stderr and "OBJECT_STORE_SSE_KEY" in r.stderr
    for secret in (FIELD_KEY, SSE_KEY, RETIRED_KEY):
        assert secret not in r.stderr
