"""TC-002.7 / TC-003.6: decision tables of the appointment, module and identity decisions
(RISK-004 control).

Characterisation first (TASK-187): the table was written and run green against the
decisions as they were made in ``AppointmentService.list_for``, ``can_view_appointment`` and
``require_module_enabled``, then the logic moved into ``AuthorizationService`` and the same
table stayed green, unchanged. It exercises the public entry points (service methods and the
mounted module gate), so it does not depend on where the decision is made.

SR-005 AC 1, AC 3 (one deny-by-default mechanism); SR-011 AC 4 (a not-visible appointment is
answered as not found); SR-015 (module access follows the enabled groups).

Identity services (TASK-188): the account-creation, deactivate, reactivate, delete and resend
tables below were written and run green against the role comparisons inside the identity
services, then those comparisons moved into ``AuthorizationService`` and the same rows stayed
green. Only the ``_*_service`` builders changed (they inject the real ``AuthorizationService``).
SR-032 AC 1, AC 4, AC 5 (creation constrained by role); SR-034 AC 1 (SYSADMIN-only lifecycle);
SR-005 AC 1 (deny by default). Status codes and ``detail`` messages are part of the table.

Router checks (TASK-189): the router table at the end was written and run green against the
``user_type`` comparisons inside the routers (unlock, module list, consent grant/revoke/list,
patient roster), then they moved into ``AuthorizationService`` and the rows stayed unchanged.
SR-005 AC 1, AC 3; SR-008 (consent is the patient's own act); SR-009 (admin projection).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import fakeredis
import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.errors import AuthorizationError, NotFoundError, register_error_handlers
from app.appointments.service import AppointmentService
from app.audit.service import AuditService
from app.auth.password import PasswordService
from app.auth.session import SessionService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.appointment import Appointment, AppointmentState
from app.db.repositories.group_repo import GroupRepository
from app.db.repositories.module_repo import ModuleRepository
from app.db.repositories.session import get_db
from app.identity.account_service import AccountCreate, AccountService
from app.identity.activation import ActivationService
from app.identity.erasure import ErasureService
from app.identity.lifecycle import LifecycleService
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


# --- identity services (TASK-188) ---------------------------------------------------------

DENY_CREATE_ROLE = "Only ADMIN or SYSADMIN can create accounts."
DENY_CREATE_SYSADMIN = "ADMIN cannot create SYSADMIN accounts."
DENY_DEACTIVATE = "Only SYSADMIN can deactivate accounts."
DENY_DEACTIVATE_SELF = "Cannot deactivate your own account."
DENY_REACTIVATE = "Only SYSADMIN can reactivate accounts."
DENY_DELETE = "Only SYSADMIN or the account owner can request erasure."
DENY_RESEND = "Only ADMIN or SYSADMIN can resend activation emails."


def _unknown_role_actor() -> Account:
    actor = _account(UserType.PATIENT)
    actor.user_type = "GUEST"  # type: ignore[assignment]
    return actor


def _real_authz() -> AuthorizationService:
    return AuthorizationService(MagicMock(), MagicMock())


def _account_service(repo: MagicMock) -> AccountService:
    return AccountService(repo, MagicMock(), _real_authz())


def _lifecycle_service(repo: MagicMock) -> LifecycleService:
    return LifecycleService(repo, SessionService(fakeredis.FakeRedis()), MagicMock(), _real_authz())


def _activation_service(repo: MagicMock) -> ActivationService:
    return ActivationService(repo, PasswordService(), MagicMock(), _real_authz())


def _erasure_service(repo: MagicMock) -> ErasureService:
    return ErasureService(
        repo,
        MagicMock(),
        SessionService(fakeredis.FakeRedis()),
        PasswordService(),
        MagicMock(),
        _real_authz(),
    )


def _assert_outcome(call, expected_detail: str | None) -> None:
    """Allowed when ``expected_detail`` is None, else a 403 carrying exactly that detail."""
    if expected_detail is None:
        call()
        return
    with pytest.raises(AuthorizationError) as exc:
        call()
    assert exc.value.status == 403
    assert exc.value.detail == expected_detail


# account creation: creator role x target type = 16 cases (SR-032 AC 1, AC 4, AC 5)
CREATE_TABLE = [
    (UserType.PATIENT, UserType.PATIENT, DENY_CREATE_ROLE),
    (UserType.PATIENT, UserType.DOCTOR, DENY_CREATE_ROLE),
    (UserType.PATIENT, UserType.ADMIN, DENY_CREATE_ROLE),
    (UserType.PATIENT, UserType.SYSADMIN, DENY_CREATE_ROLE),
    (UserType.DOCTOR, UserType.PATIENT, DENY_CREATE_ROLE),
    (UserType.DOCTOR, UserType.DOCTOR, DENY_CREATE_ROLE),
    (UserType.DOCTOR, UserType.ADMIN, DENY_CREATE_ROLE),
    (UserType.DOCTOR, UserType.SYSADMIN, DENY_CREATE_ROLE),
    (UserType.ADMIN, UserType.PATIENT, None),
    (UserType.ADMIN, UserType.DOCTOR, None),
    (UserType.ADMIN, UserType.ADMIN, None),
    (UserType.ADMIN, UserType.SYSADMIN, DENY_CREATE_SYSADMIN),
    (UserType.SYSADMIN, UserType.PATIENT, None),
    (UserType.SYSADMIN, UserType.DOCTOR, None),
    (UserType.SYSADMIN, UserType.ADMIN, None),
    (UserType.SYSADMIN, UserType.SYSADMIN, None),
]


@pytest.mark.parametrize(("creator_role", "target", "expected"), CREATE_TABLE)
def test_create_by_role_and_target(
    creator_role: UserType, target: UserType, expected: str | None
) -> None:
    """SR-032 AC 1/4/5: creation is constrained by creator role and target type."""
    repo = MagicMock()
    repo.get_by_email.return_value = None
    svc = _account_service(repo)
    data = AccountCreate(email="new@example.com", user_type=target)

    with patch("app.workers.email_tasks.send_activation_email"):
        _assert_outcome(lambda: svc.create(_account(creator_role), data), expected)

    assert repo.add.called is (expected is None)


@pytest.mark.parametrize("role", ROLES)
def test_creation_without_a_requested_type_is_denied(role: UserType) -> None:
    """SR-032 AC 4: deny by default, no role creates without a stated type (SYSADMIN included)."""
    from app.authz.service import Resource  # noqa: PLC0415

    authz = _real_authz()
    resource = Resource(resource_type="account", owner_id=None, patient_id=None)
    assert authz.decide(_account(role), "account:create", resource).allow is False
    with pytest.raises(AuthorizationError):
        authz.authorize(_account(role), "account:create", resource)


def test_create_denied_for_actor_with_no_known_role() -> None:
    """SR-005 AC 1: deny by default, an actor with no known role may not create (403)."""
    repo = MagicMock()
    data = AccountCreate(email="new@example.com", user_type=UserType.PATIENT)
    _assert_outcome(
        lambda: _account_service(repo).create(_unknown_role_actor(), data), DENY_CREATE_ROLE
    )
    assert not repo.add.called


# deactivate / reactivate: actor role x (other | self | other SYSADMIN) = 12 + 8 cases
# (SR-034 AC 1)
DEACTIVATE_TABLE = [
    (role, relation, expected)
    for role in ROLES
    for relation, expected in (
        ("other", None if role is UserType.SYSADMIN else DENY_DEACTIVATE),
        ("other_sysadmin", None if role is UserType.SYSADMIN else DENY_DEACTIVATE),
        (
            "self",
            DENY_DEACTIVATE_SELF if role is UserType.SYSADMIN else DENY_DEACTIVATE,
        ),
    )
]
REACTIVATE_TABLE = [
    (role, relation, None if role is UserType.SYSADMIN else DENY_REACTIVATE)
    for role in ROLES
    for relation in ("other", "self")
]


def _target_for(actor: Account, relation: str) -> Account:
    if relation == "self":
        return actor
    return _account(UserType.SYSADMIN if relation == "other_sysadmin" else UserType.PATIENT)


@pytest.mark.parametrize(("role", "relation", "expected"), DEACTIVATE_TABLE)
def test_deactivate_by_role_and_relation(
    role: UserType, relation: str, expected: str | None
) -> None:
    """SR-034 AC 1: only SYSADMIN deactivates, and never its own account."""
    actor = _account(role)
    target = _target_for(actor, relation)
    repo = MagicMock()
    repo.get_by_id.return_value = target
    svc = _lifecycle_service(repo)

    with patch("app.workers.session_tasks.propagate_session_kill"):
        _assert_outcome(lambda: svc.deactivate(actor, target.id), expected)

    assert (target.status == AccountStatus.DEACTIVATED) is (expected is None)


@pytest.mark.parametrize(("role", "relation", "expected"), REACTIVATE_TABLE)
def test_reactivate_by_role_and_relation(
    role: UserType, relation: str, expected: str | None
) -> None:
    """SR-034 AC 1: only SYSADMIN reactivates."""
    actor = _account(role)
    target = _target_for(actor, relation)
    target.status = AccountStatus.DEACTIVATED
    repo = MagicMock()
    repo.get_by_id.return_value = target
    svc = _lifecycle_service(repo)

    _assert_outcome(lambda: svc.reactivate(actor, target.id), expected)

    assert (target.status == AccountStatus.ACTIVE) is (expected is None)


@pytest.mark.parametrize("method", ["deactivate", "reactivate"])
@pytest.mark.parametrize("role", [UserType.PATIENT, UserType.DOCTOR, UserType.ADMIN])
def test_lifecycle_refusal_precedes_the_lookup(role: UserType, method: str) -> None:
    """SR-034 AC 1: a refused actor gets 403 even for an unknown account (no 404 oracle)."""
    repo = MagicMock()
    repo.get_by_id.return_value = None
    expected = DENY_DEACTIVATE if method == "deactivate" else DENY_REACTIVATE
    svc = _lifecycle_service(repo)
    _assert_outcome(lambda: getattr(svc, method)(_account(role), uuid.uuid4()), expected)
    assert not repo.get_by_id.called


@pytest.mark.parametrize("method", ["deactivate", "reactivate"])
def test_lifecycle_denied_for_actor_with_no_known_role(method: str) -> None:
    """SR-005 AC 1: deny by default for an actor with no known role."""
    expected = DENY_DEACTIVATE if method == "deactivate" else DENY_REACTIVATE
    svc = _lifecycle_service(MagicMock())
    _assert_outcome(lambda: getattr(svc, method)(_unknown_role_actor(), uuid.uuid4()), expected)


# delete (erasure): actor role x (other | self | other SYSADMIN) = 12 cases (SR-034 AC 1)
DELETE_TABLE = [
    (role, relation, None if role is UserType.SYSADMIN or relation == "self" else DENY_DELETE)
    for role in ROLES
    for relation in ("other", "self", "other_sysadmin")
]


@pytest.mark.parametrize(("role", "relation", "expected"), DELETE_TABLE)
def test_delete_by_role_and_relation(role: UserType, relation: str, expected: str | None) -> None:
    """SR-034 AC 1: SYSADMIN erases any account, anyone else only their own."""
    actor = _account(role)
    target = _target_for(actor, relation)
    repo = MagicMock()
    repo.get_by_id.return_value = target
    svc = _erasure_service(repo)

    _assert_outcome(lambda: svc.delete(actor, target.id), expected)

    assert (target.status == AccountStatus.DELETED) is (expected is None)


def test_delete_denied_for_actor_with_no_known_role() -> None:
    """SR-005 AC 1: an actor with no known role may erase only their own account."""
    actor = _unknown_role_actor()
    repo = MagicMock()
    repo.get_by_id.return_value = _account(UserType.PATIENT)
    _assert_outcome(lambda: _erasure_service(repo).delete(actor, uuid.uuid4()), DENY_DELETE)


# resend activation: actor role = 4 cases + unknown role (SR-032 AC 1)
RESEND_TABLE = [
    (UserType.PATIENT, DENY_RESEND),
    (UserType.DOCTOR, DENY_RESEND),
    (UserType.ADMIN, None),
    (UserType.SYSADMIN, None),
]


@pytest.mark.parametrize(("role", "expected"), RESEND_TABLE)
def test_resend_activation_by_role(role: UserType, expected: str | None) -> None:
    """SR-032 AC 1: only ADMIN and SYSADMIN re-issue an activation token."""
    target = _account(UserType.PATIENT)
    target.status = AccountStatus.INACTIVE
    repo = MagicMock()
    repo.get_by_id.return_value = target
    svc = _activation_service(repo)

    with patch("app.workers.email_tasks.send_activation_email"):
        _assert_outcome(lambda: svc.resend_activation(_account(role), target.id), expected)

    assert (target.activation_token_hash is not None) is (expected is None)


def test_resend_activation_denied_for_actor_with_no_known_role() -> None:
    """SR-005 AC 1: deny by default for an actor with no known role."""
    _assert_outcome(
        lambda: _activation_service(MagicMock()).resend_activation(
            _unknown_role_actor(), uuid.uuid4()
        ),
        DENY_RESEND,
    )


# --- router checks (TASK-189) -------------------------------------------------------------


def _router_call(role: UserType | None, route: str, allowed_patches: list) -> tuple[int, dict]:
    """Call a mounted route as ``role`` (``None`` = no known role); return status and body."""
    from contextlib import ExitStack  # noqa: PLC0415

    from app.api.deps import get_redis  # noqa: PLC0415
    from app.main import create_app  # noqa: PLC0415

    application = create_app()
    actor = _unknown_role_actor() if role is None else _account(role)
    application.dependency_overrides[get_current_user] = lambda: actor
    application.dependency_overrides[get_redis] = lambda: fakeredis.FakeRedis()

    def _db():
        yield MagicMock()

    application.dependency_overrides[get_db] = _db
    csrf = {"headers": {"X-CSRF-Token": "tok"}, "cookies": {"medhub_csrf": "tok"}}
    method, path = route.split(" ", 1)
    path = path.replace("{id}", str(uuid.uuid4()))
    with ExitStack() as stack:
        stack.enter_context(patch.object(AuditService, "record"))
        for target, value in allowed_patches:
            stack.enter_context(patch(target, return_value=value))
        resp = TestClient(application, raise_server_exceptions=False).request(
            method, path, json={"doctorId": str(uuid.uuid4())} if method == "POST" else None, **csrf
        )
    return resp.status_code, resp.json() if resp.content else {}


# route -> (role allowed, refusal detail, patches that let an allowed call finish, allowed status)
ROUTER_RULES = {
    "POST /api/v1/accounts/{id}/unlock": (
        UserType.SYSADMIN,
        "Only SYSADMIN can unlock accounts.",
        [("app.db.repositories.account_repo.AccountRepository.get_by_id", None)],
        404,
    ),
    "GET /api/v1/modules": (
        UserType.SYSADMIN,
        "Only sysadmins may list installed modules.",
        [("app.db.repositories.module_repo.ModuleRepository.list_installed", [])],
        200,
    ),
    "POST /api/v1/consents": (
        UserType.PATIENT,
        "Only patients may grant consent.",
        [("app.authz.consent.ConsentService.grant", MagicMock())],
        None,  # allowed: any status except the 403 refusal (the stub result is not serialisable)
    ),
    "DELETE /api/v1/consents/{id}": (
        UserType.PATIENT,
        "Only patients may revoke consent.",
        [("app.db.repositories.consent_repo.ConsentRepository.get", None)],
        404,
    ),
    "GET /api/v1/me/consents": (
        UserType.PATIENT,
        "Only patients may list their consent grants.",
        [("app.authz.consent.ConsentService.list_grants", [])],
        200,
    ),
    "GET /api/v1/clinical-entries/patients": (
        UserType.DOCTOR,
        "Only doctors can access the patient roster.",
        [("app.clinical.service.ClinicalDataService.list_accessible_patients", [])],
        200,
    ),
}
ROUTER_CASES = [(route, role) for route in ROUTER_RULES for role in ROLES]


@pytest.mark.parametrize(("route", "role"), ROUTER_CASES)
def test_router_check_by_role(route: str, role: UserType) -> None:
    """SR-005 AC 1/3, SR-008: each router decision allows its one role, 403 + message otherwise."""
    allowed_role, detail, patches, allowed_status = ROUTER_RULES[route]
    status, body = _router_call(role, route, patches)
    if role is allowed_role:
        assert status != 403
        if allowed_status is not None:
            assert status == allowed_status
    else:
        assert status == 403
        assert body["detail"] == detail


@pytest.mark.parametrize("route", list(ROUTER_RULES))
def test_router_check_denies_actor_with_no_known_role(route: str) -> None:
    """SR-005 AC 1: deny by default for an actor with no known role."""
    _, detail, patches, _ = ROUTER_RULES[route]
    status, body = _router_call(None, route, patches)
    assert status == 403
    assert body["detail"] == detail
