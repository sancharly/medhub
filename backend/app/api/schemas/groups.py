"""Group API schemas (TASK-040/041/042)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class GroupCreate(_CamelModel):
    name: str


class GroupMemberResponse(_CamelModel):
    account_id: uuid.UUID
    name: str
    membership_source: str


class GroupResponse(_CamelModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    members: list[GroupMemberResponse] = []
    enabled_modules: list[str] = []

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class AddMemberRequest(_CamelModel):
    account_id: uuid.UUID


class SetModuleEnabledRequest(_CamelModel):
    enabled: bool
