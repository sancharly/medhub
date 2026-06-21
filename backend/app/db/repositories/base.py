"""Generic repository base class."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

type ModelT = object


class Repository[ModelT]:
    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self._session = session
        self._model = model

    def get(self, id: uuid.UUID) -> ModelT | None:
        return self._session.get(self._model, id)

    def list(self) -> list[ModelT]:
        result = self._session.execute(select(self._model))
        return list(result.scalars().all())

    def add(self, instance: ModelT) -> ModelT:
        self._session.add(instance)
        self._session.flush()
        return instance

    def delete(self, instance: ModelT) -> None:
        self._session.delete(instance)
        self._session.flush()
