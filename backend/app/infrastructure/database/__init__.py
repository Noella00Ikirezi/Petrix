"""Sous-paquet de persistance PostgreSQL de Petrix.

Expose les moteurs SQLAlchemy (synchrone et asynchrone), les fabriques de sessions
et la classe de base déclarative ``Base`` partagée par tous les modèles ORM.
"""
from app.infrastructure.database.connection import (
    engine,
    async_engine,
    SessionLocal,
    AsyncSessionLocal,
    get_db,
    get_async_db,
    Base,
)

__all__ = [
    "engine",
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "get_db",
    "get_async_db",
    "Base",
]
