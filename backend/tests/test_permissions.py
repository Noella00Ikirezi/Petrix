"""Tests for RBAC permissions."""
from app.core.permissions import (
    UserRole,
    Permission,
    ROLE_PERMISSIONS,
    has_permission,
    has_any_permission,
    get_role_permissions,
)


class TestRoles:
    def test_four_roles_exist(self):
        roles = list(UserRole)
        assert len(roles) == 4

    def test_role_values(self):
        assert UserRole.VIEWER.value == "viewer"
        assert UserRole.ADMIN.value == "admin"


class TestPermissions:
    def test_admin_has_all_permissions(self):
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        all_perms = set(Permission)
        assert admin_perms == all_perms

    def test_viewer_has_limited_permissions(self):
        viewer_perms = ROLE_PERMISSIONS[UserRole.VIEWER]
        assert Permission.ASSET_VIEW in viewer_perms
        assert Permission.ASSET_DELETE not in viewer_perms
        assert Permission.SYSTEM_ADMIN not in viewer_perms

    def test_analyst_superset_of_viewer(self):
        viewer = ROLE_PERMISSIONS[UserRole.VIEWER]
        analyst = ROLE_PERMISSIONS[UserRole.ANALYST]
        assert viewer.issubset(analyst)

    def test_auditor_superset_of_analyst(self):
        analyst = ROLE_PERMISSIONS[UserRole.ANALYST]
        auditor = ROLE_PERMISSIONS[UserRole.AUDITOR]
        assert analyst.issubset(auditor)


class TestHasPermission:
    def test_admin_has_system_admin(self):
        assert has_permission(UserRole.ADMIN, Permission.SYSTEM_ADMIN) is True

    def test_viewer_lacks_asset_delete(self):
        assert has_permission(UserRole.VIEWER, Permission.ASSET_DELETE) is False

    def test_analyst_can_create_assets(self):
        assert has_permission(UserRole.ANALYST, Permission.ASSET_CREATE) is True


class TestHasAnyPermission:
    def test_returns_true_when_has_one(self):
        assert has_any_permission(
            UserRole.VIEWER,
            {Permission.ASSET_VIEW, Permission.ASSET_DELETE}
        ) is True

    def test_returns_false_when_has_none(self):
        assert has_any_permission(
            UserRole.VIEWER,
            {Permission.SYSTEM_ADMIN, Permission.USER_DELETE}
        ) is False


class TestGetRolePermissions:
    def test_returns_set(self):
        result = get_role_permissions(UserRole.VIEWER)
        assert isinstance(result, set)
        assert len(result) > 0
