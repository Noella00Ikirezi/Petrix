"""Audit logs endpoints for admin viewing."""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.permissions import Permission
from app.infrastructure.database import get_db
from app.infrastructure.database.models import AuditLog, User
from app.api.v1.deps import require_permission

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None
    user_email: str | None = None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict
    ip_address: str | None
    user_agent: str | None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    items: List[AuditLogResponse]
    total: int


@router.get("", response_model=AuditLogList)
async def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AUDIT_LOG_VIEW)),
):
    """List audit logs with pagination and filters."""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    total = query.count()
    logs = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()

    items = []
    for log in logs:
        user_email = None
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            if user:
                user_email = user.email

        items.append(AuditLogResponse(
            id=str(log.id),
            user_id=str(log.user_id) if log.user_id else None,
            user_email=user_email,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details or {},
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            timestamp=log.timestamp,
        ))

    return AuditLogList(items=items, total=total)
