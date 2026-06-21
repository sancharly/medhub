"""Encryption-at-rest utilities using AES-256-GCM (SR-022).

Key material comes exclusively from Settings.at_rest_encryption_key.
The key must be a 32-byte value encoded as URL-safe base64 (44 chars with padding).
"""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

_NONCE_SIZE = 12  # 96-bit nonce for AES-GCM


def _get_key() -> bytes:
    """Decode and validate the operator-managed AES-256 key.

    Expects a URL-safe base64-encoded 32-byte key (output of base64.urlsafe_b64encode
    of 32 random bytes). Fails fast on startup if missing or wrong length.
    """
    raw = get_settings().at_rest_encryption_key.get_secret_value()
    try:
        key_bytes = base64.urlsafe_b64decode(raw.encode())
    except Exception as exc:
        raise ValueError("at_rest_encryption_key is not valid base64") from exc
    if len(key_bytes) != 32:
        raise ValueError(
            f"at_rest_encryption_key must decode to 32 bytes for AES-256, got {len(key_bytes)}"
        )
    return key_bytes


def encrypt(value: str) -> str:
    """AES-256-GCM encrypt. Returns nonce||ciphertext as URL-safe base64."""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, value.encode(), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt(value: str) -> str:
    """AES-256-GCM decrypt. Raises cryptography.exceptions.InvalidTag on bad key/ciphertext."""
    key = _get_key()
    aesgcm = AESGCM(key)
    raw = base64.urlsafe_b64decode(value.encode())
    nonce, ciphertext = raw[:_NONCE_SIZE], raw[_NONCE_SIZE:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
