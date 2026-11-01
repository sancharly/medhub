"""Crypto tests (TASK-013, TASK-193; SR-022 AC 6; TS-008 TC-008.2, TC-008.9): the AES-256-GCM
envelope ``mh1:<kid>:<payload>``, multi-key decryption and refusals."""

import base64
import os
import uuid

import pytest
from cryptography.exceptions import InvalidTag
from sqlalchemy import Column, String
from sqlalchemy.orm import DeclarativeBase, Session

import app.db.crypto as crypto_mod
from app.db.crypto import CiphertextFormatError, UnknownKeyError, decrypt, encrypt

# Ensure Docker socket on macOS
_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"


def _make_key() -> str:
    """Generate a valid 32-byte base64url key."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def _use(monkeypatch, key: str, kid: str = "k1", retired: str | None = None) -> None:
    """Point app.db.crypto at these key settings."""
    from unittest.mock import MagicMock

    from pydantic import SecretStr

    settings = MagicMock()
    settings.at_rest_encryption_key = SecretStr(key)
    settings.at_rest_encryption_key_id = kid
    settings.at_rest_encryption_retired_keys = SecretStr(retired) if retired else None
    monkeypatch.setattr(crypto_mod, "get_settings", lambda: settings)


@pytest.fixture(autouse=True)
def mock_settings_key(monkeypatch):
    """Patch get_settings so tests don't need a real .env file."""
    key = _make_key()
    _use(monkeypatch, key)
    return key


# SR-022 AC 6: round trip under the current key
def test_round_trip(mock_settings_key):
    plaintext = "sensitive patient data"
    ciphertext = encrypt(plaintext)
    assert decrypt(ciphertext) == plaintext


def test_ciphertext_differs_from_plaintext(mock_settings_key):
    plaintext = "hello world"
    ciphertext = encrypt(plaintext)
    assert ciphertext != plaintext
    assert plaintext not in ciphertext


def test_different_ciphertexts_for_same_plaintext(mock_settings_key):
    """AES-GCM with random nonce produces different ciphertext each time."""
    pt = "same input"
    c1 = encrypt(pt)
    c2 = encrypt(pt)
    assert c1 != c2


# SR-022 AC 6: the identifier of the current key is in every new value
def test_new_values_carry_the_current_key_id_in_the_prefix(monkeypatch, mock_settings_key):
    assert encrypt("x").startswith("mh1:k1:")
    _use(monkeypatch, mock_settings_key, kid="2026-11-a")
    value = encrypt("x")
    assert value.startswith("mh1:2026-11-a:")
    assert value.count(":") == 2  # ':' is not in the base64url payload


# SR-022 AC 6: a value under a retired key decrypts after the current key changes
def test_value_under_a_retired_key_decrypts_after_rotation(monkeypatch, mock_settings_key):
    old_key = mock_settings_key
    old_value = encrypt("written under the old key")
    new_key = _make_key()
    _use(monkeypatch, new_key, kid="k2", retired=f"k1:{old_key}")
    assert decrypt(old_value) == "written under the old key"
    new_value = encrypt("written under the new key")
    assert new_value.startswith("mh1:k2:")
    assert decrypt(new_value) == "written under the new key"


def test_every_configured_key_decrypts_its_own_values(monkeypatch, mock_settings_key):
    keys = {"a": mock_settings_key, "b": _make_key(), "c": _make_key()}
    values = {}
    for kid, key in keys.items():
        _use(monkeypatch, key, kid=kid)
        values[kid] = encrypt(f"value {kid}")
    retired = f"a:{keys['a']},b:{keys['b']}"
    _use(monkeypatch, keys["c"], kid="c", retired=retired)
    assert {kid: decrypt(v) for kid, v in values.items()} == {k: f"value {k}" for k in keys}


# SR-022 AC 6: an unknown key id is refused, never decrypted with another key, never returned
def test_unknown_key_id_is_refused_without_the_value(monkeypatch, mock_settings_key):
    value = encrypt("PHI marker text")
    _use(monkeypatch, _make_key(), kid="k2")  # k1 is no longer configured
    with pytest.raises(UnknownKeyError) as exc:
        decrypt(value)
    assert exc.value.key_id == "k1"
    message = str(exc.value)
    assert "k1" in message
    assert value not in message and value.split(":", 2)[2] not in message
    assert "PHI marker text" not in message


def test_encrypted_string_refuses_an_unknown_key_instead_of_returning_ciphertext(
    monkeypatch, mock_settings_key
):
    from app.db.types import EncryptedString

    value = encrypt("PHI marker text")
    _use(monkeypatch, _make_key(), kid="k2")
    with pytest.raises(UnknownKeyError):
        EncryptedString().process_result_value(value, None)


def test_no_fallback_to_another_key_when_the_named_key_fails(monkeypatch, mock_settings_key):
    """The prefix names key 'a'; 'a' is configured with a different key. 'b' holds the right key
    but is never tried: the result is InvalidTag, not plaintext."""
    right = mock_settings_key
    value = encrypt("secret")  # under kid k1 = right
    _use(monkeypatch, _make_key(), kid="b", retired=f"k1:{_make_key()}")
    with pytest.raises(InvalidTag):
        decrypt(value)
    _use(monkeypatch, right, kid="b", retired=f"k1:{_make_key()}")
    with pytest.raises(InvalidTag):
        decrypt(value)


