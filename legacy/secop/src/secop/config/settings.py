"""Application settings management."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os


class DatabaseSettings(BaseModel):
    """Database configuration."""

    path: str = "data/secop.db"
    echo: bool = False
    pool_size: int = 5
    busy_timeout: int = 30000


class SecuritySettings(BaseModel):
    """Security configuration."""

    bcrypt_rounds: int = 12
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15


class ScannerSettings(BaseModel):
    """Scanner configuration."""

    nmap_path: Optional[str] = None
    openvas_host: str = "localhost"
    openvas_port: int = 9390
    openvas_username: str = "admin"
    openvas_password: str = ""
    nuclei_path: Optional[str] = None
    nuclei_templates_path: Optional[str] = None


class LDAPSettings(BaseModel):
    """LDAP/Active Directory configuration."""

    server: str = ""
    port: int = 389
    use_ssl: bool = False
    ssl_port: int = 636
    base_dn: str = ""
    bind_dn: str = ""
    bind_password: str = ""


class GoogleWorkspaceSettings(BaseModel):
    """Google Workspace configuration."""

    credentials_file: str = ""
    admin_email: str = ""
    scopes: list[str] = Field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/admin.directory.user.readonly",
            "https://www.googleapis.com/auth/admin.directory.group.readonly",
            "https://www.googleapis.com/auth/admin.reports.audit.readonly",
        ]
    )


class UISettings(BaseModel):
    """UI configuration."""

    theme: str = "darkly"
    window_width: int = 1400
    window_height: int = 900
    font_family: str = "Segoe UI"
    font_size: int = 10


class Settings(BaseSettings):
    """Main application settings."""

    app_name: str = "SecOp Audit"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    log_file: str = "logs/secop.log"

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    scanner: ScannerSettings = Field(default_factory=ScannerSettings)
    ldap: LDAPSettings = Field(default_factory=LDAPSettings)
    google_workspace: GoogleWorkspaceSettings = Field(default_factory=GoogleWorkspaceSettings)
    ui: UISettings = Field(default_factory=UISettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent.parent


def get_data_dir() -> Path:
    """Get data directory path."""
    data_dir = get_project_root() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    """Get logs directory path."""
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir
