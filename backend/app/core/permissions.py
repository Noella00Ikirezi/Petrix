"""Modèle de contrôle d'accès basé sur les rôles (RBAC) de la plateforme Petrix.

Définit quatre rôles (VIEWER < ANALYST < AUDITOR < ADMIN) et associe à chacun
un ensemble explicite de permissions granulaires. Les permissions suivent la
convention ``ressource:action``. Les ensembles de permissions sont énumérés
explicitement (sans héritage par code) afin qu'ajouter une permission à un rôle
inférieur ne l'accorde pas silencieusement vers le haut.
"""
from enum import Enum
from typing import Set


class UserRole(str, Enum):
    """Rôles de la plateforme, ordonnés du moins au plus privilégié.

    L'héritage de ``str`` autorise la sérialisation JSON directe et le stockage
    SQLAlchemy sans adaptateur de type personnalisé.
    """
    VIEWER = "viewer"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    ADMIN = "admin"


class Permission(str, Enum):
    """Jetons de capacité atomiques suivant le schéma ``ressource:action``.

    Chaque valeur est stockée telle quelle dans les claims JWT et les messages
    d'erreur HTTP ; les noms doivent donc rester stables entre les versions.
    """
    # Actifs
    ASSET_VIEW = "asset:view"
    ASSET_CREATE = "asset:create"
    ASSET_EDIT = "asset:edit"
    ASSET_DELETE = "asset:delete"
    ASSET_EXPORT = "asset:export"

    # Vulnérabilités
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

    # Conformité
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_ASSESS = "compliance:assess"
    COMPLIANCE_EDIT = "compliance:edit"
    COMPLIANCE_EXPORT = "compliance:export"

    # Fournisseurs
    SUPPLIER_VIEW = "supplier:view"
    SUPPLIER_CREATE = "supplier:create"
    SUPPLIER_EDIT = "supplier:edit"
    SUPPLIER_DELETE = "supplier:delete"
    SUPPLIER_ASSESS = "supplier:assess"

    # Rapports
    REPORT_VIEW = "report:view"
    REPORT_CREATE = "report:create"
    REPORT_EXPORT = "report:export"

    # Utilisateurs
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_EDIT = "user:edit"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"

    # Paramètres
    SETTINGS_VIEW = "settings:view"
    SETTINGS_EDIT = "settings:edit"

    # Journaux d'audit
    AUDIT_LOG_VIEW = "audit_log:view"

    # Système
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_SETTINGS = "system:settings"

    # Pentest
    PENTEST_VIEW = "pentest:view"
    PENTEST_EXECUTE = "pentest:execute"
    PENTEST_CONFIGURE = "pentest:configure"
    PENTEST_DELETE = "pentest:delete"
    PENTEST_REPORT_EXPORT = "pentest:report_export"


# Ensembles de permissions par rôle (explicites, non hérités par code).
# ADMIN utilise ``*Permission`` (dépaquetage de l'enum) pour inclure
# automatiquement toute permission ajoutée à l'avenir.
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.VIEWER: {
        Permission.ASSET_VIEW,
        Permission.VULN_VIEW,
        Permission.SCAN_VIEW,
        Permission.COMPLIANCE_VIEW,
        Permission.SUPPLIER_VIEW,
        Permission.REPORT_VIEW,
        Permission.PENTEST_VIEW,
    },
    UserRole.ANALYST: {
        # Toutes les permissions VIEWER
        Permission.ASSET_VIEW,
        Permission.VULN_VIEW,
        Permission.SCAN_VIEW,
        Permission.COMPLIANCE_VIEW,
        Permission.SUPPLIER_VIEW,
        Permission.REPORT_VIEW,
        # Ajouts ANALYST : création/édition/exécution, sans opérations destructives
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
        Permission.PENTEST_VIEW,
        Permission.PENTEST_EXECUTE,
        Permission.PENTEST_REPORT_EXPORT,
    },
    UserRole.AUDITOR: {
        # Toutes les permissions ANALYST
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
        # Ajouts AUDITOR : lecture utilisateurs et journal d'audit, pentest complet
        Permission.AUDIT_LOG_VIEW,
        Permission.USER_VIEW,
        Permission.PENTEST_VIEW,
        Permission.PENTEST_EXECUTE,
        Permission.PENTEST_CONFIGURE,
        Permission.PENTEST_REPORT_EXPORT,
    },
    UserRole.ADMIN: {
        # Inclut dynamiquement chaque membre présent et futur de Permission
        *Permission,
    },
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Retourne True si ``role`` possède la ``permission`` demandée."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_any_permission(role: UserRole, permissions: Set[Permission]) -> bool:
    """Retourne True si ``role`` détient au moins une permission parmi ``permissions``.

    Utilise l'intersection d'ensembles pour une complexité O(min(|rôle|, |demande|)).
    """
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return bool(role_perms & permissions)


def get_role_permissions(role: UserRole) -> Set[Permission]:
    """Retourne l'ensemble complet des permissions de ``role``, ou un ensemble vide si inconnu."""
    return ROLE_PERMISSIONS.get(role, set())
