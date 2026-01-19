"""User repository for authentication and user management."""

from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy import select, and_

from .base_repository import BaseRepository
from ..models import User, UserSession, UserRole


class UserRepository(BaseRepository[User]):
    """Repository for User entity operations."""

    def __init__(self, session):
        super().__init__(session, User)

    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        stmt = select(User).where(User.username == username)
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        stmt = select(User).where(User.email == email)
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def find_active_users(self) -> List[User]:
        """Find all active users."""
        stmt = select(User).where(User.is_active == True)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_role(self, role: UserRole) -> List[User]:
        """Find users by role."""
        stmt = select(User).where(User.role == role)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_locked_users(self) -> List[User]:
        """Find locked users."""
        now = datetime.utcnow()
        stmt = select(User).where(
            and_(
                User.locked_until.isnot(None),
                User.locked_until > now,
            )
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp."""
        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            user.failed_login_attempts = 0
            self._session.flush()

    def increment_failed_login(self, user_id: int) -> int:
        """Increment failed login attempts and return new count."""
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_attempts += 1
            self._session.flush()
            return user.failed_login_attempts
        return 0

    def lock_user(self, user_id: int, until: datetime) -> None:
        """Lock user until specified time."""
        user = self.get_by_id(user_id)
        if user:
            user.locked_until = until
            self._session.flush()

    def unlock_user(self, user_id: int) -> None:
        """Unlock user."""
        user = self.get_by_id(user_id)
        if user:
            user.locked_until = None
            user.failed_login_attempts = 0
            self._session.flush()

    def deactivate_user(self, user_id: int) -> None:
        """Deactivate user."""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = False
            self._session.flush()

    def activate_user(self, user_id: int) -> None:
        """Activate user."""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = True
            self._session.flush()

    def find_by_criteria(self, **criteria: Any) -> List[User]:
        """Find users by criteria."""
        stmt = select(User)

        if "is_active" in criteria:
            stmt = stmt.where(User.is_active == criteria["is_active"])
        if "role" in criteria:
            stmt = stmt.where(User.role == criteria["role"])
        if "username_like" in criteria:
            stmt = stmt.where(User.username.ilike(f"%{criteria['username_like']}%"))

        result = self._session.execute(stmt)
        return list(result.scalars().all())


class UserSessionRepository(BaseRepository[UserSession]):
    """Repository for UserSession entity operations."""

    def __init__(self, session):
        super().__init__(session, UserSession)

    def find_by_token(self, token: str) -> Optional[UserSession]:
        """Find session by token."""
        stmt = select(UserSession).where(UserSession.session_token == token)
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def find_active_by_user(self, user_id: int) -> List[UserSession]:
        """Find active sessions for user."""
        now = datetime.utcnow()
        stmt = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.expires_at > now,
            )
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def delete_expired(self) -> int:
        """Delete expired sessions and return count."""
        now = datetime.utcnow()
        stmt = select(UserSession).where(UserSession.expires_at <= now)
        result = self._session.execute(stmt)
        sessions = list(result.scalars().all())

        for session in sessions:
            self._session.delete(session)

        self._session.flush()
        return len(sessions)

    def delete_by_user(self, user_id: int) -> int:
        """Delete all sessions for user."""
        stmt = select(UserSession).where(UserSession.user_id == user_id)
        result = self._session.execute(stmt)
        sessions = list(result.scalars().all())

        for session in sessions:
            self._session.delete(session)

        self._session.flush()
        return len(sessions)

    def find_by_criteria(self, **criteria: Any) -> List[UserSession]:
        """Find sessions by criteria."""
        stmt = select(UserSession)

        if "user_id" in criteria:
            stmt = stmt.where(UserSession.user_id == criteria["user_id"])
        if "active_only" in criteria and criteria["active_only"]:
            stmt = stmt.where(UserSession.expires_at > datetime.utcnow())

        result = self._session.execute(stmt)
        return list(result.scalars().all())
