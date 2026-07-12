"""Endpoints de gestion des utilisateurs : CRUD, attribution des rôles, permissions et mots de passe.
Protégé par les permissions USER_* ; la promotion vers le rôle ADMIN est réservée exclusivement aux ADMIN.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.security import get_password_hash, verify_password
from app.core.permissions import Permission, UserRole, get_role_permissions, has_permission
from app.core.audit import log_audit_event
from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.v1.deps import get_current_active_user, require_permission

router = APIRouter()


# ===================
# SCHEMAS
# ===================

class PermissionInfo(BaseModel):
    """Détails d'une permission RBAC : nom technique, valeur, catégorie et description."""
    name: str
    value: str
    category: str
    description: str


class RoleInfo(BaseModel):
    """Rôle avec ses permissions associées et le nombre d'utilisateurs qui le possèdent."""
    name: str
    value: str
    description: str
    permissions: List[str]
    user_count: int = 0


class UserResponse(BaseModel):
    """Représentation complète d'un utilisateur retournée par l'API, incluant ses permissions effectives."""
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    is_active: bool
    must_change_password: bool = False
    last_login: datetime | None = None
    created_at: datetime | None = None
    permissions: List[str] = []
    avatar_url: str | None = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Corps de la requête POST /users : création d'un compte par un admin, rôle requis, mot de passe temporaire auto-généré."""
    email: EmailStr
    role: UserRole = UserRole.VIEWER
    first_name: str | None = None
    last_name: str | None = None


class UserUpdate(BaseModel):
    """Payload de mise à jour d'un utilisateur par un ADMIN (prénom, nom, rôle, statut actif)."""
    first_name: str | None = None
    last_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class PasswordChange(BaseModel):
    """Payload de changement de mot de passe à l'initiative de l'utilisateur (ancien + nouveau)."""
    current_password: str
    new_password: str = Field(..., min_length=12, description="Password must be at least 12 characters")


class PasswordReset(BaseModel):
    """Payload de réinitialisation de mot de passe par un ADMIN."""
    new_password: str = Field(..., min_length=12, description="Password must be at least 12 characters")


class BulkRoleUpdate(BaseModel):
    """Payload de mise à jour en lot du rôle pour une liste d'utilisateurs."""
    user_ids: List[UUID]
    role: UserRole


class UserStats(BaseModel):
    """Statistiques des comptes utilisateurs : total, actifs, inactifs et répartition par rôle."""
    total_users: int
    active_users: int
    inactive_users: int
    users_by_role: dict


# Descriptions des permissions exposées dans la réponse de l'endpoint GET /users/permissions
PERMISSION_DESCRIPTIONS = {
    # Actifs
    "asset:view": "Consulter les actifs et leurs détails",
    "asset:create": "Créer de nouveaux actifs",
    "asset:edit": "Modifier les actifs existants",
    "asset:delete": "Supprimer des actifs",
    "asset:export": "Exporter les données d'inventaire",
    # Vulnérabilités
    "vuln:view": "Consulter les vulnérabilités",
    "vuln:create": "Créer des entrées de vulnérabilité",
    "vuln:edit": "Modifier les détails d'une vulnérabilité",
    "vuln:resolve": "Marquer des vulnérabilités comme résolues",
    "vuln:delete": "Supprimer des vulnérabilités",
    "vuln:export": "Exporter les données de vulnérabilités",
    # Scans
    "scan:view": "Consulter les résultats de scans",
    "scan:create": "Créer de nouveaux scans",
    "scan:execute": "Démarrer et annuler des scans",
    "scan:configure": "Configurer les paramètres de scan",
    "scan:delete": "Supprimer des scans",
    # Conformité
    "compliance:view": "Consulter l'état de conformité",
    "compliance:assess": "Réaliser des évaluations de conformité",
    "compliance:edit": "Modifier les données de conformité",
    "compliance:export": "Exporter les rapports de conformité",
    # Fournisseurs
    "supplier:view": "Consulter les informations fournisseurs",
    "supplier:create": "Ajouter de nouveaux fournisseurs",
    "supplier:edit": "Modifier les détails d'un fournisseur",
    "supplier:delete": "Supprimer des fournisseurs",
    "supplier:assess": "Évaluer le risque fournisseur",
    # Rapports
    "report:view": "Consulter les rapports",
    "report:create": "Générer des rapports",
    "report:export": "Exporter des rapports",
    # Utilisateurs
    "user:view": "Consulter la liste et le détail des utilisateurs",
    "user:create": "Créer de nouveaux comptes utilisateurs",
    "user:edit": "Modifier les informations d'un utilisateur",
    "user:delete": "Supprimer des comptes utilisateurs",
    "user:manage_roles": "Gérer les rôles et permissions des utilisateurs",
    # Paramètres
    "settings:view": "Consulter les paramètres système",
    "settings:edit": "Modifier les paramètres système",
    # Audit
    "audit_log:view": "Consulter les journaux d'audit",
    # Système
    "system:admin": "Administration complète du système",
    "system:settings": "Gérer les paramètres système globaux",
}

