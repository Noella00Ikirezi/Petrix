"""Dashboard endpoints - Overview and metrics."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.infrastructure.database import get_db
from app.infrastructure.database.models import (
    Asset,
    AssetStatus,
    Vulnerability,
    VulnStatus,
    Severity,
    Scan,
    ScanStatus,
    User,
)
from app.api.v1.deps import require_permission

router = APIRouter()


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_assets: int
    active_assets: int
    total_vulnerabilities: int
    open_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    total_scans: int
    completed_scans: int
    running_scans: int
    average_score: float | None
    last_scan_date: str | None


class VulnTrend(BaseModel):
    date: str
    critical: int
    high: int
    medium: int
    low: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    vuln_by_severity: dict
    vuln_by_status: dict
    assets_by_type: dict
    recent_scans: list
    vuln_trends: list[VulnTrend]


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ASSET_VIEW)),
):
    """Get dashboard overview with key metrics."""

    # Assets stats
    total_assets = db.query(Asset).count()
    active_assets = db.query(Asset).filter(Asset.status == AssetStatus.ACTIVE).count()

    # Vulnerabilities stats
    total_vulns = db.query(Vulnerability).count()
    open_vulns = db.query(Vulnerability).filter(
        Vulnerability.status == VulnStatus.OPEN
    ).count()
    critical_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == Severity.CRITICAL,
        Vulnerability.status == VulnStatus.OPEN,
    ).count()
    high_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == Severity.HIGH,
        Vulnerability.status == VulnStatus.OPEN,
    ).count()

    # Scans stats
    total_scans = db.query(Scan).count()
    completed_scans = db.query(Scan).filter(Scan.status == ScanStatus.COMPLETED).count()
    running_scans = db.query(Scan).filter(Scan.status == ScanStatus.RUNNING).count()

    # Average score from completed scans
    avg_score_result = (
        db.query(func.avg(Scan.score))
        .filter(Scan.status == ScanStatus.COMPLETED, Scan.score.isnot(None))
        .scalar()
    )
    average_score = round(float(avg_score_result), 1) if avg_score_result else None

    # Last scan date
    last_scan = (
        db.query(Scan)
        .filter(Scan.status == ScanStatus.COMPLETED)
        .order_by(Scan.completed_at.desc())
        .first()
    )
    last_scan_date = last_scan.completed_at.isoformat() if last_scan and last_scan.completed_at else None

    # Vulnerabilities by severity
    vuln_by_severity = {}
    for severity in Severity:
        count = db.query(Vulnerability).filter(Vulnerability.severity == severity).count()
        vuln_by_severity[severity.value] = count

    # Vulnerabilities by status
    vuln_by_status = {}
    for status in VulnStatus:
        count = db.query(Vulnerability).filter(Vulnerability.status == status).count()
        vuln_by_status[status.value] = count

    # Assets by type
    assets_by_type = {}
    from app.infrastructure.database.models import AssetType
    for asset_type in AssetType:
        count = db.query(Asset).filter(Asset.asset_type == asset_type).count()
        if count > 0:
            assets_by_type[asset_type.value] = count

    # Recent scans (last 5)
    recent_scans = (
        db.query(Scan)
        .order_by(Scan.created_at.desc())
        .limit(5)
        .all()
    )
    recent_scans_data = [
        {
            "id": str(s.id),
            "name": s.name,
            "status": s.status.value,
            "grade": s.grade,
            "score": s.score,
            "created_at": s.created_at.isoformat(),
        }
        for s in recent_scans
    ]

    # Vulnerability trends (last 30 days)
    vuln_trends = []
    today = datetime.utcnow().date()
    for i in range(30, -1, -1):
        date = today - timedelta(days=i)
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())

        # Count vulns discovered up to this date that were still open at that point
        # For simplicity, we count vulns discovered by this date
        critical = db.query(Vulnerability).filter(
            Vulnerability.severity == Severity.CRITICAL,
            Vulnerability.discovered_at <= date_end,
        ).count()
        high = db.query(Vulnerability).filter(
            Vulnerability.severity == Severity.HIGH,
            Vulnerability.discovered_at <= date_end,
        ).count()
        medium = db.query(Vulnerability).filter(
            Vulnerability.severity == Severity.MEDIUM,
            Vulnerability.discovered_at <= date_end,
        ).count()
        low = db.query(Vulnerability).filter(
            Vulnerability.severity == Severity.LOW,
            Vulnerability.discovered_at <= date_end,
        ).count()

        vuln_trends.append(VulnTrend(
            date=date.isoformat(),
            critical=critical,
            high=high,
            medium=medium,
            low=low,
        ))

    stats = DashboardStats(
        total_assets=total_assets,
        active_assets=active_assets,
        total_vulnerabilities=total_vulns,
        open_vulnerabilities=open_vulns,
        critical_vulnerabilities=critical_vulns,
        high_vulnerabilities=high_vulns,
        total_scans=total_scans,
        completed_scans=completed_scans,
        running_scans=running_scans,
        average_score=average_score,
        last_scan_date=last_scan_date,
    )

    return DashboardResponse(
        stats=stats,
        vuln_by_severity=vuln_by_severity,
        vuln_by_status=vuln_by_status,
        assets_by_type=assets_by_type,
        recent_scans=recent_scans_data,
        vuln_trends=vuln_trends,
    )
