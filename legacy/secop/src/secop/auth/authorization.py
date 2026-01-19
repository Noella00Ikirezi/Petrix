"""RBAC authorization system."""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Set, Optional
import threading

from secop.infrastructure.database.models import UserRole


class Permission(Enum):
    """Granular permissions for RBAC."""

    # Asset permissions
    ASSET_VIEW = auto()
    ASSET_CREATE = auto()
    ASSET_EDIT = auto()
    ASSET_DELETE = auto()
    ASSET_EXPORT = auto()

    # Scan permissions
    SCAN_VIEW = auto()
    SCAN_CREATE = auto()
    SCAN_EXECUTE = auto()
    SCAN_CONFIGURE = auto()
    SCAN_DELETE = auto()

    # Vulnerability permissions
    VULN_VIEW = auto()
    VULN_EDIT = auto()
    VULN_RESOLVE = auto()
    VULN_EXPORT = auto()

    # Audit permissions
    AUDIT_VIEW = auto()
    AUDIT_CREATE = auto()
    AUDIT_EXECUTE = auto()
    AUDIT_EXPORT = auto()
    AUDIT_DELETE = auto()

    # Directory service permissions
    AD_VIEW = auto()
    AD_AUDIT = auto()
    AD_CONFIGURE = auto()
    GWS_VIEW = auto()
    GWS_AUDIT = auto()
    GWS_CONFIGURE = auto()

    # Report permissions
    REPORT_VIEW = auto()
    REPORT_CREATE = auto()
    REPORT_EXPORT = auto()

    # User management permissions
    USER_VIEW = auto()
    USER_CREATE = auto()
    USER_EDIT = auto()
    USER_DELETE = auto()
    USER_MANAGE_ROLES = auto()

    # System permissions
    SETTINGS_VIEW = auto()
    SETTINGS_EDIT = auto()
    AUDIT_LOG_VIEW = auto()
    SYSTEM_ADMIN = auto()


class Role(Enum):
    """User roles mapping to UserRole enum."""

    VIEWER = UserRole.VIEWER
    ANALYST = UserRole.ANALYST
    AUDITOR = UserRole.AUDITOR
    ADMIN = UserRole.ADMIN


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        # View-only access
        Permission.ASSET_VIEW,
        Permission.SCAN_VIEW,
        Permission.VULN_VIEW,
        Permission.AUDIT_VIEW,
        Permission.REPORT_VIEW,
        Permission.AD_VIEW,
        Permission.GWS_VIEW,
    },
    Role.ANALYST: {
        # Viewer permissions
        Permission.ASSET_VIEW,
        Permission.SCAN_VIEW,
        Permission.VULN_VIEW,
        Permission.AUDIT_VIEW,
        Permission.REPORT_VIEW,
        Permission.AD_VIEW,
        Permission.GWS_VIEW,
        # Asset management
        Permission.ASSET_CREATE,
        Permission.ASSET_EDIT,
        Permission.ASSET_EXPORT,
        # Scan execution
        Permission.SCAN_CREATE,
        Permission.SCAN_EXECUTE,
        # Vulnerability management
        Permission.VULN_EDIT,
        Permission.VULN_RESOLVE,
        Permission.VULN_EXPORT,
        # Reports
        Permission.REPORT_CREATE,
        Permission.REPORT_EXPORT,
    },
    Role.AUDITOR: {
        # Analyst permissions
        Permission.ASSET_VIEW,
        Permission.ASSET_CREATE,
        Permission.ASSET_EDIT,
        Permission.ASSET_EXPORT,
        Permission.SCAN_VIEW,
        Permission.SCAN_CREATE,
        Permission.SCAN_EXECUTE,
        Permission.VULN_VIEW,
        Permission.VULN_EDIT,
        Permission.VULN_RESOLVE,
        Permission.VULN_EXPORT,
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EXPORT,
        Permission.AD_VIEW,
        Permission.GWS_VIEW,
        # Additional auditor permissions
        Permission.ASSET_DELETE,
        Permission.SCAN_CONFIGURE,
        Permission.SCAN_DELETE,
        Permission.AUDIT_VIEW,
        Permission.AUDIT_CREATE,
        Permission.AUDIT_EXECUTE,
        Permission.AUDIT_EXPORT,
        Permission.AUDIT_DELETE,
        Permission.AD_AUDIT,
        Permission.AD_CONFIGURE,
        Permission.GWS_AUDIT,
        Permission.GWS_CONFIGURE,
        Permission.AUDIT_LOG_VIEW,
    },
    Role.ADMIN: set(Permission),  # All permissions
}


@dataclass
class AuthContext:
    """Authentication context for current user."""

    user_id: int
    username: str
    email: str
    role: Role
    permissions: Set[Permission] = field(default_factory=set)

    def __post_init__(self):
        if not self.permissions:
            self.permissions = ROLE_PERMISSIONS.get(self.role, set())

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions

    def has_any_permission(self, *permissions: Permission) -> bool:
        """Check if user has any of the specified permissions."""
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, *permissions: Permission) -> bool:
        """Check if user has all of the specified permissions."""
        return all(p in self.permissions for p in permissions)

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == Role.ADMIN

    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.has_any_permission(
            Permission.USER_CREATE,
            Permission.USER_EDIT,
            Permission.USER_DELETE,
            Permission.USER_MANAGE_ROLES,
        )


class AuthorizationService:
    """
    Singleton service for managing authorization context.

    Thread-safe implementation using thread-local storage.
    """

    _instance: Optional["AuthorizationService"] = None
    _lock = threading.Lock()
    _local = threading.local()

    def __new__(cls) -> "AuthorizationService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def current_context(self) -> Optional[AuthContext]:
        """Get current authentication context."""
        return getattr(self._local, "context", None)

    @current_context.setter
    def current_context(self, context: Optional[AuthContext]) -> None:
        """Set current authentication context."""
        self._local.context = context

    def set_context(self, context: AuthContext) -> None:
        """Set authentication context for current thread."""
        self._local.context = context

    def clear_context(self) -> None:
        """Clear authentication context for current thread."""
        self._local.context = None

    def get_context(self) -> AuthContext:
        """Get current context or raise error if not authenticated."""
        context = self.current_context
        if context is None:
            from secop.core.exceptions import AuthenticationError

            raise AuthenticationError("Not authenticated")
        return context

    def is_authenticated(self) -> bool:
        """Check if current thread is authenticated."""
        return self.current_context is not None

    def check_permission(self, permission: Permission) -> None:
        """Check if current user has permission, raise error if not."""
        context = self.get_context()
        if not context.has_permission(permission):
            from secop.core.exceptions import AuthorizationError

            raise AuthorizationError(f"Permission required: {permission.name}")

    def check_any_permission(self, *permissions: Permission) -> None:
        """Check if current user has any of the permissions."""
        context = self.get_context()
        if not context.has_any_permission(*permissions):
            perm_names = ", ".join(p.name for p in permissions)
            from secop.core.exceptions import AuthorizationError

            raise AuthorizationError(f"One of these permissions required: {perm_names}")

    def get_user_id(self) -> int:
        """Get current user ID."""
        return self.get_context().user_id

    def get_username(self) -> str:
        """Get current username."""
        return self.get_context().username

    def get_role(self) -> Role:
        """Get current user role."""
        return self.get_context().role


def get_auth_service() -> AuthorizationService:
    """Get authorization service singleton."""
    return AuthorizationService()