ROLE_DESCRIPTIONS = {
    UserRole.VIEWER:  "Accès en lecture seule aux actifs, vulnérabilités, scans et rapports",
    UserRole.ANALYST: "Création et modification d'actifs et de vulnérabilités, exécution de scans et génération de rapports",
    UserRole.AUDITOR: "Capacités d'audit complètes incluant l'évaluation de conformité et l'accès aux journaux d'audit",
    UserRole.ADMIN:   "Accès total au système avec gestion des utilisateurs et administration globale",
}


# ===================
# HELPER FUNCTIONS
# ===================

def get_permission_category(permission_value: str) -> str:
    """Extrait la catégorie (préfixe avant ':') d'une valeur de permission et la met en forme titre."""
    return permission_value.split(":")[0].replace("_", " ").title()


def user_to_response(user: User) -> UserResponse:
    """Convertit un objet ORM User en UserResponse en incluant ses permissions effectives selon son rôle."""
    permissions = [p.value for p in get_role_permissions(user.role)]
    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        last_login=user.last_login,
        created_at=user.created_at,
        permissions=permissions,
        avatar_url=user.avatar_url,
    )


# ===================
# ROLES & PERMISSIONS ENDPOINTS
# ===================

@router.get("/roles", response_model=List[RoleInfo])
async def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Liste tous les rôles disponibles avec leurs permissions associées et le nombre d'utilisateurs — accessible à tout utilisateur authentifié."""
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
    """Retourne le détail d'un rôle par sa valeur (viewer/analyst/auditor/admin) — accessible à tout utilisateur authentifié."""
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
    """Liste toutes les permissions RBAC disponibles avec leur catégorie et description — accessible à tout utilisateur authentifié."""
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
    """Retourne la liste des permissions effectives de l'utilisateur courant selon son rôle."""
    return [p.value for p in get_role_permissions(current_user.role)]


@router.get("/permissions/check/{permission}")
async def check_permission(
    permission: str,
    current_user: User = Depends(get_current_active_user),
):
    """Vérifie si l'utilisateur courant possède une permission spécifique et retourne le résultat booléen."""
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
    """Retourne les statistiques des comptes utilisateurs — réservé aux rôles possédant USER_VIEW."""
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

@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search by email, first name, or last name"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_VIEW)),
):
    """Liste tous les utilisateurs avec filtres optionnels (recherche, rôle, statut actif) — réservé USER_VIEW."""
    query = db.query(User)

    # Application des filtres de recherche
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
    """Retourne le profil complet de l'utilisateur connecté avec ses permissions effectives."""
    return user_to_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Met à jour le prénom et le nom de l'utilisateur connecté — le rôle ne peut pas être modifié ici."""
    if user_data.first_name is not None:
        current_user.first_name = user_data.first_name
    if user_data.last_name is not None:
        current_user.last_name = user_data.last_name
    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)


class AvatarUpdate(BaseModel):
    """Corps de la requête PUT /users/me/avatar : data URL base64 de la nouvelle image de profil (ou None pour supprimer)."""

    avatar_url: str | None = None


