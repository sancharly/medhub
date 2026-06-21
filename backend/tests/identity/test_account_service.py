"""TASK-030: AccountService create + profile tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.api.errors import AuthorizationError, ConflictError, NotFoundError
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.identity.account_service import AccountCreate, AccountService


def _make_account(user_type: UserType) -> Account:
    return Account(
        id=uuid.uuid4(),
        email="creator@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _build_svc(creator: Account, existing_email: Account | None = None) -> AccountService:
    mock_repo = MagicMock()
    mock_repo.get_by_email.return_value = existing_email
    new_account = Account(
        id=uuid.uuid4(),
        email="new@example.com",
        user_type=UserType.PATIENT,
        status=AccountStatus.INACTIVE,
    )
    mock_repo.add.return_value = new_account

    mock_audit = MagicMock()

    # Real authz svc that allows everything for SYSADMIN
    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = False
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    return AccountService(mock_repo, mock_audit, authz_svc)


# --- create ---


def test_sysadmin_can_create_any_user_type() -> None:
    creator = _make_account(UserType.SYSADMIN)
    svc = _build_svc(creator)
    data = AccountCreate(email="new@example.com", user_type=UserType.DOCTOR)
    account = svc.create(creator, data)
    assert account.status == AccountStatus.INACTIVE


def test_admin_can_create_patient() -> None:
    creator = _make_account(UserType.ADMIN)
    svc = _build_svc(creator)
    data = AccountCreate(email="new@example.com", user_type=UserType.PATIENT)
    account = svc.create(creator, data)
    assert account is not None


def test_admin_cannot_create_sysadmin() -> None:
    creator = _make_account(UserType.ADMIN)
    svc = _build_svc(creator)
    data = AccountCreate(email="new@example.com", user_type=UserType.SYSADMIN)
    with pytest.raises(AuthorizationError):
        svc.create(creator, data)


def test_patient_cannot_create_account() -> None:
    creator = _make_account(UserType.PATIENT)
    svc = _build_svc(creator)
    data = AccountCreate(email="new@example.com", user_type=UserType.PATIENT)
    with pytest.raises(AuthorizationError):
        svc.create(creator, data)


def test_create_duplicate_email_raises_conflict() -> None:
    creator = _make_account(UserType.SYSADMIN)
    existing = Account(
        id=uuid.uuid4(),
        email="existing@example.com",
        user_type=UserType.PATIENT,
        status=AccountStatus.ACTIVE,
    )
    svc = _build_svc(creator, existing_email=existing)
    data = AccountCreate(email="existing@example.com", user_type=UserType.PATIENT)
    with pytest.raises(ConflictError):
        svc.create(creator, data)


def test_create_audits_account_created() -> None:
    creator = _make_account(UserType.SYSADMIN)
    mock_repo = MagicMock()
    mock_repo.get_by_email.return_value = None
    new_acct = Account(
        id=uuid.uuid4(), email="n@e.com", user_type=UserType.PATIENT, status=AccountStatus.INACTIVE
    )
    mock_repo.add.return_value = new_acct
    mock_audit = MagicMock()
    authz_svc = AuthorizationService(MagicMock(), MagicMock())
    svc = AccountService(mock_repo, mock_audit, authz_svc)

    data = AccountCreate(email="n@e.com", user_type=UserType.PATIENT)
    svc.create(creator, data)
    mock_audit.record.assert_called_once()
    assert "ACCOUNT_CREATED" in str(mock_audit.record.call_args)


# --- get_profile ---


def test_get_profile_returns_own_account_for_patient() -> None:
    acct = Account(
        id=uuid.uuid4(),
        email="me@example.com",
        user_type=UserType.PATIENT,
        status=AccountStatus.ACTIVE,
    )
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = acct
    mock_repo.get_by_email.return_value = None

    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = False
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    svc = AccountService(mock_repo, MagicMock(), authz_svc)
    result = svc.get_profile(acct, acct.id)
    assert result.id == acct.id


def test_get_profile_raises_not_found_when_missing() -> None:
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = None
    authz_svc = MagicMock()
    svc = AccountService(mock_repo, MagicMock(), authz_svc)
    actor = _make_account(UserType.PATIENT)
    with pytest.raises(NotFoundError):
        svc.get_profile(actor, uuid.uuid4())
