"""AppointmentService — create, transition, and list appointments (TASK-047/048/049/051)."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.api.errors import NotFoundError, ValidationProblem
from app.appointments.state import transition
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.authz.appointment_visibility import can_view_appointment
from app.authz.service import AuthorizationService, Resource
from app.db.models.account import Account, UserType
from app.db.models.appointment import Appointment, AppointmentState
from app.db.models.audit import AuditOutcome
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.appointment_repo import AppointmentRepository


class AppointmentService:
    def __init__(
        self,
        appt_repo: AppointmentRepository,
        account_repo: AccountRepository,
        audit_svc: AuditService,
        authz_svc: AuthorizationService,
        consent_svc: object,
    ) -> None:
        self._repo = appt_repo
        self._account_repo = account_repo
        self._audit_svc = audit_svc
        self._authz_svc = authz_svc
        self._consent_svc = consent_svc

    def create(
        self,
        actor: Account,
        doctor_id: uuid.UUID,
        patient_id: uuid.UUID,
        scheduled_at: datetime,
    ) -> Appointment:
        """Create a new appointment. Admin/SysAdmin/Doctor only."""
        self._authz_svc.authorize(
            actor,
            "appointment:create",
            Resource(resource_type="appointment", owner_id=None, patient_id=None),
        )

        doctor = self._account_repo.get_by_id(doctor_id)
        if doctor is None or doctor.user_type != UserType.DOCTOR:
            raise ValidationProblem(f"Account {doctor_id} is not a valid doctor.")

        patient = self._account_repo.get_by_id(patient_id)
        if patient is None or patient.user_type != UserType.PATIENT:
            raise ValidationProblem(f"Account {patient_id} is not a valid patient.")

        appointment = Appointment(
            doctor_id=doctor_id,
            patient_id=patient_id,
            scheduled_at=scheduled_at,
            state=AppointmentState.PENDING,
        )
        self._repo.add(appointment)

        # Enqueue email notification (best-effort)
        try:
            from app.workers.email_tasks import send_appointment_notification  # noqa: PLC0415

            send_appointment_notification.delay(str(appointment.id))
        except Exception:
            pass

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.APPOINTMENT_CREATE,
            target_type="appointment",
            target_id=str(appointment.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        return appointment

    def confirm(self, actor: Account, appointment_id: uuid.UUID) -> Appointment:
        """Patient confirms their appointment."""
        appointment = self._repo.get(appointment_id)
        if appointment is None:
            raise NotFoundError(f"Appointment {appointment_id} not found.")

        self._authz_svc.authorize(
            actor,
            "appointment:confirm",
            Resource(
                resource_type="appointment",
                owner_id=appointment.patient_id,
                patient_id=appointment.patient_id,
            ),
        )

        transition(appointment, AppointmentState.CONFIRMED)
        appointment.state = AppointmentState.CONFIRMED
        self._repo.update_state(appointment, AppointmentState.CONFIRMED)

        # Grant consent via appointment (TASK-049)
        self._consent_svc.grant(  # type: ignore[attr-defined]
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            source=f"APPOINTMENT:{appointment.id}",
        )

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.APPOINTMENT_CONFIRM,
            target_type="appointment",
            target_id=str(appointment.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        return appointment

    def decline(self, actor: Account, appointment_id: uuid.UUID) -> Appointment:
        """Patient declines their appointment."""
        appointment = self._repo.get(appointment_id)
        if appointment is None:
            raise NotFoundError(f"Appointment {appointment_id} not found.")

        self._authz_svc.authorize(
            actor,
            "appointment:decline",
            Resource(
                resource_type="appointment",
                owner_id=appointment.patient_id,
                patient_id=appointment.patient_id,
            ),
        )

        transition(appointment, AppointmentState.DECLINED)
        appointment.state = AppointmentState.DECLINED
        self._repo.update_state(appointment, AppointmentState.DECLINED)

        # Revoke consent granted via this appointment (TASK-049)
        self._consent_svc.revoke(  # type: ignore[attr-defined]
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            source=f"APPOINTMENT:{appointment.id}",
        )

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.APPOINTMENT_DECLINE,
            target_type="appointment",
            target_id=str(appointment.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        return appointment

    def list_for(self, actor: Account) -> list[Appointment]:
        """List appointments visible to the actor."""
        self._authz_svc.authorize(
            actor,
            "appointment:list",
            Resource(resource_type="appointment", owner_id=None, patient_id=None),
        )
        if actor.user_type in (UserType.ADMIN, UserType.SYSADMIN):
            return self._repo.list_all()
        if actor.user_type == UserType.DOCTOR:
            return self._repo.list_for_doctor(actor.id)
        if actor.user_type == UserType.PATIENT:
            return self._repo.list_for_patient(actor.id)
        return []

    def get(self, actor: Account, appointment_id: uuid.UUID) -> Appointment:
        """Get a single appointment. Returns NotFoundError if not visible (SR-011 AC-4)."""
        appointment = self._repo.get(appointment_id)
        if appointment is None or not can_view_appointment(actor, appointment):
            raise NotFoundError(f"Appointment {appointment_id} not found.")
        return appointment
