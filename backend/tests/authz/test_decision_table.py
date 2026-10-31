"""TC-002.7: decision table of the appointment and module decisions (RISK-004 control).

Characterisation first (TASK-187): the table was written and run green against the
decisions as they were made in ``AppointmentService.list_for``, ``can_view_appointment`` and
``require_module_enabled``, then the logic moved into ``AuthorizationService`` and the same
table stayed green, unchanged. It exercises the public entry points (service methods and the
mounted module gate), so it does not depend on where the decision is made.

SR-005 AC 1, AC 3 (one deny-by-default mechanism); SR-011 AC 4 (a not-visible appointment is
answered as not found); SR-015 (module access follows the enabled groups).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.errors import AuthorizationError, NotFoundError, register_error_handlers
from app.appointments.service import AppointmentService
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.appointment import Appointment, AppointmentState
from app.db.repositories.group_repo import GroupRepository
from app.db.repositories.module_repo import ModuleRepository
from app.db.repositories.session import get_db
from app.modules.router_registry import RouterRegistry

ROLES = [UserType.PATIENT, UserType.DOCTOR, UserType.ADMIN, UserType.SYSADMIN]


def _account(user_type: UserType) -> Account:
    return Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _service(repo: MagicMock, consent: bool = False) -> AppointmentService:
    consent_svc = MagicMock()
    consent_svc.has_active_grant.return_value = consent
    authz = AuthorizationService(consent_svc, MagicMock())
    return AppointmentService(repo, MagicMock(), MagicMock(), authz, consent_svc)


def _appointment(doctor_id: uuid.UUID, patient_id: uuid.UUID) -> Appointment:
    return Appointment(
        id=uuid.uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        scheduled_at=datetime.now(UTC),
        state=AppointmentState.PENDING,
    )


# --- appointment list scope: 4 cases (SR-005 AC 1, AC 3) ---------------------------------

# role -> (repository method called, takes the actor id)
LIST_SCOPE = {
    UserType.PATIENT: ("list_for_patient", True),
    UserType.DOCTOR: ("list_for_doctor", True),
    UserType.ADMIN: ("list_all", False),
    UserType.SYSADMIN: ("list_all", False),
}


@pytest.mark.parametrize("role", ROLES)
def test_list_scope_by_role(role: UserType) -> None:
    """SR-005 AC 1/AC 3: each role lists exactly the set its repository query returns."""
    repo = MagicMock()
    sentinel = [object()]
    for name in ("list_for_patient", "list_for_doctor", "list_all"):
        getattr(repo, name).return_value = sentinel
    actor = _account(role)

    assert _service(repo).list_for(actor) is sentinel

    method, with_id = LIST_SCOPE[role]
    called = [
        n for n in ("list_for_patient", "list_for_doctor", "list_all") if getattr(repo, n).called
    ]
    assert called == [method]
    if with_id:
        getattr(repo, method).assert_called_once_with(actor.id)
    else:
        getattr(repo, method).assert_called_once_with()


def test_list_denied_for_actor_with_no_known_role() -> None:
    """SR-005 AC 1: deny by default, an actor with no known role may not list (403)."""
    actor = _account(UserType.PATIENT)
    actor.user_type = "GUEST"  # type: ignore[assignment]
    repo = MagicMock()
    with pytest.raises(AuthorizationError):
        _service(repo).list_for(actor)
    for name in ("list_for_patient", "list_for_doctor", "list_all"):
        assert not getattr(repo, name).called


# --- single appointment read: 12 + 4 + 1 cases (SR-005 AC 1, SR-011 AC 4) ---------------

# relation of the actor to the appointment -> visible, per role
VISIBILITY = [
    (UserType.PATIENT, "as_patient", True),
    (UserType.PATIENT, "as_doctor", True),
    (UserType.PATIENT, "unrelated", False),
    (UserType.DOCTOR, "as_patient", True),
    (UserType.DOCTOR, "as_doctor", True),
    (UserType.DOCTOR, "unrelated", False),
    (UserType.ADMIN, "as_patient", True),
    (UserType.ADMIN, "as_doctor", True),
    (UserType.ADMIN, "unrelated", True),
    (UserType.SYSADMIN, "as_patient", True),
    (UserType.SYSADMIN, "as_doctor", True),
    (UserType.SYSADMIN, "unrelated", True),
]


@pytest.mark.parametrize(("role", "relation", "visible"), VISIBILITY)
def test_read_visibility(role: UserType, relation: str, visible: bool) -> None:
    """SR-011 AC 4: a not-visible appointment is NotFoundError, a visible one is returned."""
    actor = _account(role)
    doctor_id = actor.id if relation == "as_doctor" else uuid.uuid4()
    patient_id = actor.id if relation == "as_patient" else uuid.uuid4()
    appt = _appointment(doctor_id, patient_id)
    repo = MagicMock()
    repo.get.return_value = appt
    svc = _service(repo)

    if visible:
        assert svc.get(actor, appt.id) is appt
    else:
        with pytest.raises(NotFoundError):
            svc.get(actor, appt.id)


def test_doctor_with_active_consent_still_cannot_read_unrelated_appointment() -> None:
    """SR-005 AC 1: appointment visibility is not widened by a consent grant."""
    actor = _account(UserType.DOCTOR)
    appt = _appointment(uuid.uuid4(), uuid.uuid4())
    repo = MagicMock()
    repo.get.return_value = appt
    with pytest.raises(NotFoundError):
        _service(repo, consent=True).get(actor, appt.id)


@pytest.mark.parametrize("role", ROLES)
def test_read_missing_appointment_is_not_found(role: UserType) -> None:
    """SR-011 AC 4: a missing appointment is answered exactly like a not-visible one."""
    repo = MagicMock()
    repo.get.return_value = None
    with pytest.raises(NotFoundError):
        _service(repo).get(_account(role), uuid.uuid4())


# --- module access: 4 roles x 4 membership states = 16 cases (SR-015) --------------------

# state -> (memberships, enabled keys of those groups, module asked, expected status)
MODULE_STATES = {
    "enabled_in_group": ([MagicMock(group_id=uuid.uuid4())], {"viewer"}, "viewer", 200),
    "no_membership": ([], {"viewer"}, "viewer", 403),
    "module_not_enabled": ([MagicMock(group_id=uuid.uuid4())], {"other"}, "viewer", 403),
    "unknown_module": ([MagicMock(group_id=uuid.uuid4())], set(), "viewer", 403),
}


@pytest.mark.parametrize("state", list(MODULE_STATES))
@pytest.mark.parametrize("role", ROLES)
def test_module_access_by_role_and_membership(role: UserType, state: str) -> None:
    """SR-015: 200 only when a group of the account has the module enabled, 403 otherwise."""
    memberships, enabled, key, expected = MODULE_STATES[state]
    app = FastAPI()
    register_error_handlers(app)
    sub = APIRouter()

    @sub.get("/ping")
    def ping() -> dict:
        return {"pong": True}

    RouterRegistry(app).mount(key, sub)
    actor = _account(role)
    app.dependency_overrides[get_current_user] = lambda: actor

    def _db():
        yield MagicMock()

    app.dependency_overrides[get_db] = _db

    with (
        patch.object(GroupRepository, "memberships_for_account", return_value=memberships),
        patch.object(ModuleRepository, "enabled_module_keys_for_groups", return_value=enabled),
        patch.object(AuditService, "record"),
    ):
        resp = TestClient(app, raise_server_exceptions=False).get(f"/api/v1/modules/{key}/ping")

    assert resp.status_code == expected
    if expected == 403:
        # The refusal message is part of the unchanged behaviour (TASK-187).
        assert resp.json()["detail"] == f"Module '{key}' is not enabled for your account."
