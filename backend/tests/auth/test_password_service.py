"""TASK-020: PasswordService tests."""

from __future__ import annotations

import datetime
import uuid
from unittest.mock import MagicMock

import pytest

from app.auth.password import (
    HISTORY_DEPTH,
    MAX_AGE_DAYS,
    PasswordPolicyError,
    PasswordPolicyViolation,
    PasswordService,
    get_dummy_hash,
)
from app.db.models.account import Account, AccountStatus, UserType


def _make_account(
    email: str = "user@example.com",
    password_changed_at: datetime.datetime | None = None,
) -> Account:
    acct = Account(
        id=uuid.uuid4(),
        email=email,
        user_type=UserType.PATIENT,
        status=AccountStatus.INACTIVE,
        password_changed_at=password_changed_at,
    )
    return acct


VALID_PW = "Str0ng!Pass#99"  # meets all requirements


# --- hash / verify ---

def test_hash_produces_argon2id_prefix() -> None:
    svc = PasswordService()
    h = svc.hash(VALID_PW)
    assert h.startswith("$argon2id$")


def test_verify_correct_password() -> None:
    svc = PasswordService()
    h = svc.hash(VALID_PW)
    assert svc.verify(h, VALID_PW) is True


def test_verify_wrong_password() -> None:
    svc = PasswordService()
    h = svc.hash(VALID_PW)
    assert svc.verify(h, "WrongP@ssword1") is False


def test_verify_never_raises_on_bad_hash() -> None:
    svc = PasswordService()
    # Should return False, not raise
    assert svc.verify("not-a-valid-hash", VALID_PW) is False


def test_check_needs_rehash_fresh_hash_false() -> None:
    svc = PasswordService()
    h = svc.hash(VALID_PW)
    assert svc.check_needs_rehash(h) is False


# --- policy: length ---

def test_policy_rejects_short_password() -> None:
    svc = PasswordService()
    acct = _make_account()
    with pytest.raises(PasswordPolicyError) as exc_info:
        svc.validate_policy(acct, "Sh0rt!1")
    assert PasswordPolicyViolation.TOO_SHORT in exc_info.value.violations


# --- policy: character classes ---

def test_policy_rejects_missing_uppercase() -> None:
    svc = PasswordService()
    acct = _make_account()
    with pytest.raises(PasswordPolicyError) as exc_info:
        svc.validate_policy(acct, "str0ng!pass#99")
    assert PasswordPolicyViolation.MISSING_UPPERCASE in exc_info.value.violations


def test_policy_rejects_missing_lowercase() -> None:
    svc = PasswordService()
    acct = _make_account()
    with pytest.raises(PasswordPolicyError) as exc_info:
        svc.validate_policy(acct, "STR0NG!PASS#99")
    assert PasswordPolicyViolation.MISSING_LOWERCASE in exc_info.value.violations


def test_policy_rejects_missing_digit() -> None:
    svc = PasswordService()
    acct = _make_account()
    with pytest.raises(PasswordPolicyError) as exc_info:
        svc.validate_policy(acct, "Str!ongPass#XX")
    assert PasswordPolicyViolation.MISSING_DIGIT in exc_info.value.violations


def test_policy_rejects_missing_special() -> None:
    svc = PasswordService()
    acct = _make_account()
    with pytest.raises(PasswordPolicyError) as exc_info:
        svc.validate_policy(acct, "Str0ngPassXX99")
    assert PasswordPolicyViolation.MISSING_SPECIAL in exc_info.value.violations


# --- policy: email substring ---

def test_policy_rejects_email_as_substring() -> None:
    svc = PasswordService()
    acct = _make_account(email="alice@example.com")
    with pytest.raises(PasswordPolicyError) as exc_info:
        svc.validate_policy(acct, "Alice@example.com1!")
    assert PasswordPolicyViolation.CONTAINS_EMAIL in exc_info.value.violations


def test_policy_rejects_email_case_insensitive() -> None:
    svc = PasswordService()
    acct = _make_account(email="ALICE@EXAMPLE.COM")
    with pytest.raises(PasswordPolicyError) as exc_info:
        svc.validate_policy(acct, "alice@example.com1!")
    assert PasswordPolicyViolation.CONTAINS_EMAIL in exc_info.value.violations


# --- policy: multiple violations ---

def test_policy_collects_multiple_violations() -> None:
    svc = PasswordService()
    acct = _make_account()
    with pytest.raises(PasswordPolicyError) as exc_info:
        svc.validate_policy(acct, "short")
    violations = exc_info.value.violations
    assert PasswordPolicyViolation.TOO_SHORT in violations
    assert len(violations) >= 2  # at least short + missing char class(es)


# --- policy: history reuse ---

def test_policy_rejects_history_reuse() -> None:
    svc_no_repo = PasswordService()
    old_hash = svc_no_repo.hash(VALID_PW)

    from app.db.models.password_history import PasswordHistory
    mock_entry = MagicMock(spec=PasswordHistory)
    mock_entry.password_hash = old_hash

    mock_repo = MagicMock()
    mock_repo.list_recent.return_value = [mock_entry]

    svc = PasswordService(history_repo=mock_repo)
    acct = _make_account()

    with pytest.raises(PasswordPolicyError) as exc_info:
        svc.validate_policy(acct, VALID_PW)
    assert PasswordPolicyViolation.HISTORY_REUSE in exc_info.value.violations
    mock_repo.list_recent.assert_called_once_with(acct.id, HISTORY_DEPTH)


def test_policy_passes_when_no_history_repo() -> None:
    svc = PasswordService(history_repo=None)
    acct = _make_account()
    svc.validate_policy(acct, VALID_PW)  # should not raise


# --- is_expired / expires_within ---

def test_is_expired_false_when_no_changed_at() -> None:
    svc = PasswordService()
    acct = _make_account(password_changed_at=None)
    assert svc.is_expired(acct) is False


def test_is_expired_true_after_max_age() -> None:
    svc = PasswordService()
    old = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=MAX_AGE_DAYS + 1)
    acct = _make_account(password_changed_at=old)
    assert svc.is_expired(acct) is True


def test_is_expired_false_within_max_age() -> None:
    svc = PasswordService()
    recent = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=MAX_AGE_DAYS - 1)
    acct = _make_account(password_changed_at=recent)
    assert svc.is_expired(acct) is False


def test_expires_within_true_when_close() -> None:
    svc = PasswordService()
    almost = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=MAX_AGE_DAYS - 5)
    acct = _make_account(password_changed_at=almost)
    assert svc.expires_within(acct, 14) is True


def test_expires_within_false_when_far() -> None:
    svc = PasswordService()
    recent = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=10)
    acct = _make_account(password_changed_at=recent)
    assert svc.expires_within(acct, 14) is False


# --- dummy hash ---

def test_dummy_hash_is_argon2id() -> None:
    h = get_dummy_hash()
    assert h.startswith("$argon2id$")


def test_dummy_hash_never_matches_user_input() -> None:
    svc = PasswordService()
    h = get_dummy_hash()
    # Verify that typical passwords don't match the dummy hash
    assert svc.verify(h, VALID_PW) is False


def test_dummy_hash_is_precomputed_same_value() -> None:
    """get_dummy_hash() must return the same string on every call (pre-computed, not re-hashed)."""
    h1 = get_dummy_hash()
    h2 = get_dummy_hash()
    assert h1 == h2
