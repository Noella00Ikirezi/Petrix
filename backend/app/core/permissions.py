"""RBAC - Roles and Permissions system (adapted from SecOP)."""
from enum import Enum
from typing import Set


class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    VIEWER = "viewer"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    ADMIN = "admin"


class Permission(str, Enum):
    """Granular permissions for RBAC."""
    # Assets
    ASSET_VIEW = "asset:view"
    ASSET_CREATE = "asset:create"
    ASSET_EDIT = "asset:edit"
    ASSET_DELETE = "asset:delete"
    ASSET_EXPORT = "asset:export"

    # Vulnerabilities
    VULN_VIEW = "vuln:view"
    VULN_CREATE = "vuln:create"
    VULN_EDIT = "vuln:edit"
    VULN_RESOLVE = "vuln:resolve"
    VULN_DELETE = "vuln:delete"
    VULN_EXPORT = "vuln:export"

    # Scans
    SCAN_VIEW = "scan:view"
    SCAN_CREATE = "scan:create"
    SCAN_EXECUTE = "scan:execute"
    SCAN_CONFIGURE = "scan:configure"
    SCAN_DELETE = "scan:delete"

    # Compliance
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_ASSESS = "compliance:assess"
    COMPLIANCE_EDIT = "compliance:edit"
    COMPLIANCE_EXPORT = "compliance:export"

    # Suppliers
    SUPPLIER_VIEW = "supplier:view"
    SUPPLIER_CREATE = "supplier:create"
    SUPPLIER_EDIT = "supplier:edit"
    SUPPLIER_DELETE = "supplier:delete"
    SUPPLIER_ASSESS = "supplier:assess"

    # Reports
    REPORT_VIEW = "report:view"
    REPORT_CREATE = "report:create"
    REPORT_EXPORT = "report:export"

    # Users
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_EDIT = "user:edit"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"

    # Settings
    SETTINGS_VIEW = "settings:view"
    SETTINGS_EDIT = "settings:edit"

    # Audit logs
    AUDIT_LOG_VIEW = "audit_log:view"

    # System
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_SETTINGS = "system:settings"


# Role to permissions mapping (hierarchical)
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.VIEWER: {
        Permission.ASSET_VIEW,
        Permission.VULN_VIEW,
        Permission.SCAN_VIEW,
        Permission.COMPLIANCE_VIEW,
        Permission.SUPPLIER_VIEW,
        Permission.REPORT_VIEW,
    },
    UserRole.ANALYST: {
        # Viewer permissions
        Permission.ASSET_VIEW,
        Permission.VULN_VIEW,
        Permission.SCAN_VIEW,
        Permission.COMPLIANCE_VIEW,
        Permission.SUPPLIER_VIEW,
        Permission.REPORT_VIEW,
        # Analyst additions
        Permission.ASSET_CREATE,
        Permission.ASSET_EDIT,
        Permission.ASSET_EXPORT,
        Permission.VULN_CREATE,
        Permission.VULN_EDIT,
        Permission.VULN_RESOLVE,
        Permission.VULN_EXPORT,
        Permission.SCAN_CREATE,
        Permission.SCAN_EXECUTE,
        Permission.REPORT_CREATE,
        Permission.REPORT_EXPORT,
    },
    UserRole.AUDITOR: {
        # Analyst permissions
        Permission.ASSET_VIEW,
        Permission.ASSET_CREATE,
        Permission.ASSET_EDIT,
        Permission.ASSET_DELETE,
        Permission.ASSET_EXPORT,
        Permission.VULN_VIEW,
        Permission.VULN_CREATE,
        Permission.VULN_EDIT,
        Permission.VULN_RESOLVE,
        Permission.VULN_DELETE,
        Permission.VULN_EXPORT,
        Permission.SCAN_VIEW,
        Permission.SCAN_CREATE,
        Permission.SCAN_EXECUTE,
        Permission.SCAN_CONFIGURE,
        Permission.SCAN_DELETE,
        Permission.COMPLIANCE_VIEW,
        Permission.COMPLIANCE_ASSESS,
        Permission.COMPLIANCE_EDIT,
        Permission.COMPLIANCE_EXPORT,
        Permission.SUPPLIER_VIEW,
        Permission.SUPPLIER_CREATE,
        Permission.SUPPLIER_EDIT,
        Permission.SUPPLIER_ASSESS,
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EXPORT,
        # Auditor additions
        Permission.AUDIT_LOG_VIEW,
        Permission.USER_VIEW,
    },
    UserRole.ADMIN: {
        # All permissions
        *Permission,
    },
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_any_permission(role: UserRole, permissions: Set[Permission]) -> bool:
    """Check if a role has any of the specified permissions."""
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return bool(role_perms & permissions)


def get_role_permissions(role: UserRole) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())
