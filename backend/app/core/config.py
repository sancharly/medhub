"""Application configuration via environment variables.

All secrets are typed as SecretStr so they are never exposed in logs or repr.
Call get_settings() to obtain the cached singleton instance.
"""

import functools

from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

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

    # Session security
    session_signing_key: SecretStr

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


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # fields come from env vars
