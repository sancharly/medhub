"""AuditService tests (TASK-014, SR-023)."""

import inspect
import os
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.audit.actions import AuditAction
from app.audit.service import AuditFieldError, AuditService
from app.db.models.audit import AuditLog, AuditOutcome
from app.db.repositories.audit_repo import AuditRepository

# Ensure Docker socket on macOS
_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"


# --- Fixtures ---


@pytest.fixture
def audit_repo_mock():
    """In-memory AuditRepository mock that captures added logs."""
    repo = MagicMock(spec=AuditRepository)
    added: list[AuditLog] = []

    def capture_add(log: AuditLog) -> AuditLog:
        added.append(log)
        return log

    repo.add.side_effect = capture_add
    repo.add_independent.side_effect = capture_add
    repo._added = added
    return repo


@pytest.fixture
def service(audit_repo_mock) -> AuditService:
    return AuditService(audit_repo_mock)


# --- SR-023.1: auth attempt (success + failure) ---


def test_auth_login_success_recorded(service, audit_repo_mock):
    actor = uuid.uuid4()
    service.record(
        actor=actor,
        action=AuditAction.AUTH_LOGIN,
        target_type=None,
        target_id=None,
        outcome=AuditOutcome.SUCCESS,
        ip="192.168.1.1",
    )
    assert audit_repo_mock.add.called
    log: AuditLog = audit_repo_mock._added[0]
    assert log.actor_id == actor
    assert log.action == AuditAction.AUTH_LOGIN
    assert log.outcome == AuditOutcome.SUCCESS


def test_auth_login_failure_with_null_actor(service, audit_repo_mock):
    """Pre-auth failure — actor is None (unknown)."""
    service.record(
        actor=None,
        action=AuditAction.AUTH_LOGIN,
        target_type=None,
        target_id=None,
        outcome=AuditOutcome.FAILURE,
        ip="10.0.0.1",
    )
    log: AuditLog = audit_repo_mock._added[0]
    assert log.actor_id is None
    assert log.outcome == AuditOutcome.FAILURE


