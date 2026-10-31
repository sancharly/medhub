"""Application configuration via environment variables.

All secrets are typed as SecretStr so they are never exposed in logs or repr.
Call get_settings() to obtain the cached singleton instance.
"""

import functools

from pydantic import PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.client_address import parse_trusted_proxies


class Settings(BaseSettings):
    # extra="ignore": a leftover key (e.g. the removed SESSION_SIGNING_KEY) in an operator's .env
    # file must not stop start-up.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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
    smtp_user: str
    smtp_password: SecretStr

    # At-rest encryption
    at_rest_encryption_key: SecretStr

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
    cors_origins: list[str] = []

    # Originating client address (SR-042 AC 3, ADR-0019): comma-separated IP addresses or CIDR
    # blocks of the reverse proxy. Empty trusts no forwarded header.
    trusted_proxies: str = ""

    @field_validator("trusted_proxies")
    @classmethod
    def _check_trusted_proxies(cls, value: str) -> str:
        parse_trusted_proxies(value)  # ValueError names the invalid entry; start-up is refused
        return value


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # fields come from env vars
