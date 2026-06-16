"""Application configuration using Pydantic Settings."""
import secrets as _secrets
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "Petrix"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = _secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@petrix.local"
    smtp_from_name: str = "Petrix"
    smtp_tls: bool = False

    # Auth extended
    refresh_token_expire_days: int = 7
    mfa_token_expire_minutes: int = 5
    otp_length: int = 6
    max_failed_login_attempts: int = 5
    account_lockout_minutes: int = 30
    mfa_enabled: bool = True

    # Admin user (created on first run)
    admin_email: str = "nikirezi@outlook.fr"
    admin_password: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
