"""Pytest configuration and fixtures."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    from secop.infrastructure.database.connection import DatabaseConnection

    # Use in-memory database for tests
    db = DatabaseConnection(":memory:")
    db.create_all_tables()

    yield db

    DatabaseConnection.reset_instance()


@pytest.fixture
def db_session(test_db):
    """Get a database session for tests."""
    with test_db.get_session() as session:
        yield session


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for tests."""
    from secop.infrastructure.database.models import User, UserRole
    from secop.auth.password_utils import hash_password
    from secop.infrastructure.database.repositories.user_repository import UserRepository

    repo = UserRepository(db_session)

    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        role=UserRole.ANALYST,
    )
    repo.add(user)

    return user


@pytest.fixture
def sample_asset(db_session):
    """Create a sample asset for tests."""
    from secop.infrastructure.database.models import Asset, AssetType, AssetStatus, Criticality
    from secop.infrastructure.database.repositories.asset_repository import AssetRepository

    repo = AssetRepository(db_session)

    asset = Asset(
        name="Test Server",
        asset_type=AssetType.SERVER,
        ip_address="192.168.1.100",
        hostname="test-server",
        os="Ubuntu",
        os_version="22.04",
        status=AssetStatus.ACTIVE,
        criticality=Criticality.HIGH,
    )
    repo.add(asset)

    return asset
