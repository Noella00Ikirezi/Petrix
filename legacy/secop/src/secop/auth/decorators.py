"""Authorization decorators for permission checking."""

from functools import wraps
from typing import Callable, Any

from secop.core.exceptions import AuthenticationError, AuthorizationError
from .authorization import Permission, Role, get_auth_service


def require_authenticated(func: Callable) -> Callable:
    """
    Decorator that requires user to be authenticated.

    Raises:
        AuthenticationError: If user is not authenticated
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        auth_service = get_auth_service()
        if not auth_service.is_authenticated():
            raise AuthenticationError("Authentication required")
        return func(*args, **kwargs)

    return wrapper


def require_permission(*permissions: Permission) -> Callable:
    """
    Decorator that requires user to have specific permission(s).

    Args:
        permissions: One or more Permission values required

    Raises:
        AuthenticationError: If user is not authenticated
        AuthorizationError: If user lacks required permission
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            auth_service = get_auth_service()

            if not auth_service.is_authenticated():
                raise AuthenticationError("Authentication required")

            context = auth_service.get_context()

            # Check if user has all required permissions
            for perm in permissions:
                if not context.has_permission(perm):
                    raise AuthorizationError(
                        f"Permission required: {perm.name}"
                    )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(*permissions: Permission) -> Callable:
    """
    Decorator that requires user to have at least one of the permissions.

    Args:
        permissions: Permissions (any one is sufficient)

    Raises:
        AuthenticationError: If user is not authenticated
        AuthorizationError: If user lacks all permissions
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            auth_service = get_auth_service()

            if not auth_service.is_authenticated():
                raise AuthenticationError("Authentication required")

            context = auth_service.get_context()

            if not context.has_any_permission(*permissions):
                perm_names = ", ".join(p.name for p in permissions)
                raise AuthorizationError(
                    f"One of these permissions required: {perm_names}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles: Role) -> Callable:
    """
    Decorator that requires user to have specific role(s).

    Args:
        roles: One or more Role values (any one is sufficient)

    Raises:
        AuthenticationError: If user is not authenticated
        AuthorizationError: If user lacks required role
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            auth_service = get_auth_service()

            if not auth_service.is_authenticated():
                raise AuthenticationError("Authentication required")

            context = auth_service.get_context()

            if context.role not in roles:
                role_names = ", ".join(r.name for r in roles)
                raise AuthorizationError(
                    f"One of these roles required: {role_names}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_admin(func: Callable) -> Callable:
    """
    Decorator that requires user to be an admin.

    Raises:
        AuthenticationError: If user is not authenticated
        AuthorizationError: If user is not an admin
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        auth_service = get_auth_service()

        if not auth_service.is_authenticated():
            raise AuthenticationError("Authentication required")

        context = auth_service.get_context()

        if not context.is_admin():
            raise AuthorizationError("Administrator access required")

        return func(*args, **kwargs)

    return wrapper


def require_self_or_admin(user_id_param: str = "user_id") -> Callable:
    """
    Decorator that allows access if user is modifying their own data or is admin.

    Args:
        user_id_param: Name of the parameter containing the target user ID

    Raises:
        AuthenticationError: If user is not authenticated
        AuthorizationError: If user is not self or admin
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            auth_service = get_auth_service()

            if not auth_service.is_authenticated():
                raise AuthenticationError("Authentication required")

            context = auth_service.get_context()
            target_user_id = kwargs.get(user_id_param)

            if target_user_id is None:
                raise ValueError(f"Parameter '{user_id_param}' not found")

            # Allow if admin or self
            if context.is_admin() or context.user_id == target_user_id:
                return func(*args, **kwargs)

            raise AuthorizationError(
                "You can only modify your own data or be an administrator"
            )

        return wrapper

    return decorator