@router.put("/me/avatar", response_model=UserResponse)
async def update_my_avatar(
    body: AvatarUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Met à jour ou supprime l'avatar de l'utilisateur connecté — accepte une data URL base64 (max ~200 Ko)."""
    if body.avatar_url is not None:
        if len(body.avatar_url) > 300_000:
            raise HTTPException(status_code=413, detail="Image trop grande (max 200 KB)")
        if body.avatar_url and not body.avatar_url.startswith("data:image/"):
            raise HTTPException(status_code=400, detail="Format invalide — data URL attendue")
    current_user.avatar_url = body.avatar_url
    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_VIEW)),
):
    """Retourne le profil d'un utilisateur par son UUID — réservé USER_VIEW."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user_to_response(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_CREATE)),
):
    """Invite un utilisateur : génère un mot de passe temporaire, crée le compte et envoie un e-mail d'invitation — réservé USER_CREATE (ADMIN pour créer un ADMIN)."""
    import secrets
    import string
    from app.workers.email_tasks import send_invitation_email_task

    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if user_data.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create admin users",
        )

    # Générer un mot de passe temporaire sécurisé
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    temp_password = "".join(secrets.choice(alphabet) for _ in range(16))

    user = User(
        email=user_data.email,
        password_hash=get_password_hash(temp_password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Envoyer l'email d'invitation avec le mot de passe temporaire
    display_name = f"{user_data.first_name or ''} {user_data.last_name or ''}".strip() or user_data.email
    origin = request.headers.get("origin", "https://petrix.noellahome.org")
    login_url = f"{origin}/login"

    try:
        send_invitation_email_task.delay(
            user_data.email,
            display_name,
            temp_password,
            user_data.role.value,
            login_url,
        )
    except Exception:
        pass  # Ne pas bloquer la création si l'email échoue

    return user_to_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_EDIT)),
):
    """Met à jour un utilisateur (prénom, nom, rôle, statut actif) avec protection du dernier ADMIN — réservé USER_EDIT."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Interdire la promotion au rôle ADMIN par un non-admin
    if user_data.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can assign admin role",
        )

    # Protéger le dernier compte ADMIN contre toute rétrogradation
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

    # Interdire l'auto-désactivation d'un compte admin
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
    """Modifie le rôle d'un utilisateur avec protection du dernier ADMIN et journalisation — réservé USER_MANAGE_ROLES."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Interdire l'attribution du rôle ADMIN par un non-admin
    if role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can assign admin role",
        )

    # Protéger le dernier compte ADMIN contre toute rétrogradation
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

    # Interdire l'auto-rétrogradation depuis le rôle ADMIN
    if user.id == current_user.id and current_user.role == UserRole.ADMIN and role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin role",
        )

    old_role = user.role.value
    user.role = role
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db, action="change_role", resource_type="user",
        user_id=current_user.id, resource_id=str(user_id),
        details={"target_email": user.email, "old_role": old_role, "new_role": role.value},
    )

    return user_to_response(user)


@router.post("/bulk-role-update", response_model=List[UserResponse])
async def bulk_update_roles(
    data: BulkRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_MANAGE_ROLES)),
):
    """Met à jour en lot le rôle d'une liste d'utilisateurs en ignorant les cas protégés (dernier ADMIN, auto-rétrogradation) — réservé USER_MANAGE_ROLES."""
    # Interdire l'attribution en lot du rôle ADMIN par un non-admin
    if data.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can assign admin role",
        )

    updated_users = []
    for user_id in data.user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Ignorer si la rétrogradation toucherait le dernier admin
            if user.role == UserRole.ADMIN and data.role != UserRole.ADMIN:
                admin_count = db.query(User).filter(
                    User.role == UserRole.ADMIN,
                    User.is_active == True
                ).count()
                if admin_count <= 1:
                    continue

            # Ignorer l'auto-rétrogradation
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
    """Réactive un compte utilisateur désactivé et remet à zéro son compteur d'échecs de connexion — réservé USER_EDIT."""
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

    log_audit_event(
        db=db, action="activate_user", resource_type="user",
        user_id=current_user.id, resource_id=str(user_id),
        details={"target_email": user.email},
    )

    return user_to_response(user)


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_EDIT)),
):
    """Désactive un compte utilisateur avec protection du dernier ADMIN et de l'auto-désactivation — réservé USER_EDIT."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Interdire l'auto-désactivation
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    # Protéger le dernier compte ADMIN actif contre la désactivation
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

    log_audit_event(
        db=db, action="deactivate_user", resource_type="user",
        user_id=current_user.id, resource_id=str(user_id),
        details={"target_email": user.email},
    )

    return user_to_response(user)


@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: UUID,
    data: PasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_MANAGE_ROLES)),
):
    """Réinitialise le mot de passe d'un utilisateur après validation de la complexité — réservé exclusivement aux ADMIN."""
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

    # Vérification de la complexité : majuscule, minuscule, chiffre et caractère spécial requis
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

    log_audit_event(
        db=db, action="reset_password", resource_type="user",
        user_id=current_user.id, resource_id=str(user_id),
        details={"target_email": user.email},
    )

    return {"message": "Password reset successfully"}


@router.post("/me/change-password", response_model=dict)
async def change_my_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Modifie le mot de passe de l'utilisateur connecté après vérification de l'ancien mot de passe et de la complexité du nouveau."""
    # Vérification de l'ancien mot de passe avant la mise à jour
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Vérification de la complexité du nouveau mot de passe
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

    log_audit_event(
        db=db, action="change_password", resource_type="user",
        user_id=current_user.id, resource_id=str(current_user.id),
    )

    return {"message": "Password changed successfully"}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_DELETE)),
):
    """Supprime définitivement un compte utilisateur avec protection du dernier ADMIN et de l'auto-suppression — réservé USER_DELETE."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Interdire l'auto-suppression du compte courant
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Protéger le dernier compte ADMIN actif contre la suppression
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

    target_email = user.email
    db.delete(user)
    db.commit()

    log_audit_event(
        db=db, action="delete_user", resource_type="user",
        user_id=current_user.id, resource_id=str(user_id),
        details={"target_email": target_email},
    )
