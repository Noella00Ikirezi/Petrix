"""Audit repository for security audits."""

from typing import List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func

from .base_repository import BaseRepository
from ..models import Audit, AuditFinding, AuditStatus, AuditType, Criticality, AuditLog


class AuditRepository(BaseRepository[Audit]):
    """Repository for Audit entity operations."""

    def __init__(self, session):
        super().__init__(session, Audit)

    def find_by_type(self, audit_type: AuditType) -> List[Audit]:
        """Find audits by type."""
        stmt = select(Audit).where(Audit.audit_type == audit_type)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_status(self, status: AuditStatus) -> List[Audit]:
        """Find audits by status."""
        stmt = select(Audit).where(Audit.status == status)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_running(self) -> List[Audit]:
        """Find currently running audits."""
        stmt = select(Audit).where(Audit.status == AuditStatus.RUNNING)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_scheduled(self) -> List[Audit]:
        """Find scheduled audits."""
        stmt = select(Audit).where(Audit.status == AuditStatus.SCHEDULED)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_recent(self, days: int = 30) -> List[Audit]:
        """Find audits from last N days."""
        since = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(Audit)
            .where(Audit.created_at >= since)
            .order_by(Audit.created_at.desc())
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_user(self, user_id: int) -> List[Audit]:
        """Find audits created by specific user."""
        stmt = (
            select(Audit)
            .where(Audit.created_by == user_id)
            .order_by(Audit.created_at.desc())
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def count_by_type(self) -> dict[AuditType, int]:
        """Count audits by type."""
        stmt = (
            select(Audit.audit_type, func.count(Audit.id))
            .group_by(Audit.audit_type)
        )
        result = self._session.execute(stmt)
        return {row[0]: row[1] for row in result}

    def count_by_status(self) -> dict[AuditStatus, int]:
        """Count audits by status."""
        stmt = (
            select(Audit.status, func.count(Audit.id))
            .group_by(Audit.status)
        )
        result = self._session.execute(stmt)
        return {row[0]: row[1] for row in result}

    def start_audit(self, audit_id: int) -> Optional[Audit]:
        """Mark audit as started."""
        audit = self.get_by_id(audit_id)
        if audit:
            audit.status = AuditStatus.RUNNING
            audit.started_at = datetime.utcnow()
            self._session.flush()
        return audit

    def complete_audit(self, audit_id: int, findings_count: int = 0) -> Optional[Audit]:
        """Mark audit as completed."""
        audit = self.get_by_id(audit_id)
        if audit:
            audit.status = AuditStatus.COMPLETED
            audit.completed_at = datetime.utcnow()
            audit.findings_count = findings_count
            self._session.flush()
        return audit

    def fail_audit(self, audit_id: int, error_message: str) -> Optional[Audit]:
        """Mark audit as failed."""
        audit = self.get_by_id(audit_id)
        if audit:
            audit.status = AuditStatus.FAILED
            audit.completed_at = datetime.utcnow()
            audit.error_message = error_message
            self._session.flush()
        return audit

    def find_by_criteria(
        self,
        audit_type: Optional[AuditType] = None,
        status: Optional[AuditStatus] = None,
        created_by: Optional[int] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[Audit]:
        """Find audits by multiple criteria."""
        stmt = select(Audit)
        conditions = []

        if audit_type:
            conditions.append(Audit.audit_type == audit_type)
        if status:
            conditions.append(Audit.status == status)
        if created_by:
            conditions.append(Audit.created_by == created_by)
        if since:
            conditions.append(Audit.created_at >= since)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Audit.created_at.desc()).limit(limit).offset(offset)
        result = self._session.execute(stmt)
        return list(result.scalars().all())


class AuditFindingRepository(BaseRepository[AuditFinding]):
    """Repository for AuditFinding entity operations."""

    def __init__(self, session):
        super().__init__(session, AuditFinding)

    def find_by_audit(self, audit_id: int) -> List[AuditFinding]:
        """Find findings for specific audit."""
        stmt = select(AuditFinding).where(AuditFinding.audit_id == audit_id)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_severity(self, severity: Criticality) -> List[AuditFinding]:
        """Find findings by severity."""
        stmt = select(AuditFinding).where(AuditFinding.severity == severity)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_category(self, category: str) -> List[AuditFinding]:
        """Find findings by category."""
        stmt = select(AuditFinding).where(AuditFinding.category == category)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def count_by_severity(self, audit_id: Optional[int] = None) -> dict[Criticality, int]:
        """Count findings by severity."""
        stmt = (
            select(AuditFinding.severity, func.count(AuditFinding.id))
            .group_by(AuditFinding.severity)
        )
        if audit_id:
            stmt = stmt.where(AuditFinding.audit_id == audit_id)
        result = self._session.execute(stmt)
        return {row[0]: row[1] for row in result}

    def get_categories(self, audit_id: Optional[int] = None) -> List[str]:
        """Get distinct categories."""
        stmt = select(AuditFinding.category).distinct()
        if audit_id:
            stmt = stmt.where(AuditFinding.audit_id == audit_id)
        result = self._session.execute(stmt)
        return [row[0] for row in result]

    def find_by_criteria(
        self,
        audit_id: Optional[int] = None,
        severity: Optional[Criticality] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[AuditFinding]:
        """Find findings by multiple criteria."""
        stmt = select(AuditFinding)
        conditions = []

        if audit_id:
            conditions.append(AuditFinding.audit_id == audit_id)
        if severity:
            conditions.append(AuditFinding.severity == severity)
        if category:
            conditions.append(AuditFinding.category == category)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(AuditFinding.severity).limit(limit).offset(offset)
        result = self._session.execute(stmt)
        return list(result.scalars().all())


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog (action trail) operations."""

    def __init__(self, session):
        super().__init__(session, AuditLog)

    def find_by_user(self, user_id: int) -> List[AuditLog]:
        """Find logs for specific user."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp.desc())
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_action(self, action: str) -> List[AuditLog]:
        """Find logs by action type."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.timestamp.desc())
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_resource(self, resource_type: str, resource_id: Optional[int] = None) -> List[AuditLog]:
        """Find logs by resource."""
        stmt = select(AuditLog).where(AuditLog.resource_type == resource_type)
        if resource_id:
            stmt = stmt.where(AuditLog.resource_id == resource_id)
        stmt = stmt.order_by(AuditLog.timestamp.desc())
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_recent(self, hours: int = 24) -> List[AuditLog]:
        """Find recent logs."""
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            select(AuditLog)
            .where(AuditLog.timestamp >= since)
            .order_by(AuditLog.timestamp.desc())
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        user_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Create a new audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        return self.add(log)

    def find_by_criteria(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[AuditLog]:
        """Find logs by multiple criteria."""
        stmt = select(AuditLog)
        conditions = []

        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if since:
            conditions.append(AuditLog.timestamp >= since)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
        result = self._session.execute(stmt)
        return list(result.scalars().all())
