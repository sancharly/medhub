"""Encryption-at-rest utilities using AES-256-GCM (SR-022, ADR-0018).

Key material comes exclusively from Settings: the current key (``at_rest_encryption_key``) under
the identifier ``at_rest_encryption_key_id``, and optional retired keys
(``at_rest_encryption_retired_keys``, ``id:key`` entries) that are used for decryption only.
Every key is URL-safe base64 of 32 bytes.

Envelope (ADR-0018)::

    mh1:<kid>:<base64url(nonce || AES-GCM(key, nonce, plaintext, aad))>      aad = b"mh1:<kid>"

``:`` is not in the base64url alphabet, so a prefixed value is never mistaken for a legacy
(unprefixed) one. The prefix is the associated data, so editing the key id in a stored value fails
authentication (``InvalidTag``) instead of selecting another key. ``decrypt`` finds the key by the
id in the prefix and uses that key only: no prefix, an unknown id or a failed tag raises, and the
error names the key id at most, never the value. Nothing falls back to another key.

DECISION — columns using EncryptedString (app.db.types):
  - ClinicalEntry.description  (clinical_entry.description)
      Rationale: free-text clinical narrative is the highest-sensitivity PHI in the
      schema. Infrastructure-level volume encryption is the primary control; this
      column applies defense-in-depth field-level encryption so the row is not
      readable in plaintext from a DB dump alone (SR-022.2/3).

All other columns rely on the encrypted Postgres volume (TASK-004) for at-rest
protection. Additional columns may be added here as sensitivity is assessed.
"""

import base64
import binascii
import functools
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings
from app.core.secret_settings import AT_REST_KEY_BYTES, KEY_ID_PATTERN, split_retired_keys

_NONCE_SIZE = 12  # 96-bit nonce for AES-GCM
_TAG_SIZE = 16
_PREFIX = "mh1"


class CiphertextFormatError(ValueError):
    """The value is not an ``mh1:<kid>:<payload>`` envelope (for example a legacy value)."""


class UnknownKeyError(ValueError):
    """The envelope names a key id that is not configured. Carries the id, never the value."""

    def __init__(self, key_id: str) -> None:
        super().__init__(f"field ciphertext names key id '{key_id}', which is not configured")
        self.key_id = key_id


@dataclass(frozen=True)
class Keyring:
    """The current key id and every configured key (current and retired) by id."""

    current_id: str
    keys: dict[str, bytes]


def _decode_key(raw: str, name: str) -> bytes:
    try:
        key = base64.urlsafe_b64decode(raw.strip().encode())
    except Exception:  # noqa: BLE001 - never include the value or the decoder's message
        error = ValueError(f"{name} is not valid base64")
        raise error from None
    if len(key) != AT_REST_KEY_BYTES:
        raise ValueError(f"{name} must decode to {AT_REST_KEY_BYTES} bytes for AES-256")
    return key


@functools.lru_cache(maxsize=8)
def _build_keyring(key: str, key_id: str, retired: str | None) -> Keyring:
    keys = {key_id: _decode_key(key, "at_rest_encryption_key")}
    for retired_id, retired_key in split_retired_keys(retired):
        if retired_id in keys:
            raise ValueError(f"at_rest_encryption_retired_keys repeats key id '{retired_id}'")
        keys[retired_id] = _decode_key(retired_key, "at_rest_encryption_retired_keys")
    return Keyring(current_id=key_id, keys=keys)


def get_keyring() -> Keyring:
    """The keyring of the configured settings; built once per distinct configuration."""
    settings = get_settings()
    retired = settings.at_rest_encryption_retired_keys
    return _build_keyring(
        settings.at_rest_encryption_key.get_secret_value(),
        settings.at_rest_encryption_key_id,
        retired.get_secret_value() if retired else None,
    )


def _aad(key_id: str) -> bytes:
    return f"{_PREFIX}:{key_id}".encode()


def encrypt(value: str) -> str:
    """AES-256-GCM encrypt under the current key. Returns ``mh1:<kid>:<base64url payload>``."""
    ring = get_keyring()
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = AESGCM(ring.keys[ring.current_id]).encrypt(
        nonce, value.encode(), _aad(ring.current_id)
    )
    payload = base64.urlsafe_b64encode(nonce + ciphertext).decode()
    return f"{_PREFIX}:{ring.current_id}:{payload}"


def parse(value: str) -> tuple[str, bytes]:
    """Split an envelope into its key id and raw ``nonce || ciphertext``.

    Raises ``CiphertextFormatError`` for anything that is not ``mh1:<kid>:<base64url>``. The error
    never contains the value.
    """
    parts = value.split(":", 2)
    if len(parts) != 3 or parts[0] != _PREFIX or not KEY_ID_PATTERN.fullmatch(parts[1]):
        raise CiphertextFormatError("field ciphertext is not an mh1:<key id>:<payload> envelope")
    try:
        raw = base64.b64decode(parts[2].encode(), altchars=b"-_", validate=True)
    except (binascii.Error, ValueError):
        raw = b""
        canonical = False
    else:
        canonical = base64.urlsafe_b64encode(raw).decode() == parts[2]  # URL-safe, padded, exact
    if not canonical:
        raise CiphertextFormatError("field ciphertext payload is not valid base64url")
    if len(raw) < _NONCE_SIZE + _TAG_SIZE:
        raise CiphertextFormatError("field ciphertext payload is too short")
    return parts[1], raw


def decrypt(value: str) -> str:
    """Decrypt an envelope with the key its prefix names.

    Raises ``CiphertextFormatError`` (no envelope), ``UnknownKeyError`` (key id not configured) or
    ``cryptography.exceptions.InvalidTag`` (wrong key, edited prefix or tampered payload).
    """
    key_id, raw = parse(value)
    key = get_keyring().keys.get(key_id)
    if key is None:
        raise UnknownKeyError(key_id)
    nonce, ciphertext = raw[:_NONCE_SIZE], raw[_NONCE_SIZE:]
    return AESGCM(key).decrypt(nonce, ciphertext, _aad(key_id)).decode()


def decrypt_legacy(value: str, key: bytes) -> str:
    """Decrypt a pre-envelope value: ``base64url(nonce || ciphertext)``, no prefix, no AAD.

    Public because TASK-194's migration and TASK-195's command import it; they are its only
    callers (none in ``app/`` today). ``EncryptedString`` never calls it, so a legacy value read
    through the ORM is refused (``CiphertextFormatError`` from ``decrypt``).
    """
    raw = base64.urlsafe_b64decode(value.encode())
    return AESGCM(key).decrypt(raw[:_NONCE_SIZE], raw[_NONCE_SIZE:], None).decode()