# SR-022 AC 6: the prefix is associated data, so an edited key id fails authentication
def test_edited_key_id_to_another_configured_key_fails_authentication(
    monkeypatch, mock_settings_key
):
    other = _make_key()
    _use(monkeypatch, mock_settings_key, kid="k1", retired=f"k2:{other}")
    value = encrypt("secret")
    assert value.startswith("mh1:k1:")
    with pytest.raises(InvalidTag):
        decrypt(value.replace("mh1:k1:", "mh1:k2:", 1))


def test_edited_key_id_with_the_same_key_under_both_ids_fails_authentication(
    monkeypatch, mock_settings_key
):
    """Even when both ids resolve to the SAME key bytes, the edited prefix no longer matches the
    associated data: this isolates the AAD binding from the key selection."""
    _use(monkeypatch, mock_settings_key, kid="k1", retired=f"k2:{mock_settings_key}")
    value = encrypt("secret")
    with pytest.raises(InvalidTag):
        decrypt(value.replace("mh1:k1:", "mh1:k2:", 1))


def test_edited_version_marker_is_refused(mock_settings_key):
    value = encrypt("secret")
    with pytest.raises(CiphertextFormatError):
        decrypt(value.replace("mh1:", "mh2:", 1))


def test_tampered_payload_fails_authentication(mock_settings_key):
    prefix, kid, payload = encrypt("secret").split(":", 2)
    raw = bytearray(base64.urlsafe_b64decode(payload))
    raw[14] ^= 0x01
    tampered = f"{prefix}:{kid}:" + base64.urlsafe_b64encode(bytes(raw)).decode()
    with pytest.raises(InvalidTag):
        decrypt(tampered)


# SR-022 AC 6: a value with no envelope (legacy or garbage) is refused, with no value in the text
def test_unprefixed_value_is_refused(mock_settings_key):
    legacy = base64.urlsafe_b64encode(os.urandom(40)).decode()
    with pytest.raises(CiphertextFormatError) as exc:
        decrypt(legacy)
    assert legacy not in str(exc.value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "plaintext",
        "mh1:",
        "mh1:k1",
        "mh1:k1:",
        "mh1::AAAA",
        "mh1:K1:" + "A" * 40,
        "mh1:" + "a" * 33 + ":" + "A" * 40,
        "mh1:k1:not base64 !!!",
        "mh1:k1:AAAA",
    ],
)
def test_malformed_envelopes_are_refused_without_the_value(value, mock_settings_key):
    with pytest.raises(CiphertextFormatError) as exc:
        decrypt(value)
    assert len(value) < 12 or value not in str(exc.value)  # short ones occur in the fixed text


def _valid_payload(mock_settings_key) -> tuple[str, str]:
    prefix, payload = encrypt("secret").rsplit(":", 1)
    return prefix, payload


def test_non_canonical_payloads_are_refused(mock_settings_key):
    """The payload is exactly padded base64url: nothing else decodes to the same bytes."""
    prefix, payload = _valid_payload(mock_settings_key)
    standard = base64.b64encode(base64.urlsafe_b64decode(payload)).decode()
    variants = {
        "trailing newline": payload + "\n",
        "inserted exclamation mark": payload[:10] + "!" + payload[10:],
        "junk after the padding": payload + "AAAA",
        "stripped padding": payload.rstrip("="),
        "leading space": " " + payload,
    }
    if standard != payload:
        variants["standard alphabet"] = standard
    for label, bad in variants.items():
        with pytest.raises(CiphertextFormatError, match="base64url"):
            decrypt(f"{prefix}:{bad}")
        assert label


def test_a_colon_in_the_payload_is_refused(mock_settings_key):
    prefix, payload = _valid_payload(mock_settings_key)
    with pytest.raises(CiphertextFormatError):
        decrypt(f"{prefix}:{payload[:8]}:{payload[8:]}")


def test_the_canonical_payload_still_decrypts(mock_settings_key):
    prefix, payload = _valid_payload(mock_settings_key)
    assert decrypt(f"{prefix}:{payload}") == "secret"


def test_a_key_id_with_characters_outside_the_pattern_is_not_echoed(mock_settings_key):
    hostile = "mh1:PHI Marker Text:" + "A" * 40
    with pytest.raises(CiphertextFormatError) as exc:
        decrypt(hostile)
    assert "PHI" not in str(exc.value)


def test_a_misconfigured_key_is_refused_without_the_key(monkeypatch):
    short = base64.urlsafe_b64encode(os.urandom(16)).decode()
    _use(monkeypatch, short)
    with pytest.raises(ValueError) as exc:
        encrypt("x")
    assert short not in str(exc.value)
    _use(monkeypatch, _make_key(), kid="k2", retired=f"k1:{short}")
    with pytest.raises(ValueError) as exc2:
        encrypt("x")
    assert short not in str(exc2.value)


def test_keyring_is_built_once_per_configuration(monkeypatch, mock_settings_key):
    crypto_mod._build_keyring.cache_clear()
    for _ in range(3):
        encrypt("x")
    assert crypto_mod._build_keyring.cache_info().misses == 1


def test_wrong_key_fails_decryption(monkeypatch, mock_settings_key):
    """Decrypting with a different key under the same id raises: no plaintext fallback."""
    ciphertext = encrypt("secret value")
    _use(monkeypatch, _make_key())
    with pytest.raises(InvalidTag):
        decrypt(ciphertext)


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
        assert raw_value.startswith("mh1:k1:")  # AC 6: the stored value names its key

    EncBase.metadata.drop_all(pg_engine)


def test_secret_str_not_in_repr():
    """at_rest_encryption_key SecretStr must not leak in repr."""
    from pydantic import SecretStr

    key = _make_key()
    s = SecretStr(key)
    assert key not in repr(s)
    assert key not in str(s)
