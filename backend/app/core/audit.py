"""Audit logging helper."""
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
    """Create an audit log entry."""
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
