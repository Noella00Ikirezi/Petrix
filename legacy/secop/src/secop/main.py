"""SecOp Audit - Main entry point."""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def init_database() -> None:
    """Initialize database and create tables."""
    from secop.infrastructure.database.connection import get_db
    from secop.infrastructure.database.models import Base

    db = get_db()
    db.create_all_tables()


def create_admin_if_needed() -> None:
    """Create admin user if no users exist."""
    from secop.infrastructure.database.connection import get_db
    from secop.infrastructure.database.repositories.user_repository import UserRepository
    from secop.infrastructure.database.models import UserRole
    from secop.auth.password_utils import hash_password

    db = get_db()

    with db.get_session() as session:
        repo = UserRepository(session)

        if repo.count() == 0:
            from secop.infrastructure.database.models import User

            admin = User(
                username="admin",
                email="admin@secop.local",
                password_hash=hash_password("admin"),
                role=UserRole.ADMIN,
                is_active=True,
            )
            repo.add(admin)

            from loguru import logger
            logger.info("Admin user created (username: admin, password: admin)")
            logger.warning("Please change the admin password after first login!")


def main() -> None:
    """Main entry point."""
    from secop.config.settings import get_settings
    from secop.config.logging_config import setup_logging

    # Setup logging
    setup_logging()

    from loguru import logger
    logger.info("Starting SecOp Audit...")

    # Initialize database
    logger.info("Initializing database...")
    init_database()

    # Create admin if needed
    create_admin_if_needed()

    # Start application
    logger.info("Starting UI...")
    from secop.presentation.app import SecOpApplication

    app = SecOpApplication()
    app.run()


if __name__ == "__main__":
    main()
