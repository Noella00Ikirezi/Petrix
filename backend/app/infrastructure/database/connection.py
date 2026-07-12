"""Gestion des connexions et des sessions de base de données pour Petrix.

Expose les moteurs SQLAlchemy synchrone et asynchrone, les fabriques de sessions,
et les injecteurs de dépendances FastAPI (get_db, get_async_db) utilisés par tous
les routeurs de la couche API.
"""
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings

# Moteur synchrone — utilisé par Alembic et les dépendances synchrones
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Moteur asynchrone — remplace le schéma postgresql:// par postgresql+asyncpg://
async_database_url = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)
async_engine = create_async_engine(
    async_database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Fabrique de sessions synchrones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Fabrique de sessions asynchrones
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Classe de base déclarative partagée par tous les modèles ORM
Base = declarative_base()


def get_db() -> Generator:
    """Fournit une session synchrone et garantit sa fermeture même en cas d'exception.

    Utilisé comme dépendance FastAPI : ``db: Session = Depends(get_db)``.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Fournit une session asynchrone et garantit sa fermeture même en cas d'exception.

    Utilisé comme dépendance FastAPI :
    ``session: AsyncSession = Depends(get_async_db)``.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
