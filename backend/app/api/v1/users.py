"""Users management endpoints with comprehensive role and permission management."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.security import get_password_hash, verify_password
from app.core.permissions import Permission, UserRole, ROLE_PERMISSIONS, get_role_permissions, has_permission
from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.v1.deps import get_current_active_user, require_permission

router = APIRouter()


# ===================
# SCHEMAS
# ===================

class PermissionInfo(BaseModel):
    """Permission details."""
    name: str
    value: str
    category: str
    description: str


class RoleInfo(BaseModel):
    """Role with its permissions."""
    name: str
    value: str
    description: str
    permissions: List[str]
    user_count: int = 0


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    is_active: bool
    last_login: datetime | None = None
    created_at: datetime | None = None
    permissions: List[str] = []

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Create user schema with password validation."""
    email: EmailStr
    password: str = Field(..., min_length=12, description="Password must be at least 12 characters")
    first_name: str | None = None
    last_name: str | None = None
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    """Update user schema."""
    first_name: str | None = None
    last_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class PasswordChange(BaseModel):
    """Password change schema."""
    current_password: str
    new_password: str = Field(..., min_length=12, description="Password must be at least 12 characters")


class PasswordReset(BaseModel):
    """Admin password reset schema."""
    new_password: str = Field(..., min_length=12, description="Password must be at least 12 characters")


class BulkRoleUpdate(BaseModel):
    """Bulk role update schema."""
    user_ids: List[UUID]
    role: UserRole


class UserStats(BaseModel):
    """User statistics."""
    total_users: int
    active_users: int
    inactive_users: int
    users_by_role: dict


# Permission descriptions for documentation
PERMISSION_DESCRIPTIONS = {
    # Assets
    "asset:view": "View assets and their details",
    "asset:create": "Create new assets",
    "asset:edit": "Edit existing assets",
    "asset:delete": "Delete assets",
    "asset:export": "Export asset data",
    # Vulnerabilities
    "vuln:view": "View vulnerabilities",
    "vuln:create": "Create vulnerability entries",
    "vuln:edit": "Edit vulnerability details",
    "vuln:resolve": "Mark vulnerabilities as resolved",
    "vuln:delete": "Delete vulnerabilities",
    "vuln:export": "Export vulnerability data",
    # Scans
    "scan:view": "View scan results",
    "scan:create": "Create new scans",
    "scan:execute": "Execute scans",
    "scan:configure": "Configure scan settings",
    "scan:delete": "Delete scans",
    # Compliance
    "compliance:view": "View compliance status",
    "compliance:assess": "Perform compliance assessments",
    "compliance:edit": "Edit compliance data",
    "compliance:export": "Export compliance reports",
    # Suppliers
    "supplier:view": "View supplier information",
    "supplier:create": "Add new suppliers",
    "supplier:edit": "Edit supplier details",
    "supplier:delete": "Remove suppliers",
    "supplier:assess": "Assess supplier risk",
    # Reports
    "report:view": "View reports",
    "report:create": "Generate reports",
    "report:export": "Export reports",
    # Users
    "user:view": "View user list and details",
    "user:create": "Create new users",
    "user:edit": "Edit user information",
    "user:delete": "Delete users",
    "user:manage_roles": "Manage user roles and permissions",
    # Settings
    "settings:view": "View system settings",
    "settings:edit": "Modify system settings",
    # Audit
    "audit_log:view": "View audit logs",
    # System
    "system:admin": "Full system administration",
    "system:settings": "Manage system-wide settings",
}

ROLE_DESCRIPTIONS = {
    UserRole.VIEWER: "Read-only access to view assets, vulnerabilities, scans, and reports",
    UserRole.ANALYST: "Can create and edit assets, vulnerabilities, execute scans, and generate reports",
    UserRole.AUDITOR: "Full audit capabilities including compliance assessment and audit log access",
    UserRole.ADMIN: "Full system access with user management and system administration",
}


# ===================
# HELPER FUNCTIONS
# ===================

def get_permission_category(permission_value: str) -> str:
    """Extract category from permission value."""
    return permission_value.split(":")[0].replace("_", " ").title()


def user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse with permissions."""
    permissions = [p.value for p in get_role_permissions(user.role)]
    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        permissions=permissions,
    )


# ===================
# ROLES & PERMISSIONS ENDPOINTS
# ===================

@router.get("/roles", response_model=List[RoleInfo])
async def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all available roles with their permissions and user counts."""
    roles = []
    for role in UserRole:
        user_count = db.query(User).filter(User.role == role).count()
        permissions = [p.value for p in get_role_permissions(role)]
        roles.append(RoleInfo(
            name=role.name,
            value=role.value,
            description=ROLE_DESCRIPTIONS.get(role, ""),
            permissions=permissions,
            user_count=user_count,
        ))
    return roles


