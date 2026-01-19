from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    app_name: str = "SuperAssistant"
    debug: bool = True
    database_url: str = "sqlite:///./superassistant.db"
    anthropic_api_key: str

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
