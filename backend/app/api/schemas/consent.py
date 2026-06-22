"""Consent API schemas (TASK-064)."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.db.models.consent import ConsentSourceType


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ConsentGrantRequest(_CamelModel):
    doctor_id: uuid.UUID
    # Only MANUAL grants may be created via the API; appointment grants are
    # created automatically by the appointment confirm flow (TASK-049).
    source: Literal["MANUAL"] = "MANUAL"


class ConsentGrantResponse(_CamelModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    source_type: ConsentSourceType
    appointment_id: uuid.UUID | None
    active: bool
