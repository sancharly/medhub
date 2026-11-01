"""Application configuration via environment variables.

All secrets are typed as SecretStr so they are never exposed in logs or repr.
Call get_settings() to obtain the cached singleton instance.
"""

import functools
import json
from typing import Annotated, Any

from pydantic import PostgresDsn, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from app.core.client_address import parse_trusted_proxies
from app.core.secret_settings import keyring_problems

_RETIRED_KEY = "session_signing_key"


class Settings(BaseSettings):
    # hide_input_in_errors: a validation error names the setting and never echoes a value.
    # Unknown keys in the .env file are refused (a mistyped setting must not be silently ignored);
    # the one retired key is dropped by _drop_retired_keys below.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", hide_input_in_errors=True
    )

    environment: str = "local"  # local | staging | production

    # Database
    database_url: PostgresDsn

    # Redis (sessions + Celery broker)
    redis_url: str

    # Object store (MinIO / S3-compatible)
    object_store_endpoint: str
    object_store_access_key: SecretStr
    object_store_secret_key: SecretStr
    object_store_bucket: str

    # SMTP
    smtp_host: str
    smtp_port: int = 587
    # SMTP without authentication is supported (CR-004 Q-5): the password is required only
    # when a user is set.
    smtp_user: str = ""
    smtp_password: SecretStr | None = None

    # At-rest encryption
    at_rest_encryption_key: SecretStr
    # Identifier written into every new field ciphertext (SR-022 AC 6, ADR-0018): [a-z0-9-]{1,32}.
    at_rest_encryption_key_id: str
    # Earlier keys, "id:base64key,id:base64key", used to decrypt values written under them only.
    at_rest_encryption_retired_keys: SecretStr | None = None

    # Session timeouts (seconds)
    session_inactivity_clinical_seconds: int = 900
    session_inactivity_admin_seconds: int = 1800
    session_absolute_lifetime_seconds: int = 28800
    session_max_concurrent: int = 3

    # Cookie security
    session_cookie_secure: bool = True

    # SMTP extras
    smtp_use_tls: bool = True  # STARTTLS (port 587)
    smtp_use_ssl: bool = False  # implicit TLS (port 465); takes precedence over smtp_use_tls
    mail_from: str = ""
    public_base_url: str = "https://medhub.example"

    # Retention sweep cron
    retention_sweep_cron: str = "0 2 * * *"  # daily at 02:00

    # CORS
    # An empty value is [], a JSON list or a comma-separated list is accepted (PRB-056, D-6).
    cors_origins: Annotated[list[str], NoDecode] = []

    # Originating client address (SR-042 AC 3, ADR-0019): comma-separated IP addresses or CIDR
    # blocks of the reverse proxy. Empty trusts no forwarded header.
    trusted_proxies: str = ""

    @model_validator(mode="before")
    @classmethod
    def _drop_retired_keys(cls, data: Any) -> Any:
        """A leftover SESSION_SIGNING_KEY (removed in TASK-140) must not stop start-up."""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if str(k).lower() != _RETIRED_KEY}
        return data

    @model_validator(mode="after")
    def _require_smtp_password_with_user(self) -> "Settings":
        if self.smtp_user.strip() and self.smtp_password is None:
            raise ValueError("SMTP_PASSWORD is required when SMTP_USER is set")
        return self

    @model_validator(mode="after")
    def _check_key_ring(self) -> "Settings":
        retired = self.at_rest_encryption_retired_keys
        problems = keyring_problems(
            self.at_rest_encryption_key_id,
            self.at_rest_encryption_key.get_secret_value(),
            retired.get_secret_value() if retired else None,
        )
        if problems:  # the messages name settings and key ids, never a key
            raise ValueError("; ".join(problems))
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        text = value.strip()
        if text == "":
            return []
        if text.startswith("["):
            return json.loads(text)  # a malformed list is refused; pydantic checks the items
        return [origin.strip() for origin in text.split(",") if origin.strip()]

    @field_validator("trusted_proxies")
    @classmethod
    def _check_trusted_proxies(cls, value: str) -> str:
        parse_trusted_proxies(value)  # ValueError names the invalid entry; start-up is refused
        return value


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # fields come from env vars
