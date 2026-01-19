"""Application configuration using Pydantic Settings."""
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
    app_name: str = "GRC Platform"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql://grc:REMOVED_SECRET@localhost:5432/grc_platform"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "REMOVED_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # AI
    anthropic_api_key: str = ""

    # Admin user (created on first run)
    admin_email: str = "admin@grc-platform.local"
    admin_password: str = "GrcAdmin@2024!Secure"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
