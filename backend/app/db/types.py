"""Custom SQLAlchemy column types."""

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from app.db.crypto import decrypt, encrypt


class EncryptedString(TypeDecorator[str]):
    """Transparently encrypts/decrypts string columns using AES-256-GCM."""

    impl = String
    # False: encrypt/decrypt reads a global key from Settings; caching compiled
    # statements across key-rotation or test monkeypatching would be incorrect.
    cache_ok = False

    def process_bind_param(self, value: str | None, dialect: object) -> str | None:
        if value is None:
            return None
        return encrypt(value)

    def process_result_value(self, value: str | None, dialect: object) -> str | None:
        if value is None:
            return None
        return decrypt(value)