@router.get("/roles/{role_name}", response_model=RoleInfo)
async def get_role(
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get details of a specific role."""
    try:
        role = UserRole(role_name.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found",
        )

    user_count = db.query(User).filter(User.role == role).count()
    permissions = [p.value for p in get_role_permissions(role)]

    return RoleInfo(
        name=role.name,
        value=role.value,
        description=ROLE_DESCRIPTIONS.get(role, ""),
        permissions=permissions,
        user_count=user_count,
    )


@router.get("/permissions", response_model=List[PermissionInfo])
async def list_permissions(
    current_user: User = Depends(get_current_active_user),
):
    """List all available permissions with descriptions."""
    permissions = []
    for perm in Permission:
        permissions.append(PermissionInfo(
            name=perm.name,
            value=perm.value,
            category=get_permission_category(perm.value),
            description=PERMISSION_DESCRIPTIONS.get(perm.value, ""),
        ))
    return permissions


@router.get("/permissions/mine", response_model=List[str])
async def get_my_permissions(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's permissions."""
    return [p.value for p in get_role_permissions(current_user.role)]


@router.get("/permissions/check/{permission}")
async def check_permission(
    permission: str,
    current_user: User = Depends(get_current_active_user),
):
    """Check if current user has a specific permission."""
    try:
        perm = Permission(permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission: {permission}",
        )

    return {
        "permission": permission,
        "has_permission": has_permission(current_user.role, perm),
        "user_role": current_user.role.value,
    }


# ===================
# USER STATS ENDPOINT
# ===================

@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_VIEW)),
):
    """Get user statistics (requires USER_VIEW permission)."""
    total = db.query(User).count()
    active = db.query(User).filter(User.is_active == True).count()
    inactive = db.query(User).filter(User.is_active == False).count()

    users_by_role = {}
    for role in UserRole:
        count = db.query(User).filter(User.role == role).count()
        users_by_role[role.value] = count

    return UserStats(
        total_users=total,
        active_users=active,
        inactive_users=inactive,
        users_by_role=users_by_role,
    )


# ===================
# USER CRUD ENDPOINTS
# ===================

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search by email, first name, or last name"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_VIEW)),
):
    """List all users with optional filtering (requires USER_VIEW permission)."""
    query = db.query(User)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
            )
        )

    if role:
        query = query.filter(User.role == role)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return [user_to_response(u) for u in users]


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's information."""
    return user_to_response(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_VIEW)),
):
    """Get a specific user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user_to_response(user)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_CREATE)),
):
    """Create a new user (requires USER_CREATE permission)."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate password strength
    password = user_data.password
    if len(password) < 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 12 characters",
        )

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    if not (has_upper and has_lower and has_digit and has_special):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain uppercase, lowercase, digit, and special character",
        )

    # Only admins can create admin users
    if user_data.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create admin users",
        )

    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user_to_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_EDIT)),
):
    """Update a user (requires USER_EDIT permission)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent non-admins from promoting to admin
    if user_data.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can assign admin role",
        )

    # Prevent demoting the last admin
    if user.role == UserRole.ADMIN and user_data.role and user_data.role != UserRole.ADMIN:
        admin_count = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True
        ).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last admin user",
            )

    # Prevent self-deactivation for admins
    if user.id == current_user.id and user_data.is_active == False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user_to_response(user)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_MANAGE_ROLES)),
):
    """Update a user's role (requires USER_MANAGE_ROLES permission)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent non-admins from assigning admin role
    if role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can assign admin role",
        )

    # Prevent demoting the last admin
    if user.role == UserRole.ADMIN and role != UserRole.ADMIN:
        admin_count = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True
        ).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last admin user",
            )

    # Prevent self-demotion from admin
    if user.id == current_user.id and current_user.role == UserRole.ADMIN and role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin role",
        )

    user.role = role
    db.commit()
    db.refresh(user)

    return user_to_response(user)


@router.post("/bulk-role-update", response_model=List[UserResponse])
async def bulk_update_roles(
    data: BulkRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_MANAGE_ROLES)),
):
    """Bulk update user roles (requires USER_MANAGE_ROLES permission)."""
    # Prevent non-admins from assigning admin role
    if data.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can assign admin role",
        )

    updated_users = []
    for user_id in data.user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Skip if trying to demote last admin
            if user.role == UserRole.ADMIN and data.role != UserRole.ADMIN:
                admin_count = db.query(User).filter(
                    User.role == UserRole.ADMIN,
                    User.is_active == True
                ).count()
                if admin_count <= 1:
                    continue

            # Skip self-demotion
            if user.id == current_user.id and current_user.role == UserRole.ADMIN and data.role != UserRole.ADMIN:
                continue

            user.role = data.role
            updated_users.append(user)

    db.commit()
    return [user_to_response(u) for u in updated_users]


@router.patch("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_EDIT)),
):
    """Activate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = True
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    db.refresh(user)

    return user_to_response(user)


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_EDIT)),
):
    """Deactivate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent self-deactivation
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    # Prevent deactivating the last admin
    if user.role == UserRole.ADMIN:
        admin_count = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True
        ).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last admin user",
            )

    user.is_active = False
    db.commit()
    db.refresh(user)

    return user_to_response(user)


@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: UUID,
    data: PasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_MANAGE_ROLES)),
):
    """Reset a user's password (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can reset passwords",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate password strength
    password = data.new_password
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    if not (has_upper and has_lower and has_digit and has_special):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain uppercase, lowercase, digit, and special character",
        )

    user.password_hash = get_password_hash(data.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    return {"message": "Password reset successfully"}


@router.post("/me/change-password", response_model=dict)
async def change_my_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Change current user's password."""
    # Verify current password
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password strength
    password = data.new_password
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    if not (has_upper and has_lower and has_digit and has_special):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain uppercase, lowercase, digit, and special character",
        )

    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_DELETE)),
):
    """Delete a user (requires USER_DELETE permission)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Prevent deleting the last admin
    if user.role == UserRole.ADMIN:
        admin_count = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True
        ).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin user",
            )

    db.delete(user)
    db.commit()