def test_auth_login_timestamp_is_server_assigned(service, audit_repo_mock):
    """Timestamp is set by AuditService, not supplied by caller."""
    before = datetime.now(UTC)
    service.record(
        actor=uuid.uuid4(),
        action=AuditAction.AUTH_LOGIN,
        target_type=None,
        target_id=None,
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    after = datetime.now(UTC)
    log: AuditLog = audit_repo_mock._added[0]
    assert before <= log.timestamp <= after


# --- SR-023.2: clinical access ---


def test_clinical_access_event(service, audit_repo_mock):
    actor = uuid.uuid4()
    target_patient = str(uuid.uuid4())
    service.record(
        actor=actor,
        action=AuditAction.CLINICAL_ACCESS,
        target_type="clinical_entry",
        target_id=target_patient,
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    log: AuditLog = audit_repo_mock._added[0]
    assert log.actor_id == actor
    assert log.target_type == "clinical_entry"
    assert log.target_id == target_patient
    assert log.timestamp is not None


# --- SR-023.3: consent grant/revoke ---


def test_consent_grant_event(service, audit_repo_mock):
    actor = uuid.uuid4()
    service.record(
        actor=actor,
        action=AuditAction.CONSENT_GRANTED,
        target_type="account",
        target_id=str(uuid.uuid4()),
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    log: AuditLog = audit_repo_mock._added[0]
    assert log.action == AuditAction.CONSENT_GRANTED
    assert log.timestamp is not None


def test_consent_revoke_event(service, audit_repo_mock):
    service.record(
        actor=uuid.uuid4(),
        action=AuditAction.CONSENT_REVOKE,
        target_type="account",
        target_id=str(uuid.uuid4()),
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    log: AuditLog = audit_repo_mock._added[0]
    assert log.action == AuditAction.CONSENT_REVOKE


# --- SR-023.4: administrative action ---


def test_user_type_change_recorded(service, audit_repo_mock):
    admin = uuid.uuid4()
    target = str(uuid.uuid4())
    service.record(
        actor=admin,
        action=AuditAction.USER_TYPE_CHANGE,
        target_type="account",
        target_id=target,
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    log: AuditLog = audit_repo_mock._added[0]
    assert log.action == AuditAction.USER_TYPE_CHANGE
    assert log.actor_id == admin
    assert log.target_id == target


# --- SR-023.5: immutability — no modify path ---


def test_audit_service_has_no_modify_methods():
    assert not hasattr(AuditService, "update")
    assert not hasattr(AuditService, "delete")
    assert not hasattr(AuditService, "modify")
    assert hasattr(AuditService, "record")


def test_audit_repo_has_only_add():
    assert not hasattr(AuditRepository, "get")
    assert not hasattr(AuditRepository, "list")
    assert not hasattr(AuditRepository, "update")
    assert not hasattr(AuditRepository, "delete")


# --- SR-023.5: no credentials in stored record ---


def test_password_scrubbed_by_second_line():
    """The key=value scrub stays as a second line behind the closed-set check (SR-023 AC 5)."""
    from app.audit.service import _scrub

    cleaned = _scrub("AUTH token=abc123 secret=xyz password=hunter2")
    assert "abc123" not in cleaned
    assert "xyz" not in cleaned
    assert "hunter2" not in cleaned


def test_action_with_embedded_credential_is_refused(service, audit_repo_mock):
    """An action string carrying key=value credentials is not an AuditAction (SR-023 AC 9)."""
    with pytest.raises(AuditFieldError):
        service.record(
            actor=uuid.uuid4(),
            action="AUTH_LOGIN password=secret123",
            target_type=None,
            target_id=None,
            outcome=AuditOutcome.FAILURE,
            ip=None,
        )
    assert audit_repo_mock._added == []


# --- Two records stored with different server timestamps ---


def test_two_records_have_timestamps(service, audit_repo_mock):
    actor = uuid.uuid4()
    service.record(
        actor=actor,
        action=AuditAction.AUTH_LOGIN,
        target_type=None,
        target_id=None,
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    service.record(
        actor=actor,
        action=AuditAction.LOGIN_FAILURE,
        target_type=None,
        target_id=None,
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    assert audit_repo_mock._added[0].timestamp is not None
    assert audit_repo_mock._added[1].timestamp is not None


# --- ADR-0016: failure and refusal events commit on their own transaction ---


def _record(service, action: str, outcome: AuditOutcome) -> None:
    service.record(
        actor=uuid.uuid4(),
        action=action,
        target_type=None,
        target_id=None,
        outcome=outcome,
        ip=None,
    )


def test_failure_event_goes_through_add_independent(service, audit_repo_mock):
    _record(service, AuditAction.AUTHZ_DENIED, AuditOutcome.FAILURE)
    audit_repo_mock.add_independent.assert_called_once()
    audit_repo_mock.add.assert_not_called()


def test_success_event_joins_the_request_transaction(service, audit_repo_mock):
    _record(service, AuditAction.AUTH_LOGIN, AuditOutcome.SUCCESS)
    audit_repo_mock.add.assert_called_once()
    audit_repo_mock.add_independent.assert_not_called()


def test_account_lockout_success_event_goes_through_add_independent(service, audit_repo_mock):
    _record(service, AuditAction.ACCOUNT_LOCKOUT, AuditOutcome.SUCCESS)
    audit_repo_mock.add_independent.assert_called_once()
    audit_repo_mock.add.assert_not_called()


def test_record_has_no_durable_parameter():
    assert "durable" not in inspect.signature(AuditService.record).parameters


def test_repository_has_no_session_wide_commit():
    assert not hasattr(AuditRepository, "commit")


# --- SR-023 AC 6 / SR-042: originating client address (TASK-137, TC-009.9) ---


def _record_login(service, ip=None) -> None:
    service.record(
        actor=uuid.uuid4(),
        action=AuditAction.AUTH_LOGIN,
        target_type=None,
        target_id=None,
        outcome=AuditOutcome.SUCCESS,
        ip=ip,
    )


def test_explicit_ip_wins_over_request_address(service, audit_repo_mock):  # SR-023 AC 6
    from app.core.client_address import _current  # noqa: PLC0415

    token = _current.set("203.0.113.7")
    try:
        _record_login(service, ip="198.51.100.1")
    finally:
        _current.reset(token)
    assert audit_repo_mock._added[0].ip == "198.51.100.1"


def test_request_address_used_when_ip_is_none(service, audit_repo_mock):  # SR-023 AC 6
    from app.core.client_address import _current  # noqa: PLC0415

    token = _current.set("203.0.113.7")
    try:
        _record_login(service)
    finally:
        _current.reset(token)
    assert audit_repo_mock._added[0].ip == "203.0.113.7"


def test_no_request_context_records_no_address(service, audit_repo_mock):  # SR-023 AC 6
    _record_login(service)
    assert audit_repo_mock._added[0].ip is None


# --- SR-023 AC 9: valid shapes from every current caller pass ---

_UID = str(uuid.uuid4())


@pytest.mark.parametrize(
    ("action", "target_type", "target_id"),
    [
        (AuditAction.ACCOUNT_CREATED, "account", _UID),
        (AuditAction.AUTHZ_ALLOWED, "account", "user_type:PATIENT"),  # account:create decision
        (AuditAction.AUTHZ_DENIED, "appointment", ""),  # decision with no resource id
        (AuditAction.APPOINTMENT_CREATE, "appointment", _UID),
        (AuditAction.ATTACHMENT_ACCESS, "attachment", _UID),
        (AuditAction.DICOM_STUDY_READ, "attachment", _UID),
        (AuditAction.CLINICAL_ACCESS, "clinical_entry", _UID),
        (AuditAction.CLINICAL_ACCESS, "patient_roster", _UID),
        (AuditAction.CONSENT_GRANTED, "consent_grant", _UID),
        (AuditAction.AUTHZ_DENIED, "consent", _UID),
        (AuditAction.GROUP_CREATE, "group", _UID),
        (AuditAction.GROUP_MEMBER_ADD, "group_membership", f"{_UID}:{_UID}"),
        (AuditAction.MODULE_ENABLE, "group_module", f"{_UID}:dicom-viewer"),
        (AuditAction.MODULE_DISCOVERED, "module", "dicom-viewer"),
        (AuditAction.MODULE_REGISTRY_SYNC, "module_registry", None),
        (AuditAction.DATA_ANONYMIZED, "anonymized_dataset", _UID),
        (AuditAction.LOGIN_FAILURE, "account", None),
        (AuditAction.LOGOUT, "account", _UID),
        (AuditAction.PASSWORD_CHANGED, "account", _UID),
        (AuditAction.AUTH_LOGIN, None, None),
    ],
)
def test_valid_caller_shapes_are_recorded(service, audit_repo_mock, action, target_type, target_id):
    service.record(
        actor=None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    assert len(audit_repo_mock._added) == 1
    assert audit_repo_mock._added[0].target_id == target_id
