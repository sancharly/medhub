"""AnonymizedDataset repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.anonymized_dataset import AnonymizedDataset
from app.db.repositories.base import Repository


class AnonymizedDatasetRepository(Repository[AnonymizedDataset]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, AnonymizedDataset)

    def get_by_code_hash(self, code_hash: str) -> AnonymizedDataset | None:
        result = self._session.execute(
            select(AnonymizedDataset).where(AnonymizedDataset.code_hash == code_hash)
        )
        return result.scalar_one_or_none()
