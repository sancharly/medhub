"""Clinical entry API schemas (TASK-044)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ClinicalEntryCreate(_CamelModel):
    occurred_at: datetime
    description: str


class ClinicalEntryResponse(_CamelModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    author_id: uuid.UUID
    occurred_at: datetime
    description: str
    created_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
