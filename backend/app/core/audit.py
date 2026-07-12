"""Utilitaire de journalisation des événements d'audit métier.

Découple l'écriture des entrées d'audit de la logique métier : chaque route ou
service appelle ``log_audit_event`` sans connaître le schéma de la table sous-jacente.
Toutes les opérations sensibles (connexion, suppression, changement de rôle…)
doivent transiter par cette fonction pour garantir la traçabilité.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from app.infrastructure.database.models import AuditLog


def log_audit_event(
    db: Session,
    action: str,
    resource_type: str,
    user_id: Optional[UUID] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Crée et persiste une entrée dans le journal d'audit.

    Args:
        db: Session SQLAlchemy active fournie par injection de dépendances.
        action: Libellé de l'action effectuée (ex. ``"user.login"``, ``"asset.delete"``).
        resource_type: Type de la ressource concernée (ex. ``"user"``, ``"scan"``).
        user_id: Identifiant de l'utilisateur à l'origine de l'action ; ``None``
            pour les événements système non authentifiés.
        resource_id: Identifiant (sous forme de chaîne) de la ressource cible.
        details: Données contextuelles libres sérialisées en JSON (diff, raison…).
        ip_address: Adresse IP du client, extraite de la requête HTTP.
        user_agent: En-tête ``User-Agent`` du client.

    Returns:
        L'instance ``AuditLog`` créée et commitée.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    db.commit()
    return entry
