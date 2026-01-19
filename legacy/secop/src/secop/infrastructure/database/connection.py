"""SQLite database connection with WAL mode and optimizations."""

from pathlib import Path
from contextlib import contextmanager
from typing import Generator
import threading

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import StaticPool
from loguru import logger

from secop.config.settings import get_settings, get_data_dir


class DatabaseConnection:
    """
    Thread-safe SQLite connection manager with WAL mode.

    Implements singleton pattern for global database access.
    Optimized for multi-user scenarios with proper locking.
    """

    _instance: "DatabaseConnection | None" = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str | None = None) -> "DatabaseConnection":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self, db_path: str | None = None):
        if self._initialized:
            return

        settings = get_settings()

        if db_path is None:
            data_dir = get_data_dir()
            db_path = str(data_dir / "secop.db")

        self.db_path = db_path
        self._ensure_db_directory()

        # Create engine with SQLite optimizations
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={
                "check_same_thread": False,
                "timeout": settings.database.busy_timeout / 1000,
            },
            poolclass=StaticPool,
            echo=settings.database.echo,
        )

        # Configure SQLite pragmas on each connection
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Faster sync (safe with WAL)
            cursor.execute("PRAGMA synchronous=NORMAL")
            # 64MB cache
            cursor.execute("PRAGMA cache_size=-65536")
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            # Busy timeout in ms
            cursor.execute(f"PRAGMA busy_timeout={settings.database.busy_timeout}")
            # Memory-mapped I/O (256MB)
            cursor.execute("PRAGMA mmap_size=268435456")
            # Temp tables in memory
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()

        # Thread-safe session factory
        session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        self.Session = scoped_session(session_factory)

        self._initialized = True
        logger.info(f"Database initialized: {db_path}")

    def _ensure_db_directory(self) -> None:
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Handles commit/rollback automatically.
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            self.Session.remove()

    def create_all_tables(self) -> None:
        """Create all database tables."""
        from .models import Base

        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")

    def drop_all_tables(self) -> None:
        """Drop all database tables (use with caution!)."""
        from .models import Base

        Base.metadata.drop_all(self.engine)
        logger.warning("All database tables dropped")

    def execute_raw(self, sql: str) -> None:
        """Execute raw SQL statement."""
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()

    def backup(self, backup_path: str) -> None:
        """Create a backup of the database."""
        import shutil

        # Checkpoint WAL before backup
        self.execute_raw("PRAGMA wal_checkpoint(TRUNCATE)")
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Database backed up to: {backup_path}")

    def get_stats(self) -> dict:
        """Get database statistics."""
        with self.engine.connect() as conn:
            result = conn.execute(text("PRAGMA page_count")).fetchone()
            page_count = result[0] if result else 0

            result = conn.execute(text("PRAGMA page_size")).fetchone()
            page_size = result[0] if result else 0

            result = conn.execute(text("PRAGMA journal_mode")).fetchone()
            journal_mode = result[0] if result else "unknown"

        return {
            "path": self.db_path,
            "size_bytes": page_count * page_size,
            "page_count": page_count,
            "page_size": page_size,
            "journal_mode": journal_mode,
        }

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (useful for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.Session.remove()
                cls._instance.engine.dispose()
                cls._instance = None


def get_db() -> DatabaseConnection:
    """Get database connection singleton."""
    return DatabaseConnection()
