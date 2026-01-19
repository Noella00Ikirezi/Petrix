"""Authentication service for user login/logout."""

from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from secop.config.settings import get_settings
from secop.core.exceptions import AuthenticationError
from secop.core.events import EventBus, Event, EventType
from secop.infrastructure.database.connection import get_db
from secop.infrastructure.database.models import User, UserSession, UserRole
from secop.infrastructure.database.repositories.user_repository import (
    UserRepository,
    UserSessionRepository,
)
from secop.infrastructure.database.repositories.audit_repository import AuditLogRepository
from .authorization import AuthContext, AuthorizationService, Role, get_auth_service
from .password_utils import hash_password, verify_password, generate_session_token


class AuthenticationService:
    """Service for user authentication operations."""

    def __init__(self):
        self._settings = get_settings()
        self._event_bus = EventBus()

    def login(
        self, username: str, password: str, ip_address: Optional[str] = None
    ) -> tuple[AuthContext, str]:
        """
        Authenticate user and create session.

        Args:
            username: User's username
            password: User's password
            ip_address: Client IP address (optional)

        Returns:
            Tuple of (AuthContext, session_token)

        Raises:
            AuthenticationError: If authentication fails
        """
        db = get_db()

        with db.get_session() as session:
            user_repo = UserRepository(session)
            session_repo = UserSessionRepository(session)
            audit_repo = AuditLogRepository(session)

            # Find user
            user = user_repo.find_by_username(username)
            if not user:
                logger.warning(f"Login failed: user not found - {username}")
                raise AuthenticationError("Invalid username or password")

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login failed: user inactive - {username}")
                raise AuthenticationError("Account is disabled")

            # Check if user is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                remaining = (user.locked_until - datetime.utcnow()).seconds // 60
                logger.warning(f"Login failed: user locked - {username}")
                raise AuthenticationError(
                    f"Account is locked. Try again in {remaining} minutes"
                )

            # Verify password
            if not verify_password(password, user.password_hash):
                attempts = user_repo.increment_failed_login(user.id)
                max_attempts = self._settings.security.max_login_attempts

                if attempts >= max_attempts:
                    lockout = timedelta(
                        minutes=self._settings.security.lockout_duration_minutes
                    )
                    user_repo.lock_user(user.id, datetime.utcnow() + lockout)
                    logger.warning(f"User locked after {attempts} failed attempts - {username}")

                logger.warning(f"Login failed: invalid password - {username} ({attempts}/{max_attempts})")
                raise AuthenticationError("Invalid username or password")

            # Create session
            session_token = generate_session_token()
            session_timeout = timedelta(
                minutes=self._settings.security.session_timeout_minutes
            )
            user_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                expires_at=datetime.utcnow() + session_timeout,
                ip_address=ip_address,
            )
            session_repo.add(user_session)

            # Update last login
            user_repo.update_last_login(user.id)

            # Log action
            audit_repo.log_action(
                action="LOGIN",
                resource_type="user",
                resource_id=user.id,
                user_id=user.id,
                ip_address=ip_address,
            )

            # Create auth context
            role = Role(user.role)
            context = AuthContext(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=role,
            )

            # Set context in service
            get_auth_service().set_context(context)

            # Publish event
            self._event_bus.publish(
                Event(
                    type=EventType.USER_LOGIN,
                    data={"user_id": user.id, "username": username},
                    source="AuthenticationService",
                    user_id=user.id,
                )
            )

            logger.info(f"User logged in: {username}")
            return context, session_token

    def logout(self, session_token: str) -> None:
        """
        Invalidate session and logout user.

        Args:
            session_token: Session token to invalidate
        """
        db = get_db()
        auth_service = get_auth_service()

        with db.get_session() as session:
            session_repo = UserSessionRepository(session)
            audit_repo = AuditLogRepository(session)

            user_session = session_repo.find_by_token(session_token)
            if user_session:
                user_id = user_session.user_id

                # Log action
                audit_repo.log_action(
                    action="LOGOUT",
                    resource_type="user",
                    resource_id=user_id,
                    user_id=user_id,
                )

                # Delete session
                session_repo.delete(user_session)

                # Publish event
                self._event_bus.publish(
                    Event(
                        type=EventType.USER_LOGOUT,
                        data={"user_id": user_id},
                        source="AuthenticationService",
                        user_id=user_id,
                    )
                )

                logger.info(f"User logged out: user_id={user_id}")

        # Clear auth context
        auth_service.clear_context()

    def validate_session(self, session_token: str) -> Optional[AuthContext]:
        """
        Validate session token and return auth context.

        Args:
            session_token: Session token to validate

        Returns:
            AuthContext if valid, None otherwise
        """
        db = get_db()

        with db.get_session() as session:
            session_repo = UserSessionRepository(session)
            user_repo = UserRepository(session)

            user_session = session_repo.find_by_token(session_token)
            if not user_session:
                return None

            # Check if expired
            if user_session.expires_at <= datetime.utcnow():
                session_repo.delete(user_session)
                return None

            # Get user
            user = user_repo.get_by_id(user_session.user_id)
            if not user or not user.is_active:
                session_repo.delete(user_session)
                return None

            # Create auth context
            role = Role(user.role)
            context = AuthContext(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=role,
            )

            # Set context in service
            get_auth_service().set_context(context)

            return context

    def refresh_session(self, session_token: str) -> Optional[str]:
        """
        Refresh session expiration time.

        Args:
            session_token: Current session token

        Returns:
            New session token if successful, None otherwise
        """
        db = get_db()

        with db.get_session() as session:
            session_repo = UserSessionRepository(session)

            user_session = session_repo.find_by_token(session_token)
            if not user_session or user_session.expires_at <= datetime.utcnow():
                return None

            # Extend expiration
            session_timeout = timedelta(
                minutes=self._settings.security.session_timeout_minutes
            )
            user_session.expires_at = datetime.utcnow() + session_timeout

            return session_token

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if successful

        Raises:
            AuthenticationError: If current password is wrong
        """
        db = get_db()

        with db.get_session() as session:
            user_repo = UserRepository(session)
            session_repo = UserSessionRepository(session)
            audit_repo = AuditLogRepository(session)

            user = user_repo.get_by_id(user_id)
            if not user:
                raise AuthenticationError("User not found")

            if not verify_password(current_password, user.password_hash):
                raise AuthenticationError("Current password is incorrect")

            # Update password
            user.password_hash = hash_password(new_password)

            # Invalidate all other sessions
            session_repo.delete_by_user(user_id)

            # Log action
            audit_repo.log_action(
                action="PASSWORD_CHANGE",
                resource_type="user",
                resource_id=user_id,
                user_id=user_id,
            )

            logger.info(f"Password changed for user: {user.username}")
            return True

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        """
        Create a new user.

        Args:
            username: Username
            email: Email address
            password: Password
            role: User role

        Returns:
            Created User object

        Raises:
            ValueError: If username or email already exists
        """
        db = get_db()

        with db.get_session() as session:
            user_repo = UserRepository(session)
            audit_repo = AuditLogRepository(session)

            # Check if username exists
            if user_repo.find_by_username(username):
                raise ValueError(f"Username already exists: {username}")

            # Check if email exists
            if user_repo.find_by_email(email):
                raise ValueError(f"Email already exists: {email}")

            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                role=role,
            )
            user_repo.add(user)

            # Log action
            auth_service = get_auth_service()
            current_user_id = (
                auth_service.get_user_id()
                if auth_service.is_authenticated()
                else None
            )
            audit_repo.log_action(
                action="USER_CREATE",
                resource_type="user",
                resource_id=user.id,
                user_id=current_user_id,
                details=f"Created user: {username}",
            )

            # Publish event
            self._event_bus.publish(
                Event(
                    type=EventType.USER_CREATED,
                    data={"user_id": user.id, "username": username},
                    source="AuthenticationService",
                    user_id=current_user_id,
                )
            )

            logger.info(f"User created: {username}")
            return user

    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from database.

        Returns:
            Number of sessions removed
        """
        db = get_db()

        with db.get_session() as session:
            session_repo = UserSessionRepository(session)
            count = session_repo.delete_expired()
            logger.info(f"Cleaned up {count} expired sessions")
            return count


def get_auth_service_instance() -> AuthenticationService:
    """Get authentication service instance."""
    return AuthenticationService()
