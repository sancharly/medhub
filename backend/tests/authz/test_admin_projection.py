"""TASK-029: Admin projection tests."""

from __future__ import annotations

import uuid
from datetime import date

from app.authz.admin_projection import AdminAccountView, project_for_admin
from app.db.models.account import Account, AccountStatus, UserType


def test_projection_includes_whitelisted_fields() -> None:
    acct = Account(
        id=uuid.uuid4(),
        email="secret@example.com",
        user_type=UserType.DOCTOR,
        status=AccountStatus.ACTIVE,
        first_name="Alice",
        surname="Smith",
        date_of_birth=date(1985, 3, 14),
        password_hash="$argon2id$...",
    )
    view = project_for_admin(acct)
    assert isinstance(view, AdminAccountView)
    assert view.id == acct.id
    assert view.account_type == UserType.DOCTOR
    assert view.first_name == "Alice"
    assert view.family_name == "Smith"
    assert view.date_of_birth == date(1985, 3, 14)


def test_projection_excludes_credentials() -> None:
    acct = Account(
        id=uuid.uuid4(),
        email="secret@example.com",
        user_type=UserType.PATIENT,
        status=AccountStatus.ACTIVE,
        password_hash="$argon2id$verysecret",
    )
    view = project_for_admin(acct)
    # View must be a dataclass with only the listed fields
    view_dict = view.__dict__
    assert "password_hash" not in view_dict
    assert "email" not in view_dict


def test_projection_excludes_activation_token() -> None:
    acct = Account(
        id=uuid.uuid4(),
        email="secret@example.com",
        user_type=UserType.PATIENT,
        status=AccountStatus.INACTIVE,
        activation_token_hash="sha256-hash",
    )
    view = project_for_admin(acct)
    view_dict = view.__dict__
    assert "activation_token_hash" not in view_dict


def test_projection_handles_null_fields() -> None:
    acct = Account(
        id=uuid.uuid4(),
        email="none@example.com",
        user_type=UserType.ADMIN,
        status=AccountStatus.ACTIVE,
    )
    view = project_for_admin(acct)
    assert view.first_name is None
    assert view.family_name is None
    assert view.date_of_birth is None
