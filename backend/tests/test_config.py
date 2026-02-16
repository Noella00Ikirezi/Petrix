"""Tests for application config."""
from app.config import Settings


class TestSettings:
    def test_default_app_name(self):
        s = Settings(database_url="sqlite:///test.db", secret_key="test")
        assert s.app_name == "Petrix"

    def test_cors_origins_list(self):
        s = Settings(
            database_url="sqlite:///test.db",
            secret_key="test",
            cors_origins="http://a.com,http://b.com",
        )
        assert s.cors_origins_list == ["http://a.com", "http://b.com"]

    def test_jwt_algorithm_default(self):
        s = Settings(database_url="sqlite:///test.db", secret_key="test")
        assert s.jwt_algorithm == "HS256"
