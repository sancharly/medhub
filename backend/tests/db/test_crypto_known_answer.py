"""Known-answer test for field encryption at rest (TASK-163, CR-003 AC-9, TS-008 TC-008.5).

ENVELOPE below was produced under cryptography 49.0.0 on 2026-10-29, before the lock moved to
50.0.2. It was made with MedHub's own ``app.db.crypto.encrypt`` in a scratch script run from
``backend/`` with ``uv run`` (``cryptography.__version__`` printed ``49.0.0``), from the fixed
KEY, NONCE and PLAINTEXT below and with ``os.urandom`` patched to return NONCE (the only patch).
KEY and NONCE are test values and are not used anywhere else.

These tests show that a value already encrypted at rest under 49.0.0 still decrypts under the
locked version, and that the locked version writes the identical bytes for the same key and nonce
(AES-GCM is deterministic for a fixed key and nonce), so data it writes stays readable by the
old version. They need no database.
"""

import base64
from unittest.mock import MagicMock, patch

import pytest
from cryptography.exceptions import InvalidTag
from pydantic import SecretStr

import app.db.crypto as crypto_mod
from app.db.crypto import decrypt, encrypt

KEY = "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="  # bytes 0x00..0x1f, URL-safe base64
NONCE = bytes.fromhex("a0a1a2a3a4a5a6a7a8a9aaab")
PLAINTEXT = "Nota clínica: dolor torácico — paciente José Núñez"
ENVELOPE = (
    "oKGio6SlpqeoqaqrqHcITGWobnzPC-6wZkDguh_ANmKywy0eX69F7xzEVeNS4mePzkE6WDHoYehDFfA67jsIi9gT"
    "qxs7MiPYZfXcEUkt4G4jS5k_QA=="
)


@pytest.fixture(autouse=True)
def fixed_key(monkeypatch):
    settings = MagicMock()
    settings.at_rest_encryption_key = SecretStr(KEY)
    monkeypatch.setattr(crypto_mod, "get_settings", lambda: settings)


def test_decrypts_ciphertext_written_under_49_0_0():
    assert decrypt(ENVELOPE) == PLAINTEXT


def test_encrypt_is_byte_identical_for_fixed_nonce():
    with patch("app.db.crypto.os.urandom", return_value=NONCE):
        assert encrypt(PLAINTEXT) == ENVELOPE


def test_tampered_tag_is_rejected():
    raw = bytearray(base64.urlsafe_b64decode(ENVELOPE))
    raw[-1] ^= 0x01  # last byte belongs to the 16-byte GCM tag
    tampered = base64.urlsafe_b64encode(bytes(raw)).decode()
    with pytest.raises(InvalidTag):
        decrypt(tampered)
