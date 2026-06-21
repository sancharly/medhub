"""Appointment API schemas (TASK-047/048/051)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.db.models.appointment import AppointmentState


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AppointmentCreate(_CamelModel):
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    scheduled_at: datetime


class AppointmentResponse(_CamelModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    scheduled_at: datetime
    state: AppointmentState
    created_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
