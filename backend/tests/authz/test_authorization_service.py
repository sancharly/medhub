"""TASK-027: AuthorizationService tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.api.errors import AuthorizationError
from app.authz.service import AuthorizationService, Resource
from app.db.models.account import Account, AccountStatus, UserType


def _make_account(user_type: UserType) -> Account:
    return Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _svc(effective_access: bool = False) -> AuthorizationService:
    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = effective_access
    mock_audit = MagicMock()
    return AuthorizationService(mock_consent, mock_audit)


def _resource(
    rtype: str = "account",
    owner_id: uuid.UUID | None = None,
    patient_id: uuid.UUID | None = None,
) -> Resource:
    return Resource(resource_type=rtype, owner_id=owner_id, patient_id=patient_id)


# --- PATIENT ---

def test_patient_can_read_own_account() -> None:
    actor = _make_account(UserType.PATIENT)
    svc = _svc()
    r = _resource("account", owner_id=actor.id)
    decision = svc.authorize(actor, "account:read", r)
    assert decision.allow is True
    assert decision.basis == "OWNER"


def test_patient_can_read_own_clinical() -> None:
    actor = _make_account(UserType.PATIENT)
    svc = _svc()
    r = _resource("clinical_entry", patient_id=actor.id)
    decision = svc.authorize(actor, "clinical:read", r)
    assert decision.allow is True


def test_patient_denied_other_patient_clinical() -> None:
    actor = _make_account(UserType.PATIENT)
    other_id = uuid.uuid4()
    svc = _svc()
    r = _resource("clinical_entry", patient_id=other_id)
    with pytest.raises(AuthorizationError):
        svc.authorize(actor, "clinical:read", r)


def test_patient_denied_clinical_write() -> None:
    actor = _make_account(UserType.PATIENT)
    svc = _svc()
    r = _resource("clinical_entry", patient_id=actor.id)
    with pytest.raises(AuthorizationError):
        svc.authorize(actor, "clinical:write", r)


# --- DOCTOR ---

def test_doctor_with_consent_can_read_clinical() -> None:
    actor = _make_account(UserType.DOCTOR)
    patient_id = uuid.uuid4()
    svc = _svc(effective_access=True)
    r = _resource("clinical_entry", patient_id=patient_id)
    decision = svc.authorize(actor, "clinical:read", r)
    assert decision.allow is True


def test_doctor_without_consent_denied_clinical() -> None:
    actor = _make_account(UserType.DOCTOR)
    patient_id = uuid.uuid4()
    svc = _svc(effective_access=False)
    r = _resource("clinical_entry", patient_id=patient_id)
    with pytest.raises(AuthorizationError):
        svc.authorize(actor, "clinical:read", r)


def test_doctor_can_read_own_account() -> None:
    actor = _make_account(UserType.DOCTOR)
    svc = _svc()
    r = _resource("account", owner_id=actor.id)
    decision = svc.authorize(actor, "account:read", r)
    assert decision.allow is True


# --- ADMIN ---

def test_admin_denied_clinical_read() -> None:
    actor = _make_account(UserType.ADMIN)
    svc = _svc()
    r = _resource("clinical_entry", patient_id=uuid.uuid4())
    with pytest.raises(AuthorizationError):
        svc.authorize(actor, "clinical:read", r)


def test_admin_can_read_account() -> None:
    actor = _make_account(UserType.ADMIN)
    svc = _svc()
    r = _resource("account", owner_id=uuid.uuid4())
    decision = svc.authorize(actor, "account:read", r)
    assert decision.allow is True


# --- SYSADMIN ---

def test_sysadmin_can_create_account() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc = _svc()
    r = _resource("account")
    decision = svc.authorize(actor, "account:create", r)
    assert decision.allow is True


def test_sysadmin_denied_clinical_read() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc = _svc()
    r = _resource("clinical_entry", patient_id=uuid.uuid4())
    with pytest.raises(AuthorizationError):
        svc.authorize(actor, "clinical:read", r)


# --- Audit ---

def test_authz_denied_emits_audit_record() -> None:
    actor = _make_account(UserType.PATIENT)
    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = False
    mock_audit = MagicMock()
    svc = AuthorizationService(mock_consent, mock_audit)
    r = _resource("account", owner_id=uuid.uuid4())  # not own account
    with pytest.raises(AuthorizationError):
        svc.authorize(actor, "account:read", r)
    call_str = str(mock_audit.record.call_args)
    assert "AUTHZ_DENIED" in call_str


def test_authz_allowed_emits_audit_record() -> None:
    actor = _make_account(UserType.PATIENT)
    mock_audit = MagicMock()
    svc = AuthorizationService(MagicMock(), mock_audit)
    r = _resource("account", owner_id=actor.id)
    svc.authorize(actor, "account:read", r)
    call_str = str(mock_audit.record.call_args)
    assert "AUTHZ_ALLOWED" in call_str


def test_authz_denied_error_does_not_leak_role_or_action() -> None:
    """403 error detail must not expose the actor's role name or the action string."""
    actor = _make_account(UserType.PATIENT)
    svc = _svc()
    r = _resource("account", owner_id=uuid.uuid4())  # not own account
    with pytest.raises(AuthorizationError) as exc_info:
        svc.authorize(actor, "account:read", r)
    detail = exc_info.value.detail
    assert "PATIENT" not in detail
    assert "account:read" not in detail
