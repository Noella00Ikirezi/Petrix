"""Scan repository for vulnerability scanning."""

from typing import List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func

from .base_repository import BaseRepository
from ..models import Scan, ScanStatus, ScannerType


class ScanRepository(BaseRepository[Scan]):
    """Repository for Scan entity operations."""

    def __init__(self, session):
        super().__init__(session, Scan)

    def find_by_status(self, status: ScanStatus) -> List[Scan]:
        """Find scans by status."""
        stmt = select(Scan).where(Scan.status == status)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_scanner_type(self, scanner_type: ScannerType) -> List[Scan]:
        """Find scans by scanner type."""
        stmt = select(Scan).where(Scan.scanner_type == scanner_type)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_running(self) -> List[Scan]:
        """Find currently running scans."""
        stmt = select(Scan).where(Scan.status == ScanStatus.RUNNING)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_pending(self) -> List[Scan]:
        """Find pending scans."""
        stmt = select(Scan).where(Scan.status == ScanStatus.PENDING)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_recent(self, days: int = 7) -> List[Scan]:
        """Find scans from last N days."""
        since = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(Scan)
            .where(Scan.created_at >= since)
            .order_by(Scan.created_at.desc())
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_user(self, user_id: int) -> List[Scan]:
        """Find scans created by specific user."""
        stmt = (
            select(Scan)
            .where(Scan.created_by == user_id)
            .order_by(Scan.created_at.desc())
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def count_by_status(self) -> dict[ScanStatus, int]:
        """Count scans by status."""
        stmt = (
            select(Scan.status, func.count(Scan.id))
            .group_by(Scan.status)
        )
        result = self._session.execute(stmt)
        return {row[0]: row[1] for row in result}

    def count_by_scanner_type(self) -> dict[ScannerType, int]:
        """Count scans by scanner type."""
        stmt = (
            select(Scan.scanner_type, func.count(Scan.id))
            .group_by(Scan.scanner_type)
        )
        result = self._session.execute(stmt)
        return {row[0]: row[1] for row in result}

    def get_average_duration(self, scanner_type: Optional[ScannerType] = None) -> float:
        """Get average scan duration in seconds."""
        stmt = select(
            func.avg(
                func.julianday(Scan.completed_at) - func.julianday(Scan.started_at)
            ) * 86400
        ).where(
            and_(
                Scan.status == ScanStatus.COMPLETED,
                Scan.started_at.isnot(None),
                Scan.completed_at.isnot(None),
            )
        )

        if scanner_type:
            stmt = stmt.where(Scan.scanner_type == scanner_type)

        result = self._session.execute(stmt)
        avg = result.scalar()
        return float(avg) if avg else 0.0

    def start_scan(self, scan_id: int) -> Optional[Scan]:
        """Mark scan as started."""
        scan = self.get_by_id(scan_id)
        if scan:
            scan.status = ScanStatus.RUNNING
            scan.started_at = datetime.utcnow()
            self._session.flush()
        return scan

    def complete_scan(self, scan_id: int, findings_count: int = 0) -> Optional[Scan]:
        """Mark scan as completed."""
        scan = self.get_by_id(scan_id)
        if scan:
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            scan.findings_count = findings_count
            scan.progress = 100
            self._session.flush()
        return scan

    def fail_scan(self, scan_id: int, error_message: str) -> Optional[Scan]:
        """Mark scan as failed."""
        scan = self.get_by_id(scan_id)
        if scan:
            scan.status = ScanStatus.FAILED
            scan.completed_at = datetime.utcnow()
            scan.error_message = error_message
            self._session.flush()
        return scan

    def cancel_scan(self, scan_id: int) -> Optional[Scan]:
        """Mark scan as cancelled."""
        scan = self.get_by_id(scan_id)
        if scan:
            scan.status = ScanStatus.CANCELLED
            scan.completed_at = datetime.utcnow()
            self._session.flush()
        return scan

    def update_progress(self, scan_id: int, progress: int) -> Optional[Scan]:
        """Update scan progress (0-100)."""
        scan = self.get_by_id(scan_id)
        if scan:
            scan.progress = min(max(progress, 0), 100)
            self._session.flush()
        return scan

    def find_by_criteria(
        self,
        status: Optional[ScanStatus] = None,
        scanner_type: Optional[ScannerType] = None,
        created_by: Optional[int] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[Scan]:
        """Find scans by multiple criteria."""
        stmt = select(Scan)
        conditions = []

        if status:
            conditions.append(Scan.status == status)
        if scanner_type:
            conditions.append(Scan.scanner_type == scanner_type)
        if created_by:
            conditions.append(Scan.created_by == created_by)
        if since:
            conditions.append(Scan.created_at >= since)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Scan.created_at.desc()).limit(limit).offset(offset)
        result = self._session.execute(stmt)
        return list(result.scalars().all())
