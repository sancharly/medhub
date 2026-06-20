"""Crypto tests (TASK-013): AES-256-GCM encrypt/decrypt."""

import base64
import os
import uuid

import pytest
from sqlalchemy import Column, String
from sqlalchemy.orm import DeclarativeBase, Session

from app.db.crypto import decrypt, encrypt

# Ensure Docker socket on macOS
_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"


def _make_key() -> str:
    """Generate a valid 32-byte base64url key."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


@pytest.fixture(autouse=True)
def mock_settings_key(monkeypatch):
    """Patch get_settings so tests don't need a real .env file."""
    key = _make_key()
    from unittest.mock import MagicMock

    from pydantic import SecretStr

    settings = MagicMock()
    settings.at_rest_encryption_key = SecretStr(key)

    import app.db.crypto as crypto_mod

    monkeypatch.setattr(crypto_mod, "get_settings", lambda: settings)
    return key


def test_round_trip(mock_settings_key):
    plaintext = "sensitive patient data"
    ciphertext = encrypt(plaintext)
    assert decrypt(ciphertext) == plaintext


def test_ciphertext_differs_from_plaintext(mock_settings_key):
    plaintext = "hello world"
    ciphertext = encrypt(plaintext)
    assert ciphertext != plaintext


def test_different_ciphertexts_for_same_plaintext(mock_settings_key):
    """AES-GCM with random nonce produces different ciphertext each time."""
    pt = "same input"
    c1 = encrypt(pt)
    c2 = encrypt(pt)
    assert c1 != c2


def test_wrong_key_fails_decryption():
    """Decrypting with a different key raises an exception — no plaintext fallback."""
    key1 = base64.urlsafe_b64encode(os.urandom(32)).decode()
    key2 = base64.urlsafe_b64encode(os.urandom(32)).decode()

    from unittest.mock import MagicMock

    from pydantic import SecretStr

    import app.db.crypto as crypto_mod

    settings1 = MagicMock()
    settings1.at_rest_encryption_key = SecretStr(key1)

    settings2 = MagicMock()
    settings2.at_rest_encryption_key = SecretStr(key2)

    # Encrypt with key1
    original = crypto_mod.get_settings
    crypto_mod.get_settings = lambda: settings1
    ciphertext = encrypt("secret value")

    # Decrypt with key2 — must fail
    crypto_mod.get_settings = lambda: settings2
    with pytest.raises(Exception):
        decrypt(ciphertext)

    crypto_mod.get_settings = original


def test_encrypted_string_type_stores_ciphertext(pg_engine, db_session):
    """EncryptedString stores ciphertext in the DB, returns plaintext on read."""
    from app.db.types import EncryptedString

    class EncBase(DeclarativeBase):
        pass

    class SecretModel(EncBase):
        __tablename__ = "secret_model_test"
        id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        sensitive: str = Column(EncryptedString)  # type: ignore[assignment]

    EncBase.metadata.create_all(pg_engine)

    plaintext = "very secret"
    with Session(pg_engine) as sess:
        obj = SecretModel(sensitive=plaintext)
        sess.add(obj)
        sess.commit()
        obj_id = obj.id

    # Read back via ORM — should be decrypted
    with Session(pg_engine) as sess:
        fetched = sess.get(SecretModel, obj_id)
        assert fetched is not None
        assert fetched.sensitive == plaintext

    # Read the raw DB value — must NOT be plaintext
    from sqlalchemy import text

    with pg_engine.connect() as conn:
        row = conn.execute(
            text("SELECT sensitive FROM secret_model_test WHERE id = :id"), {"id": obj_id}
        ).fetchone()
        assert row is not None
        raw_value = row[0]
        assert raw_value != plaintext
        assert plaintext not in raw_value

    EncBase.metadata.drop_all(pg_engine)


def test_secret_str_not_in_repr():
    """at_rest_encryption_key SecretStr must not leak in repr."""
    from pydantic import SecretStr

    key = _make_key()
    s = SecretStr(key)
    assert key not in repr(s)
    assert key not in str(s)
