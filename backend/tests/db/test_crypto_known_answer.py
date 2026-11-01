"""Known-answer tests for field encryption at rest (TASK-163, TASK-193; CR-004 SR-022 AC 6;
TS-008 TC-008.5, TC-008.9).

LEGACY_ENVELOPE is a pre-envelope value (``base64url(nonce || ciphertext)``, no prefix, no
associated data). It was produced under cryptography 49.0.0 on 2026-10-29, before the lock moved
to 50.0.2, with MedHub's own ``encrypt`` of that date from the fixed KEY, NONCE and PLAINTEXT
below and ``os.urandom`` patched to return NONCE (the only patch). It shows that a value already
at rest under 49.0.0 still decrypts under the locked version (CR-003 AC-9, §7.4.3). Since
TASK-193 only ``decrypt_legacy`` reads it, as TASK-194 will when it converts existing rows.

ENVELOPE is the ``mh1:`` form of the same plaintext under key id ``k1``. It was NOT made with
MedHub's ``encrypt``: it was computed on 2026-11-01 under cryptography 50.0.2 with ``AESGCM``
directly (key KEY, nonce NONCE, associated data ``b"mh1:k1"``), so the test compares the
implementation with an independent construction. KEY and NONCE are test values used nowhere else.
They need no database.
"""

import base64
from unittest.mock import MagicMock, patch

import pytest
from cryptography.exceptions import InvalidTag
from pydantic import SecretStr

import app.db.crypto as crypto_mod
from app.db.crypto import CiphertextFormatError, decrypt, decrypt_legacy, encrypt

KEY = "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="  # bytes 0x00..0x1f, URL-safe base64
NONCE = bytes.fromhex("a0a1a2a3a4a5a6a7a8a9aaab")
PLAINTEXT = "Nota clínica: dolor torácico — paciente José Núñez"
LEGACY_ENVELOPE = (
    "oKGio6SlpqeoqaqrqHcITGWobnzPC-6wZkDguh_ANmKywy0eX69F7xzEVeNS4mePzkE6WDHoYehDFfA67jsIi9gT"
    "qxs7MiPYZfXcEUkt4G4jS5k_QA=="
)
ENVELOPE = (
    "mh1:k1:oKGio6SlpqeoqaqrqHcITGWobnzPC-6wZkDguh_ANmKywy0eX69F7xzEVeNS4mePzkE6WDHoYehDFfA67jsIi9gT"
    "qxs7c8zjaNpbCBRV-rPIkp1Qcg=="
)


@pytest.fixture(autouse=True)
def fixed_key(monkeypatch):
    settings = MagicMock()
    settings.at_rest_encryption_key = SecretStr(KEY)
    settings.at_rest_encryption_key_id = "k1"
    settings.at_rest_encryption_retired_keys = None
    monkeypatch.setattr(crypto_mod, "get_settings", lambda: settings)


# SR-022 AC 6 / TC-008.9: a fixed key, nonce and kid give a fixed envelope
def test_encrypt_is_byte_identical_for_fixed_key_nonce_and_kid():
    with patch("app.db.crypto.os.urandom", return_value=NONCE):
        assert encrypt(PLAINTEXT) == ENVELOPE


def test_decrypts_the_known_envelope():
    assert decrypt(ENVELOPE) == PLAINTEXT


def test_tampered_tag_is_rejected():
    prefix, kid, payload = ENVELOPE.split(":", 2)
    raw = bytearray(base64.urlsafe_b64decode(payload))
    raw[-1] ^= 0x01  # last byte belongs to the 16-byte GCM tag
    tampered = f"{prefix}:{kid}:" + base64.urlsafe_b64encode(bytes(raw)).decode()
    with pytest.raises(InvalidTag):
        decrypt(tampered)


# TC-008.5: a value encrypted at rest under cryptography 49.0.0 still decrypts under the lock
def test_decrypts_ciphertext_written_under_49_0_0_with_the_legacy_reader():
    assert decrypt_legacy(LEGACY_ENVELOPE, base64.urlsafe_b64decode(KEY)) == PLAINTEXT


def test_the_application_reader_refuses_the_legacy_value():
    with pytest.raises(CiphertextFormatError):
        decrypt(LEGACY_ENVELOPE)
