"""Account API schemas (TASK-061)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.db.models.account import AccountStatus, UserType


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AccountCreateRequest(_CamelModel):
    email: str
    user_type: UserType
    first_name: str | None = None
    surname: str | None = None
    date_of_birth: date | None = None


class AccountResponse(_CamelModel):
    id: uuid.UUID
    email: str
    user_type: UserType
    state: AccountStatus = Field(validation_alias="status")
    first_name: str | None
    surname: str | None
    date_of_birth: date | None
    created_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class AccountListResponse(_CamelModel):
    items: list[AccountResponse]
    total: int
    page: int
    page_size: int


class AdminAccountResponse(_CamelModel):
    id: uuid.UUID
    account_type: UserType
    first_name: str | None
    family_name: str | None
    date_of_birth: date | None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class AdminAccountListResponse(_CamelModel):
    items: list[AdminAccountResponse]
    total: int
    page: int
    page_size: int


class ActivationTokenStatus(_CamelModel):
    valid: bool
    account_id: uuid.UUID | None = None


class ActivationRequest(_CamelModel):
    account_id: uuid.UUID
    password: str
    confirm_password: str
