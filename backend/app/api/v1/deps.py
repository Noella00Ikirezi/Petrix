"""Dépendances FastAPI partagées : authentification JWT, session DB et contrôle d'accès RBAC.

Ce module est le point d'entrée unique pour l'injection de sécurité dans les routes API.
Les routes déclarent leurs exigences via ``Depends(get_current_user)`` ou
``Depends(require_permission(Permission.X))``, garantissant un contrôle d'accès
cohérent sans duplication de logique de validation.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_token
from app.core.permissions import Permission, has_permission
from app.infrastructure.database import get_db
from app.infrastructure.database.models import User

# tokenUrl est utilisé par Swagger UI pour générer le formulaire OAuth2 interactif.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login"
)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Résout l'utilisateur courant à partir du token JWT de la requête.

    Args:
        db: Session SQLAlchemy injectée par FastAPI.
        token: Token Bearer extrait de l'en-tête ``Authorization``.

    Returns:
        L'instance ``User`` correspondant au token validé et actif.

    Raises:
        HTTPException 401: Token absent, invalide, expiré ou révoqué (liste noire Redis).
        HTTPException 403: Compte utilisateur désactivé (``is_active = False``).

    Validation en trois étapes : (1) décodage JWT + vérification du type ``access``
    et de la liste noire, (2) présence de la claim ``sub``, (3) existence et activité
    du compte en base de données.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token, expected_type="access")
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Alias de ``get_current_user`` avec assertion explicite de l'état actif.

    Utilisé par les dépendances en chaîne qui ont besoin de ré-asserter l'activité
    du compte après d'éventuelles modifications en cours de cycle de requête.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_permission(permission: Permission):
    """Fabrique de dépendances FastAPI vérifiant une permission RBAC spécifique.

    Args:
        permission: La permission requise pour accéder à la route cible.

    Returns:
        Une dépendance injectable (closure) qui retourne l'utilisateur courant si
        autorisé, ou lève ``HTTPException 403`` dans le cas contraire.

    Utilisation dans une route :
        ``current_user: User = Depends(require_permission(Permission.ASSET_DELETE))``
    """
    def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )
        return current_user
    return permission_checker
