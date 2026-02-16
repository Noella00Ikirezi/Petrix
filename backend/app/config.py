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

    # AI - Anthropic
    anthropic_api_key: str = ""

    # AI - Ollama (100% open-source, self-hosted)
    OLLAMA_API_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen2:0.5b"  # Modèle ultra-léger 0.5B (~352MB), fonctionne avec très peu de RAM

    # MinIO (S3-compatible storage)
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "petrix"
    MINIO_SECURE: bool = False

    # Pentest
    PENTEST_NMAP_DEFAULT_PORTS: str = "21-23,25,53,80,110,139,143,443,445,993,995,1433,3306,3389,5432,5900,6379,8080,8443,27017"
    PENTEST_NMAP_TIMING: str = "T4"
    PENTEST_MAX_SCAN_DURATION: int = 3600
    PENTEST_AI_MAX_FINDINGS: int = 15
    PENTEST_REPORT_BUCKET: str = "pentest-reports"
    PENTEST_SSH_TIMEOUT: int = 30

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

    # Admin user (created on first run)
    admin_email: str = "admin@petrix.local"
    admin_password: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
