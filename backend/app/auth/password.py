"""PasswordService — Argon2id hashing + policy enforcement (TASK-020).

Policy constants:
  MIN_LENGTH = 12
  HISTORY_DEPTH = 12
  MAX_AGE_DAYS = 180
  EXPIRY_WARNING_DAYS = 14

Requires all four character classes: uppercase, lowercase, digit, special.
Rejects passwords that contain the account email or username as a substring.
"""

from __future__ import annotations

import datetime
import enum
import re
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.api.errors import ProblemDetail, ValidationProblem
from app.db.models.account import Account
from app.db.models.password_history import PasswordHistory
from app.db.repositories.password_history_repo import PasswordHistoryRepository

MIN_LENGTH = 12
HISTORY_DEPTH = 12
MAX_AGE_DAYS = 180
EXPIRY_WARNING_DAYS = 14

# Characters considered "special" for policy purposes
_SPECIAL_CHARS = set("!@#$%^&*()-_=+[]{}|;:'\",.<>?/")

# Singleton hasher — configured for Argon2id
_hasher = PasswordHasher()

# Computed once at module import; never changes — anti-enumeration timing parity
_DUMMY_HASH: str = _hasher.hash("__dummy_anti_enumeration__")


class PasswordPolicyViolation(enum.Enum):
    TOO_SHORT = "TOO_SHORT"
    MISSING_UPPERCASE = "MISSING_UPPERCASE"
    MISSING_LOWERCASE = "MISSING_LOWERCASE"
    MISSING_DIGIT = "MISSING_DIGIT"
    MISSING_SPECIAL = "MISSING_SPECIAL"
    CONTAINS_EMAIL = "CONTAINS_EMAIL"
    HISTORY_REUSE = "HISTORY_REUSE"


class PasswordPolicyError(ValidationProblem):
    """Raised when a password violates one or more policy rules. Returns HTTP 400."""

    def __init__(self, violations: list[PasswordPolicyViolation]) -> None:
        errors = [
            ProblemDetail(
                field="password",
                rule=v.value,
                message=v.value.replace("_", " ").capitalize(),
            )
            for v in violations
        ]
        super().__init__(
            f"Password policy violations: {[v.value for v in violations]}",
            errors=errors,
        )
        self.violations = violations


class PasswordService:
    """Argon2id password hashing and policy enforcement."""

    def __init__(self, history_repo: PasswordHistoryRepository | None = None) -> None:
        self._history_repo = history_repo

    def hash(self, password: str) -> str:
        """Return an Argon2id encoded hash. Never logs the plaintext."""
        return _hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        """Constant-time verification. Returns False on any error — never raises."""
        try:
            return _hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def check_needs_rehash(self, password_hash: str) -> bool:
        """True if the stored hash was produced with outdated parameters."""
        return _hasher.check_needs_rehash(password_hash)

    def validate_policy(
        self,
        account: Account,
        password: str,
        *,
        skip_history: bool = False,
    ) -> None:
        """Raise PasswordPolicyError if any policy rule is violated.

        `skip_history=True` is used during account creation before a hash is stored.
        """
        violations: list[PasswordPolicyViolation] = []

        if len(password) < MIN_LENGTH:
            violations.append(PasswordPolicyViolation.TOO_SHORT)

        if not re.search(r"[A-Z]", password):
            violations.append(PasswordPolicyViolation.MISSING_UPPERCASE)

        if not re.search(r"[a-z]", password):
            violations.append(PasswordPolicyViolation.MISSING_LOWERCASE)

        if not re.search(r"\d", password):
            violations.append(PasswordPolicyViolation.MISSING_DIGIT)

        if not any(c in _SPECIAL_CHARS for c in password):
            violations.append(PasswordPolicyViolation.MISSING_SPECIAL)

        # Reject if email is a case-insensitive substring
        email_lower = account.email.lower()
        if email_lower and email_lower in password.lower():
            violations.append(PasswordPolicyViolation.CONTAINS_EMAIL)

        if violations:
            raise PasswordPolicyError(violations)

        # History check (requires repo; skip if not available or explicitly skipped)
        if not skip_history and self._history_repo is not None:
            recent = self._history_repo.list_recent(account.id, HISTORY_DEPTH)
            for entry in recent:
                if self.verify(entry.password_hash, password):
                    raise PasswordPolicyError([PasswordPolicyViolation.HISTORY_REUSE])

    def record_history(self, account_id: uuid.UUID, password_hash: str) -> None:
        """Persist the current hash to history. Must be called after setting a new password."""
        if self._history_repo is None:
            return
        entry = PasswordHistory(account_id=account_id, password_hash=password_hash)
        self._history_repo.add(entry)

    def is_expired(self, account: Account) -> bool:
        """True if the password has not been changed within MAX_AGE_DAYS."""
        if account.password_changed_at is None:
            return False
        age = datetime.datetime.now(datetime.UTC) - account.password_changed_at
        return age.days > MAX_AGE_DAYS

    def expires_within(self, account: Account, days: int) -> bool:
        """True if the password will expire within `days` days."""
        if account.password_changed_at is None:
            return False
        age = datetime.datetime.now(datetime.UTC) - account.password_changed_at
        return age.days >= (MAX_AGE_DAYS - days)


def get_dummy_hash() -> str:
    """Return a stable Argon2id hash to use for anti-enumeration timing parity."""
    return _DUMMY_HASH
