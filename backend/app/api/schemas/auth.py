"""Auth API schemas (TASK-060)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.db.models.account import UserType


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class LoginRequest(_CamelModel):
    email: str
    password: str


class MeSummary(_CamelModel):
    id: uuid.UUID
    first_name: str | None
    surname: str | None
    account_type: UserType

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class LoginResponse(_CamelModel):
    user: MeSummary
    must_change_password: bool
    evicted_session: bool


class PasswordChangeRequest(_CamelModel):
    current_password: str
    new_password: str
    confirm_new_password: str


class SessionExtendResponse(_CamelModel):
    expires_at: datetime
