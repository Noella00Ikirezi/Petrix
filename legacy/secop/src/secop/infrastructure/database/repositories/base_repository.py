"""Base repository with generic CRUD operations."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository with common CRUD operations.

    Implements the Repository pattern for data access abstraction.
    """

    def __init__(self, session: Session, model_class: type[T]):
        self._session = session
        self._model_class = model_class

    @property
    def session(self) -> Session:
        """Get the current session."""
        return self._session

    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        return self._session.get(self._model_class, id)

    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with pagination."""
        stmt = select(self._model_class).limit(limit).offset(offset)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def count(self) -> int:
        """Count all entities."""
        stmt = select(func.count()).select_from(self._model_class)
        result = self._session.execute(stmt)
        return result.scalar() or 0

    def add(self, entity: T) -> T:
        """Add a new entity."""
        self._session.add(entity)
        self._session.flush()
        return entity

    def add_all(self, entities: List[T]) -> List[T]:
        """Add multiple entities."""
        self._session.add_all(entities)
        self._session.flush()
        return entities

    def update(self, entity: T) -> T:
        """Update an existing entity."""
        self._session.merge(entity)
        self._session.flush()
        return entity

    def delete(self, entity: T) -> None:
        """Delete an entity."""
        self._session.delete(entity)
        self._session.flush()

    def delete_by_id(self, id: int) -> bool:
        """Delete entity by ID."""
        entity = self.get_by_id(id)
        if entity:
            self.delete(entity)
            return True
        return False

    def exists(self, id: int) -> bool:
        """Check if entity exists."""
        return self.get_by_id(id) is not None

    def refresh(self, entity: T) -> T:
        """Refresh entity from database."""
        self._session.refresh(entity)
        return entity

    @abstractmethod
    def find_by_criteria(self, **criteria: Any) -> List[T]:
        """Find entities by specific criteria. Must be implemented by subclasses."""
        pass
