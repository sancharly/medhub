"""Me API schemas (TASK-067)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.db.models.account import AccountStatus, UserType


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class MeResponse(_CamelModel):
    id: uuid.UUID
    email: str
    user_type: UserType
    status: AccountStatus
    first_name: str | None
    surname: str | None
    date_of_birth: date | None
    created_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class MeModulesResponse(_CamelModel):
    modules: list[str]
