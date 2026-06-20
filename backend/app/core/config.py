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

    # CORS
    cors_origins: list[str] = []


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # fields come from env vars
