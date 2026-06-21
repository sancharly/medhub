"""AuditService tests (TASK-014, SR-023)."""

import os
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.audit.actions import AuditAction
from app.audit.service import AuditService
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
        target_type="patient",
        target_id=target_patient,
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    log: AuditLog = audit_repo_mock._added[0]
    assert log.actor_id == actor
    assert log.target_type == "patient"
    assert log.target_id == target_patient
    assert log.timestamp is not None


# --- SR-023.3: consent grant/revoke ---


def test_consent_grant_event(service, audit_repo_mock):
    actor = uuid.uuid4()
    service.record(
        actor=actor,
        action=AuditAction.CONSENT_GRANT,
        target_type="account",
        target_id=str(uuid.uuid4()),
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    log: AuditLog = audit_repo_mock._added[0]
    assert log.action == AuditAction.CONSENT_GRANT
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


def test_password_scrubbed_from_action(service, audit_repo_mock):
    """Passing action with password=... must not appear in stored record."""
    service.record(
        actor=uuid.uuid4(),
        action="AUTH_LOGIN password=secret123",
        target_type=None,
        target_id=None,
        outcome=AuditOutcome.FAILURE,
        ip=None,
    )
    log: AuditLog = audit_repo_mock._added[0]
    assert "secret123" not in log.action
    assert "password=secret123" not in log.action


def test_multiple_credentials_scrubbed(service, audit_repo_mock):
    service.record(
        actor=None,
        action="AUTH token=abc123 secret=xyz password=hunter2",
        target_type=None,
        target_id=None,
        outcome=AuditOutcome.FAILURE,
        ip=None,
    )
    log: AuditLog = audit_repo_mock._added[0]
    assert "abc123" not in log.action
    assert "xyz" not in log.action
    assert "hunter2" not in log.action


# --- Two records stored with different server timestamps ---


def test_two_records_have_timestamps(service, audit_repo_mock):
    actor = uuid.uuid4()
    service.record(
        actor=actor,
        action="A1",
        target_type=None,
        target_id=None,
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    service.record(
        actor=actor,
        action="A2",
        target_type=None,
        target_id=None,
        outcome=AuditOutcome.SUCCESS,
        ip=None,
    )
    assert audit_repo_mock._added[0].timestamp is not None
    assert audit_repo_mock._added[1].timestamp is not None
