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
from app.core.secret_settings import keyring_problems, sse_key_problems

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

    # The object store's SSE key (SR-041 AC 5, ADR-0018). Only the object store and its preflight
    # use it (Compose gives it to no Python service), so it is optional here; when present it must
    # be a valid key distinct from the field keys.
    object_store_sse_key: SecretStr | None = None

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

    # Largest attachment accepted, in bytes: 150 MiB (SR-013 AC 6, SR-017 AC 6, CR-006 D-2). The
    # reverse proxy's client_max_body_size (infra/reverse-proxy/nginx.conf) must stay above it.
    attachment_max_bytes: int = 157286400

    # DICOM module bounds checked before any pixel data is decoded (SR-017 AC 6, CR-006 D-2,
    # PRB-006): the largest stored object (150 MiB) and the largest decoded size declared in the
    # header (1 GiB).
    dicom_max_stored_bytes: int = 157286400
    dicom_max_decoded_bytes: int = 1073741824

    # Blocking IO runs in worker threads, so the thread limit and the database connection pool are
    # sized together (SR-026 AC 5, ADR-0022). API_THREADPOOL_SIZE is applied to AnyIO's default
    # limiter at start-up and is also the Redis pool size; DB_POOL_SIZE + DB_MAX_OVERFLOW is the
    # most database connections the engine opens. Start-up is refused when the threads outnumber
    # the connections, because the surplus threads would queue for a connection until
    # DB_POOL_TIMEOUT and then fail with a 500 (PRB-072). This does not make a checkout wait-free: a
    # connection belongs to the request (its get_db session, kept through a streaming download and
    # until after the response is sent), not to the thread, so one worker serves about threads +
    # connections concurrent requests and answers 500 beyond that (PRB-081). The defaults are the
    # largest thread limit the engine's pool (5 + 10, 30 s) can serve (CR-006 D-25); the deployed
    # values are in infra/ (D-24).
    api_threadpool_size: int = 15
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

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
    def _check_pool_sizes(self) -> "Settings":
        """Threads must not outnumber database connections (ADR-0022, PRB-072)."""
        if (
            min(self.api_threadpool_size, self.db_pool_size, self.db_pool_timeout) < 1
            or self.db_max_overflow < 0
        ):
            raise ValueError(
                "API_THREADPOOL_SIZE, DB_POOL_SIZE and DB_POOL_TIMEOUT must be at least 1 and "
                "DB_MAX_OVERFLOW at least 0"
            )
        if self.api_threadpool_size > self.db_pool_size + self.db_max_overflow:
            raise ValueError(
                f"API_THREADPOOL_SIZE ({self.api_threadpool_size}) must not exceed DB_POOL_SIZE + "
                f"DB_MAX_OVERFLOW ({self.db_pool_size + self.db_max_overflow})"
            )
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

    @model_validator(mode="after")
    def _check_sse_key(self) -> "Settings":
        sse = self.object_store_sse_key
        if sse is not None and sse.get_secret_value().strip():
            retired = self.at_rest_encryption_retired_keys
            problems = sse_key_problems(
                sse.get_secret_value(),
                self.at_rest_encryption_key.get_secret_value(),
                retired.get_secret_value() if retired else None,
            )
            if problems:  # the messages name settings, never a key
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
