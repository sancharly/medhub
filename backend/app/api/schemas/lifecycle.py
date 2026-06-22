"""Lifecycle & anonymized data API schemas (TASK-062)."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.db.models.account import UserType


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DeleteConfirmationRequest(_CamelModel):
    confirm_email: str
    confirm_account_type: UserType


class DeletionResponse(_CamelModel):
    dataset_id: uuid.UUID
    message: str


class AnonymizedRetrieveRequest(_CamelModel):
    retrieval_code: str


class AnonymizedRetrieveResponse(_CamelModel):
    dataset_id: uuid.UUID
    payload: dict[str, Any]
