"""Attachment API schemas (TASK-045/046)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AttachmentResponse(_CamelModel):
    id: uuid.UUID
    clinical_entry_id: uuid.UUID
    patient_id: uuid.UUID
    filename: str
    content_type: str
    size: int
    checksum: str
    created_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
